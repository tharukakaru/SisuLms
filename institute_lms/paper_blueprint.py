"""Non-executable, bounded assessment configuration."""
from .pricing_rules import integer

def validate(count, blueprint=None, template=None):
    rows=blueprint or [{'kind':'MCQ','count':count,'marks':1}]
    if not isinstance(rows,list) or not 1<=len(rows)<=3:raise ValueError('Use one to three question type groups')
    normalized=[];kinds=set()
    for row in rows:
        if not isinstance(row,dict) or set(row)-{'kind','count','marks'}:raise ValueError('Invalid blueprint')
        kind=row.get('kind');n=integer(row.get('count'),'Count',100);marks=integer(row.get('marks',1),'Marks',100)
        if kind not in ('MCQ','True/False','Written') or kind in kinds or n<1 or marks<1:raise ValueError('Invalid question type/count/marks')
        normalized.append({'kind':kind,'count':n,'marks':marks});kinds.add(kind)
    if sum(r['count'] for r in normalized)!=count:raise ValueError('Blueprint counts must equal requested count')
    meta=template or {}
    if not isinstance(meta,dict) or set(meta)-{'heading','instructions','show_marks'}:raise ValueError('Only plain-text template metadata is allowed')
    if any(not isinstance(meta.get(k,''),str) or len(meta.get(k,''))>1000 for k in ('heading','instructions')):raise ValueError('Template text too long')
    if 'show_marks' in meta and type(meta['show_marks']) is not bool:raise ValueError('Invalid marks display')
    return normalized,meta

def batches(blueprint):
    for group in blueprint:
        for offset in range(0,group['count'],20):
            yield {**group,'count':min(20,group['count']-offset)}
