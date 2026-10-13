# The Attention Ablation Test

A controlled test of whether self-attention is a separable cause of hallucination
in language models. It is the architectural experiment (Study IV) of the
undergraduate thesis "MRI of a Mad Machine: The Structural Origins of Hallucination"
(Department of CSE, Metropolitan University, Sylhet).

The design holds everything fixed except the sequence-mixing mechanism. Two models
at the same parameter count, trained on the same corpus (the Pile) with the same
tokenizer (GPT-NeoX), are compared: one mixes information through attention, the
other through a selective state space. Attention is therefore the only manipulated
variable, which is what lets a behavioural difference be attributed to attention
rather than to data or scale.

## Results at a glance

| Probe | Attention (Pythia-2.8B) | No attention (Mamba-2.8B) | Test | Verdict |
| --- | --- | --- | --- | --- |
| Free recall (SimpleQA) | ~98.5% error | ~98.5% error | McNemar p = 1.000, kappa = 0.85 | no architectural difference (control) |
| Context competition (31-line) | 97% follow (70/72) | 24% follow (17/72) | McNemar p < 0.0001, 53/0 discordant | attention-specific dissociation |

## Findings

Two probes, two results that point in opposite directions, and that split is the
finding.

1. Free-recall probe (SimpleQA, 200 questions). No architectural difference.
   Pythia-2.8B and Mamba-2.8B fail at the same rate and on the same questions.
   Blind double-scoring agreement Cohen's kappa = 0.85; paired McNemar p = 1.000;
   difference bounded within +/-2 points. For plain factual recall drawn from
   parametric memory, swapping attention out changes nothing. Attention is not the
   source of this failure mode.

2. Context-competition probe (31-line context). A strong, one-directional split.
   Given a passage that contradicts the model's prior, the attention model
   (Pythia-2.8B) follows the passage 97% of the time (70/72); the state-space model
   (Mamba-2.8B) follows it 24% (17/72) and otherwise answers from its prior. Paired
   McNemar p < 0.0001, with 53 items where the attention model used the context and
   the state-space model did not, and none the other way.

Reading: attention is the machinery of context-grounding -- the mechanism by which
an input is allowed to override stored belief. That machinery is double-edged. It is
what makes in-context and retrieval-augmented use work when the context is correct,
and a direct route to confident error when the context is misleading. A model that
follows a false planted fact 97% of the time has context-faithfulness and
context-induced hallucination as the same property seen from two sides.

Two honest bounds. Part of the second-probe gap is a known capability limit of
state-space models at in-context retrieval, not a pure pathology; the 9-line version
of the probe did not separate the two architectures, which is why the 31-line build
is the decisive one. And the multi-model survey below has only two non-attention
models, so it is reported descriptively; the matched 2.8B paired test carries the
inferential weight.

## Models

All open-weight.

- EleutherAI/pythia-2.8b, EleutherAI/pythia-1.4b  (attention; Pile, GPT-NeoX)
- state-spaces/mamba-2.8b-hf, state-spaces/mamba-1.4b-hf  (selective state space; Pile, GPT-NeoX)
- Qwen/Qwen2.5-1.5B  (attention; separate lineage, used only as a consistency check)

The Pythia-2.8B vs Mamba-2.8B pair is the controlled comparison. The others check
that the result is not a one-checkpoint artefact.

## Layout

Experiment 1 -- free-recall probe
  p5_local_harness_v2.py     run a model over the question pool; build the blind sheet
  pool_v2.json               200 SimpleQA questions
  pythia_2_8b.json           raw Pythia-2.8B outputs
  mamba_2_8b.json            raw Mamba-2.8B outputs
  p5_scoresheet_BLIND.csv    shuffled, de-identified responses for scoring
  p5_key_SEALED.csv          response-id to model mapping (opened only after scoring)
  p5_scored_SADI.csv         annotator 1 failure-type scores
  p5_scored_DEWAN.csv        annotator 2 failure-type scores

Experiment 2 -- context competition
  stage1b_run.py             run one model over the context pool
  pool_stage1b.json          96 items, 31-line context build
  s1b_p28.json s1b_m28.json  raw outputs, 2.8B pair
  s1b_p14.json s1b_m14.json  raw outputs, 1.4B pair
  s1b_qwen.json              raw outputs, Qwen2.5-1.5B
  stage1b_analyze.py         paired per-position analysis + McNemar (2.8B pair)
  stage1b_survey.py          per-model table across all five models
  stage1b_log.txt            run log, 2.8B pair
  stage1b_survey_hard_log.txt run log, full survey on the 31-line build

  Thesis_2_0_RTX5050.ipynb   notebook mirror of the free-recall setup

## Reproduce

Python 3.12. The RTX 5050 is Blackwell (sm_120) and needs the CUDA 12.8 build of
PyTorch; the default wheel will not use the GPU.

  py -3.12 -m venv p5env
  .\p5env\Scripts\Activate.ps1
  pip install --index-url https://download.pytorch.org/whl/cu128 torch
  pip install -r requirements.txt

Experiment 1:
  python p5_local_harness_v2.py run --model EleutherAI/pythia-2.8b     --out pythia_2_8b.json
  python p5_local_harness_v2.py run --model state-spaces/mamba-2.8b-hf --out mamba_2_8b.json
  python p5_local_harness_v2.py blind --inputs pythia_2_8b.json mamba_2_8b.json --out p5_scoresheet_BLIND.csv --key p5_key_SEALED.csv
  (two annotators score p5_scoresheet_BLIND.csv independently and blind)

Experiment 2:
  python stage1b_run.py --model EleutherAI/pythia-2.8b     --out s1b_p28.json
  python stage1b_run.py --model state-spaces/mamba-2.8b-hf --out s1b_m28.json
  python stage1b_analyze.py --pythia s1b_p28.json --mamba s1b_m28.json
  python stage1b_survey.py --attn s1b_p28.json s1b_p14.json s1b_qwen.json --noattn s1b_m28.json s1b_m14.json

## Hardware

Single consumer GPU (ASUS A16, RTX 5050 Laptop, 8 GB). Models are run one at a time;
Mamba uses the transformers reference implementation, so no custom CUDA kernels are
required.

## Scoring

Experiment 1 is scored by two human annotators, blind to which model produced each
response, into four failure types (correct, factual error, abstention, degenerate);
reliability is Cohen's kappa = 0.85. Experiment 2 is scored automatically against a
fixed answer key (context-followed / prior-fallback), so it carries no annotator
step.
