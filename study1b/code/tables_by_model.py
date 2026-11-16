import csv,collections,json
from statsmodels.stats.contingency_tables import mcnemar
from scipy.stats import mannwhitneyu
rows=list(csv.DictReader(open('results/scored_items.csv',encoding='utf-8')))
M=collections.defaultdict(dict)
for r in rows: M[r['model']][r['item_id']]=r
base={m:{r['fact_id']:r['label']=='correct' for r in d.values() if r['condition']=='baseline'} for m,d in M.items()}
ORDER=["EleutherAI/pythia-160m","state-spaces/mamba-130m-hf","EleutherAI/pythia-410m","state-spaces/mamba-370m-hf","EleutherAI/pythia-1b","state-spaces/mamba-790m-hf","EleutherAI/pythia-1.4b","state-spaces/mamba-1.4b-hf","EleutherAI/pythia-2.8b","state-spaces/mamba-2.8b-hf","Qwen/Qwen2.5-0.5B","Qwen/Qwen2.5-1.5B","Qwen/Qwen2.5-3B","HuggingFaceTB/SmolLM2-1.7B"]
out={}
for m in ORDER:
    d=M[m]; kn=base[m]
    def cnt(cond,L=None,lab='followed',pos=None,facts=None):
        s=[r for r in d.values() if r['condition']==cond and (L is None or r['length']==L) and (pos is None or r['position']==pos) and (facts is None or r['fact_id'] in facts)]
        return sum(r['label']==lab for r in s),len(s)
    unk={f for f,k in kn.items() if not k}
    o=dict(known=sum(kn.values()),
        fs=cnt('conflict','short'),fl=cnt('conflict','long'),
        ps=cnt('conflict','short',lab='prior'),pl=cnt('conflict','long',lab='prior'),
        read_unk_l=cnt('support','long',lab='correct',facts=unk),read_unk_s=cnt('support','short',lab='correct',facts=unk),
        pos={p:cnt('conflict','long',pos=p) for p in ('early','middle','late')})
    out[m]=o
    pc=lambda t:f"{100*t[0]/t[1]:.1f}"
    print(f"{m.split('/')[1]:20} known {o['known']:3}/111  follow S {pc(o['fs'])} L {pc(o['fl'])}  prior S {pc(o['ps'])} L {pc(o['pl'])}  read-unknown L {o['read_unk_l'][0]}/{o['read_unk_l'][1]} S {o['read_unk_s'][0]}/{o['read_unk_s'][1]}  pos L {[pc(v) for v in o['pos'].values()]}")
cat=collections.defaultdict(dict)
for m in ORDER:
    for c in ['capital','symbol','currency','author','painter','planet']:
        s=[r for r in M[m].values() if r['condition']=='conflict' and r['length']=='long' and r['category']==c]
        cat[m][c]=(sum(r['label']=='followed' for r in s),len(s))
print('\ncategory follow (long):')
for m in ORDER[2:10]: print(' ',m.split('/')[1], {c:f"{v[0]}/{v[1]}" for c,v in cat[m].items()})
# attention-mamba group pooled by category for the four reliable pairs
print('\npooled 4 reliable pairs, long follow by category:')
for arch,ms in [('pythia',ORDER[2:10:2]),('mamba',ORDER[3:10:2])]:
    agg=collections.defaultdict(lambda:[0,0])
    for m in ms:
        for c,v in cat[m].items(): agg[c][0]+=v[0]; agg[c][1]+=v[1]
    print(' ',arch,{c:f"{100*v[0]/v[1]:.0f}% ({v[0]}/{v[1]})" for c,v in agg.items()})
json.dump({m:{k:(v if not isinstance(v,dict) else v) for k,v in o.items()} for m,o in out.items()},open('tab.json','w'))
