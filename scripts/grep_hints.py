# -*- coding: utf-8 -*-
"""找 QuestionCard 中 提示(first/second) 与 可视化解析 URL 的加载逻辑"""
import re
import pathlib

src = pathlib.Path(r'e:\lianping\408\.trae\chunks\QuestionCard-xHUDYSfM.js').read_text(encoding='utf-8', errors='replace')

print('--- Na(可视化) 赋值 ---')
for m in list(re.finditer(r'Na\.value\s*=', src))[:8]:
    s = max(0, m.start() - 260)
    print(src[s:m.end() + 160].replace('\n', ' ')[:420])
    print('---')

print('--- Ot(提示) 赋值 / first second ---')
for m in list(re.finditer(r'Ot\.value\s*=', src))[:8]:
    s = max(0, m.start() - 300)
    print(src[s:m.end() + 160].replace('\n', ' ')[:460])
    print('---')

print('--- first/second 键构造 ---')
for m in list(re.finditer(r'first\s*:', src))[:8]:
    s = max(0, m.start() - 220)
    print(src[s:m.end() + 160].replace('\n', ' ')[:400])
    print('---')

print('--- hints/wrong-option 等 URL ---')
for m in sorted(set(re.findall(r'["\'][^"\']*enhanced-analysis[^"\']*["\']', src))):
    print(m)
