"""Scores all outputs/*.jsonl and writes results/summary.txt, results/per_model.csv,
results/pairs.csv and results/scored_items.csv.

Scoring (word-boundary match after accent folding and lower-casing):
  conflict items: followed = planted (wrong) answer present and true answer absent
                  prior    = true answer present and planted answer absent
  support items:  correct  = true answer present
  baseline items: correct  = true answer present
"""
import csv
import glob
import json
import os
import re
import unicodedata

from scipy.stats import mannwhitneyu
from statsmodels.stats.contingency_tables import mcnemar

PAIRS = [
    ("EleutherAI/pythia-160m", "state-spaces/mamba-130m-hf"),
    ("EleutherAI/pythia-410m", "state-spaces/mamba-370m-hf"),
    ("EleutherAI/pythia-1b", "state-spaces/mamba-790m-hf"),
    ("EleutherAI/pythia-1.4b", "state-spaces/mamba-1.4b-hf"),
    ("EleutherAI/pythia-2.8b", "state-spaces/mamba-2.8b-hf"),
]


def fold(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def has(text, ans):
    return re.search(r"(?<![a-z0-9])" + re.escape(fold(ans)) + r"(?![a-z0-9])", fold(text)) is not None


def label(r):
    t, w = has(r["response"], r["real_answer"]), has(r["response"], r["context_answer"])
    if r["condition"] == "conflict":
        if w and not t:
            return "followed"
        if t and not w:
            return "prior"
        return "both" if (t and w) else ("empty" if not r["response"].strip() else "other")
    return "correct" if t else "incorrect"


def pct(n, d):
    return f"{100 * n / d:.1f}" if d else "-"


def main():
    os.makedirs("results", exist_ok=True)
    data = {}
    for f in sorted(glob.glob("outputs/*.jsonl")):
        rows = [json.loads(x) for x in open(f, encoding="utf-8") if x.strip()]
        if rows:
            for r in rows:
                r["label"] = label(r)
            data[rows[0]["model"]] = rows

    with open("results/scored_items.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["model", "item_id", "fact_id", "category", "condition", "length", "position",
                    "real_answer", "context_answer", "response", "label"])
        for m, rows in data.items():
            for r in rows:
                w.writerow([m, r["item_id"], r["fact_id"], r["category"], r["condition"], r["length"],
                            r["position"], r["real_answer"], r["context_answer"], r["response"], r["label"]])

    lines, per_model = [], []
    hdr = ["model", "n_items", "prior_correct", "follow_short", "follow_long", "follow_known_long",
           "prior_fallback_long", "support_short", "support_long", "follow_long_early",
           "follow_long_middle", "follow_long_late"]
    for m, rows in data.items():
        base = {r["fact_id"]: r["label"] == "correct" for r in rows if r["condition"] == "baseline"}
        def rate(cond, length=None, pos=None, lab="followed", known=False):
            sel = [r for r in rows if r["condition"] == cond and (length is None or r["length"] == length)
                   and (pos is None or r["position"] == pos) and (not known or base.get(r["fact_id"]))]
            return sum(r["label"] == lab for r in sel), len(sel)
        pc = sum(base.values()), len(base)
        row = [m, len(rows), pct(*pc), pct(*rate("conflict", "short")), pct(*rate("conflict", "long")),
               pct(*rate("conflict", "long", known=True)), pct(*rate("conflict", "long", lab="prior")),
               pct(*rate("support", "short", lab="correct")), pct(*rate("support", "long", lab="correct")),
               pct(*rate("conflict", "long", "early")), pct(*rate("conflict", "long", "middle")),
               pct(*rate("conflict", "long", "late"))]
        per_model.append(row)

    with open("results/per_model.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(hdr)
        w.writerows(per_model)

    lines.append("PER-MODEL RATES (%)")
    lines.append("  ".join(f"{h:>18}" if i else f"{h:34}" for i, h in enumerate(hdr)))
    for row in per_model:
        lines.append("  ".join(f"{str(v):>18}" if i else f"{str(v)[:33]:34}" for i, v in enumerate(row)))

    pair_rows = []
    lines.append("\nMATCHED PAIRS (Pythia vs Mamba): conflict items, followed = 1")
    for pa, ma in PAIRS:
        if pa not in data or ma not in data:
            lines.append(f"  {pa} / {ma}: missing outputs")
            continue
        A = {r["item_id"]: r for r in data[pa]}
        B = {r["item_id"]: r for r in data[ma]}
        for length in ("short", "long", "all"):
            ids = [i for i, r in A.items() if r["condition"] == "conflict" and i in B
                   and (length == "all" or r["length"] == length)]
            a_only = sum(A[i]["label"] == "followed" and B[i]["label"] != "followed" for i in ids)
            b_only = sum(B[i]["label"] == "followed" and A[i]["label"] != "followed" for i in ids)
            both = sum(A[i]["label"] == "followed" and B[i]["label"] == "followed" for i in ids)
            neither = len(ids) - a_only - b_only - both
            p = mcnemar([[both, a_only], [b_only, neither]], exact=True).pvalue
            fa = sum(A[i]["label"] == "followed" for i in ids)
            fb = sum(B[i]["label"] == "followed" for i in ids)
            sa = [r for r in data[pa] if r["condition"] == "support" and (length == "all" or r["length"] == length)]
            sb = [r for r in data[ma] if r["condition"] == "support" and (length == "all" or r["length"] == length)]
            pair_rows.append([pa, ma, length, len(ids), fa, fb, a_only, b_only, f"{p:.3g}",
                              sum(r["label"] == "correct" for r in sa), len(sa),
                              sum(r["label"] == "correct" for r in sb), len(sb)])
            lines.append(f"  {pa.split('/')[1]:12} vs {ma.split('/')[1]:16} {length:5}  n={len(ids):3}  "
                         f"followed {fa:3} vs {fb:3}  discordant {a_only:3}/{b_only:3}  McNemar p={p:.3g}  "
                         f"support-correct {pair_rows[-1][9]}/{len(sa)} vs {pair_rows[-1][11]}/{len(sb)}")

    with open("results/pairs.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["pythia", "mamba", "length", "n_conflict", "pythia_followed", "mamba_followed",
                    "pythia_only", "mamba_only", "mcnemar_p", "pythia_support_correct", "n_support",
                    "mamba_support_correct", "n_support"])
        w.writerows(pair_rows)

    attn = [float(r[4]) for r in per_model if "mamba" not in r[0].lower() and r[4] != "-"]
    ssm = [float(r[4]) for r in per_model if "mamba" in r[0].lower() and r[4] != "-"]
    if len(attn) >= 2 and len(ssm) >= 2:
        p = mannwhitneyu(attn, ssm, alternative="two-sided").pvalue
        lines.append(f"\nGROUP (long conflict follow rate): attention mean {sum(attn)/len(attn):.1f}% (n={len(attn)}), "
                     f"state-space mean {sum(ssm)/len(ssm):.1f}% (n={len(ssm)}), Mann-Whitney p={p:.3g}")

    open("results/summary.txt", "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
