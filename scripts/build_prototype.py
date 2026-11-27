# -*- coding: utf-8 -*-
"""生成刷题原型的数据文件
读取 data/index.json + data/{year}.json + html/data/enhanced-analysis/
-> prototype-data/index.js + prototype-data/{year}.js + prototype-data/enhanced-{year}.js
图片引用统一改写为相对 html/ 目录的本地路径（原型 HTML 位于工作区根目录）
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
OUT = os.path.join(ROOT, 'prototype-data')
HEADER = 'window.P408 = window.P408 || {};\n'

# <img src> 改写规则 -> 相对工作区根目录
SRC_PATTERNS = [
    (re.compile(r'src="/static/'), 'src="html/static/'),
    (re.compile(r'src="https://www\.408os\.cn/static/'), 'src="html/static/'),
    (re.compile(r'src="\.\./\.\./static/'), 'src="html/static/'),
    (re.compile(r'src="https://oss\.408os\.cn/image/'), 'src="html/image/'),
]


def fix_src(html):
    if not html:
        return html
    for pat, rep in SRC_PATTERNS:
        html = pat.sub(rep, html)
    return html


def fix_src_url(src):
    """把原解析 HTML 中的单个图片 URL 改写为本地相对路径"""
    if not src:
        return src
    return fix_src('src="' + src + '"')[5:-1]


# 增强解析 Markdown 里的源站图片引用：![alt](/data/enhanced-analysis/assets/YYYY/NN/original-analysis-M.ext)
MD_IMG_RE = re.compile(
    r'(!\[(?P<alt>[^\]]*)\]\()/data/enhanced-analysis/assets/'
    r'(?P<year>\d{4})/(?P<q>\d{1,2})/original-analysis-(?P<n>\d+)\.(?P<ext>\w+)\)'
)


def fix_md(md, year):
    """按素材实存路径改写增强解析中的图片引用；无素材时保持原样。"""
    def repl(m):
        y, q, n = m.group('year'), int(m.group('q')), int(m.group('n'))
        if y != year:
            return m.group(0)
        srv = 'server/static/questions/' + y + '_' + str(q) + '_analysis_'
        candidates = [srv + str(n - 1) + '.svg', srv + str(n) + '.svg']
        orig = os.path.join(ROOT, 'html', 'analysis', y, str(q) + '.html')
        if os.path.isfile(orig):
            with open(orig, encoding='utf-8', errors='ignore') as fp:
                srcs = re.findall(r'<img[^>]+src="([^"]+)"', fp.read())
            if len(srcs) >= n:
                candidates.append(fix_src_url(srcs[n - 1]))
        for rel in candidates:
            if rel and os.path.isfile(os.path.join(ROOT, rel)):
                return '![' + m.group('alt') + '](' + rel + ')'
        return m.group(0)
    return MD_IMG_RE.sub(repl, md)


def fix_question(q):
    q = dict(q)
    q['stemHtml'] = fix_src(q.get('stemHtml'))
    q['answerHtml'] = fix_src(q.get('answerHtml'))
    q['analysisHtml'] = fix_src(q.get('analysisHtml'))
    q['options'] = [
        {'label': o['label'], 'html': fix_src(o['html'])} for o in (q.get('options') or [])
    ]
    return q


def main():
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(DATA, 'index.json'), encoding='utf-8') as f:
        index = json.load(f)

    header = HEADER
    with open(os.path.join(OUT, 'index.js'), 'w', encoding='utf-8') as f:
        f.write(header + 'P408.index = ' + json.dumps(index, ensure_ascii=False) + ';\n')
    write_visual_index()

    for y in index['years']:
        year = y['year']
        with open(os.path.join(DATA, f'{year}.json'), encoding='utf-8') as f:
            data = json.load(f)
        data['questions'] = [fix_question(q) for q in data['questions']]
        with open(os.path.join(OUT, f'{year}.js'), 'w', encoding='utf-8') as f:
            f.write(header + f'P408.years["{year}"] = ' + json.dumps(data, ensure_ascii=False) + ';\n')
        build_enhanced(year)
        print(year, 'ok')

    total = sum(os.path.getsize(os.path.join(OUT, fn)) for fn in os.listdir(OUT))
    print(f'共 {len(os.listdir(OUT))} 个文件, {total/1048576:.1f} MB')


def write_visual_index():
    """扫描 html/lessons-v2/ 下已下载的可视化解析 -> P408.visual"""
    vis_root = os.path.join(ROOT, 'html', 'lessons-v2', 'visual-analysis-20261026')
    vis = {}
    if os.path.isdir(vis_root):
        for ydir in sorted(os.listdir(vis_root)):
            items = [int(d) for d in sorted(os.listdir(os.path.join(vis_root, ydir)))
                     if os.path.exists(os.path.join(vis_root, ydir, d, 'index.html'))]
            if items:
                vis[ydir] = items
    with open(os.path.join(OUT, 'index.js'), 'a', encoding='utf-8') as f:
        f.write('P408.visual = ' + json.dumps(vis, ensure_ascii=False) + ';\n')


def build_enhanced(year):
    """按年打包增强解析 md 与错误选项反馈 json -> enhanced-{year}.js"""
    ea = os.path.join(ROOT, 'html', 'data', 'enhanced-analysis')
    md, wof = {}, {}
    ydir = os.path.join(ea, str(year))
    if os.path.isdir(ydir):
        for fn in sorted(os.listdir(ydir)):
            if fn.endswith('.md'):
                idx = str(int(fn[:-3]))
                with open(os.path.join(ydir, fn), encoding='utf-8') as fp:
                    md[idx] = fix_md(fp.read(), str(year))
    wdir = os.path.join(ea, 'wrong-option-feedback', str(year))
    if os.path.isdir(wdir):
        for fn in sorted(os.listdir(wdir)):
            if not fn.endswith('.json'):
                continue
            path = os.path.join(wdir, fn)
            # 源站对主观大题(41-47)无错误反馈，404 回退为 SPA index.html，按空数据处理
            with open(path, encoding='utf-8') as fp:
                content = fp.read().lstrip()
            if not content.startswith('{'):
                continue
            wof[str(int(fn[:-5]))] = json.loads(content)
    payload = {'md': md, 'wof': wof}
    with open(os.path.join(OUT, f'enhanced-{year}.js'), 'w', encoding='utf-8') as f:
        f.write(HEADER + f'P408.enhanced["{year}"] = ' + json.dumps(payload, ensure_ascii=False) + ';\n')


if __name__ == '__main__':
    main()
