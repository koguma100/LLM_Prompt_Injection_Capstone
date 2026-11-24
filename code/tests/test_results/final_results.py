# Final results for each detection component and for the pipeline as a whole, using the weights in
# sanitizer/config.py. Reads detector_features.csv (from detector_features.py) and llm_validator_eval.csv (from
# llm_validator_eval.py). From code/ run:
#     python tests/test_results/final_results.py
# Writes final_results.csv, final_results.md and confusion_matrices.png next to this file.
import csv
import os
import sys

CODE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, CODE_DIR)

from sanitizer.config import DETECTOR_WEIGHTS as W, INJECTION_THRESHOLD, SKIP_LLM_THRESHOLD  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SET_ORDER = ["datasetv2_holdout", "hugging_face_prompts", "resumes_half_pi", "resumes_all_benign",
             "embedded_pi_tests", "simple_prompts", "imperative_tests"]


def read(name):
    with open(os.path.join(HERE, name), newline="") as f:
        return list(csv.DictReader(f))


def cheap_score(r):
    return (W["rf_malicious"] * (int(r["rf_hits"]) > 0) + W["instruction_overrides"] * int(r["instruction"])
            + W["authority_overrides"] * int(r["authority"]))


def full_score(r):
    cheap = cheap_score(r)
    if SKIP_LLM_THRESHOLD is not None and cheap >= SKIP_LLM_THRESHOLD:
        return cheap  # LLM stage skipped
    return cheap + W["llm_validation"] * (r["sanitized_valid"] == "0")


# Each method: name -> (rows it applies to, prediction function)
def methods(features, llm_rows):
    return [
        ("Random Forest", features, lambda r: int(r["rf_hits"]) > 0),
        ("Instruction regex", features, lambda r: r["instruction"] == "1"),
        ("Authority regex", features, lambda r: r["authority"] == "1"),
        ("LLM output check", llm_rows, lambda r: r["sanitized_valid"] == "0"),
        ("Old rule: any detector fires", features,
         lambda r: int(r["rf_hits"]) > 0 or r["instruction"] == "1" or r["authority"] == "1"),
        ("Old rule + LLM check", llm_rows,
         lambda r: int(r["rf_hits"]) > 0 or r["instruction"] == "1" or r["authority"] == "1"
         or r["sanitized_valid"] == "0"),
        ("Weighted pipeline, detectors only", features, lambda r: cheap_score(r) >= INJECTION_THRESHOLD),
        ("Weighted pipeline, full (with LLM check)", llm_rows, lambda r: full_score(r) >= INJECTION_THRESHOLD),
    ]


def stats(rows, predict):
    tp = fp = tn = fn = 0
    for r in rows:
        p, y = predict(r), r["label"] == "1"
        tp += p and y
        fp += p and not y
        tn += (not p) and not y
        fn += (not p) and y
    n = tp + fp + tn + fn
    div = lambda a, b: a / b if b else None  # noqa: E731
    return dict(n=n, tp=tp, fp=fp, tn=tn, fn=fn, accuracy=div(tp + tn, n), precision=div(tp, tp + fp),
                recall=div(tp, tp + fn), fpr=div(fp, fp + tn),
                f1=div(2 * tp, 2 * tp + fp + fn))


def pct(x):
    return "—" if x is None else f"{x:.1%}"


def main():
    features = read("detector_features.csv")
    llm = read("llm_validator_eval.csv")
    by_key = {(r["set"], r["sample"]): r for r in features}
    llm_rows = [{**by_key[(r["set"], r["sample"])], "sanitized_valid": r["sanitized_valid"]} for r in llm
                if (r["set"], r["sample"]) in by_key]

    out, md = [], []
    md.append("# Final results\n")
    md.append(f"Weights: {', '.join(f'{k} {v:g}' for k, v in W.items())}; injection at a vote of "
              f"{INJECTION_THRESHOLD:g}; LLM stage skipped at {SKIP_LLM_THRESHOLD:g}.\n")
    md.append("`datasetv2_holdout` is the 20% of dataset v2 the Random Forest never trained on. The LLM rows use a "
              f"random subset of {len(llm_rows)} samples (resumes, holdout, Hugging Face). `imperative_tests` is "
              "labeled all benign but contains lines like \"Ignore all previous instructions\".\n")

    groups = [("All realistic sets (holdout + Hugging Face + resumes)",
               {"datasetv2_holdout", "hugging_face_prompts", "resumes_half_pi", "resumes_all_benign"})]
    groups += [(s, {s}) for s in SET_ORDER]
    for title, sets in groups:
        md.append(f"\n## {title}\n")
        md.append("| Method | Samples | Accuracy | Precision | Recall | False-positive rate | F1 |")
        md.append("|---|---|---|---|---|---|---|")
        for name, rows, predict in methods(features, llm_rows):
            s = stats([r for r in rows if r["set"] in sets], predict)
            if not s["n"]:
                continue
            out.append({"group": title, "method": name, **s})
            md.append(f"| {name} | {s['n']} | {pct(s['accuracy'])} | {pct(s['precision'])} | {pct(s['recall'])} "
                      f"| {pct(s['fpr'])} | {pct(s['f1'])} |")

    with open(os.path.join(HERE, "final_results.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    with open(os.path.join(HERE, "final_results.md"), "w") as f:
        f.write("\n".join(md) + "\n")
    print("\n".join(md))
    confusion_matrices(features, llm_rows)


# Confusion matrices for the whole pipeline: with the LLM check on the LLM-checked samples, and without it (the
# detectors' vote alone) on the much larger holdout set
def confusion_matrices(features, llm_rows):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    holdout = [r for r in features if r["set"] == "datasetv2_holdout"]
    m = {name: (rows, predict) for name, rows, predict in methods(features, llm_rows)}
    panels = [
        ("Weighted pipeline, full (with LLM check)", llm_rows, "LLM-checked samples"),
        ("Weighted pipeline, detectors only", holdout, "holdout"),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.8))
    for ax, (name, rows, where) in zip(axes.flat, panels):
        s = stats(rows, m[name][1])
        grid = [[s["tn"], s["fp"]], [s["fn"], s["tp"]]]
        ax.imshow(grid, cmap="Blues")
        top = max(max(row) for row in grid)
        for i in range(2):
            for j in range(2):
                ax.text(j, i, grid[i][j], ha="center", va="center", fontsize=15,
                        color="white" if grid[i][j] > top / 2 else "black")
        ax.set_xticks([0, 1], ["Benign", "Injection"])
        ax.set_yticks([0, 1], ["Benign", "Injection"])
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Actual")
        ax.set_title(f"{name}\n{where}, n={s['n']}: acc {pct(s['accuracy'])}, "
                     f"prec {pct(s['precision'])}, rec {pct(s['recall'])}", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "confusion_matrices.png"), dpi=150)


if __name__ == "__main__":
    main()
