# -*- coding: utf-8 -*-
"""question 公共模块中找 aiTip(提示 first/second)加载逻辑"""
import re
import pathlib

src = pathlib.Path(r'e:\lianping\408\.trae\chunks\question-4Myjuaap.js').read_text(encoding='utf-8', errors='replace')
print('size:', len(src))

m = re.search(r'export\{[^}]+\}', src)
print('EXPORT:', m.group(0)[:500] if m else 'none')
print()

for kw in ('hint', 'Tip', 'tip'):
    print(kw, src.count(kw))

print('\n--- first/second 结构 ---')
for m in list(re.finditer(r'first', src))[:10]:
    s = max(0, m.start() - 200)
    print(repr(src[s:m.end() + 120][:340]))
    print('---')

print('\n--- URL 资源 ---')
for m in sorted(set(re.findall(r'["\']/(?:data|static|api)[^"\']+["\']', src))):
    print(m)
