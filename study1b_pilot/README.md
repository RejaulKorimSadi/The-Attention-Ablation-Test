# Study 1b pilot: context conflict, 24 facts

The item pool covers 24 facts: 12 national capitals, 6 chemical symbols and 6 currencies. Each fact appears four times:

- `baseline`: the question with no context, to record the model's prior answer;
- `context_early`, `context_middle`, `context_late`: the same question after a nine-sentence text in which a false version of the fact (for example, "The capital of Canada is Toronto.") is placed first, in the middle or last among eight unrelated true statements.

This gives 96 items, of which 72 are context items. Context items are preceded by a two-example instruction to answer only from the text (`PREAMBLE` in `stage1b_run.py`). Generation is greedy with 16 new tokens; the first line of output is kept.

A response is `context_followed` if, after lower-casing and removing non-alphanumeric characters, it contains the planted answer and not the true answer, and `prior_fallback` in the reverse case (`score` in `stage1b_analyze.py`).

| File | Description |
|---|---|
| `pool_stage1b.json` | Item pool (96 items) |
| `stage1b_run.py` | Runs one model over the item pool |
| `stage1b_analyze.py` | Prior accuracy, per-position rates and exact McNemar test for a model pair (Appendix B) |
| `stage1b_survey.py` | Per-model table and group comparison across attention and non-attention models |
| `s1b_p28.json`, `s1b_m28.json` | Outputs of Pythia-2.8B and Mamba-2.8B |
| `s1b_p14.json`, `s1b_m14.json` | Outputs of Pythia-1.4B and Mamba-1.4B |
| `s1b_qwen.json` | Outputs of Qwen2.5-1.5B |

Each output file stores the full item record, including the prompt, next to the model response.

Reproduce:

```
cd study1b_pilot
python stage1b_analyze.py --pythia s1b_p28.json --mamba s1b_m28.json
python stage1b_analyze.py --pythia s1b_p14.json --mamba s1b_m14.json
python stage1b_survey.py --attn s1b_p28.json s1b_p14.json s1b_qwen.json --noattn s1b_m28.json s1b_m14.json
```

Regenerate outputs (one 8 GB GPU is sufficient):

```
python stage1b_run.py --model EleutherAI/pythia-2.8b --out s1b_p28.json
python stage1b_run.py --model state-spaces/mamba-2.8b-hf --out s1b_m28.json
python stage1b_run.py --model EleutherAI/pythia-1.4b --out s1b_p14.json
python stage1b_run.py --model state-spaces/mamba-1.4b-hf --out s1b_m14.json
python stage1b_run.py --model Qwen/Qwen2.5-1.5B --out s1b_qwen.json
```
