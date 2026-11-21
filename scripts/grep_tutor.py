# -*- coding: utf-8 -*-
"""深挖练习页 chunk 中 AI 助教 / 提示相关逻辑"""
import re
import pathlib

src = pathlib.Path(r'e:\lianping\408\.trae\exercise_view.js').read_text(encoding='utf-8', errors='replace')

print('--- tutor 上下文 ---')
for m in list(re.finditer(r'tutor', src))[:20]:
    s = max(0, m.start() - 120)
    seg = src[s:m.end() + 200].replace('\n', ' ')
    print(seg[:330])
    print('---')

print('\n--- ai 相关路径/字段 ---')
for m in sorted(set(re.findall(r'["\'][/\w\-]*ai[/\w\-]*["\']', src))):
    print(m)

print('\n--- 中文 UI 文案（示例采样）---')
cn = sorted(set(re.findall(r'"([\w（）()·、，。：！？\u4e00-\u9fff]{2,14})"', src)))
cjk = [c for c in cn if re.search(r'[\u4e00-\u9fff]', c)]
print('共', len(cjk), '条，含关键字的：')
for c in cjk:
    if re.search(r'提示|解析|强化|思路|引导|逐步', c):
        print(c)
