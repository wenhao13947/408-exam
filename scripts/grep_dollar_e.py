# -*- coding: utf-8 -*-
"""找 QuestionCard 中 $e(aiTip) 解析函数与 {first,second} 构造"""
import re
import pathlib

src = pathlib.Path(r'e:\lianping\408\.trae\chunks\QuestionCard-xHUDYSfM.js').read_text(encoding='utf-8', errors='replace')

i = src.find('function $e(')
if i < 0:
    i = src.find('$e=')
if i >= 0:
    print('DEF:', src[i:i + 900])
else:
    print('no $e def; 搜索 {first 构造:')
    for mm in re.finditer(r'\{first', src):
        s = max(0, mm.start() - 300)
        print(repr(src[s:mm.end() + 250][:600]))
        print('---')
