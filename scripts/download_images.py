# -*- coding: utf-8 -*-
"""补下载 HTML 中引用的图片资源到 html/ 下对应路径"""
import os
import re
import subprocess
import sys

root = r'e:\lianping\408\html'

BASE = 'https://www.408os.cn'

# src -> (base_url, 相对 html/ 的本地路径)
def map_src(src):
    if src.startswith('https://www.408os.cn/'):
        src = '/' + src[len('https://www.408os.cn/'):]
    if src.startswith('/'):
        url = BASE + src
        local = src.lstrip('/')
        return url, os.path.join(root, local.replace('/', os.sep))
    if src.startswith('../../'):
        url = BASE + '/static/assets/exam/'
        # ../../static/xxx 相对于 /questions/{y}/ 页面 -> html/static/xxx
        rel = src[6:]  # static/...
        return BASE + '/' + rel, os.path.join(root, rel.replace('/', os.sep))
    # OSS 外链
    if src.startswith('https://oss.408os.cn/'):
        rel = src[len('https://oss.408os.cn/'):]
        return src, os.path.join(root, rel.replace('/', os.sep))
    return None, None


# 重新扫描收集 src
all_srcs = set()
for kind in ('questions', 'answers', 'analysis'):
    d = os.path.join(root, kind)
    for y in os.listdir(d):
        yd = os.path.join(d, y)
        for f in os.listdir(yd):
            h = open(os.path.join(yd, f), encoding='utf-8').read()
            for m in re.finditer(r'<img[^>]*?src=["\']([^"\']+)', h):
                all_srcs.add(m.group(1))

fail = []
for src in sorted(all_srcs):
    url, local = map_src(src)
    if not url:
        print('[SKIP]', src)
        continue
    os.makedirs(os.path.dirname(local), exist_ok=True)
    if os.path.exists(local) and os.path.getsize(local) > 200:
        print('[OK-EXIST]', src)
        continue
    r = subprocess.run(['curl.exe', '-s', '--max-time', '30', '-o', local, '-w', '%{http_code}', url],
                       capture_output=True, text=True)
    code = r.stdout.strip()
    ok = code == '200' and os.path.getsize(local) > 200
    print('[OK]' if ok else f'[FAIL {code}]', src, '->', os.path.relpath(local, root))
    if not ok:
        fail.append(src)
    import time
    time.sleep(0.3)

print('失败:', len(fail))
sys.exit(1 if fail else 0)
