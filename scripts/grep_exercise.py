# -*- coding: utf-8 -*-
"""在练习页 chunk 中找提示/强化解析相关字段与 API"""
import re
import pathlib

src = pathlib.Path(r'e:\lianping\408\.trae\exercise_view.js').read_text(encoding='utf-8', errors='replace')

print('hint count:', src.count('hint'), '/ Hint:', src.count('Hint'))
print('questionId count:', src.count('questionId'))

print('\n--- hint 上下文 ---')
for m in list(re.finditer(r'hint', src))[:30]:
    s = max(0, m.start() - 100)
    seg = src[s:m.end() + 150].replace('\n', ' ')
    print(seg)
    print('---')

print('\n--- URL 类字符串 ---')
for m in sorted(set(re.findall(r'["\'][/a-zA-Z0-9_?\-]{6,120}["\']', src))):
    s = m[1:-1]
    low = s.lower()
    if 'question' in low or 'detail' in low or 'analysis' in low or 'api' in low:
        print(s)
