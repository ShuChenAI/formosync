# SPDX-License-Identifier: Apache-2.0
"""Fetch and pin all 67 TMMLU+ test CSVs; does not load a model."""
import argparse,csv,gzip,hashlib,io,json,urllib.request,urllib.parse
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,default=Path('benchmarks/tmmlu-source-manifest.json'))
    p.add_argument('--output',type=Path,default=Path('data/tmmlu-full.jsonl.gz'))
    p.add_argument('--source-dir',type=Path)
    args=p.parse_args();manifest=json.loads(args.manifest.read_text());rows=[]
    for source in manifest['sources']:
        filename=Path(source['source']).name
        if args.source_dir:body=(args.source_dir/filename).read_bytes()
        else:
            path=urllib.parse.quote(source['source'],safe='/')
            url=f"https://huggingface.co/datasets/{manifest['dataset']}/resolve/{manifest['revision']}/{path}"
            with urllib.request.urlopen(url,timeout=60) as response:body=response.read()
        if hashlib.sha256(body).hexdigest()!=source['sha256']:raise ValueError('Source hash mismatch: '+filename)
        subject=filename.removesuffix('_test.csv')
        records=list(csv.DictReader(io.StringIO(body.decode('utf-8-sig'))))
        if len(records)!=source['original_test_rows']:raise ValueError('Source count mismatch: '+filename)
        for index,r in enumerate(records):
            if r['answer'] not in 'ABCD':raise ValueError('Invalid answer label')
            rows.append({'id':f'tmmlu:{subject}:{index}','benchmark':'tmmluplus','subject':subject,
                         'question':r['question'],'choices':{k:r[k] for k in 'ABCD'},'answer':r['answer']})
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('wb') as raw,gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as stream:
        for row in rows:stream.write((json.dumps(row,ensure_ascii=False)+'\n').encode())
    print(json.dumps({'rows':len(rows),'subjects':len(manifest['sources']),
                      'sha256':hashlib.sha256(args.output.read_bytes()).hexdigest()}))

if __name__=='__main__':main()
