# -*- coding: utf-8 -*-
"""扫描 html/ 下所有页面的 img 引用，统计需补下的资源"""
import os
import re

root = r'e:\lianping\408\html'
srcs = {}
for kind in ('questions', 'answers', 'analysis'):
    d = os.path.join(root, kind)
    for y in os.listdir(d):
        yd = os.path.join(d, y)
        for f in os.listdir(yd):
            h = open(os.path.join(yd, f), encoding='utf-8').read()
            for m in re.finditer(r'<img[^>]*?src=["\']([^"\']+)', h):
                srcs.setdefault(m.group(1), []).append(kind + '/' + y + '/' + f)

print('unique srcs:', len(srcs))
print('pages containing img:', len(set(l for ls in srcs.values() for l in ls)))
for s in sorted(srcs):
    print(s, '->', len(srcs[s]), 'pages')
