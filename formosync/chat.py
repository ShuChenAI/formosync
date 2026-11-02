# SPDX-License-Identifier: Apache-2.0
"""Local text inference. This command does not execute tools."""
import argparse
import hashlib
import os
from pathlib import Path

ADAPTER_SHA = "fecf928856466c605aed86cc55d23e9fdb8da7f8c7fb06a381c140c2da53bd05"

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base-dir', type=Path, default=Path('models/base'))
    p.add_argument('--adapter-dir', type=Path, default=Path('models/adapter'))
    p.add_argument('--output-dir', default='results/chat')
    p.add_argument('--prompt', required=True)
    p.add_argument('--max-new-tokens', type=int, default=256)
    args = p.parse_args()
    with (args.adapter_dir/'adapter_model.safetensors').open('rb') as f:
        if hashlib.file_digest(f,'sha256').hexdigest() != ADAPTER_SHA:
            raise ValueError('Adapter differs from the v0.1.0 release')
    os.environ['FORMOSYNC_BASE_DIR'] = str(args.base_dir)
    os.environ['FORMOSYNC_OUTPUT_DIR'] = str(args.output_dir)
    import torch
    from transformers import AutoTokenizer
    from .runtime import load_model,render
    config={'model':'nvidia/NVIDIA-Nemotron-3.5-Bolt-E4B-BF16',
            'revision':'49843eed8db1f1c616c47af75cfd36e07aec0667'}
    model=load_model(config,args.adapter_dir,False)
    tokenizer=AutoTokenizer.from_pretrained(args.adapter_dir,local_files_only=True)
    row={'messages':[{'role':'user','content':args.prompt}],'tools':[]}
    inputs=tokenizer(render(tokenizer,row),return_tensors='pt',add_special_tokens=False).to(model.device)
    with torch.inference_mode():
        generated=model.generate(**inputs,do_sample=False,max_new_tokens=args.max_new_tokens,
                                 pad_token_id=tokenizer.pad_token_id)
    print(tokenizer.decode(generated[0,inputs.input_ids.shape[1]:],skip_special_tokens=False))

if __name__=='__main__':main()
