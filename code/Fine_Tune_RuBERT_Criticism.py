#!/usr/bin/env python3
"""
ruBERT Criticism Classifier — Training Script
==============================================

This script fine-tunes DeepPavlov/rubert-base-cased on a labeled dataset of Russian Telegram messages
to classify whether a message contains criticism of Russian authorities.


"""

import os
import json
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

import torch
from datasets import Dataset
from transformers import (
    BertTokenizer,
    BertForSequenceClassification,
    Trainer,
    TrainingArguments,
)

# ========================
# CONFIGURATION
# ========================
DATA_PATH = "data/Training_Dataset.csv"   # expects columns: message, is_criticism
OUTPUT_DIR = "outputs"
MODEL_DIR = os.path.join(OUTPUT_DIR, "models", "rubert_criticism_classifier")

RANDOM_SEED = 42
MAX_LEN = 128
BATCH_SIZE = 8
EPOCHS = 3
LR = 2e-5
WEIGHT_DECAY = 0.01
THRESHOLD = 0.5  # probability threshold for label=1


def ensure_dirs():
    """Create output directories if they don’t exist."""
    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_data(path: str) -> pd.DataFrame:
    """Load CSV dataset and prepare text/labels."""
    df = pd.read_csv(path)
    if not {"message", "is_criticism"}.issubset(df.columns):
        raise ValueError("Dataset must contain 'message' and 'is_criticism' columns.")

    df = df[["message", "is_criticism"]].dropna()
    df["message"] = df["message"].astype(str).str.strip()
    df = df[df["message"] != ""]
    df["is_criticism"] = df["is_criticism"].astype(int)

    return df


def make_hf_datasets(df: pd.DataFrame):
    """Split dataset into train/test and convert to Hugging Face Datasets."""
    train_texts, test_texts, train_labels, test_labels = train_test_split(
        df["message"].tolist(),
        df["is_criticism"].tolist(),
        test_size=0.2,
        stratify=df["is_criticism"],
        random_state=RANDOM_SEED,
    )

    train_ds = Dataset.from_dict({"text": train_texts, "label": train_labels})
    test_ds = Dataset.from_dict({"text": test_texts, "label": test_labels})
    return train_ds, test_ds, test_texts


def tokenize_datasets(train_ds: Dataset, test_ds: Dataset, tokenizer):
    """Tokenize texts and convert to Torch format."""
    def _tok(ex):
        return tokenizer(ex["text"], padding="max_length", truncation=True, max_length=MAX_LEN)

    train_ds = train_ds.map(_tok, batched=True).remove_columns(["text"])
    test_ds  = test_ds.map(_tok, batched=True).remove_columns(["text"])
    train_ds.set_format("torch")
    test_ds.set_format("torch")
    return train_ds, test_ds


def main():
    ensure_dirs()
    os.environ["WANDB_DISABLED"] = "true"
    torch.manual_seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    print(f" Loading dataset from: {DATA_PATH}")
    df = load_data(DATA_PATH)
    print(f"Loaded {len(df)} samples")

    # --- Split and tokenize ---
    train_ds, test_ds, test_texts = make_hf_datasets(df)
    tokenizer = BertTokenizer.from_pretrained("DeepPavlov/rubert-base-cased")
    train_ds, test_ds = tokenize_datasets(train_ds, test_ds, tokenizer)

    # --- Model and training setup ---
    model = BertForSequenceClassification.from_pretrained(
        "DeepPavlov/rubert-base-cased", num_labels=2
    )

    args = TrainingArguments(
        output_dir=os.path.join(OUTPUT_DIR, "results"),
        evaluation_strategy="epoch",
        save_strategy="epoch",
        learning_rate=LR,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        num_train_epochs=EPOCHS,
        weight_decay=WEIGHT_DECAY,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        logging_steps=50,
        save_total_limit=2,
        report_to=[],
        seed=RANDOM_SEED,
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=test_ds,
        tokenizer=tokenizer,
    )

    # --- Training ---
    print(" Training started...")
    trainer.train()

    model.save_pretrained(MODEL_DIR)
    tokenizer.save_pretrained(MODEL_DIR)
    print(f" Model saved to: {MODEL_DIR}")

    # --- Evaluation ---
    pred = trainer.predict(test_ds)
    y_true = pred.label_ids.astype(int)
    logits = pred.predictions
    probs = torch.softmax(torch.tensor(logits), dim=-1).numpy()[:, 1]
    y_hat = (probs >= THRESHOLD).astype(int)

    report = classification_report(y_true, y_hat, digits=3, output_dict=True)
    cm = confusion_matrix(y_true, y_hat).tolist()

    with open(os.path.join(OUTPUT_DIR, "rubert_test_classification_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    with open(os.path.join(OUTPUT_DIR, "rubert_test_confusion_matrix.json"), "w", encoding="utf-8") as f:
        json.dump({"confusion_matrix": cm, "labels": [0, 1]}, f, ensure_ascii=False, indent=2)

    # --- FP / FN / TP / TN ---
    df_pred = pd.DataFrame({
        "text": test_texts,
        "true_label": y_true,
        "pred_label": y_hat,
        "prob_criticism": probs,
    })

    def etype(row):
        if row.true_label == 1 and row.pred_label == 1: return "TP"
        if row.true_label == 0 and row.pred_label == 0: return "TN"
        if row.true_label == 0 and row.pred_label == 1: return "FP"
        if row.true_label == 1 and row.pred_label == 0: return "FN"
    df_pred["case_type"] = df_pred.apply(etype, axis=1)

    def top_k(df_local, k=10, by="prob_criticism", ascending=False):
        return df_local.sort_values(by=by, ascending=ascending).head(k)

    FP = top_k(df_pred[df_pred["case_type"] == "FP"], k=10, ascending=False)
    FN = top_k(df_pred[df_pred["case_type"] == "FN"], k=10, ascending=True)
    TP = top_k(df_pred[df_pred["case_type"] == "TP"], k=10, ascending=False)
    TN = top_k(df_pred[df_pred["case_type"] == "TN"], k=10, ascending=True)

    df_pred.to_csv(os.path.join(OUTPUT_DIR, "rubert_test_predictions_all.csv"), index=False)
    FP.to_csv(os.path.join(OUTPUT_DIR, "rubert_examples_FP_top.csv"), index=False)
    FN.to_csv(os.path.join(OUTPUT_DIR, "rubert_examples_FN_top.csv"), index=False)
    TP.to_csv(os.path.join(OUTPUT_DIR, "rubert_examples_TP_top.csv"), index=False)
    TN.to_csv(os.path.join(OUTPUT_DIR, "rubert_examples_TN_top.csv"), index=False)

    print("\n Training complete. Reports and examples saved to:")
    print(f"{OUTPUT_DIR}/rubert_test_classification_report.json")
    print(f"{OUTPUT_DIR}/rubert_test_confusion_matrix.json")
    print(f"FP/FN/TP/TN CSV files in {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
