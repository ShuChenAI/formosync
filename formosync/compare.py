# SPDX-License-Identifier: Apache-2.0
"""Compare two complete runs with identical data, runtime and precision."""
import argparse,json
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True)
    p.add_argument('--formosync',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    for folder in [args.base,args.formosync]:
        if not (folder/'COMPLETE').exists():raise ValueError('Incomplete benchmark: '+str(folder))
    base=json.loads((args.base/'summary.json').read_text());tuned=json.loads((args.formosync/'summary.json').read_text())
    for key in ['base_model','base_revision','base_manifest_sha256','data_sha256','fixture_sha256','seed','versions','protocol','quantization','runner_sha256']:
        if base['identity'][key]!=tuned['identity'][key]:raise ValueError('Comparison mismatch: '+key)
    def predictions(folder):return {r['id']:r for r in map(json.loads,(folder/'tmmlu-predictions.jsonl').read_text().splitlines())}
    before=predictions(args.base);after=predictions(args.formosync)
    if set(before)!=set(after):raise ValueError('Question IDs differ')
    paired={'both_correct':0,'base_only':0,'formosync_only':0,'both_wrong':0}
    for key,b in before.items():
        a=after[key]
        if a['answer']!=b['answer']:raise ValueError('Gold label mismatch')
        label='both_correct' if a['correct'] and b['correct'] else 'base_only' if b['correct'] else 'formosync_only' if a['correct'] else 'both_wrong'
        paired[label]+=1
    result={'base':base,'formosync':tuned,'tmmlu_accuracy_delta':tuned['tmmluplus']['accuracy']-base['tmmluplus']['accuracy'],
            'paired':paired,'protocol_matches':True,'model_acceptance_implied':False,
            'limits':['Zero-shot likelihood adaptation, not the official few-shot leaderboard protocol.',
                      'Base pretraining contamination is unknown.','Authored tests share training scenario rules and have prior diagnostic use.']}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'base_accuracy':base['tmmluplus']['accuracy'],'formosync_accuracy':tuned['tmmluplus']['accuracy'],'paired':paired}))

if __name__=='__main__':main()
