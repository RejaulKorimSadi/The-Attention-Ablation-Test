"""Study 1a: inter-annotator agreement and paired comparison of Pythia-2.8B vs Mamba-2.8B on free recall.

Usage: python analyze_study1a.py
"""
import csv
import collections
from sklearn.metrics import cohen_kappa_score
from statsmodels.stats.contingency_tables import mcnemar

LABELS = {"0": "correct", "1": "factual_error", "2": "abstention", "3": "degenerate"}
PYTHIA = "EleutherAI/pythia-2.8b"
MAMBA = "state-spaces/mamba-2.8b-hf"


def read(path, key="response_id"):
    return {r[key]: r for r in csv.DictReader(open(path, encoding="utf-8"))}


key = read("data/model_key.csv")
a = read("data/annotator_A.csv")
b = read("data/annotator_B.csv")
ids = sorted(key)

agree = sum(a[i]["failure_type"] == b[i]["failure_type"] for i in ids)
kappa = cohen_kappa_score([a[i]["failure_type"] for i in ids], [b[i]["failure_type"] for i in ids])
print(f"responses: {len(ids)}  raw agreement: {agree}/{len(ids)} = {agree / len(ids):.2%}  Cohen's kappa: {kappa:.3f}")

counts = collections.Counter((key[i]["true_model"], a[i]["failure_type"]) for i in ids)
for model in (PYTHIA, MAMBA):
    row = ", ".join(f"{LABELS[c]}={counts[(model, c)]}" for c in "0123")
    print(f"{model}: {row}")

by_item = collections.defaultdict(dict)
for i in ids:
    by_item[key[i]["item_id"]][key[i]["true_model"]] = a[i]["failure_type"]

for label, code in (("factual_error", "1"), ("correct", "0")):
    t = collections.Counter((v[PYTHIA] == code, v[MAMBA] == code) for v in by_item.values())
    table = [[t[(True, True)], t[(True, False)]], [t[(False, True)], t[(False, False)]]]
    p = mcnemar(table, exact=True).pvalue
    print(f"paired {label}: both={t[(True, True)]} pythia_only={t[(True, False)]} "
          f"mamba_only={t[(False, True)]} neither={t[(False, False)]}  exact McNemar p={p:.3f}")
