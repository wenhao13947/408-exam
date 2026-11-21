# -*- coding: utf-8 -*-
"""定位 QuestionCard 中增强解析清单、可视化解析、提示的 URL"""
import re
import pathlib

src = pathlib.Path(r'e:\lianping\408\.trae\chunks\QuestionCard-xHUDYSfM.js').read_text(encoding='utf-8', errors='replace')

print('--- 所有 fetch/URL 模板 ---')
for m in sorted(set(re.findall(r'fetch\(([^)]{1,150})\)', src))):
    print('FETCH:', m)
print()
for m in sorted(set(re.findall(r'["\'][^"\']*manifest[^"\']*["\']', src))):
    print('MANIFEST:', m)
print()
for m in sorted(set(re.findall(r'["\'][^"\']*\.(?:json|html|md)[^"\']*["\']', src))):
    print('RES:', m)

print('\n--- 清单 上下文 ---')
for m in re.finditer('清单', src):
    s = max(0, m.start() - 200)
    print(src[s:m.end() + 100].replace('\n', ' ')[:320])
    print('---')

print('\n--- crowdHint / first/second 提示结构 上下文 ---')
for kw in ('crowdHint', 'Ot.value', 'hintHtml', 'hint1', 'hints'):
    for m in list(re.finditer(re.escape(kw), src))[:5]:
        s = max(0, m.start() - 150)
        print(f'[{kw}]', src[s:m.end() + 150].replace('\n', ' ')[:320])
        print('---')
