# SPDX-License-Identifier: Apache-2.0
"""One-model, inference-only TMMLU+ and optional authored-scenario benchmark."""
import argparse,collections,datetime,hashlib,importlib.metadata,json,math,os,time
from pathlib import Path

def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');temporary.replace(path)

def mcq_prompt(row):
    choices='\n'.join(f"{key}. {row['choices'][key]}" for key in 'ABCD')
    return '請回答以下單選題。只輸出正確選項的英文字母（A、B、C 或 D）。\n\n'+row['question']+'\n'+choices+'\n答案：'

def wilson(passed,n):
    if not n:return [None,None]
    z=1.959963984540054;p=passed/n;den=1+z*z/n
    center=(p+z*z/(2*n))/den;half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [center-half,center+half]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label',choices=['base','formosync'],required=True)
    parser.add_argument('--base-dir',type=Path,default=Path('models/base'))
    parser.add_argument('--adapter-dir',type=Path,default=Path('models/adapter'))
    parser.add_argument('--base-manifest',type=Path,default=Path('models/base-manifest.json'))
    parser.add_argument('--data',type=Path,default=Path('data/tmmlu-full.jsonl.gz'))
    parser.add_argument('--fixtures',type=Path,action='append',default=[])
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--deadline',help='Optional timezone-aware ISO8601 operational cutoff')
    args=parser.parse_args();args.output_dir.mkdir(parents=True,exist_ok=True)
    deadline=datetime.datetime.fromisoformat(args.deadline) if args.deadline else None
    def check():
        if deadline and datetime.datetime.now(datetime.timezone.utc)>=deadline:raise TimeoutError('Benchmark deadline reached')
    check();manifest=json.loads(args.base_manifest.read_text())
    for item in manifest['files']:
        check();p=args.base_dir/item['name']
        if p.stat().st_size!=item['bytes'] or sha(p)!=item['sha256']:raise ValueError('Base mismatch: '+item['name'])
    adapter=args.adapter_dir if args.label=='formosync' else None
    from .chat import ADAPTER_SHA
    if adapter and sha(adapter/'adapter_model.safetensors')!=ADAPTER_SHA:raise ValueError('Unexpected adapter')
    os.environ['FORMOSYNC_BASE_DIR']=str(args.base_dir)
    os.environ['FORMOSYNC_OUTPUT_DIR']=str(args.output_dir)
    import torch
    from transformers import AutoTokenizer,set_seed
    from .runtime import load_model,render,read
    set_seed(20261102);torch.set_num_threads(1)
    config={'model':manifest['model_id'],'revision':manifest['revision']}
    identity={'label':args.label,'base_model':manifest['model_id'],'base_revision':manifest['revision'],
        'base_manifest_sha256':sha(args.base_manifest),'base_all_files_sha256_verified':True,
        'adapter_sha256':ADAPTER_SHA if adapter else None,'data_sha256':sha(args.data),
        'fixture_sha256':[sha(p) for p in args.fixtures],'seed':20261102,
        'versions':{p:importlib.metadata.version(p) for p in ['torch','transformers','peft','bitsandbytes']},
        'protocol':'Full supplied TMMLU+ rows; zero-shot next-token likelihood restricted to A/B/C/D; no tools; no answer-dependent filtering; same native template; thinking disabled.',
        'quantization':'NF4 double quantization, BF16 compute, checkpoint-BF16 frozen embeddings, FP32 norms',
        'optimizer_updates':0,'runner_sha256':sha(Path(__file__))}
    write(args.output_dir/'identity.json',identity)
    write(args.output_dir/'state.json',{'stage':'loading_model','label':args.label,'time':time.time()})
    tokenizer=AutoTokenizer.from_pretrained(args.base_dir,local_files_only=True)
    tokenizer.chat_template=(args.base_dir/'chat_template.jinja').read_text()
    model=load_model(config,adapter,False);records=[];started=time.time();rows=list(read(args.data))
    assert len({r['id'] for r in rows})==len(rows) and rows
    letters=list('ABCD');letter_tokens=[tokenizer(x,add_special_tokens=False)['input_ids'] for x in letters]
    assert all(len(x)==1 for x in letter_tokens)
    ids=[x[0] for x in letter_tokens]
    with (args.output_dir/'tmmlu-predictions.jsonl').open('w') as stream,torch.inference_mode():
        for index,row in enumerate(rows):
            check();native={'messages':[{'role':'user','content':mcq_prompt(row)}],'tools':[]}
            encoded=tokenizer(render(tokenizer,native),return_tensors='pt',add_special_tokens=False).to(model.device)
            if encoded.input_ids.shape[1]>32768:
                record={'id':row['id'],'subject':row['subject'],'prediction':None,'answer':row['answer'],'correct':False,'over_context':True}
            else:
                with torch.autocast('cuda',dtype=torch.bfloat16):output=model(**encoded,logits_to_keep=1,use_cache=False)
                logits=output.logits[0,-1].float();choice_logits=logits[ids]
                prediction=letters[int(choice_logits.argmax())]
                record={'id':row['id'],'subject':row['subject'],'prediction':prediction,'answer':row['answer'],
                    'correct':prediction==row['answer'],'choice_probabilities':dict(zip(letters,choice_logits.softmax(-1).cpu().tolist())),
                    'unconstrained_top1_is_choice':int(logits.argmax()) in ids,'over_context':False}
                del output,logits,choice_logits
            records.append(record);stream.write(json.dumps(record,ensure_ascii=False)+'\n');stream.flush();del encoded
            if (index+1)%25==0 or index+1==len(rows):
                value={'stage':'tmmluplus','label':args.label,'done':index+1,'total':len(rows),'seconds':time.time()-started,'time':time.time()}
                write(args.output_dir/'state.json',value);print(json.dumps(value),flush=True)
    subjects=collections.defaultdict(list)
    for r in records:subjects[r['subject']].append(r['correct'])
    passed=sum(r['correct'] for r in records);tmmlu={'n':len(records),'passed':passed,'accuracy':passed/len(records),
        'wilson_95':wilson(passed,len(records)),'subject_macro':sum(sum(v)/len(v) for v in subjects.values())/len(subjects),
        'by_subject':{s:{'n':len(v),'passed':sum(v),'accuracy':sum(v)/len(v)} for s,v in sorted(subjects.items())},
        'over_context_counted_in_denominator':sum(r['over_context'] for r in records),'seconds':time.time()-started}
    write(args.output_dir/'tmmlu-metrics.json',tmmlu);authored={}
    if args.fixtures:
        from .scoring.joint_scoring import score
        from .scoring.selection import summarize
        eos=model.generation_config.eos_token_id;eos={eos} if isinstance(eos,int) else set(eos)
        with torch.inference_mode():
            for fixture in args.fixtures:
                group=fixture.stem;outputs=[];cases=list(read(fixture));cap=256 if group=='test_frozen' else 512
                with (args.output_dir/(group+'-predictions.jsonl')).open('w') as stream:
                    for index,row in enumerate(cases):
                        check();encoded=tokenizer(render(tokenizer,row),return_tensors='pt',add_special_tokens=False).to(model.device)
                        budget=min(cap,32768-encoded.input_ids.shape[1]);assert budget>0
                        with torch.autocast('cuda',dtype=torch.bfloat16):out=model.generate(**encoded,do_sample=False,max_new_tokens=budget,pad_token_id=tokenizer.pad_token_id,use_cache=True)
                        generated=out[0,encoded.input_ids.shape[1]:];text=tokenizer.decode(generated,skip_special_tokens=False)
                        truncated=len(generated)>=budget and int(generated[-1]) not in eos;verdict=score(row,text)
                        if truncated:verdict['success']=False
                        import re
                        record={'id':row['id'],'category':row.get('category',row.get('benchmark','unknown')),'family':row['family'],
                            'case_id':row.get('case_id'),'pair_id':row.get('pair_id'),'truncated':bool(truncated),
                            'attempted_call':bool(verdict.get('calls')) or '<|tool_call>' in text,
                            'attempted_commit':bool(re.search(r'call:custom_tables_(?:insert_record|update_record|delete_record|bulk_record_actions|execute_staged_)',text)),**verdict}
                        outputs.append(record);stream.write(json.dumps(record,ensure_ascii=False)+'\n');stream.flush()
                        del out,generated,encoded
                        if (index+1)%10==0 or index+1==len(cases):write(args.output_dir/'state.json',{'stage':group,'label':args.label,'done':index+1,'total':len(cases),'time':time.time()})
                authored[group]=summarize(outputs);write(args.output_dir/(group+'-metrics.json'),authored[group])
    write(args.output_dir/'summary.json',{'identity':identity,'tmmluplus':tmmlu,'authored':authored,
          'completed_at':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    write(args.output_dir/'state.json',{'stage':'complete','label':args.label,'time':time.time()})
    (args.output_dir/'COMPLETE').write_text('Inference benchmark complete; no model updates or backend operations.\n')

if __name__=='__main__':main()
