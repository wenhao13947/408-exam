# -*- coding: utf-8 -*-
"""在 exercise chunk 中定位 增强解析/可视化解析/提示 的来源"""
import re
import pathlib

src = pathlib.Path(r'e:\lianping\408\.trae\exercise_view.js').read_text(encoding='utf-8', errors='replace')

for kw in ('增强解析', '可视化解析', '原解析', '提示', '教材', '视频', '笔记', 'AI辅导'):
    print(kw, '出现次数:', src.count(kw))

print('\n--- 上下文采样 ---')
for kw in ('增强解析', '可视化解析', '提示', '教材'):
    for m in list(re.finditer(re.escape(kw), src))[:6]:
        s = max(0, m.start() - 100)
        seg = src[s:m.end() + 150].replace('\n', ' ')
        print(f'[{kw}]', seg[:280])
        print('---')
