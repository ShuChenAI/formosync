# SPDX-License-Identifier: Apache-2.0
"""Round-3 rubrics frozen before measuring the warm-start checkpoint."""
import json,re,unicodedata
from decimal import Decimal,InvalidOperation
from jsonschema import Draft202012Validator
from .legacy_scoring import parse_calls,score_v1

SPECIAL=re.compile(r'<\|[^>]*>|<turn\|>|<bos>|<eos>')
INTERNAL=re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|\b[0-9a-f]{32}\b',re.I)
def normalized(x):return re.sub(r'\s+','',unicodedata.normalize('NFKC',x)).strip('。.!！')
def answer_schema(value):
    if isinstance(value,dict):return {'type':'object','properties':{k:answer_schema(v) for k,v in value.items()},'required':list(value),'additionalProperties':False}
    if isinstance(value,list):return {'type':'array','items':answer_schema(value[0]) if value else {}}
    if isinstance(value,bool):return {'type':'boolean'}
    if value is None:return {'type':['number','string','null']}
    if isinstance(value,int):return {'type':'integer'}
    if isinstance(value,float):return {'type':'number'}
    if isinstance(value,str) and re.fullmatch(r'-?\d+(?:\.\d+)?',value):return {'type':['number','string']}
    return {'type':'string'}
def add_answer_format(row):
    schema=answer_schema(row['semantic_expected'])
    def no_answers(node):
        if isinstance(node,dict):
            assert not {'enum','const','default','examples','minimum','maximum'}.intersection(node)
            for value in node.values():no_answers(value)
        elif isinstance(node,list):
            for value in node:no_answers(value)
    no_answers(schema)
    row['answer_schema']=schema
    row['messages'][0]['content']+='\n輸出格式：只回覆符合以下JSON Schema的物件；此結構只規定欄名與型別，答案必須從題目推導。\n'+json.dumps(schema,ensure_ascii=False)
    return row

ALIASES={
 ('wan','currency'):r'(?i:^(?:TWD|NTD|NT\$|新臺幣|新台幣)$)',
 ('decimal','currency'):r'(?i:^(?:TWD|NTD|NT\$|新臺幣|新台幣)$)',
 ('double_negative','issue'):r'(短少|少了?|不足).*(兩|二|2).*包',
 ('missing_date','missing'):r'(年.*月|月.*年)',
 ('table','target'):r'請購',
 ('cause','cause'):r'(缺料|物料不足|材料不足|缺少.*料)',
 ('difference','direction'):r'(減少|減|降低|下降)',
 ('summary','文件'):r'(收齊|齊全|已齊)',
 ('summary','審核'):r'(未.*(通過|核准)|不通過|未過)',
 ('summary','付款'):r'(未|尚未|還沒|待).*付',
}
def equal_value(actual,gold,slug='',path=()):
    if isinstance(gold,dict):return isinstance(actual,dict) and set(actual)==set(gold) and all(equal_value(actual[k],v,slug,path+(k,)) for k,v in gold.items())
    if isinstance(gold,list):
        if not isinstance(actual,list) or len(actual)!=len(gold):return False
        if path and path[-1] in {'years','notify','regions','days','not_causes','missing'}:
            remaining=list(actual)
            for value in gold:
                match=next((i for i,item in enumerate(remaining) if equal_value(item,value,slug,path)),None)
                if match is None:return False
                remaining.pop(match)
            return True
        return all(equal_value(a,b,slug,path) for a,b in zip(actual,gold))
    if isinstance(gold,bool):return isinstance(actual,bool) and actual is gold
    if gold is None:return actual is None
    if isinstance(gold,(int,float)) or isinstance(gold,str) and re.fullmatch(r'-?\d+(?:\.\d+)?',gold):
        try:return not isinstance(actual,bool) and Decimal(str(actual))==Decimal(str(gold))
        except (InvalidOperation,ValueError):return False
    if not isinstance(actual,str):return False
    if normalized(actual)==normalized(gold):return True
    rule=ALIASES.get((slug,path[-1] if path else ''))
    return bool(rule and re.search(rule,normalized(actual)))

NO_CALL={
 'ambiguous_target':[r'(指定|哪|選|確認)'],
 'negative_consent':[r'(不執行|不會|不進行|不要|取消|暫停)'],
 'unclear_consent':[r'(待確認|尚未|還沒|不會執行|未確認|不執行)'],
 'expired':[r'(過期|逾期|失效)',r'(重新|不能|無法)'],
 'revoked':[r'(權限|授權)',r'(不能|不可|不會|無法)'],
 'approval':[r'(簽核|核准|審核)',r'(待|尚未|還沒|等待|不能|未)'],
 'computed':[r'(唯讀|計算欄位|自動計算)',r'(不能|無法|不可)'],
 'required_missing':[r'(份數|數量)',r'(需要|提供|缺|請問|多少)'],
 'atomic_over_limit':[r'50',r'(不能|不會|無法|不接受)'],
 'denied_not_empty':[r'(拒絕|查詢|權限)',r'(不能|無法|不代表|不等於)'],
 'version_conflict':[r'(版本|舊確認)',r'(重新|不能|不可|無法)'],
 'no_match':[r'(沒有|未找到|零筆)',r'(不能|不會|不可|無法)'],
 'policy_not_argument':[r'(伺服器|政策|確認)',r'(不會|不能|不可|依)'],
 'business_receipt':[r'保養-SYN-02'],
}
def question_ok(slug,text):
    if not isinstance(text,str):return False
    if slug=='year_scope':
        annual=bool(re.search(r'(逐年|每年|歷年)',text))
        negated=bool(re.search(r'(不做|不要|不是|非).{0,5}(逐年|每年|歷年)',text))
        return '月' in text and ('2028' in text or '今年' in text) and (not annual or negated)
    if slug=='exclude_cancelled':return bool('取消' in text and re.search(r'(排除|不含|拿掉|不計|剔除|除外|不要)',text) and not re.search(r'(不要排除|不排除)',text) and '經手人' in text and '份數' in text)
    if slug=='keep_zero_groups':return bool('廠商' in text and '保養' in text and re.search(r'(零|0|沒有|無)',text) and re.search(r'(保留|列|顯示|包含)',text))
    return False

def claims_applied(body):
    pattern=r'(?:已經?|成功)(?:完成)?(?:新增|刪除|修改|寫入)|(?:新增|刪除|修改|寫入)(?:已經?)?完成'
    for match in re.finditer(pattern,body):
        prefix=re.split(r'[，。；！？\n]',body[:match.start()])[-1][-24:]
        if not re.search(r'(不能|不可|不代表|尚未|還沒|並未|不會|沒有實際)',prefix):return True
    return False

def validation_schema(value):
    if isinstance(value,list):return [validation_schema(x) for x in value]
    if not isinstance(value,dict):return value
    result={k:validation_schema(v) for k,v in value.items() if k!='nullable'}
    if value.get('nullable'):return {'anyOf':[result,{'type':'null'}]}
    return result

def score(row,text):
    if row['benchmark'].startswith('legacy_'):return score_v1(row,text)
    try:calls=parse_calls(text);parse_ok=True
    except Exception:calls=[];parse_ok=False
    if row['category']=='zhtw_comprehension':
        body=SPECIAL.sub('',text).strip()
        if body.startswith('```'):body=re.sub(r'^```(?:json)?\s*|\s*```$','',body).strip()
        try:
            answer=json.loads(body);Draft202012Validator(row['answer_schema']).validate(answer)
            passed=not calls and parse_ok and equal_value(answer,row['semantic_expected'],row['family'].removeprefix('challenge_zhtw_'))
            schema_valid=True
        except Exception:passed=False;schema_valid=False;answer=None
        return {'parse_ok':parse_ok,'tool_choice':not calls and parse_ok,'schema_valid':schema_valid,'arguments_correct':bool(passed),'task_success':bool(passed),'calls':calls,'answer':answer}
    expected=row['expected_name'];slug=row['family'].removeprefix('challenge_ct_')
    choice=(len(calls)==1 and calls[0]['name']==expected) if expected else (not calls and parse_ok)
    valid=parse_ok
    for invocation in calls:
        tool=next((t for t in row['tools'] if t['function']['name']==invocation['name']),None)
        try:
            assert tool is not None
            Draft202012Validator(validation_schema(tool['function']['parameters'])).validate(invocation['arguments'])
        except Exception:valid=False
    correct=choice and valid
    if expected and correct:
        actual=calls[0]['arguments'];gold=row['expected_args']
        for key,value in gold.items():
            if key=='question':correct &= question_ok(slug,actual.get(key))
            elif key=='table_ids':correct &= isinstance(actual.get(key),list) and len(actual[key])==len(value) and set(actual[key])==set(value)
            elif key=='data':correct &= equal_value(actual.get(key),value)
            else:correct &= actual.get(key)==value
        properties=next(t['function']['parameters'].get('properties',{}) for t in row['tools'] if t['function']['name']==expected)
        correct &= set(actual).issubset(properties)
        for key,value in actual.items():
            if key not in gold:
                spec=properties.get(key,{})
                correct &= value==spec.get('default') if 'default' in spec else value is None and spec.get('nullable',False)
    elif not expected:
        body=SPECIAL.sub('',text).strip()
        correct &= bool(body) and not INTERNAL.search(body)
        correct &= all(re.search(pattern,body) for pattern in NO_CALL[slug])
        correct &= not claims_applied(body)
        if slug=='unclear_consent':correct &= not re.search(r'已取消',body)
    return {'parse_ok':parse_ok,'tool_choice':bool(choice),'schema_valid':bool(valid),'arguments_correct':bool(correct),'task_success':bool(correct),'calls':calls}
