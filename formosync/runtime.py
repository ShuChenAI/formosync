# SPDX-License-Identifier: Apache-2.0
"""Verified parent loading and common training I/O, derived from Round 2."""
import array,collections,gc,gzip,hashlib,importlib.metadata,json,math,os,struct,time
from pathlib import Path
import torch
from peft import PeftModel,LoraConfig,get_peft_model,get_peft_model_state_dict,prepare_model_for_kbit_training
from safetensors.torch import load_file
from transformers import AutoModelForImageTextToText,AutoTokenizer,BitsAndBytesConfig,Trainer,TrainingArguments,TrainerCallback,set_seed
ROOT=Path(os.environ.get('FORMOSYNC_OUTPUT_DIR','results'))
ROOT.mkdir(parents=True,exist_ok=True)
BASE_DIR=Path(os.environ.get('FORMOSYNC_BASE_DIR','models/base'))


def read(path):
    opener=gzip.open if str(path).endswith('.gz') else open
    with opener(path,'rt',encoding='utf-8') as stream:
        for line in stream:yield json.loads(line)

def write(name,value):
    path=ROOT/name;path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(path.name+'.tmp');tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2));tmp.replace(path)

def phase(name,**kwargs):write('state.json',{'stage':name,'time':time.time(),**kwargs})

def render(tokenizer,row,target=False):
    if target:
        return tokenizer.apply_chat_template(row['messages']+[row['target']],tools=row['tools'],tokenize=False,add_generation_prompt=False,enable_thinking=False)
    # The publisher template forward-scans consecutive assistant/tool turns.
    # An answer-independent empty continuation boundary prevents it from closing
    # the preceding tool turn merely because the future assistant is absent.
    marker='__TS_NEXT_ASSISTANT_BOUNDARY_6b082ce1__'
    rendered=tokenizer.apply_chat_template(row['messages']+[{'role':'assistant','content':marker}],tools=row['tools'],tokenize=False,add_generation_prompt=False,enable_thinking=False)
    assert rendered.count(marker)==1
    return rendered[:rendered.index(marker)]

def load_model(config,adapter,trainable):
    quant=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='nf4',bnb_4bit_use_double_quant=True,bnb_4bit_compute_dtype=torch.bfloat16)
    base=AutoModelForImageTextToText.from_pretrained(BASE_DIR,quantization_config=quant,device_map={'':0},dtype=torch.bfloat16,attn_implementation={'':'eager','text_config':'sdpa','vision_config':'eager','audio_config':'eager'},low_cpu_mem_usage=True,local_files_only=True)
    base=prepare_model_for_kbit_training(base,use_gradient_checkpointing=trainable)
    # k-bit preparation promotes all frozen embeddings to FP32. This Gemma
    # checkpoint contains ~3.49B embedding values that were originally BF16.
    # Restore only checkpoint-confirmed, frozen BF16 embedding parameters,
    # checking every value for an exact FP32 round trip. Norms stay FP32.
    original={}
    for shard in (BASE_DIR).glob('*.safetensors'):
        with shard.open('rb') as stream:
            size=struct.unpack('<Q',stream.read(8))[0];header=json.loads(stream.read(size))
        original.update({k:v for k,v in header.items() if k!='__metadata__'})
    allocated_before=torch.cuda.memory_allocated()
    restored=[];seen=set()
    for name,module in base.named_modules():
        if not isinstance(module,torch.nn.Embedding):continue
        parameter=module.weight;key=name+'.weight'
        if id(parameter) in seen:continue
        seen.add(id(parameter))
        if original.get(key,{}).get('dtype')!='BF16':continue
        assert not parameter.requires_grad,key
        if parameter.dtype==torch.bfloat16:continue
        assert parameter.dtype==torch.float32,key
        old=parameter.data;new=old.to(torch.bfloat16)
        old_flat=old.reshape(-1);new_flat=new.reshape(-1)
        for start in range(0,old.numel(),16*1024*1024):
            end=min(start+16*1024*1024,old.numel())
            assert torch.equal(old_flat[start:end],new_flat[start:end].float()),('Embedding precision would discard values',key)
        parameter.data=new
        restored.append({'parameter':key,'elements':parameter.numel(),'original_checkpoint_dtype':'BF16',
                         'restored_dtype':'bfloat16','exact_fp32_value_roundtrip':True,'bytes_saved':parameter.numel()*2})
        del old,old_flat,new_flat,new;gc.collect();torch.cuda.empty_cache()
    norm_parameters=[p for n,p in base.named_parameters() if 'norm' in n.lower() and p.is_floating_point()]
    assert all(p.dtype==torch.float32 for p in norm_parameters),'Norm precision changed'
    write('frozen-embedding-precision.json',{'parameters':restored,'bytes_saved':sum(x['bytes_saved'] for x in restored),
          'observed_allocated_bytes_reduced':allocated_before-torch.cuda.memory_allocated(),
          'norms_kept_fp32':True,'norm_parameter_tensors_checked':len(norm_parameters),
          'frozen_only':True,'source_weights_unchanged':True})
    if adapter is None:
        if trainable:
            lora=LoraConfig(r=config['lora_r'],lora_alpha=config['lora_alpha'],lora_dropout=.05,bias='none',task_type='CAUSAL_LM',target_modules=r'.*language_model.*\.(q_proj|k_proj|v_proj|o_proj|gate_proj|up_proj|down_proj)')
            model=get_peft_model(base,lora);model.peft_config['default'].base_model_name_or_path=config['model'];model.peft_config['default'].revision=config['revision']
            state=get_peft_model_state_dict(model,save_embedding_layers=False);b=[v for n,v in state.items() if 'lora_B' in n]
            assert b and all(torch.count_nonzero(v)==0 for v in b),'Fresh LoRA must initially have zero B matrices'
            write('fresh-initialization.json',{'from_base':True,'prior_round_adapter_loaded':False,'zero_B_tensors':len(b),'adapter_tensors':len(state)})
            model.eval();model.config.use_cache=True
            return model
        base.eval();base.config.use_cache=True
        return base
    model=PeftModel.from_pretrained(base,adapter,is_trainable=trainable,local_files_only=True)
    saved=load_file(str(adapter/'adapter_model.safetensors'),device='cpu');loaded=get_peft_model_state_dict(model,save_embedding_layers=False)
    assert set(saved)==set(loaded),'Adapter tensor-key mismatch'
    for name,value in saved.items():assert torch.equal(value,loaded[name].detach().cpu()),name
    del saved,loaded
    model.peft_config['default'].base_model_name_or_path=config['model'];model.peft_config['default'].revision=config['revision']
    model.eval();model.config.use_cache=True
    return model
