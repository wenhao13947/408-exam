# -*- coding: utf-8 -*-
"""408 真题结构化提取脚本
读取 data/raw/{year}.api.json + html/ 下三类静态页，
输出 data/{year}.json 与 data/index.json
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, 'html')
RAW = os.path.join(ROOT, 'data', 'raw')
DATA = os.path.join(ROOT, 'data')

TYPE_NAMES = {1: '单选题', 2: '综合应用题', 3: '综合应用题'}


def load_knowledge_map():
    """解析 knowledge.js 内嵌树 -> {id: (name, root_subject)}"""
    path = os.path.join(RAW, 'knowledge.js')
    with open(path, encoding='utf-8') as f:
        src = f.read()
    start = src.index('[')
    # 找匹配的闭括号
    depth = 0
    end = start
    in_str = None
    i = start
    while i < len(src):
        c = src[i]
        if in_str:
            if c == '\\':
                i += 1
            elif c == in_str:
                in_str = None
        elif c in '"\'':
            in_str = c
        elif c in '[{':
            depth += 1
        elif c in ']}':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
        i += 1
    lit = src[start:end]
    # JS 字面量 -> JSON：给无引号键加引号
    lit = re.sub(r'([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*:)', r'\1"\2"\3', lit)
    tree = json.loads(lit)

    name_map, subject_of = {}, {}

    def walk(node, root_name):
        name_map[node['id']] = node['name']
        subject_of[node['id']] = root_name
        for ch in node.get('children', []) or []:
            walk(ch, root_name)

    for root in tree:
        walk(root, root['name'])
    return name_map, subject_of


def extract_balanced_div(html, class_name):
    """提取 <div class="class_name"> ... </div> 的 inner HTML（处理嵌套 div）"""
    m = re.search(r'<div[^>]*class="[^"]*\b%s\b[^"]*"[^>]*>' % re.escape(class_name), html)
    if not m:
        return None
    i = m.end()
    depth = 1
    while i < len(html) and depth > 0:
        open_m = re.compile(r'<div\b').search(html, i)
        close_m = re.compile(r'</div>').search(html, i)
        if not close_m:
            break
        if open_m and open_m.start() < close_m.start():
            depth += 1
            i = open_m.end()
        else:
            depth -= 1
            i = close_m.end()
    return html[m.end():close_m.start()] if depth == 0 else html[m.end():i]


def strip_page(html):
    """去掉文档外壳，保留 body 内部"""
    m = re.search(r'<body[^>]*>(.*)</body>', html, re.S)
    return m.group(1) if m else html


def extract_options(content_html):
    """从题干 HTML 提取选项 [{label, html}]"""
    options = []
    for m in re.finditer(
            r'<div class="option">\s*<span class="opt-label">\s*([A-D])\s*\.?\s*</span>\s*'
            r'<span class="opt-content">(.*?)</span>\s*</div>', content_html, re.S):
        options.append({'label': m.group(1), 'html': m.group(2).strip()})
    # 无 .opt-content 的兜底：整个 option div 内容
    if not options:
        for m in re.finditer(r'<div class="option">(.*?)</div>', content_html, re.S):
            inner = m.group(1)
            lm = re.match(r'\s*<span class="opt-label">\s*([A-D])', inner)
            if lm:
                body = re.sub(r'^\s*<span class="opt-label">\s*[A-D]\s*\.?\s*</span>', '', inner).strip()
                options.append({'label': lm.group(1), 'html': body})
    return options


def stem_without_options(content_html):
    """题干去掉选项部分"""
    return re.sub(r'<div class="option">.*?</div>\s*', '', content_html, flags=re.S).strip()


def answer_from_html(answer_html):
    m = re.search(r'答案[:：\s]*([A-D])', re.sub(r'<[^>]+>', '', answer_html))
    return m.group(1) if m else None


def load_tips():
    """读取 tips.json -> {year: {index: "first||second"}}"""
    path = os.path.join(RAW, 'tips.json')
    if not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def main():
    name_map, subject_of = load_knowledge_map()
    tips = load_tips()
    os.makedirs(DATA, exist_ok=True)
    index = []
    total = 0
    problems = []

    api_files = sorted(f for f in os.listdir(RAW) if f.endswith('.api.json'))
    for fn in api_files:
        year = int(fn.split('.')[0])
        with open(os.path.join(RAW, fn), encoding='utf-8') as f:
            resp = json.load(f)
        questions = []
        for item in resp.get('data') or []:
            q = item.get('question') or {}
            n = q.get('questionIndex')

            def read_page(kind):
                p = os.path.join(HTML, kind, str(year), f'{n}.html')
                if not os.path.exists(p) or os.path.getsize(p) < 200:
                    problems.append(f'{year}/{n} 缺 {kind} 页面')
                    return ''
                with open(p, encoding='utf-8') as fh:
                    return fh.read()

            qhtml = read_page('questions')
            ahtml = read_page('answers')
            xhtml = read_page('analysis')

            content = extract_balanced_div(qhtml, 'content') if qhtml else ''
            options = extract_options(content or '')
            stem = stem_without_options(content or '') if options else (content or '').strip()

            answer_html = extract_balanced_div(ahtml, 'content') if ahtml else ''
            analysis_html = (extract_balanced_div(xhtml, 'analysis-content') or
                             extract_balanced_div(xhtml, 'content') or '') if xhtml else ''

            answer = q.get('answer') or answer_from_html(answer_html) or ''
            if not answer and q.get('questionType') == 1:
                problems.append(f'{year}/{n} 单选题无答案')

            tip_raw = (tips.get(str(year)) or {}).get(str(n)) or ''
            tip_first, _, tip_second = tip_raw.partition('||')

            kp_ids = q.get('knowledgePointIds') or []
            kps = [name_map[int(i)] for i in kp_ids if int(i) in name_map]
            subject = subject_of.get(int(kp_ids[0])) if kp_ids else None

            stats = {
                'avgDifficulty': q.get('avgDifficulty'),
                'optionCounts': {
                    'A': q.get('optionACount'), 'B': q.get('optionBCount'),
                    'C': q.get('optionCCount'), 'D': q.get('optionDCount'),
                },
            }

            questions.append({
                'year': year,
                'index': n,
                'id': q.get('id'),
                'type': q.get('questionType'),
                'typeName': TYPE_NAMES.get(q.get('questionType'), f'类型{q.get("questionType")}'),
                'subject': subject,
                'score': q.get('score'),
                'answer': answer,
                'hintFirst': tip_first.strip(),
                'hintSecond': tip_second.strip(),
                'knowledgePoints': kps,
                'stemHtml': stem,
                'options': options,
                'answerHtml': answer_html.strip(),
                'analysisHtml': analysis_html.strip(),
                'stats': stats,
            })

        # 兜底：知识点 id 无效的题目，从相邻题目继承科目（408 试卷按科目分块排序）
        for i, q in enumerate(questions):
            if not q['subject']:
                for j in (i - 1, i + 1):
                    if 0 <= j < len(questions) and questions[j]['subject']:
                        q['subject'] = questions[j]['subject']
                        break
                else:
                    problems.append(f"{q['year']}/{q['index']} 无科目（知识点缺失）")

        out = {'year': year, 'count': len(questions), 'questions': questions}
        with open(os.path.join(DATA, f'{year}.json'), 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        total += len(questions)
        by_subject = {}
        for q in questions:
            by_subject[q['subject'] or '未知'] = by_subject.get(q['subject'] or '未知', 0) + 1
        index.append({'year': year, 'count': len(questions),
                      'totalScore': sum(q['score'] or 0 for q in questions),
                      'bySubject': by_subject})
        print(f'{year}: {len(questions)} 题')

    with open(os.path.join(DATA, 'index.json'), 'w', encoding='utf-8') as f:
        json.dump({'total': total, 'years': index}, f, ensure_ascii=False, indent=1)
    print(f'总计 {total} 题')
    if problems:
        print('问题清单:')
        for p in problems:
            print('  ' + p)
        sys.exit(2)


if __name__ == '__main__':
    main()
