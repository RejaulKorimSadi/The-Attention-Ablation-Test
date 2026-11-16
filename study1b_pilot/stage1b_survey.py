import argparse, json, re
from scipy.stats import mannwhitneyu

def norm(s): return re.sub(r"[^a-z0-9]", "", s.lower())

def followed(r):
    a, c, p = norm(r["response"]), norm(r["context_answer"]), norm(r["real_answer"])
    return (c in a) and (p not in a)

def stats(fn):
    D = json.load(open(fn))
    name = D[0]["model"] if D else fn
    base = [r for r in D if r["condition"] == "baseline"]
    prior = sum(norm(r["real_answer"]) in norm(r["response"]) for r in base) / max(len(base), 1)
    pos = {}
    for p in ("early", "middle", "late"):
        items = [r for r in D if r["position"] == p]
        pos[p] = sum(followed(r) for r in items) / max(len(items), 1)
    ctx = [r for r in D if r["condition"].startswith("context")]
    foll = sum(followed(r) for r in ctx) / max(len(ctx), 1)
    dip = (pos["early"] + pos["late"]) / 2 - pos["middle"]
    return dict(name=name, prior=prior, foll=foll, dip=dip, **pos)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--attn", nargs="+", required=True)
    ap.add_argument("--noattn", nargs="+", required=True)
    args = ap.parse_args()

    A = [stats(f) for f in args.attn]
    N = [stats(f) for f in args.noattn]

    hdr = f"{'model':34}{'prior':>7}{'follow':>8}{'early':>7}{'mid':>7}{'late':>7}{'mid-dip':>9}"
    def row(s): return (f"{s['name'][:33]:34}{s['prior']*100:6.0f}%{s['foll']*100:7.0f}%"
                        f"{s['early']*100:6.0f}%{s['middle']*100:6.0f}%{s['late']*100:6.0f}%{s['dip']*100:8.0f}%")
    print("\nATTENTION models"); print(hdr)
    for s in A: print(row(s))
    print("\nNON-ATTENTION models"); print(hdr)
    for s in N: print(row(s))

    fa = [s["foll"] for s in A]; fn = [s["foll"] for s in N]
    da = [s["dip"] for s in A]; dn = [s["dip"] for s in N]
    ma, mn = sum(fa)/len(fa), sum(fn)/len(fn)
    print("\n" + "=" * 62)
    print(f"mean context-following   attention {ma*100:.0f}%   non-attention {mn*100:.0f}%")
    print(f"mean middle-dip          attention {sum(da)/len(da)*100:.0f}%   non-attention {sum(dn)/len(dn)*100:.0f}%")
    if len(fa) >= 2 and len(fn) >= 2:
        u, p = mannwhitneyu(fa, fn, alternative="two-sided")
        print(f"group comparison (Mann-Whitney on following rate): p = {p:.4f}")
        verdict = "DIFFER" if p < 0.05 else "do NOT differ"
        print(f"VERDICT: attention and non-attention groups {verdict} on context competition.")
    else:
        print("add >=2 models per group for a group-level test.")
    print("A positive middle-dip concentrated in the attention group is the "
          "lost-in-the-middle attention signature.")
    print("=" * 62)

if __name__ == "__main__":
    main()
