# Licensing and source attribution

FormoSync E4B combines a derived model artifact with independently documented training and evaluation work. Component terms remain distinct.

| Component | Terms / notice |
|---|---|
| Source code and newly authored repository documentation | [Apache-2.0](LICENSE) |
| NVIDIA base and distributed model materials | [OpenMDW-1.1](licenses/OpenMDW-1.1.txt); retain applicable notices from the [pinned NVIDIA model card](licenses/NVIDIA-MODEL-CARD.md) |
| Google foundation | NVIDIA identifies `google/gemma-4-E4B-it` and Apache-2.0; preserve the applicable upstream origin notices |
| Public TWLLM dialogue component | Apache-2.0 per publisher; preserve [TWLLM-README.md](licenses/TWLLM-README.md) and per-record provenance |
| Glaive public replay component | Preserve [Glaive-README.md](licenses/Glaive-README.md) and its applicable terms |

The base is `nvidia/NVIDIA-Nemotron-3.5-Bolt-E4B-BF16`, revision `49843eed8db1f1c616c47af75cfd36e07aec0667`. The preserved NVIDIA card has SHA-256 `5b6689e7b829b0e79a78802b9581c6c01529a23f87b39925e0b57f3eaeacbfac`.

The OpenMDW-1.1 and Apache-2.0 texts are retained verbatim. Their SHA-256 values are `2ab44b68365473c112f5092211a38f231cb23e50de68b75a13369adbd76a74df` and `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`, respectively.

The training dialogue source is `yentinglin/twllm-data`, revision `027f9f20c0d80d3695e1477c874ca9f102eccb68`. Its publisher card requests attribution to:

> Yen-Ting Lin and Yun-Nung Chen. *Taiwan LLM: Bridging the Linguistic Divide with a Culturally Aligned Language Model*. 2023. arXiv:2311.17487. https://doi.org/10.48550/arXiv.2311.17487

The documentation license does not relicense upstream models or third-party dataset components. Distribute each artifact with the notices applicable to it.
