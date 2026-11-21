# -*- coding: utf-8 -*-
"""查看 user/current 的 features 与 question/detail 的字段"""
import json
import pathlib

u = json.loads(pathlib.Path(r'e:\lianping\408\.trae\user_current.json').read_text(encoding='utf-8'))
print('--- user ---')
print(json.dumps(u, ensure_ascii=False, indent=1)[:1500])

d = json.loads(pathlib.Path(r'e:\lianping\408\.trae\q800.json').read_text(encoding='utf-8'))
print('\n--- detail 响应结构 ---')
print(json.dumps(d, ensure_ascii=False, indent=1)[:2500])
