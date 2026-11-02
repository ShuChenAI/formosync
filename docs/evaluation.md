# Evaluation of FormoSync E4B v0.1

This document describes the Round 6 step768 adapter. The source measurements are preserved in [evaluation-results.json](evaluation-results.json), with the infrastructure-specific adapter location removed. Counts and gate outcomes are unchanged.

The candidate was selected on development data and retained at the project owner's direction. Automatic development acceptance and final joint acceptance were false. That distinction is part of the release description.

## Saved-artifact comparison

| Suite / category | Base correct | Adapter correct | Base rate | Adapter rate |
|---|---:|---:|---:|---:|
| Frozen / Custom Tables | 25/40 | 24/40 | 62.50% | 60.00% |
| Frozen / TeamSync | 94/114 | 109/114 | 82.46% | 95.61% |
| Frozen / generic | 25/30 | 24/30 | 83.33% | 80.00% |
| Frozen / zh-TW comprehension | 28/40 | 32/40 | 70.00% | 80.00% |
| Pragmatics / semantics | 0/28 | 9/28 | 0.00% | 32.14% |
| Pragmatics / tool use | 13/28 | 16/28 | 46.43% | 57.14% |
| Joint Custom Tables | 13/32 | 31/32 | 40.63% | 96.88% |
| Reserved knowledge sample | 336/670 | 319/670 | 50.15% | 47.61% |

The large joint-CT improvement is a result on 32 authored scenarios. It should not be generalized to all Custom Table operations: the separate frozen CT suite regresses by one example.

## No-call behavior and recorded commit attempts

| Suite | Base no-unwanted-call | Adapter no-unwanted-call | Recorded unwanted commit attempts, base / adapter |
|---|---:|---:|---:|
| Frozen | 100.00% | 82.00% | 0 / 0 |
| Pragmatics | 100.00% | 66.67% | 0 / 0 |
| Joint CT | 100.00% | 100.00% | 0 / 0 |

These are evaluator-derived model-output metrics. No live backend write was performed, and a zero recorded count does not certify the absence of unsafe behavior outside this test set.

## Truncation

The frozen CT suite recorded seven truncated base outputs and zero truncated adapter outputs. The frozen TeamSync suite recorded three for the base and one for the adapter. No truncation was recorded for the remaining categories in the table. Output budgets are part of the original evaluation harness; do not silently substitute another budget when reproducing these numbers.

## Gate outcomes

| Gate | Passed |
|---|---|
| Development acceptance | No |
| Protected groups non-regressing | No |
| No-call/schema non-regression with zero unwanted commits | No |
| Reserved knowledge non-regression | No |
| Complete joint acceptance | No |

The model is presented as a research artifact with useful task-specific improvements and documented regressions. It is not a claim of all-metric superiority or a production acceptance result.

## What the evidence does and does not cover

Authored tests share scenario rules and have prior diagnostic use. There is no independent human assessment of broad Taiwan language quality. The 670-question knowledge sample is reserved for the saved-artifact comparison, but base-pretraining contamination is unknown. Exact long known benchmark questions were filtered from the public dialogue training pool; semantic near-duplicates and short generic prompts cannot be certified absent.

Future hyperparameter selection should use development data. If these final tests are reused during subsequent development, disclose the reuse and obtain a new independent holdout for the next final comparison.
