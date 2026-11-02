# New base versus FormoSync benchmark

This run compares the pinned NVIDIA base with the unmodified FormoSync E4B v0.1.0 adapter. It does not train or select a new checkpoint. Archived R6 results remain separately identified in [evaluation.md](evaluation.md).

## Protocol

- Base: `nvidia/NVIDIA-Nemotron-3.5-Bolt-E4B-BF16`, revision `49843eed8db1f1c616c47af75cfd36e07aec0667`.
- Adapter: SHA-256 `fecf928856466c605aed86cc55d23e9fdb8da7f8c7fb06a381c140c2da53bd05`.
- TMMLU+: all **19,680 test questions across 67 subjects** at revision `639a64db464b4661feb91817b9edfe43932bdf18`.
- Zero-shot next-token likelihood restricted to A/B/C/D, no tools, the same native template and tokenizer, thinking disabled.
- NF4 double quantization, BF16 computation, checkpoint-BF16 frozen embeddings and FP32 norms for both models.
- No answer-dependent filtering; over-context failures remain in the denominator.
- Report overall accuracy, subject macro-average, Wilson intervals and paired wins/losses.
- Additional authored fixtures: 224 frozen, 56 pragmatic and 32 joint CT scenarios, using the recorded rubrics and generation budgets.

This is a controlled zero-shot likelihood adaptation. It is not the official few-shot leaderboard protocol. Authored fixtures share training rules and have prior diagnostic use; benchmark contamination in base pretraining is unknown.

## Reproduce the public TMMLU+ portion

```bash
python -m formosync.prepare_tmmlu
python -m formosync.benchmark --label base --output-dir results/base
python -m formosync.benchmark --label formosync --output-dir results/formosync
python -m formosync.compare --base results/base --formosync results/formosync \
  --output results/comparison.json
```

Run the two model processes sequentially on the same GPU. The commands require the pinned base in `models/base/` and the release adapter in `models/adapter/`. Source CSV hashes are checked before preparation. The deterministic compressed input SHA-256 is `c1097f67e9d0d7294f556a0b943b4ffb67cfba64f9b935e5c349d15b32c9512d`.

The optional `--fixtures` argument accepts a locally available authored test file. Frozen fixture labels are not included in the public training-data asset. The public source includes the recorded scoring code, but exact reproduction of those private authored suites requires those fixture files.

## Completed results

Both models completed the full test split and all 312 authored cases. The comparison verified matching protocols, question IDs, versions and precision. Stored MCQ predictions were independently re-counted before publication. GPU stop and quota release were confirmed.

| Metric | NVIDIA base | FormoSync E4B |
|---|---:|---:|
| TMMLU+ / full test | 10049/19680 (51.06%) | 9743/19680 (49.51%) |
| TMMLU+ / 67-subject macro | 51.53% | 49.99% |
| Frozen Custom Tables | 25/40 (62.50%) | 24/40 (60.00%) |
| Frozen TeamSync | 94/114 (82.46%) | 109/114 (95.61%) |
| Frozen generic tools | 25/30 (83.33%) | 24/30 (80.00%) |
| Frozen zh-TW comprehension | 28/40 (70.00%) | 32/40 (80.00%) |
| Pragmatic semantics | 0/28 (0.00%) | 9/28 (32.14%) |
| Pragmatic tool use | 13/28 (46.43%) | 16/28 (57.14%) |
| Joint Custom Tables | 13/32 (40.62%) | 31/32 (96.88%) |
| Frozen no-unwanted-call | 100.00% | 82.00% |
| Pragmatic no-unwanted-call | 100.00% | 66.67% |
| Joint CT no-unwanted-call | 100.00% | 100.00% |

[Structured results](benchmark-20261102-results.json) · [Release and checksums](https://github.com/ShuChenAI/formosync/releases/tag/benchmark-20261102).
