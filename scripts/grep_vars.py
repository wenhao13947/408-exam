# -*- coding: utf-8 -*-
"""找 Ot/Na 的定义与赋值（压缩名需要先确定）"""
import re
import pathlib

src = pathlib.Path(r'e:\lianping\408\.trae\chunks\QuestionCard-xHUDYSfM.js').read_text(encoding='utf-8', errors='replace')

# Ga computed 里用的变量名 e=Na.value —— 找 "Na=" 的定义
for var in ('Na', 'Ot'):
    print(f'=== {var} 定义/赋值 ===')
    # 定义: ,Na=X(!1) 之类
    for m in list(re.finditer(r'[,;(' + var + r'=]\b' + var + r'\s*=\s*[\w$]+\(([^)]{0,40})\)', src))[:10]:
        s = max(0, m.start() - 60)
        print('DEF:', src[s:m.end() + 40].replace('\n', ' ')[:180])
    # 赋值
    for m in list(re.finditer(var + r'\.value\s*=\s*([^;,]{1,140})', src))[:12]:
        s = max(0, m.start() - 120)
        print('SET:', src[s:m.end() + 10].replace('\n', ' ')[:260])
    print()
