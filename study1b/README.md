# Study 1b: context conflict

111 facts in six types (56 national capitals, 12 chemical symbols, 16 currencies, 15 book authors, 9 painters, 3 planet facts). Each fact has a true answer and a plausible false one. Each fact appears in nine conditions:

- `baseline`: the question with no context, to record the model's prior answer;
- six `conflict` items: the false version of the fact placed early, in the middle or late among unrelated true statements, in a 9-line (`short`) or 31-line (`long`) text;
- two `support` items: the true version placed in the middle of a 9-line or 31-line text.

This gives 999 items per model. Context items are preceded by two worked examples with invented facts (`PREAMBLE` in `code/run_probe.py`). Generation is greedy, fp16, 12 new tokens; the first line of output is kept.

Scoring (`label` in `code/analyze_probe.py`), after accent folding and lower-casing, whole-word match: a conflict response is `followed` if it contains the planted answer and not the true one, `prior` in the reverse case, otherwise `both`, `other` or `empty`. A support or baseline response is `correct` if it contains the true answer.

| File | Description |
|---|---|
| `pool_probe_v2.json` | Item pool (999 items, with prompts) |
| `outputs/*.jsonl` | Raw outputs of the 14 models (999 lines each) |
| `results/summary.txt`, `results/per_model.csv`, `results/pairs.csv` | Per-model rates and paired McNemar tests |
| `results/scored_items.csv` | Every response with its label |
| `code/build_probe.py` | Builds the item pool (deterministic) |
| `code/run_probe.py` | Runs one model over the pool; resumable |
| `code/analyze_probe.py` | Scores all outputs, writes `results/` (per-model rates, pair tests, group test) |
| `code/tables_by_model.py` | Per-model numbers in Table 2, reading control, position and fact-type breakdowns |
| `code/controls_known_facts.py` | Reading control and pair tests restricted to facts both models knew (Table 3, right-hand block) |

Models: `EleutherAI/pythia-{160m,410m,1b,1.4b,2.8b}`, `state-spaces/mamba-{130m,370m,790m,1.4b,2.8b}-hf`, `Qwen/Qwen2.5-{0.5B,1.5B,3B}`, `HuggingFaceTB/SmolLM2-1.7B`.

Reproduce the reported numbers from the released outputs:

```
cd study1b
python code/analyze_probe.py
python code/tables_by_model.py
python code/controls_known_facts.py
```

Regenerate outputs (an 8 GB GPU is sufficient; roughly 3-4 hours for all 14 models). Run from `study1b/`; `run_probe.py` resumes from existing files, so move the released `outputs/` aside first:

```
cd study1b
python code/build_probe.py
python code/run_probe.py --model EleutherAI/pythia-2.8b
python code/analyze_probe.py
```
