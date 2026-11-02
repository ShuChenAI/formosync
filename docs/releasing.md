# Release layout

The public repository is `ShuChenAI/formosync`. Code and documentation use Apache-2.0; model and data materials retain the component terms described in [NOTICE.md](../NOTICE.md).

Version `v0.1.0` identifies the R6 step768 LoRA adapter and its exact 7,000-example corpus. The separately prepared 10k corpus did not train this model.

GitHub Releases carry the adapter archive, data archive, Python wheel, release manifest and SHA256SUMS. Weight binaries are not stored in regular Git. The adapter archive is a complete PEFT state, not a merged standalone base model. Its native tokenizer/template are included.

Keep the adapter weight hash, base revision, training-file hash, component licenses and evaluation limitations with any mirror. Preserve regression results as well as improvements. Fresh benchmark outputs are separately versioned from the historical R6 comparison.

Public packages exclude private customer exports, authentication material, private-backup receipts and infrastructure controllers. Source provenance accompanies the filtered training file. The unfiltered TWLLM source is not part of the package.
