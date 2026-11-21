# -*- coding: utf-8 -*-
"""搜索主 bundle 与练习 chunk 中 AI 助教相关接口与子 chunk"""
import re
import pathlib

for name in ('index.js', 'exercise_view.js'):
    p = pathlib.Path(rf'e:\lianping\408\.trae\{name}')
    src = p.read_text(encoding='utf-8', errors='replace')
    print(f'===== {name} =====')
    # 动态 import 的 chunk 名
    for m in sorted(set(re.findall(r'[\w\-]+-[\w\-]+\.js', src))):
        if re.search(r'ai|tutor|chat', m, re.I):
            print('CHUNK:', m)
    # ai 接口路径（宽松）
    for m in sorted(set(re.findall(r'["\'](/api/[\w/\-]*ai[\w/\-]*)["\']', src))):
        print('API:', m)
    # features 相关
    for m in list(re.finditer(r'features', src))[:10]:
        s = max(0, m.start() - 100)
        print('FEAT:', src[s:m.end() + 150].replace('\n', ' ')[:250])
        print('---')
