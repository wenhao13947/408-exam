# -*- coding: utf-8 -*-
"""找 QuestionCard 中 $e 的导入来源模块"""
import re
import pathlib

src = pathlib.Path(r'e:\lianping\408\.trae\chunks\QuestionCard-xHUDYSfM.js').read_text(encoding='utf-8', errors='replace')

for m in re.finditer(r'import\{[^}]+\}from"\./([\w\-]+\.js)"', src):
    stmt = m.group(0)
    mod = m.group(1)
    if '$e' in stmt:
        i = stmt.find('$e')
        print('IMPORT $e from', mod, '->', stmt[max(0, i - 150):i + 80])
    else:
        print('module:', mod)
