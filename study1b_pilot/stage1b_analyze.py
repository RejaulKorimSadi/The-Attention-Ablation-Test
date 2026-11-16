import argparse, json, re
from statsmodels.stats.contingency_tables import mcnemar

def norm(s): return re.sub(r"[^a-z0-9]", "", s.lower())

def score(resp, ctx_ans, real_ans):
    r, c, p = norm(resp), norm(ctx_ans), norm(real_ans)
    has_c, has_p = c in r, p in r
    if has_c and not has_p: return "context_followed"
    if has_p and not has_c: return "prior_fallback"
    if not r: return "empty"
    return "other"

def load(fn): return {r["item_id"]: r for r in json.load(open(fn))}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pythia", required=True)
    ap.add_argument("--mamba", required=True)
    args = ap.parse_args()
    A, B = load(args.pythia), load(args.mamba)
    ids = sorted(set(A) & set(B))

    def summarise(D, name):
        base = [r for r in D.values() if r["condition"] == "baseline"]
        hit = sum(norm(r["real_answer"]) in norm(r["response"]) for r in base)
        print(f"\n=== {name} ===")
        print(f"baseline prior accuracy: {hit}/{len(base)} ({100*hit/max(len(base),1):.0f}%)")
        for pos in ("early", "middle", "late"):
            items = [r for r in D.values() if r["position"] == pos]
            foll = sum(score(r["response"], r["context_answer"], r["real_answer"]) == "context_followed" for r in items)
            fall = sum(score(r["response"], r["context_answer"], r["real_answer"]) == "prior_fallback" for r in items)
            n = len(items)
            print(f"  {pos:7}  context-followed {foll:2}/{n} ({100*foll/n:3.0f}%)   prior-fallback {fall:2}/{n} ({100*fall/n:3.0f}%)")
        ctx = [r for r in D.values() if r["condition"].startswith("context")]
        foll = sum(score(r["response"], r["context_answer"], r["real_answer"]) == "context_followed" for r in ctx)
        return foll, len(ctx)

    fa, na = summarise(A, "Pythia-2.8B (attention)")
    fb, nb = summarise(B, "Mamba-2.8B (no attention)")

    ctx_ids = [i for i in ids if A[i]["condition"].startswith("context")]
    b01 = b10 = 0
    for i in ctx_ids:
        sa = score(A[i]["response"], A[i]["context_answer"], A[i]["real_answer"]) == "context_followed"
        sb = score(B[i]["response"], B[i]["context_answer"], B[i]["real_answer"]) == "context_followed"
        if sa and not sb: b01 += 1
        if sb and not sa: b10 += 1
    res = mcnemar([[0, b01], [b10, 0]], exact=True)
    print("\n" + "=" * 60)
    print(f"Pythia context-following: {fa}/{na} ({100*fa/na:.0f}%)   Mamba: {fb}/{nb} ({100*fb/nb:.0f}%)")
    print(f"Paired McNemar (Pythia-only={b01}, Mamba-only={b10}): p = {res.pvalue:.4f}")
    if res.pvalue < 0.05:
        print("VERDICT: architectures handle context competition DIFFERENTLY -> attention survives Stage 1b.")
    else:
        print("VERDICT: no difference -> Stage 1b agrees with P5; attention remains reducible to the objective.")
    print("=" * 60)

if __name__ == "__main__":
    main()
