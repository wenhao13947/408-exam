# -*- coding: utf-8 -*-
"""在 ErrorReasonPicker 中找增强解析清单的真实 URL 与提示数据结构"""
import re
import pathlib

src = pathlib.Path(r'e:\lianping\408\.trae\chunks\ErrorReasonPicker-DLkFAHyk.js').read_text(encoding='utf-8', errors='replace')
print('size:', len(src))

print('\n--- URL/资源 ---')
for m in sorted(set(re.findall(r'["\'][^"\']{4,160}\.(?:json|html|md)["\']', src))):
    print(m)
for m in sorted(set(re.findall(r'["\']/(?:static|data|assets)/[^"\']+["\']', src))):
    print(m)

print('\n--- 清单中不存在 上下文 ---')
for m in re.finditer('清单中不存在', src):
    s = max(0, m.start() - 400)
    print(src[s:m.end() + 150].replace('\n', ' ')[:600])
    print('---')

print('\n--- enhanced/visual/hint 键名 ---')
for m in sorted(set(re.findall(r'["\']\w*[eE]nhanced\w*["\']|["\']\w*[vV]isual\w*["\']|["\']\w*[hH]int\w*["\']', src))):
    print(m)

print('\n--- first/second 提示加载 ---')
for kw in ('first', 'second', 'markdown'):
    for m in list(re.finditer(re.escape(kw), src))[:6]:
        s = max(0, m.start() - 120)
        seg = src[s:m.end() + 120].replace('\n', ' ')
        print(f'[{kw}]', seg[:260])
        print('---')
