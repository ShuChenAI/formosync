# SPDX-License-Identifier: Apache-2.0
"""Pure-metadata aggregation and selection; no final-test checkpoint choice."""
import collections,statistics
def mean(values):
    v=list(values);return sum(v)/len(v) if v else None
def summarize(records):
    categories={};families=collections.defaultdict(list)
    for r in records:families[(r['category'],r['family'])].append(r)
    for category in sorted({r['category'] for r in records}):
        subset=[r for r in records if r['category']==category]
        categories[category]={'n':len(subset),'passed':sum(bool(r.get('success')) for r in subset),
                              'rate':mean(bool(r.get('success')) for r in subset),'schema_valid':mean(r['schema_valid'] for r in subset if r.get('schema_valid') is not None),
                              'truncated':sum(r.get('truncated',False) for r in subset)}
    macro={c:mean(mean(bool(r.get('success')) for r in values) for (cat,f),values in families.items() if cat==c) for c in categories}
    ct_generated=mean(macro[c] for c in ['ct_generated','ct_joint'] if c in macro)
    ct=(.7*ct_generated+.3*macro['pragmatic_tool']) if ct_generated is not None and 'pragmatic_tool' in macro else ct_generated
    language=(.6*macro['language_generated']+.4*macro['pragmatic_semantic']) if 'language_generated' in macro and 'pragmatic_semantic' in macro else macro.get('pragmatic_semantic',macro.get('zhtw_comprehension'))
    tool_categories={'ct_generated','ct_joint','pragmatic_tool','custom_tables','legacy_teamsync','legacy_generic'}
    nocall=[r for r in records if r['category'] in tool_categories and not r.get('calls_expected')]
    toolrows=[r for r in records if r['category'] in tool_categories]
    per_case=collections.defaultdict(dict);per_pair=collections.defaultdict(list)
    for r in records:
        if r.get('case_id'):per_case[r['case_id']][r['category']]=bool(r.get('success'))
    for r in records:
        if r.get('pair_id') and r['category']=='pragmatic_semantic':per_pair[r['pair_id']].append(all(per_case[r['case_id']].get(c,False) for c in ['pragmatic_semantic','pragmatic_tool']))
    return {'by_category':categories,'family_macro':macro,'features':{'ct':ct,'language':language,
            'schema':mean(r['schema_valid'] for r in toolrows if r.get('schema_valid') is not None),
            'no_unwanted_call':mean(not r.get('attempted_call',False) for r in nocall),
            'unwanted_commits':sum(r.get('attempted_commit',False) for r in nocall),
            'joint_pairs':mean(all(values) for values in per_pair.values())},'total':len(records)}
def rank(metrics,parent):
    a=metrics['features'];b=parent['features'];g1=a['ct']-b['ct'];g2=a['language']-b['language']
    return (min(g1,g2),g1+g2,a.get('joint_pairs') or 0.,-(a.get('unwanted_commits') or 0))
def accepted(metrics,parent):
    a=metrics['features'];b=parent['features'];eps=1e-9
    improve=lambda key:a[key]>=b[key]-eps and (a[key]>b[key]+eps or b[key]>=1-eps)
    return bool(improve('ct') and improve('language') and a['schema']>=b['schema']-eps and a['no_unwanted_call']>=b['no_unwanted_call']-eps and a['unwanted_commits']<=b['unwanted_commits'])
