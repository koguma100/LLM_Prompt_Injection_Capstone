#!/usr/bin/env python3
"""
validate_injection_dataset.py

Checks injection_detector_dataset.csv against the contract implied by
build_injection_dataset.py, and reports quality metrics that the build
script does not enforce (duplicates, leakage, trivial shortcuts).

Usage:
    python3 validate_injection_dataset.py [path/to/dataset.csv]

Exit code is 1 if any hard check FAILs, 0 otherwise (WARNs don't fail).
"""

import sys
from collections import Counter

import numpy as np
import pandas as pd

from build_injection_dataset import FRAMINGS, SUBTYPE_TO_ID, sentence_is_imperative

EXPECTED_COLS = ["text", "label", "subtype", "source", "origin_blog_id",
                 "injected_text", "span_start", "span_end", "framing", "instruction_source",
                 "subtype_id"]
EXPECTED_COUNTS = {"injection": 3000, "benign_imperative": 3000, "normal": 6000}
SUBTYPE_TO_LABEL = {"normal": 0, "benign_imperative": 0, "injection": 1}
SUBTYPE_TO_SOURCE = {"normal": "blog_corpus", "benign_imperative": "blog_corpus",
                     "injection": "blog_corpus+instruction_dataset"}
TRIGGER_PHRASES = ["ignore the previous text", "new instructions:", "disregard everything above",
                   "system override", "forget what i said before"]

results = []  # (status, name, detail)


def check(name, ok, detail="", warn_only=False):
    status = "PASS" if ok else ("WARN" if warn_only else "FAIL")
    results.append((status, name, detail))


def pct(n, d):
    return f"{n}/{d} ({100 * n / d:.2f}%)" if d else f"{n}/0"


def main(path):
    df = pd.read_csv(path, keep_default_na=True)
    n = len(df)
    print(f"Loaded {n} rows from {path}\n")

    # ------------------------------------------------------------------ schema
    check("columns match build script output", list(df.columns) == EXPECTED_COLS,
          f"got {list(df.columns)}")
    check("no null text", df["text"].notna().all(), pct(df["text"].isna().sum(), n))

    counts = df["subtype"].value_counts().to_dict()
    for st, exp in EXPECTED_COUNTS.items():
        got = counts.get(st, 0)
        check(f"row count for '{st}' == {exp}", got == exp, f"got {got}", warn_only=True)
    check("no unknown subtypes", set(counts) <= set(SUBTYPE_TO_ID), f"got {set(counts)}")

    # ------------------------------------------------------- label consistency
    bad_label = (df["label"] != df["subtype"].map(SUBTYPE_TO_LABEL)).sum()
    check("label consistent with subtype", bad_label == 0, pct(bad_label, n))
    bad_id = (df["subtype_id"] != df["subtype"].map(SUBTYPE_TO_ID)).sum()
    check("subtype_id consistent with subtype", bad_id == 0, pct(bad_id, n))
    bad_src = (df["source"] != df["subtype"].map(SUBTYPE_TO_SOURCE)).sum()
    check("source consistent with subtype", bad_src == 0, pct(bad_src, n))

    inj = df[df["subtype"] == "injection"]
    ben = df[df["subtype"] == "benign_imperative"]
    nor = df[df["subtype"] == "normal"]
    neg = df[df["label"] == 0]

    # --------------------------------------------------- per-subtype nullness
    # instruction_source was added later; CSVs from older builds lack it, and
    # the schema check above already FAILs for that, so don't crash on it here.
    inj_cols = [c for c in ["injected_text", "span_start", "span_end", "framing", "instruction_source"]
                if c in df.columns]
    missing = inj[inj_cols].isna().any(axis=1).sum()
    check(f"injection rows have {'/'.join(inj_cols)}", missing == 0, pct(missing, len(inj)))
    leaked = neg[inj_cols].notna().any(axis=1).sum()
    check("benign rows have empty injection fields", leaked == 0, pct(leaked, len(neg)))

    # ------------------------------------------------------ span correctness
    span_ok, span_missing, span_ambiguous = 0, 0, 0
    for _, r in inj.iterrows():
        if pd.isna(r["span_start"]) or r["span_start"] == -1:
            span_missing += 1
            continue
        s, e = int(r["span_start"]), int(r["span_end"])
        expected = r["framing"].format(instr=r["injected_text"])
        if r["text"][s:e] == expected:
            span_ok += 1
        if r["text"].count(expected) > 1:
            span_ambiguous += 1
    check("span_start != -1 (injection located)", span_missing == 0, pct(span_missing, len(inj)))
    check("text[span_start:span_end] == framing.format(injected_text)",
          span_ok == len(inj), f"{pct(span_ok, len(inj))} correct")
    check("injected string occurs exactly once in text", span_ambiguous == 0,
          pct(span_ambiguous, len(inj)), warn_only=True)

    # base post (text with span removed) should still be a real post (>= 60 chars)
    base_lens = inj.apply(lambda r: len(r["text"]) - (r["span_end"] - r["span_start"]), axis=1)
    short_base = (base_lens < 60).sum()
    check("injection base post >= 60 chars", short_base == 0, pct(short_base, len(inj)), warn_only=True)

    # ----------------------------------------------------------- framings
    bad_framing = (~inj["framing"].isin(FRAMINGS)).sum()
    check("framing values come from FRAMINGS", bad_framing == 0, pct(bad_framing, len(inj)))
    bare = (inj["framing"] == "{instr}").mean()
    check("~3/8 of injections are unframed (expected 37.5%)", abs(bare - 0.375) < 0.03,
          f"observed {bare:.1%}", warn_only=True)

    # ------------------------------------------------- normal post contract
    short_norm = (nor["text"].str.len() < 60).sum()
    check("normal posts >= 60 chars", short_norm == 0, pct(short_norm, len(nor)))
    urllink = df["text"].str.contains("urlLink", case=False).sum()
    check("no residual 'urlLink' tokens", urllink == 0, pct(urllink, n))
    ws_neg = neg["text"].str.contains(r"\s{2,}|[\n\t]", regex=True).sum()
    check("benign text whitespace-normalized", ws_neg == 0, pct(ws_neg, len(neg)))
    ws_inj = inj["injected_text"].str.contains(r"\s{2,}|[\n\t]", regex=True).sum()
    check("injected instructions whitespace-normalized", ws_inj == 0, pct(ws_inj, len(inj)))

    # --------------------------------------- benign_imperative contract
    short_bi = (ben["text"].str.len() < 15).sum()
    check("benign_imperative sentences >= 15 chars", short_bi == 0, pct(short_bi, len(ben)))
    q_bi = ben["text"].str.strip().str.endswith("?").sum()
    check("benign_imperative not questions", q_bi == 0, pct(q_bi, len(ben)))
    still_imp = ben["text"].apply(sentence_is_imperative).sum()
    check("benign_imperative re-passes sentence_is_imperative()", still_imp == len(ben),
          pct(len(ben) - still_imp, len(ben)) + " fail")
    first_words = ben["text"].str.extract(r"^\W*(?:[Pp]lease\s+)?([A-Za-z']+)")[0].str.lower()
    top_first = first_words.value_counts().head(15)

    # ------------------------------------------------ duplicates & overlap
    dup_text = df["text"].duplicated().sum()
    check("no duplicate text rows", dup_text == 0, pct(dup_text, n), warn_only=True)
    dup_neg_pos = len(set(inj["text"]) & set(neg["text"]))
    check("no text shared between label 0 and label 1", dup_neg_pos == 0, str(dup_neg_pos))

    ids_ben, ids_nor, ids_inj = (set(x["origin_blog_id"]) for x in (ben, nor, inj))
    ov_bn = len(ids_ben & ids_nor)
    check("benign_imperative / normal blog ids disjoint (build script intent)", ov_bn == 0,
          f"{ov_bn} shared blog ids")
    ov_inj = len(ids_inj & (ids_ben | ids_nor))
    check("injection blog ids disjoint from benign blog ids", ov_inj == 0,
          f"{ov_inj} of {len(ids_inj)} injection blog ids also appear in benign rows "
          f"(build only dedups at post level -> author leakage across train/test)", warn_only=True)

    # benign imperative sentences that literally appear inside a normal/injection text
    big_text = "\n".join(pd.concat([nor["text"], inj["text"]]))
    contained = sum(1 for s in ben["text"].sample(min(1000, len(ben)), random_state=0) if s in big_text)
    check("benign_imperative sentences not found inside other rows (1000 sample)", contained == 0,
          f"{contained}/1000", warn_only=True)

    # instruction reuse
    reuse = inj["injected_text"].value_counts()
    check("injected instructions mostly unique", (reuse > 1).sum() / len(reuse) < 0.2,
          f"{len(reuse)} unique of {len(inj)}; max reuse {reuse.max()}", warn_only=True)

    # trigger phrases in negatives (would be label noise if present)
    lower_neg = neg["text"].str.lower()
    trig = sum(lower_neg.str.contains(p, regex=False).sum() for p in TRIGGER_PHRASES)
    check("negatives do not contain framing trigger phrases", trig == 0, str(trig), warn_only=True)

    # encoding: mojibake from latin-1 decoding of utf-8 bytes
    moji = df["text"].str.contains(r"[ÃÂâ€]", regex=True).sum()
    check("low mojibake rate (Ã/Â/â€ artifacts)", moji / n < 0.01, pct(moji, n), warn_only=True)

    # ------------------------------------------------- shortcut / leakage
    # features a model could exploit without understanding the text
    newline_pos = inj["text"].str.contains("\n").mean()
    newline_neg = neg["text"].str.contains("\n").mean()
    check("newline presence not a label shortcut", abs(newline_pos - newline_neg) < 0.05,
          f"injection {newline_pos:.1%} vs benign {newline_neg:.1%} contain '\\n'", warn_only=True)

    # ------------------------------------------------------------ report
    print(f"{'STATUS':6}  CHECK")
    print("-" * 90)
    for status, name, detail in results:
        print(f"{status:6}  {name}" + (f"\n        -> {detail}" if detail else ""))

    print("\n=== Class balance ===")
    print(df["subtype"].value_counts().to_string())
    print(f"label=1 share: {df['label'].mean():.1%}")

    print("\n=== Text length (chars) by subtype ===")
    print(df.assign(L=df["text"].str.len()).groupby("subtype")["L"]
          .describe()[["min", "25%", "50%", "mean", "75%", "max"]].round(0).to_string())

    print("\n=== Injection position within text (span_start / len) ===")
    rel = inj["span_start"] / inj["text"].str.len()
    print(pd.cut(rel, [-0.01, 0.0, 0.25, 0.5, 0.75, 1.0], labels=["at start", "0-25%", "25-50%", "50-75%", "75-100%"])
          .value_counts().sort_index().to_string())

    print("\n=== Framing distribution ===")
    print(inj["framing"].value_counts().to_string())

    if "instruction_source" in df.columns:
        print("\n=== Instruction source ===")
        print(inj["instruction_source"].value_counts().to_string())

    print("\n=== Top first words of benign_imperative sentences ===")
    print(top_first.to_string())

    print("\n=== Unique origin_blog_id per subtype ===")
    for st, ids in (("injection", ids_inj), ("benign_imperative", ids_ben), ("normal", ids_nor)):
        print(f"  {st:18} {len(ids)}")

    shortcut_baselines(df)

    n_fail = sum(1 for s, *_ in results if s == "FAIL")
    n_warn = sum(1 for s, *_ in results if s == "WARN")
    print(f"\nSummary: {len(results) - n_fail - n_warn} PASS, {n_warn} WARN, {n_fail} FAIL")
    return 1 if n_fail else 0


def shortcut_baselines(df):
    """How well can trivial, non-semantic features predict the label?

    If a model can hit high accuracy from length/newlines alone, the dataset
    has a shortcut that a real detector will learn instead of the task.
    """
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import GroupShuffleSplit, cross_val_score
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.pipeline import make_pipeline
    from sklearn.tree import DecisionTreeClassifier

    t = df["text"]
    X = pd.DataFrame({
        "len": t.str.len(),
        "n_sent": t.str.count(r"[.!?](\s|$)"),
        "has_newline": t.str.contains("\n").astype(int),
        "n_colon": t.str.count(":"),
    })
    y = df["label"]
    print("\n=== Shortcut baselines (5-fold CV accuracy; majority class = "
          f"{max(y.mean(), 1 - y.mean()):.1%}) ===")
    for feats in (["len"], ["has_newline"], ["len", "n_sent", "has_newline", "n_colon"]):
        acc = cross_val_score(DecisionTreeClassifier(max_depth=4, random_state=0), X[feats], y, cv=5).mean()
        print(f"  depth-4 tree on {feats}: {acc:.1%}")

    # subtype (3-class) from length alone: benign_imperative is single sentences
    acc3 = cross_val_score(DecisionTreeClassifier(max_depth=4, random_state=0), X[["len"]],
                           df["subtype_id"], cv=5).mean()
    print(f"  depth-4 tree on ['len'] -> 3-class subtype: {acc3:.1%}")

    # bag-of-words reference, grouped by blog id so authors don't span splits
    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=0)
    tr, te = next(gss.split(df, y, groups=df["origin_blog_id"]))
    pipe = make_pipeline(TfidfVectorizer(max_features=50000, ngram_range=(1, 2), min_df=2),
                         LogisticRegression(max_iter=2000))
    pipe.fit(t.iloc[tr], y.iloc[tr])
    pred = pipe.predict(t.iloc[te])
    from sklearn.metrics import classification_report
    print("\n  TF-IDF + LogReg, blog-id-grouped 80/20 split:")
    print("  " + classification_report(y.iloc[te], pred, digits=3).replace("\n", "\n  "))
    te_df = df.iloc[te].assign(pred=pred)
    print("  accuracy by subtype:")
    print("  " + (te_df["pred"] == te_df["label"]).groupby(te_df["subtype"]).mean()
          .round(3).to_string().replace("\n", "\n  "))
    unframed = te_df[te_df["framing"] == "{instr}"]
    if len(unframed):
        print(f"  recall on unframed injections only: {(unframed['pred'] == 1).mean():.3f}")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "injection_detector_dataset.csv"))
