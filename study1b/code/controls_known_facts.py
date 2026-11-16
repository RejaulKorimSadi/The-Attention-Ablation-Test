import csv,collections
from statsmodels.stats.contingency_tables import mcnemar
rows=list(csv.DictReader(open('results/scored_items.csv',encoding='utf-8')))
M=collections.defaultdict(dict)
for r in rows: M[r['model']][r['item_id']]=r
base={m:{r['fact_id']:r['label']=='correct' for r in d.values() if r['condition']=='baseline'} for m,d in M.items()}
print('SUPPORT accuracy on facts the model did NOT know at baseline (requires reading):')
for m,d in sorted(M.items()):
    unk={f for f,k in base[m].items() if not k}
    for L in ('short','long'):
        s=[r for r in d.values() if r['condition']=='support' and r['length']==L and r['fact_id'] in unk]
        c=sum(r['label']=='correct' for r in s)
        print(f"  {m.split('/')[1]:22} {L:5} unknown facts={len(unk):3}  support correct {c}/{len(s)}")
PAIRS=[("EleutherAI/pythia-410m","state-spaces/mamba-370m-hf"),("EleutherAI/pythia-1b","state-spaces/mamba-790m-hf"),("EleutherAI/pythia-1.4b","state-spaces/mamba-1.4b-hf"),("EleutherAI/pythia-2.8b","state-spaces/mamba-2.8b-hf"),("EleutherAI/pythia-160m","state-spaces/mamba-130m-hf")]
print('\nPAIRS restricted to facts BOTH models knew at baseline:')
for pa,ma in PAIRS:
    kn={f for f in base[pa] if base[pa][f] and base[ma][f]}
    for L in ('short','long'):
        ids=[i for i,r in M[pa].items() if r['condition']=='conflict' and r['length']==L and r['fact_id'] in kn]
        a=sum(M[pa][i]['label']=='followed' and M[ma][i]['label']!='followed' for i in ids)
        b=sum(M[ma][i]['label']=='followed' and M[pa][i]['label']!='followed' for i in ids)
        fa=sum(M[pa][i]['label']=='followed' for i in ids); fb=sum(M[ma][i]['label']=='followed' for i in ids)
        pr=sum(M[ma][i]['label']=='prior' for i in ids)
        bt=len(ids)-a-b-min(fa,fb) if False else sum(M[pa][i]['label']=='followed' and M[ma][i]['label']=='followed' for i in ids)
        p=mcnemar([[bt,a],[b,len(ids)-a-b-bt]],exact=True).pvalue
        print(f"  {pa.split('/')[1]:12} vs {ma.split('/')[1]:16} {L:5} known facts={len(kn):3} n={len(ids):3} followed {fa}/{len(ids)} vs {fb}/{len(ids)}  mamba prior-fallback {pr}  discordant {a}/{b} p={p:.2g}")
print('\nMamba label distribution, long conflict:')
for m in [p[1] for p in PAIRS]:
    print(' ',m.split('/')[1], collections.Counter(r['label'] for r in M[m].values() if r['condition']=='conflict' and r['length']=='long'))
print('\nBy category, 2.8B long conflict follow:')
for m in ["EleutherAI/pythia-2.8b","state-spaces/mamba-2.8b-hf"]:
    c=collections.defaultdict(lambda:[0,0])
    for r in M[m].values():
        if r['condition']=='conflict' and r['length']=='long': c[r['category']][0]+=r['label']=='followed'; c[r['category']][1]+=1
    print(' ',m.split('/')[1],{k:f"{v[0]}/{v[1]}" for k,v in sorted(c.items())})
