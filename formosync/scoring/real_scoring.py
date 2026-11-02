# SPDX-License-Identifier: Apache-2.0
"""Frozen synthetic scoring plus explicitly labeled real teacher agreement."""
import collections,json,re
from jsonschema import Draft202012Validator
from .legacy_scoring import parse_calls
from .frozen_scoring import score as synthetic_score,validation_schema,SPECIAL

def canonical_calls(calls,tools):
    schemas={t['function']['name']:t['function']['parameters'] for t in tools}
    canonical=[]
    for call in calls:
        args=dict(call['arguments']);properties=schemas.get(call['name'],{}).get('properties',{})
        for k,spec in properties.items():
            if k not in args and 'default' in spec:args[k]=spec['default']
        canonical.append(json.dumps({'name':call['name'],'arguments':args},ensure_ascii=False,sort_keys=True))
    return sorted(canonical)

def score(row,text):
    if row.get('benchmark')!='real_teacher_reference':return synthetic_score(row,text)
    try:calls=parse_calls(text);parse_ok=True
    except Exception:calls=[];parse_ok=False
    expected=[{'name':c['function']['name'],'arguments':c['function']['arguments']} for c in row['target'].get('tool_calls',[])]
    names=collections.Counter(c['name'] for c in calls);gold_names=collections.Counter(c['name'] for c in expected)
    valid=parse_ok
    for call in calls:
        schema=next((t['function']['parameters'] for t in row['tools'] if t['function']['name']==call['name']),None)
        try:
            assert schema is not None
            Draft202012Validator(validation_schema(schema)).validate(call['arguments'])
        except Exception:valid=False
    choice=parse_ok and names==gold_names
    args=bool(valid and choice and canonical_calls(calls,row['tools'])==canonical_calls(expected,row['tools'])) if expected else None
    response_exact=None
    if not expected:
        normalize=lambda s:re.sub(r'\s+','',SPECIAL.sub('',s)).strip()
        response_exact=not calls and normalize(text)==normalize(row['target'].get('content',''))
    return {'teacher_tool_choice_agreement':bool(choice),'schema_valid':bool(valid),
            'teacher_arguments_exact_agreement':args,'response_exact_match_reference':response_exact,
            'parse_ok':parse_ok,'calls':calls,'label_status':'unverified_teacher_reference_not_task_success'}
