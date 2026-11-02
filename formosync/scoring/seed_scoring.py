# SPDX-License-Identifier: Apache-2.0
"""Structured semantics is the comprehension metric; no-call alone is not."""
import json,re,sys,os
from pathlib import Path
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parent
from .legacy_scoring import parse_calls
SPECIAL=re.compile(r'<\|[^>]*>|<turn\|>|<bos>|<eos>')
def validation_schema(value):
 if isinstance(value,list):return [validation_schema(x) for x in value]
 if not isinstance(value,dict):return value
 result={k:validation_schema(v) for k,v in value.items() if k!='nullable'}
 return {'anyOf':[result,{'type':'null'}]} if value.get('nullable') else result
SCHEMA=json.loads((ROOT/'answer-schema.json').read_text())

def score(row,text):
 try:calls=parse_calls(text);parse_ok=True
 except Exception:calls=[];parse_ok=False
 if row['view']=='semantic':
  body=SPECIAL.sub('',text).strip()
  if body.startswith('```'):body=re.sub(r'^```(?:json)?\s*|\s*```$','',body).strip()
  try:answer=json.loads(body);Draft202012Validator(SCHEMA).validate(answer);valid=True
  except Exception:answer=None;valid=False
  expected=row['expected'];exact=valid and not calls and answer==expected
  slots=['對象','數量','單價','約略','日期','時間起','時間迄','時間是否精確']
  return {'parse_ok':parse_ok,'schema_valid':valid,'semantic_exact':bool(exact),
          'next_action_correct':bool(valid and answer['下一步']==expected['下一步']),
          'resolved_slots_correct':bool(valid and all(answer[k]==expected[k] for k in slots)),
          'missing_fields_correct':bool(valid and set(answer['缺少資訊'])==set(expected['缺少資訊'])),
          'write_effect_correct':bool(valid and answer['本步寫入']==expected['本步寫入'])}
 expected=row['expected_name'];choice=parse_ok and ((len(calls)==1 and calls[0]['name']==expected) if expected else not calls)
 valid=parse_ok
 for call in calls:
  spec=next((t['function']['parameters'] for t in row['tools'] if t['function']['name']==call['name']),None)
  try:
   assert spec is not None
   Draft202012Validator(validation_schema(spec)).validate(call['arguments'])
  except Exception:valid=False
 args=False if expected else None
 if expected and choice and valid:
  actual=calls[0]['arguments'];gold=row['expected_args'];args=True
  for key,value in gold.items():
   if expected=='custom_tables_analyze' and key=='question':
    question=actual.get(key,'');args &= isinstance(question,str) and all(s in question for s in ['甲單','數量','單價','總額']) and bool(re.search('核對|比對|一致|正確',question))
   else:args &= actual.get(key)==value
  spec=next(t['function']['parameters'] for t in row['tools'] if t['function']['name']==expected)
  for key,value in actual.items():
   if key not in gold:args &= value==spec.get('properties',{}).get(key,{}).get('default')
 return {'parse_ok':parse_ok,'tool_choice_correct':bool(choice),'schema_valid':bool(valid),
         'arguments_correct':args,'natural_reply_quality':'not_automatically_scored',
         'no_call_is_not_comprehension_success':True}
