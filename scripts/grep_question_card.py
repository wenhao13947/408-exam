# -*- coding: utf-8 -*-
"""在 QuestionCard chunk 中定位 增强解析/提示 的数据来源"""
import re
import pathlib

src = pathlib.Path(r'e:\lianping\408\.trae\chunks\QuestionCard-xHUDYSfM.js').read_text(encoding='utf-8', errors='replace')

print('size:', len(src))
print('\n--- 关键词上下文 ---')
for kw in ('增强解析', '可视化解析', '原解析', '提示', 'AI辅导'):
    for m in list(re.finditer(re.escape(kw), src))[:8]:
        s = max(0, m.start() - 130)
        seg = src[s:m.end() + 180].replace('\n', ' ')
        print(f'[{kw}]', seg[:320])
        print('---')

print('\n--- 静态资源路径 ---')
for m in sorted(set(re.findall(r'["\'](/(?:static|data)/[^"\']+)["\']', src))):
    print(m)
for m in sorted(set(re.findall(r'["\'](/api/[^"\']+)["\']', src))):
    print(m)
