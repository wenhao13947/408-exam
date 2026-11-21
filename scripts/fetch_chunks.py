# -*- coding: utf-8 -*-
"""从 index.js 提取全部 chunk 文件名并下载，搜索 增强解析/可视化解析/提示"""
import re
import pathlib
import subprocess
import time

idx = pathlib.Path(r'e:\lianping\408\.trae\index.js').read_text(encoding='utf-8', errors='replace')
names = sorted(set(re.findall(r'([\w\-]+-[A-Za-z0-9_\-]{8}\.js)', idx)))
print('chunks:', len(names))

out = pathlib.Path(r'e:\lianping\408\.trae\chunks')
out.mkdir(exist_ok=True)
targets = []
for n in names:
    p = out / n
    if not p.exists() or p.stat().st_size == 0:
        r = subprocess.run(['curl.exe', '-s', '--max-time', '30', '-o', str(p), '-w', '%{http_code}',
                            f'https://www.408os.cn/assets/{n}'], capture_output=True, text=True)
        if r.stdout.strip() != '200':
            print('FAIL', n, r.stdout.strip())
        time.sleep(0.15)
    targets.append(p)

print('downloaded, searching...')
for kw in ('增强解析', '可视化解析', '原解析', 'AI辅导', '提示'):
    hits = [p.name for p in targets if p.exists() and kw in p.read_text(encoding='utf-8', errors='replace')]
    print(kw, '->', hits)
