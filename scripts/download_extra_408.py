# -*- coding: utf-8 -*-
"""下载提示/增强解析/错误选项反馈/可视化解析/KaTeX
输出:
  data/raw/tips.json                          提示 {year: {index: "first||second"}}
  html/data/enhanced-analysis/{y}/{nn}.md     增强解析
  html/data/enhanced-analysis/wrong-option-feedback/{y}/{nn}.json
  html/lessons-v2/visual-analysis-20261026/2026/{nn}/index.html + frames/*.svg
  html/vendor/katex/                          KaTeX 离线包
用法: python -X utf8 scripts/download_extra_408.py
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = 'https://www.408os.cn'
TOKEN = ('eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJsb2dpblR5cGUiOiJsb2dpbiIsImxvZ2luSWQiOiJ6dF91c2VyOjIxMTI3NjM0'
         'NTA3OTA1MzUxNjkiLCJyblN0ciI6Ik05SlFlSUdvS3JheWJFbUlEY2hPOVh1b1VYanlzS2ZKIiwiY2xpZW50aWQiOiI4MTgwMWRiZDdk'
         'M2U0YmY0NmRiOGY0OWUzYWQ2MzNjNyIsInVzZXJJZCI6MjExMjc2MzQ1MDc5MDUzNTE2OSwidXNlck5hbWUiOiI2MjU2NDk5NzhAcXEu'
         'Y29tIn0.VLO2t1LrTjg-03y9SFZe4VE2N9Uqt253d-74B4QOW6E')
CLIENT_ID = '81801dbd7d3e4bf46db8f49e3ad633c7'
YEARS = list(range(2009, 2027))
VISUAL_2026 = [1, 2, 3, 4, 44]

TIPS_OUT = os.path.join(ROOT, 'data', 'raw', 'tips.json')
EA_DIR = os.path.join(ROOT, 'html', 'data', 'enhanced-analysis')
VIS_DIR = os.path.join(ROOT, 'html', 'lessons-v2', 'visual-analysis-20261026', '2026')
KATEX_DIR = os.path.join(ROOT, 'html', 'vendor', 'katex')

fail = []


def curl(url, out, headers=(), min_size=10):
    """下载单个文件，成功返回 True"""
    if os.path.exists(out) and os.path.getsize(out) >= min_size:
        return True  # 增量：已存在则跳过
    os.makedirs(os.path.dirname(out), exist_ok=True)
    cmd = ['curl.exe', '-s', '--max-time', '30', '-o', out, '-w', '%{http_code}']
    for h in headers:
        cmd += ['-H', h]
    cmd.append(url)
    r = subprocess.run(cmd, capture_output=True, text=True)
    code = (r.stdout or '').strip()
    ok = code == '200' and os.path.exists(out) and os.path.getsize(out) >= min_size
    if not ok and os.path.exists(out):
        os.remove(out)
    time.sleep(0.15)
    return ok


def main():
    # ---- 1. 提示 API（需认证，846 次）----
    tips_path = os.path.join(ROOT, 'data', 'raw', 'manifest.json')
    manifest = json.load(open(tips_path, encoding='utf-8')) if os.path.exists(tips_path) else []
    auth = (f'Authorization: Bearer {TOKEN}', f'clientid: {CLIENT_ID}')
    tips = {}
    if os.path.exists(TIPS_OUT):
        tips = json.load(open(TIPS_OUT, encoding='utf-8'))
    ids = sorted({int(m.split('/')[-1].split('.')[0]) for m in
                  [u.split('/api/zt/')[0] or '' for u in []]} if False else [])
    # 从 manifest 构造 year->index->questionId 映射需经 api json；直接用题号清单
    year_idx = []
    for y in YEARS:
        api = os.path.join(ROOT, 'data', 'raw', f'{y}.api.json')
        resp = json.load(open(api, encoding='utf-8'))
        for item in resp['data']:
            q = item['question']
            year_idx.append((y, q['questionIndex'], q['id']))
    print(f'共 {len(year_idx)} 题')

    n_missing = 0
    for i, (y, idx, qid) in enumerate(year_idx):
        yd = tips.setdefault(str(y), {})
        if str(idx) in yd and yd[str(idx)].strip():
            continue
        out_tmp = os.path.join(ROOT, '.trae', 'tip_resp.json')
        url = f'{BASE}/api/zt/question/tip/{qid}'
        if not curl(url, out_tmp, headers=auth, min_size=20):
            fail.append(f'tip {y}/{idx}')
            n_missing += 1
            continue
        try:
            d = json.load(open(out_tmp, encoding='utf-8'))
            val = d.get('data') or ''
        except Exception:
            val = ''
        yd[str(idx)] = val
        if (i + 1) % 50 == 0:
            json.dump(tips, open(TIPS_OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
            print(f'tip 进度 {i + 1}/{len(year_idx)}')
    json.dump(tips, open(TIPS_OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    n_tip = sum(1 for y in tips for k in tips[y] if tips[y][k].strip())
    print(f'[OK] tips: {n_tip}/{len(year_idx)}')

    # ---- 2. 增强解析 md + 错误选项反馈 json（3 线程并行）----
    from concurrent.futures import ThreadPoolExecutor
    n_md = n_wof = 0

    def dl_pair(args):
        y, idx = args
        nn = f'{idx:02d}'
        ok_md = curl(f'{BASE}/data/enhanced-analysis/{y}/{nn}.md',
                     os.path.join(EA_DIR, str(y), f'{nn}.md'), min_size=50)
        ok_wof = curl(f'{BASE}/data/enhanced-analysis/wrong-option-feedback/{y}/{nn}.json',
                      os.path.join(EA_DIR, 'wrong-option-feedback', str(y), f'{nn}.json'), min_size=10)
        return y, idx, ok_md, ok_wof

    with ThreadPoolExecutor(max_workers=3) as ex:
        for i, (y, idx, ok_md, ok_wof) in enumerate(ex.map(dl_pair, [(y, idx) for y, idx, _ in year_idx])):
            if ok_md:
                n_md += 1
            else:
                fail.append(f'md {y}/{idx}')
            if ok_wof:
                n_wof += 1
            else:
                fail.append(f'wof {y}/{idx}')
            if (i + 1) % 100 == 0:
                print(f'md/wof 进度 {i + 1}/{len(year_idx)}')
    print(f'[OK] 增强解析: {n_md}/{len(year_idx)}, 错误反馈: {n_wof}/{len(year_idx)}')

    # ---- 3. 可视化解析（2026 指定题）----
    for idx in VISUAL_2026:
        nn = f'{idx:02d}'
        vdir = os.path.join(VIS_DIR, nn)
        idx_html = os.path.join(vdir, 'index.html')
        if not curl(f'{BASE}/lessons-v2/visual-analysis-20261026/2026/{nn}/index.html',
                    idx_html, min_size=1000):
            fail.append(f'visual {nn} index.html')
            continue
        h = open(idx_html, encoding='utf-8', errors='replace').read()
        m = re.search(r'lessonPages\s*=\s*(\[[^\]]*\])', h, re.S)
        n_frames = 0
        if m:
            try:
                n_frames = len(json.loads(m.group(1)))
            except Exception:
                n_frames = len(re.findall(r'"start"\s*:', m.group(1)))
        for f in range(n_frames):
            if not curl(f'{BASE}/lessons-v2/visual-analysis-20261026/2026/{nn}/frames/{f}.svg',
                        os.path.join(vdir, 'frames', f'{f}.svg'), min_size=100):
                fail.append(f'visual {nn} frame {f}')
        print(f'[OK] visual {nn}: {n_frames} 帧')

    # ---- 4. KaTeX 离线包 ----
    kj = os.path.join(KATEX_DIR, 'katex.min.js')
    ka = os.path.join(KATEX_DIR, 'auto-render.min.js')
    kc = os.path.join(KATEX_DIR, 'katex.min.css')
    ok_k = all([curl('https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js', kj, min_size=10000),
                curl('https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js', ka, min_size=2000),
                curl('https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css', kc, min_size=5000)])
    if ok_k:
        css = open(kc, encoding='utf-8').read()
        fonts = sorted(set(re.findall(r'url\((fonts/[^)]+)\)', css)))
        for f in fonts:
            fp = f.replace('fonts/', '')
            if not curl(f'https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/{urllib.parse.quote(f)}',
                        os.path.join(KATEX_DIR, 'fonts', fp), min_size=100):
                fail.append(f'katex font {fp}')
        print(f'[OK] KaTeX: js+css+{len(fonts)} 字体')
    else:
        fail.append('katex core')

    print('\n失败清单' if fail else '\n全部下载成功')
    for f in fail[:50]:
        print(' ', f)
    if len(fail) > 50:
        print(f'  ...共 {len(fail)} 项')
    sys.exit(1 if fail else 0)


if __name__ == '__main__':
    main()
