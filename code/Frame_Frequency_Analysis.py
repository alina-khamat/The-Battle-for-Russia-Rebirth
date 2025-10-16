#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Frame Counting by Cluster (Postgres or CSV)
===========================================
"""

import os
import re
import sys
import pandas as pd
from pathlib import Path
from collections import defaultdict, OrderedDict
import psycopg2

# ===== REQUIRED ENV VARS  =====
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

# ===== SQL =====
QUERY = """
SELECT message, cluster, "time"
FROM public.telegram_data
WHERE cluster IS NOT NULL
  AND "time" >= TIMESTAMP '2022-02-22 00:00:00'
ORDER BY "time" ASC
"""

# ===== Outputs =====
OUT_COUNTS = Path("frame_counts_by_cluster.csv")
OUT_PCTS   = Path("frame_percentages_by_cluster.csv")

# ===== Progress =====
PROGRESS_EVERY = 500
PRINT_ALL_CLUSTERS = True
TOPN_CLUSTERS = 10

# ===== Frames  =====
FRAMES = OrderedDict({
    "Anti-immigration sentiments and Isolationism": [
        "приезжие","нерусские","русофобия","русофобный","чурки","русорез",
        "замещение коренного населения","этнозамещение","криминальные диаспоры",
        "этническая война","цивилизационный кризис","единокровные",
        "русский вопрос","геноцид русского народа","боевики-мигранты", "нелегал",
        "введение визового режима"
    ],
    "Anti-peace-deal conspiratorial thinking": [
        "охранители","договорняк","договорнячок","заговорщики","изменники",
        "предательство","пятая колона","позорный мир","государственная измена",
        "позорная сделка","шестая колона","партия страха"
    ],
    "Hawkish criticism": [
        "военные рельсы", "недееспособность", "некомпетентность", "подлинный патриотизм","тотальная война","полная победа", "болтовня",
        "настоящая война","вредительство","ввести военное положение","надлежащее обеспечение войск",
        "всеобщая мобилизация", "необучаемость", "новая мобилизация","решительные действия", "дефицит на фронте",
        "паркетные генералы", "замалчивание", "дегенералы","удар по центру принятия решений", "кризис снабжения", "халатность", "самокастрация", "бронежилетов не хватает", "больно ударить"
    ],
    "Left-wing Criticism": [
        "госкапитализм","новая национальная элита","деолигархизация",
        "компрадорский режим","национализация","госплан","капиталисты",
        "классовая борьба","буржуазия","социальная справедливость",
        "национализация собственности"
    ],
    "Populism": [
        "элитка","псевдоэлита","олигархи","олигархат","олигархический",
        "клан","клановоолигархический","анти-народный","коррупционеры","казнокрады",
        "официальная пропаганда","бесправие","развал","самозванцы","безответственность",
        "общак","алчность","за счет народа",
        "воровство","глупость","идиотизм",
        "обманывать народ", "наплевать на закон"
    ],
    "Religious language": [
        "армагеддон","апокалипсис","единоверцы",
        "христианский","садом","закон божий","битва света и тьмы","молитва"
    ],
    "Revanchism and Exceptionalism (Russianness)": [
        "государственность","реальный суверенитет","суверенная россия",
        "единая и неделимая россия","русская цивилизация","евразийская цивилизация",
        "русская нация","империя","большая россия","державность","единая держава",
        "родная земля","исконные земли","утраченные земли","объединить земли",
        "возрождение россии",
        "историческое выживание россии","самоочищение","русское самосознание",
        "национальное самосознание","восточно-славянский союз",
        "восточно-славянский мир","русский мир","русское жизненное пространство",
        "деоккупация","русских земель","единый русский народ",
        "государство-цивилизация","русский характер"
    ],
    "Traditionalism": [
        "традиционные ценности","традиционализм","русская культура",
        "традиции отцов","многодетные семьи","великие предки",
        "хранить память","славное прошлое","историческая память"
    ],
})

# ===== Lemmatization  =====
def get_lemmatizer():
    try:
        import spacy
        for model in ("ru_core_news_lg","ru_core_news_md","ru_core_news_sm"):
            try:
                nlp = spacy.load(model, disable=["ner","textcat"])
                def _lem(text: str) -> str:
                    return " ".join([t.lemma_ for t in nlp(text.lower()) if t.lemma_.strip()])
                return _lem, f"spacy:{model}"
            except Exception:
                continue
    except Exception:
        pass
    try:
        import pymorphy2
        morph = pymorphy2.MorphAnalyzer()
        token_re = re.compile(r"[А-Яа-яA-Za-zЁё]+", re.UNICODE)
        def _lem(text: str) -> str:
            toks = token_re.findall(text.lower())
            return " ".join(morph.parse(tok)[0].normal_form if morph.parse(tok) else tok for tok in toks)
        return _lem, "pymorphy2"
    except Exception:
        pass
    def _lem_lower(text: str) -> str:
        return re.sub(r"[^а-яa-zё\s]", " ", text.lower(), flags=re.UNICODE)
    return _lem_lower, "lowercase_only"

def normalize_spaces(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip())

def phrase_to_regex(lem_phrase: str):
    return re.compile(rf"(?<!\w){re.escape(normalize_spaces(lem_phrase))}(?!\w)",
                      flags=re.UNICODE)

def contains_any(text: str, regex_list) -> bool:
    return any(r.search(text) is not None for r in regex_list)

# ===== Progress print  =====

def print_progress(i, overall_counts, cluster_counts):
    print(f"\n[PROGRESS] processed {i} messages")
    print("  TOTAL by frames:")
    for frame in FRAMES.keys():
        print(f"    - {frame}: {overall_counts[frame]}")
    print("  By clusters:")
    items = list(cluster_counts.items())
    if not PRINT_ALL_CLUSTERS:
        items = sorted(items, key=lambda kv: sum(kv[1].values()), reverse=True)[:TOPN_CLUSTERS]
        # if PRINT_ALL_CLUSTERS is True, print all
    for cl_name, fr_dict in items:
        print(f"    • {cl_name!s}:")
        for frame in FRAMES.keys():
            print(f"        {frame}: {fr_dict[frame]}")

# ===== Load from DB -> DataFrame =====
def load_df_from_postgres():
    conn = psycopg2.connect(
        host=PGHOST, port=PGPORT, dbname=PGDB, user=PGUSER, password=PGPASS
    )
    try:
        with conn, conn.cursor() as cur:
            cur.execute(QUERY)
            rows = cur.fetchall()
            colnames = [desc[0] for desc in cur.description]  # auto column names
            df = pd.DataFrame(rows, columns=colnames)
            return df
    finally:
        conn.close()

# ===== Main  =====
def main():
    # Fetch data
    df = load_df_from_postgres()
    if df.empty:
        sys.exit("Query returned no results. Please check your SQL filters or connection settings.")

    # Lemmatizer
    lemmatize, used = get_lemmatizer()
    print(f"[LEMMA] active lemmatization backend: {used}")

    # Compile regexes per frame (lemmatized phrases)
    frame_regexes = {}
    for frame, kws in FRAMES.items():
        lem_phrases = [normalize_spaces(lemmatize(k)) for k in kws]
        frame_regexes[frame] = [phrase_to_regex(p) for p in lem_phrases if p]

    # Scan + progress
    n = len(df)
    results = {frame: [False]*n for frame in FRAMES}
    overall_counts = {frame: 0 for frame in FRAMES}
    cluster_counts = defaultdict(lambda: {frame: 0 for frame in FRAMES})
    cluster_totals = defaultdict(int)

    for i, (msg, cl) in enumerate(zip(df["message"].fillna("").astype(str),
                                      df["cluster"]), start=1):
        text = normalize_spaces(lemmatize(msg))
        cluster_totals[cl] += 1
        for frame, regs in frame_regexes.items():
            if contains_any(text, regs):
                results[frame][i-1]   = True
                overall_counts[frame] += 1
                cluster_counts[cl][frame] += 1

        if i % PROGRESS_EVERY == 0 or i == n:
            print_progress(i, overall_counts, cluster_counts)

    #  Output tables
    for frame in FRAMES:
        df["has__"+frame] = results[frame]

    count_cols = [c for c in df.columns if c.startswith("has__")]
    cluster_totals_df = (
        df.groupby("cluster", dropna=False)["message"]
          .count().rename("total_messages").reset_index()
    )
    counts = df.groupby("cluster", dropna=False)[count_cols].sum().reset_index()
    for c in count_cols:
        counts[c] = counts[c].astype(int)
    counts = counts.merge(cluster_totals_df, on="cluster", how="left")

    pct = counts.copy()
    for c in count_cols:
        pct[c] = (pct[c] / pct["total_messages"] * 100).round(2)

    rename_map = {c: c.replace("has__","") for c in count_cols}
    counts = counts.rename(columns=rename_map)
    pct    = pct.rename(columns=rename_map)

    # CSV output
    counts.to_csv(OUT_COUNTS, index=False)
    pct.to_csv(OUT_PCTS, index=False)
    print(f"\n[DONE] CSV сохранены:\n  {OUT_COUNTS.resolve()}\n  {OUT_PCTS.resolve()}")

if __name__ == "__main__":
    main()
