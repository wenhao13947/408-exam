# -*- coding: utf-8 -*-
"""在 QuestionCard 中找 embed iframe 变量与提示数据来源"""
import re
import pathlib

src = pathlib.Path(r'e:\lianping\408\.trae\chunks\QuestionCard-xHUDYSfM.js').read_text(encoding='utf-8', errors='replace')

print('--- embed=1 上下文 ---')
for m in list(re.finditer(re.escape('?embed=1'), src))[:5]:
    s = max(0, m.start() - 300)
    print(src[s:m.end() + 100].replace('\n', ' ')[:450])
    print('---')

print('--- .first / .second 访问上下文 ---')
for m in list(re.finditer(r'\.first\b', src))[:10]:
    s = max(0, m.start() - 200)
    print(src[s:m.end() + 120].replace('\n', ' ')[:340])
    print('---')

print('--- hint 相关 URL/键 ---')
for m in sorted(set(re.findall(r'["\'][^"\']*hint[^"\']*["\']', src)))[:20]:
    print(m)
