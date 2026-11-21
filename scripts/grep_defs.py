# -*- coding: utf-8 -*-
"""查看 Na 与 Ot 的 computed 定义体"""
import re
import pathlib

src = pathlib.Path(r'e:\lianping\408\.trae\chunks\QuestionCard-xHUDYSfM.js').read_text(encoding='utf-8', errors='replace')

for var in ('Na', 'Ot'):
    m = re.search(r'[\(\[,;\s]' + var + r'=\(_\(\(\)=>\{', src)
    if not m:
        m = re.search(var + r'=\(_\(', src)
    if m:
        seg = src[m.start():m.start() + 900].replace('\n', ' ')
        print(f'=== {var} ===')
        print(seg)
        print()
