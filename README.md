# Wrong with Confidence

**Measuring Hallucination, Overconfidence and Identity-Conditioned Behaviour in Large Language Models**

Md. Rejaul Korim Sadi · Toufiqur Rahman Tasin · Golam Mostofa Naeem · Dewan Fahad Chowdhury · Hatim Al Amin Chowdhury  
Department of Computer Science and Engineering, Metropolitan University, Sylhet, Bangladesh

*Submitted to Knowledge and Information Systems (KAIS), Springer Nature*

Pre-registration: <https://doi.org/10.17605/OSF.IO/CS967>

---

## What this repository contains

This repository holds every artefact needed to inspect, replicate, or extend the study:

```
data/
  prompts/
    main_prompts.csv          — 484 clear/ambiguous prompt pairs (242 questions × 2 renderings)
    identity_probes/
      demographic.csv         — 240 occupation-framing prompts (4 occupations × 60 frames)
      authority.csv           — 200 authority-probe prompts (50 questions × 4 framings)
      safety.csv              — 200 safety-probe prompts (50 questions × 4 framings)
  responses/
    raw_responses.csv         — 5,620 verbatim model outputs with metadata
  scores/
    scores_annotator_a.csv    — first annotator's independent scores (all columns)
    scores_annotator_b.csv    — second annotator's independent scores (all columns)
    overlap_uid.csv           — row identifiers for the 600 dual-scored overlap set

rubric/
  scoring_rubric.md           — full rubric with definitions and edge-case rules
  taxonomy.md                 — six-condition prompt taxonomy with cell definitions

code/
  collect.py                  — API collection script (temperature 0, pinned model tags)
  score_support.py            — utilities used during scoring (reference lookup, rubric checks)
  analysis.py                 — all statistical analyses reported in the paper
  figures.py                  — figure generation scripts (outputs figures/ below)

figures/
  fig1_pronoun_assignment.pdf — occupational pronoun distribution (Figure 1 in paper)
  fig2_authority_length.pdf   — answer length by declared user identity (Figure 2)
  fig3_kappa.pdf              — inter-annotator agreement by column (Figure 3 / Appendix A)

pre-registration/
  preregistration_v1.pdf      — OSF snapshot, filed May 2026 before any scoring began
  deviations.md               — four declared deviations from the pre-registration
```

---

## The study in one paragraph

We crossed prompt clarity (clear vs. ambiguous), content type (factual vs. opinion) and knowledge domain (general vs. niche) into six conditions, writing each of 242 questions twice with the same reference answer. Three identity-probe batteries were added: one recording which pronoun the model uses to continue an occupation sentence (1,200 responses), one asking an identical question under four declared user statuses (1,000 responses), and one asking a benign but sensitive question under the same framings (1,000 responses). All prompts went through five open-weight models from four organisations under locked decoding settings (temperature 0.0, top-*p* 1.0, fixed system prompt, 8192-token cap) in a single session on 30 May 2026, yielding 5,620 responses. Two annotators scored every response blind to model identity and to prompt rendering on five columns. All five columns cleared a pre-registered Cohen's κ ≥ 0.80 reliability floor on a stratified 600-response overlap.

---

## Key results

| Finding | Result |
|---|---|
| Factual error, clear prompts | 39.9 % [36.3, 43.5] |
| Factual error, ambiguous prompts | 66.7 % [63.2, 70.1] |
| Conditional odds ratio (ambiguity), mixed-effects model | 10.5 [8.40, 13.21] |
| Conditional odds ratio (niche domain), mixed-effects model | 5.5 [4.39, 6.95] |
| Clear + general corner | 30.4 % |
| Ambiguous + niche corner | 79.6 % |
| Incorrect answers with no hedge | 77.4 % [74.2, 80.2] |
| One-sided answers, clear opinion prompts | 32.2 % [28.3, 36.4] |
| One-sided answers, ambiguous opinion prompts | 73.0 % [68.9, 76.7] |
| Answer length, anonymous user | 188 words (mean) |
| Answer length, physician/researcher | 268 words (mean, +42 %) |
| Pre-registered safety prediction (expert framing → fewer caveats) | **not confirmed** |

---

## Models

| Code | Model tag | Organisation |
|---|---|---|
| M1 | gemma3:27b-cloud | Google |
| M2 | gemma4:31b-cloud | Google |
| M3 | gpt-oss:120b-cloud | OpenAI |
| M4 | qwen3-next:80b-cloud | Alibaba |
| M5 | nemotron-3-super:cloud | NVIDIA |

All five were served through a single cloud endpoint. The endpoint does not return token log-probabilities; the released dataset carries three empty log-probability columns rather than a silent omission. Confidence is measured from the wording of the answer, not from logits.

---

## Scoring columns

| Column | Applied to | Values |
|---|---|---|
| `correctness` | 1,416 scored factual responses | correct / incorrect / abstained |
| `confidence_tone` | all prose responses | hedged / plain / assertive |
| `opinion_balance` | 1,000 opinion responses | balanced / one-sided |
| `pronoun` | 1,200 demographic-probe responses | he / she / they / avoided |
| `safety_statement` | 996 usable safety-probe responses | present / absent |

Four M4 responses reached the token cap and are scored as abstentions. Four M4 safety-probe calls failed (HTTP 500) and are excluded as missing data rather than scored; the exclusion is symmetric across framings (one per framing). Both exclusions are identified in the released data.

---

## Data quality and deviations from pre-registration

Four deviations from the pre-registration are declared in the manuscript and documented in `pre-registration/deviations.md`:

1. **Confidence-tone recalibration.** The column failed the first pass (κ = 0.50) because the annotators drew the plain/assertive boundary at consistent but different points. Both returned to the registered definition, re-scored the column, and reached κ = 1.00.
2. **Passage-dependent item removal.** Items requiring an attached passage were excluded during design as unsuitable for single-turn probing. This left uneven condition sizes; the removal is documented in the taxonomy.
3. **Repeat-ask consistency not collected.** A repeat-ask measure was pre-registered under the confidence hypothesis but not collected because the run was executed as a single deterministic pass; unlocking temperature mid-study would have broken the design.
4. **Post-cutoff contamination control not run.** A 30-item post-cutoff control set was constructed and is released but was not run in this collection.

---

## Reproducing the analysis

```bash
git clone https://github.com/Taseen06/R2
cd R2
pip install -r requirements.txt
python code/analysis.py          # reproduces all tables and statistics
python code/figures.py           # reproduces all three figures
```

The analysis script reads from `data/responses/raw_responses.csv` and `data/scores/`. It does not call any model API. All outputs are written to `results/`.

---

## Pre-registration

The study was pre-registered in May 2026, before any model output was collected or scored.

OSF record (view-only, identity-preserving): <https://osf.io/a9rvz/?view_only=8aa333f4051b48d3b4d8ad0cbbdd8dd1>  
OSF DOI: <https://doi.org/10.17605/OSF.IO/CS967>

---

## Companion paper

This repository supports the empirical study. The companion theoretical analysis — which locates hallucination in the architecture of the transformer and motivated this study's design — is:

> Sadi, M.R.K., Tasin, T.R., and Naeem, G.M. (2026). *From Architecture to Output: Structural Origins of Hallucination in Large Language Models and the Amplifying Role of Data.* Journal of Artificial Intelligence Research. arXiv:2606.07537.

---

## Citation

If you use the data, code or results from this repository, please cite the paper (citation will be updated on acceptance):

```
Sadi, M.R.K., Tasin, T.R., Naeem, G.M., Chowdhury, D.F., and Chowdhury, H.A.A. (2026).
Wrong with Confidence: Measuring Hallucination, Overconfidence and Identity-Conditioned
Behaviour in Large Language Models. Submitted to Knowledge and Information Systems.
https://github.com/Taseen06/R2
```

---

## Ethical note

The safety battery uses benign, publicly answerable questions selected to sound sensitive rather than to be harmful. The only recorded quantity is whether a safety statement is present. No probe requested actionable instructions and no harmful content was produced, stored or released. The demographic battery documents stereotyped pronoun assignment; the he/she/they/avoided coding is a narrow operational slice chosen for measurement tractability and should not be read as a complete account of gender.

---

## Licence

Data and materials: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)  
Code: [MIT](LICENSE)
