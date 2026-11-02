# FormoSync E4B

**Traditional Chinese for Taiwan. Tool use grounded in the conversation.**

[繁體中文](README.zh-TW.md) · [Evaluation](docs/evaluation.md) · [Training data](docs/data.md) · [Licenses and attribution](NOTICE.md)

FormoSync E4B is a text-only research LoRA adapter for Taiwan Mandarin workplace conversations and TeamSync-style tool use. Its focus is the connection between language and action: understanding what a user means, finding the relevant schema, choosing a tool, and carrying known values into its arguments.

The name combines **Formosa** and **Sync**. The release identifier is **FormoSync-Nemotron-E4B-zhTW-Tool-v0.1**.

This version corresponds to **Round 6, step 768**. It improves several authored tool-use and language tests over the base model, while other tool, no-call and knowledge results regress. It is a research artifact with published limitations; the complete automatic acceptance gate did not pass.

## What it is designed to study

- **Schema-grounded operations:** discover tables and fields, bind record identifiers, and select read, prepare or execution tools from the capabilities actually supplied.
- **Taiwan Mandarin in context:** interpret omitted subjects, references such as 「剛剛那筆」, corrections, quantities, dates and confirmation language.
- **Action boundaries:** distinguish a request for status from a new command, an acknowledgment from authorization, and a pending proposal from a completed operation.

For example, 「可以」 can confirm a displayed proposal or acknowledge a field explanation. The preceding conversation and server-issued capabilities determine the intended next step. These are training objectives, not a guarantee that every ambiguous expression is handled correctly.

## Model identity

| Item | Value |
|---|---|
| Artifact | Complete PEFT LoRA adapter; base weights are a separate dependency |
| Base | [`nvidia/NVIDIA-Nemotron-3.5-Bolt-E4B-BF16`](https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Bolt-E4B-BF16) |
| Base revision | `49843eed8db1f1c616c47af75cfd36e07aec0667` |
| Upstream foundation | Google Gemma 4 E4B-it, as identified by NVIDIA |
| Initialization | Fresh LoRA on the pinned base |
| Selected checkpoint | Round 6, step 768 |
| LoRA rank / alpha | 16 / 32 |
| Training | NF4 4-bit base, BF16 computation, learning rate `1e-5`, effective batch 8 |
| Training schedule | One 875-update epoch over 7,000 examples; step 768 selected on development |
| Training modality | Text and tool-call conversations |
| Adapter bytes | 139,602,808 |

Adapter SHA-256:

```text
fecf928856466c605aed86cc55d23e9fdb8da7f8c7fb06a381c140c2da53bd05
```

The saved adapter was reloaded against a fresh base and its adapter tensors were verified equal to the saved state. `E4B` follows the upstream family name; it should not be read as a statement of total stored parameter count or VRAM requirements.

## Fresh full-test comparison — 2026-11-02

Both fixed-artifact runs completed with matching input IDs, runtime versions and protocol. This is zero-shot option-letter likelihood, not the official few-shot leaderboard protocol.

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

Paired TMMLU+ outcomes: both_correct=8943, base_only=1106, formosync_only=800, both_wrong=8831.

[Results and verification release](https://github.com/ShuChenAI/formosync/releases/tag/benchmark-20261102) · [Machine-readable comparison](docs/benchmark-20261102-results.json). Authored tests share training scenario rules and prior diagnostic use; broad language or production safety acceptance is not established.

Full TMMLU+ accuracy decreases by **1.55 percentage points** (306 fewer correct answers). Several authored tool and language metrics improve, while other tool and no-call metrics regress; these results do not establish across-the-board superiority.

## Archived R6 results

The table below preserves the original archived R6 measurements, separately from the new full-test comparison above.

The following are saved-artifact results, not training loss or development scores.

| Evaluation | Base | FormoSync E4B |
|---|---:|---:|
| Authored joint Custom Table test | 13/32 | **31/32** |
| Frozen TeamSync scenarios | 94/114 | **109/114** |
| Frozen zh-TW comprehension | 28/40 | **32/40** |
| Taiwan Mandarin pragmatic semantics | 0/28 | **9/28** |
| Taiwan Mandarin pragmatic tool use | 13/28 | **16/28** |
| Frozen Custom Table test | **25/40** | 24/40 |
| Frozen generic tool scenarios | **25/30** | 24/30 |
| Reserved knowledge sample | **336/670 (50.15%)** | 319/670 (47.61%) |

No-unwanted-call scores also fall from 100% to 82% on the frozen suite and from 100% to 66.67% on the pragmatic suite. The joint Custom Table suite remains at 100%. No unwanted commit attempt was recorded by the authored evaluators, but no live backend operation was executed.

The authored tests share scenario rules with training fixtures. They are useful diagnostics, not an independent human evaluation of broad Taiwan language competence. The sampled knowledge test does not establish that the base model's pretraining was free of benchmark contamination. See [the complete evaluation notes](docs/evaluation.md) and [machine-readable results](docs/evaluation-results.json).

## Exact training data

| Component | Examples | Share |
|---|---:|---:|
| TeamSync operations | 2,800 | 40% |
| Public Taiwan Mandarin conversations | 2,450 | 35% |
| Grounded language and semantic tasks | 1,050 | 15% |
| Paired permission, ambiguity and confirmation boundaries | 700 | 10% |
| **Total** | **7,000** | **100%** |

All examples initially have weight 1.0. The 700 boundary records form 350 pairs, containing 400 legitimate calls and 300 no-call targets. The exact compressed training file has SHA-256:

```text
9eaaef69d7b827c8996f5b565289b6def000b0c800d11dda1a32007373722d09
```

TeamSync and semantic worlds are assistant-authored fictional fixtures. Public dialogue comes from filtered TWLLM data with model-generated replacement answers. **No private LangSmith customer conversation was used to train this adapter.** Filtering and teacher replacement do not independently establish factual correctness or anonymity.

A later 10,000-example mixture was prepared with a 50% tool / 40% natural zh-TW / 10% grounded-semantics allocation. That corpus did **not** train this checkpoint. It is documented separately in [the data notes](docs/data.md).

## Download and run

Release assets are published in [ShuChenAI/formosync Releases](https://github.com/ShuChenAI/formosync/releases/tag/v0.1.0). The adapter package contains the weights, matching tokenizer/template, model identity, licenses and checksums. The data package contains the exact 7,000-example training file and provenance.

```bash
gh release download v0.1.0 --repo ShuChenAI/formosync --dir downloads
mkdir -p models/adapter
tar -xzf downloads/formosync-e4b-v0.1.0-adapter.tar.gz --strip-components=1 -C models/adapter
python -m pip install torch==2.7.1 --index-url https://download.pytorch.org/whl/cu118
python -m pip install "transformers==5.21.0" "peft==0.21.2" "bitsandbytes==0.50.2"
python -m pip install downloads/formosync-0.1.0-py3-none-any.whl
```

Obtain the pinned base as described below, then run:

```bash
python -m formosync.chat --base-dir models/base --adapter-dir models/adapter \
  --prompt "我說的不是每年，是今年一月到十二月。請幫我把需求說清楚。"
```

The CLI uses the recorded precision-restoration path, checks the release adapter hash and does not execute tools. Use a CUDA-capable Linux environment compatible with the recorded dependencies. Hardware requirements and compatibility beyond the reference environment have not been newly certified.

## Loading the adapter

The reference environment used Python 3.12.16, PyTorch 2.7.1+cu118, Transformers 5.21.0, PEFT 0.21.2 and bitsandbytes 0.50.2 on an H100 MIG 40GB instance. This is the recorded environment, not a minimum hardware claim or a newly verified installation matrix.

1. Obtain the complete pinned NVIDIA base, including its configuration, tokenizer, index, and `model-frozen-shared-kv.safetensors`. Keep the upstream files together in `models/base/`.
2. Obtain the adapter and its matching tokenizer/template from the release package and place them in `models/adapter/`.
3. Use the native chat template and apply the complete adapter state.

The upstream download command is:

```bash
hf download nvidia/NVIDIA-Nemotron-3.5-Bolt-E4B-BF16 \
  --revision 49843eed8db1f1c616c47af75cfd36e07aec0667 \
  --local-dir models/base
```

The following loading example follows the recorded model class and quantization settings. It has not received a new GPU smoke test outside the preserved reference environment.

```python
import os
from pathlib import Path
import torch
from transformers import AutoTokenizer

os.environ["FORMOSYNC_BASE_DIR"] = "models/base"
os.environ["FORMOSYNC_OUTPUT_DIR"] = "results/example"
from formosync.runtime import load_model, render

config = {
    "model": "nvidia/NVIDIA-Nemotron-3.5-Bolt-E4B-BF16",
    "revision": "49843eed8db1f1c616c47af75cfd36e07aec0667",
}
model = load_model(config, Path("models/adapter"), False)
tokenizer = AutoTokenizer.from_pretrained("models/base", local_files_only=True)
row = {
    "messages": [
        {"role": "system", "content": "你是使用臺灣繁體中文的助理。依上下文理解需求，資訊不足時先澄清。"},
        {"role": "user", "content": "我說的不是每年，是今年一月到十二月。請幫我把這句需求說清楚。"},
    ],
    "tools": [],
}
inputs = tokenizer(
    render(tokenizer, row), return_tensors="pt", add_special_tokens=False
).to(model.device)
with torch.inference_mode():
    generated = model.generate(
        **inputs, do_sample=False, max_new_tokens=256,
        pad_token_id=tokenizer.pad_token_id,
    )
print(tokenizer.decode(
    generated[0, inputs.input_ids.shape[1]:], skip_special_tokens=False
))
```

For tool use, supply the current tool JSON schemas through the template's `tools` argument. Parse the publisher's native tool-call representation before considering execution. This adapter does not provide a tool runner or a backend authorization layer.

## Application boundaries

The application remains responsible for permissions, record scope, confirmation, argument validation and execution. In particular:

- `requires_confirmation_for_ct_action` is server policy, never a model-generated tool parameter.
- A staged-operation executor is available only when the server has armed the current proposal. Its token comes from the current server-supplied capability.
- A model response is not evidence that a write succeeded. Report completion only from the corresponding successful tool result.

Evaluate the model against your own schemas and no-call cases before connecting write-capable tools. The observed no-call regressions make those application boundaries material to this release.

## Known limits

This release has no independent human validation of general Taiwanese fluency, Hokkien or code-switching. Its training modality does not establish improved image or audio performance. Public teacher answers can contain mistakes, and knowledge scores regress on the recorded reserved sample. The complete joint acceptance gate remains false.

## Licensing and attribution

Source code and repository-authored documentation are under [Apache-2.0](LICENSE). Model materials retain [OpenMDW-1.1](licenses/OpenMDW-1.1.txt) and applicable upstream notices. Data components retain their own source licenses and attribution; the repository's documentation license does not replace them.

See [NOTICE.md](NOTICE.md) for NVIDIA, Google, TWLLM and Glaive source notices. Preserve those files when redistributing the corresponding materials.

## Contributing

Useful contributions include independently written zh-TW evaluation cases, clearer ambiguity/confirmation contrasts, schema-grounding checks and reproducible runtime reports. Describe the exact base revision, adapter hash, template and decoding settings with a result. Keep customer conversations, credentials and private business records out of public issues and pull requests.
