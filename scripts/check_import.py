# -*- coding: utf-8 -*-
"""校验迁移结果：年份覆盖、题号唯一、图片引用与 SVG 文件存在。

用法：python scripts/check_import.py
"""
import json
import os
import re
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, 'server', 'data', 'questions.db')
STATIC_DIR = os.path.join(ROOT, 'server', 'static', 'questions')

IMG_RE = re.compile(r'<img[^>]+src="(/(?:static|image)/[^"]+)"')


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    years = conn.execute('SELECT COUNT(*) FROM years').fetchone()[0]
    questions = conn.execute('SELECT COUNT(*) FROM questions').fetchone()[0]
    duplicates = conn.execute('''SELECT year,question_no,COUNT(*) c FROM questions
                                GROUP BY year,question_no HAVING c>1''').fetchall()
    md_count = conn.execute('SELECT COUNT(*) FROM enhanced_md').fetchone()[0]
    wof_count = conn.execute('SELECT COUNT(*) FROM wrong_option_feedback').fetchone()[0]

    print('年份: %d, 题目: %d, 增强解析: %d, 错误反馈: %d' % (years, questions, md_count, wof_count))
    if duplicates:
        raise SystemExit('题号重复: %s' % [tuple(r) for r in duplicates[:5]])

    missing = set()
    total_refs = 0
    for row in conn.execute('SELECT stem_html,answer_html,analysis_html FROM questions'):
        for field in row:
            for src in IMG_RE.findall(field or ''):
                total_refs += 1
                if src.startswith('/static/questions/'):
                    local_server = os.path.join(ROOT, 'server', src.lstrip('/'))
                    local_html = os.path.join(ROOT, 'html', src.lstrip('/'))
                    local = local_server if os.path.exists(local_server) else local_html
                elif src.startswith('/static/'):
                    local = os.path.join(ROOT, 'html', src.lstrip('/'))
                elif src.startswith('/image/'):
                    local = os.path.join(ROOT, 'html', src.lstrip('/'))
                else:
                    local = os.path.join(ROOT, 'server', src.lstrip('/'))
                if not os.path.exists(local):
                    missing.add(src)
    print('静态图片引用: %d, 缺失: %d' % (total_refs, len(missing)))
    if missing:
        print('缺失示例:', list(sorted(missing))[:10])

    svg_files = [f for f in os.listdir(STATIC_DIR)] if os.path.isdir(STATIC_DIR) else []
    print('抽取 SVG 文件: %d' % len(svg_files))
    conn.close()

    if questions < 800 or md_count < 100:
        raise SystemExit('题库数量异常，请重新执行 import_prototype_data.py')
    if missing:
        raise SystemExit('存在缺失的静态图片引用')
    print('校验通过')


if __name__ == '__main__':
    main()
