# -*- coding: utf-8 -*-
"""检查可视化解析 HTML 的外部引用"""
import re

h = open(r'e:\lianping\408\.trae\vis_2026_01.html', encoding='utf-8', errors='replace').read()
print('size:', len(h))
for m in sorted(set(re.findall(r'(?:src|href)=["\']([^"\']+)["\']', h))):
    print(m)
