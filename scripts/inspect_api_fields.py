# -*- coding: utf-8 -*-
"""检查 API 元数据中与提示/强化解析相关的字段"""
import json

with open(r'e:\lianping\408\data\raw\2026.api.json', encoding='utf-8') as f:
    resp = json.load(f)

item = resp['data'][0]
q = item['question']

print('--- question 顶层键 ---')
for k in sorted(q.keys()):
    v = q[k]
    s = json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v)
    print(f'{k}: {s[:120]}')

print('\n--- item 顶层键（question 之外）---')
for k in sorted(item.keys()):
    if k == 'question':
        continue
    v = item[k]
    s = json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v)
    print(f'{k}: {s[:300]}')

print('\n--- 全量搜索 hint 相关键名 ---')
text = json.dumps(resp, ensure_ascii=False)
for kw in ('hint', 'Hint', '提示', '强化', 'enhance', 'Enhance'):
    print(kw, text.count(kw))
