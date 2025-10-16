#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Rule-based detection of political criticism in Telegram messages.
This script reads text data from a PostgreSQL database and flags messages
that express criticism toward Russian leadership using lexical and syntactic rules.
"""

import os
import sys
import pickle
import pandas as pd
from tqdm import tqdm
import spacy
from spacy.matcher import PhraseMatcher
import psycopg2

# ========= DATABASE CONFIGURATION =========
def _get_env_required(name: str) -> str:
    val = os.getenv(name)
    if not val:
        sys.exit(f"Environment variable {name} is required but not set.")
    return val

PGHOST = _get_env_required("PGHOST")
PGPORT = int(_get_env_required("PGPORT"))
PGDB   = _get_env_required("PGDATABASE")
PGUSER = _get_env_required("PGUSER")
PGPASS = _get_env_required("PGPASSWORD")

# Optional filter variable
CHANNEL_ID = os.getenv("CHANNEL_ID")  # if not set → all channels included

# ========= SQL QUERY =========
# Reads text from `messages` (if present) or `message` column.
# Applies optional filtering by channel_id if provided
QUERY_BASE = """
SELECT
  COALESCE(messages, message) AS message,
  "time",
  channel_id
FROM public.telegram_data
WHERE "time" >= TIMESTAMP '2022-02-22 00:00:00'
{channel_filter}
ORDER BY "time" ASC
"""

def build_query() -> str:
    """Constructs SQL query with optional channel_id filtering."""
    if CHANNEL_ID:
        return QUERY_BASE.format(channel_filter="AND channel_id = %s")
    else:
        return QUERY_BASE.format(channel_filter="")


# ========= LEXICAL DICTIONARIES =========
MULTIWORD_SUBJECTS = [
    "администрация президента", "режим путина", "министерство обороны",
    "спикер госдумы", "единая россия", "путинский режим",
    "власти рф", "силовой блок", "наше руководство", "наша власть", "партия страха"
]

SINGLEWORD_SUBJECTS = [
    "путин", "кремль", "минобороны", "шойгу",  "лавров", "патрушев", "силовики",
    "госдума", "медведев", "мишустин", "фсб", "мвд", "единоросы",
    "дегенералы", "набулина", "мантуров", "песков", "охранители"
]

NEGATIVE_LEMMAS = {
    "предавать", "сливать", "трусить", "бояться", "тянуть", "молчать", "оправдываться", "сдавать",
    "отступать", "обманывать", "прикрываться", "мешать", "медлить", "врать", "запаздывать",
    "игнорировать", "прятаться", "провалить", "саботировать", "замалчивать", "бездействовать", "зажраться",
    "трусливый", "нерешительный", "медлительный", "пассивный", "слабый", "бессильный", "виновный",
    "неадекватный", "отстранённый", "глухой", "виноватый", "коррумпированный", "провальный",
    "ничтожный", "смешной", "жалкий", "некомпетентный", "преступный", "плохой", "продажный",
    "договорняк", "провал", "ошибка", "враньё", "вранье", "бездействие", "некомпетентность", "позор",
    "неспособность", "безответственность", "беспредел", "коррупция", "предательство",
    "кризис", "развал", "крах", "беззаконие", "несправедливость", "кумовство", "бардак", "казнокрадство",
    "обман", "ложь", "обрушение", "наглость", "недееспособность", "общак", "идиотизм", "заговор", "измена"
}

NEGATIVE_VERBS_WITH_NOT = {"мочь", "решаться", "вмешиваться", "отвечать", "справляться"}
PRONOUNS = {"он", "она", "они", "его", "её", "их", "ему", "ей", "им", "них"}

# ========= SPACY INITIALIZATION =========
nlp = spacy.load("ru_core_news_lg")
phrase_matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
phrase_patterns = [nlp(text) for text in MULTIWORD_SUBJECTS]
phrase_matcher.add("MULTI_SUBJECT", phrase_patterns)

def contains_multiword_subject(doc):
    return len(phrase_matcher(doc)) > 0

def criticism_targeting_subject(doc):
    """Check if a message contains negative expressions directed at leadership-related subjects."""
    for token in doc:
        lemma = token.lemma_.lower()
        if lemma in NEGATIVE_LEMMAS or (
            lemma in NEGATIVE_VERBS_WITH_NOT and token.i > 0 and doc[token.i - 1].text.lower() == "не"
        ):
            for child in token.children:
                if child.lemma_.lower() in SINGLEWORD_SUBJECTS or child.text.lower() in PRONOUNS:
                    return True
            for ancestor in token.ancestors:
                if ancestor.lemma_.lower() in SINGLEWORD_SUBJECTS or ancestor.text.lower() in PRONOUNS:
                    return True
    return False

def is_criticism_of_russian_leadership_spacy(text):
    """Return True if message contains criticism of Russian leadership."""
    doc = nlp(text)
    lemmas = [t.lemma_.lower() for t in doc]
    has_single_subject = any(sub in lemmas for sub in SINGLEWORD_SUBJECTS)
    has_multi_subject = contains_multiword_subject(doc)
    has_subject = has_single_subject or has_multi_subject
    has_criticism = criticism_targeting_subject(doc)
    return has_subject and has_criticism

# ========= DATABASE CONNECTION =========
def load_df_from_postgres() -> pd.DataFrame:
    """Load data from PostgreSQL into a DataFrame."""
    conn = psycopg2.connect(
        host=PGHOST, port=PGPORT, dbname=PGDB, user=PGUSER, password=PGPASS
    )
    try:
        with conn, conn.cursor() as cur:
            cur.execute(QUERY)
            rows = cur.fetchall()
            colnames = [desc[0] for desc in cur.description]
            return pd.DataFrame(rows, columns=colnames)
    finally:
        conn.close()

# ========= MAIN PIPELINE =========
def main():
    print("📡 Loading data from PostgreSQL...")
    df = load_df_from_postgres()
    if df.empty or "message" not in df.columns:
        sys.exit("No data returned or missing 'message' column. Check your query or filters.")

    df = df[df["message"].notna()].copy()
    df["message"] = df["message"].astype(str)

    if "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"], errors="coerce")
        df = df.dropna(subset=["time"])

    print(f" Loaded {len(df)} rows. Starting text analysis (approx. 15–20 min)...")
    criticism_flags = []

    for i, msg in enumerate(tqdm(df["message"], desc="Analyzing messages")):
        is_crit = is_criticism_of_russian_leadership_spacy(msg)
        criticism_flags.append(is_crit)

        if (i + 1) % 1000 == 0:
            count = int(sum(criticism_flags))
            print(f"• Processed {i+1} messages | Found critical: {count}")

    df["is_criticism"] = criticism_flags

    # Output
    tag = "anti_regime_nationalists"
    with open(f"{tag}_analyzed_data.pkl", "wb") as f:
        pickle.dump(df, f)
    print(f" Results saved to '{tag}_analyzed_data.pkl'")

    df[df["is_criticism"] == True].to_excel(f"{tag}_critical_messages.xlsx", index=False)
    print(f"📄 Critical messages saved to '{tag}_critical_messages.xlsx'")

if __name__ == "__main__":
    main()
