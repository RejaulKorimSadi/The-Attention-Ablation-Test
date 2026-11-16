# The Attention Ablation Test

Does self-attention decide whether a false statement in the input becomes a confident error? This experiment holds the training data, tokenizer and scale fixed and changes only how a model mixes information across a sentence. It is Study A of the B.Sc. thesis *MRI of a Mad Machine: The Structural Origins of Hallucination* (Department of CSE, Metropolitan University, Sylhet).

## Design

Pythia (attention) and Mamba (selective state space) were both trained on the Pile with the GPT-NeoX tokenizer. We use five size-matched pairs (160M/130M, 410M/370M, 1B/790M, 1.4B/1.4B, 2.8B/2.8B) and four further attention models (Qwen2.5-0.5B, 1.5B, 3B and SmolLM2-1.7B): 14 models, all run on one 8 GB consumer GPU.

- **Free recall:** 200 SimpleQA questions, 2.8B pair, two annotators scoring blind (Cohen's kappa = 0.85).
- **Context conflict:** 111 facts. Each fact is asked alone, with a planted false version in a 9-line or 31-line text (666 conflict items per model), and with a planted true version (support items).

## Results

| Probe | Pythia-2.8B | Mamba-2.8B | Test |
|---|:---:|:---:|:---:|
| Free recall, correct of 200 | 3 | 3 | McNemar p = 1.000 |
| Planted false line repeated, of 666 | 650 | 566 | 90 vs 6 discordant, p = 2.5e-20 |
| Same, on facts both models knew (31-line), of 279 | 264 | 210 | p = 9.0e-13 |
| Planted true line read correctly (31-line), of 111 | 111 | 110 | reading control |

From 410M upward, every attention model repeats the planted falsehood more often than its matched state-space model (1.4B: 648 vs 186, 462 vs 0 discordant). Free recall from memory does not change. Attention decides whether a passage can override what the model knows.

## Note on the pilot

An earlier 24-fact pilot with 9-line texts is kept for the record. In that pilot both 2.8B models followed the planted statement on all 72 context items, and the 1.4B pair separated (Pythia-1.4B 70/72, Mamba-1.4B 17/72). An earlier version of this README credited the 70/72 vs 17/72 split to the 2.8B pair; it belongs to the 1.4B pair. The final 111-fact probe removes the pilot's ceiling. It replicates the 1.4B split and also separates the 2.8B pair.

## Files

The full 14-model release (outputs, scored items, analysis scripts, known-facts control and pilot) is part of the thesis package under `evidence/study_A_attention_ablation`. The free-recall files in this repository are the same ones used there.
