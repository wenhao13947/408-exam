# -*- coding: utf-8 -*-
"""把 prototype-data/*.js 迁移到 server/data/questions.db。

数据来源：原型的 37 个 JS 文件（内部是 JSON 字面量）。
输出到：server/data/questions.db（SQLite）+ server/static/questions/*.svg。

用法：python scripts/import_prototype_data.py
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'prototype-data')
DB_DIR = os.path.join(ROOT, 'server', 'data')
DB_PATH = os.path.join(DB_DIR, 'questions.db')
STATIC_DIR = os.path.join(ROOT, 'server', 'static', 'questions')

ASSIGN_RE = re.compile(r'^P408\.(\w+)(?:\["(\d+)"\])?\s*=\s*(.+);\s*$', re.M)
SVG_RE = re.compile(r'<svg\b[^>]*>.*?</svg>', re.S | re.I)
SVG_CONTENT_ATTR_RE = re.compile(r'\scontent\s*=\s*(["\'])[\s\S]*?\1')


def parse_js(path):
    """逐行解析 P408.xxx = {...}; 形式，返回 [(key, subkey, value)]。"""
    with open(path, encoding='utf-8') as f:
        text = f.read()
    out = []
    for m in ASSIGN_RE.finditer(text):
        key, subkey, raw = m.group(1), m.group(2), m.group(3)
        try:
            out.append((key, subkey, json.loads(raw)))
        except json.JSONDecodeError as exc:
            raise ValueError('无法解析 %s 中的 P408.%s: %s' % (path, key, exc))
    return out


def rewrite_image_src(value):
    """把原型里的相对图片路径改成后端 Nginx 静态路径。"""
    if not value:
        return value
    rules = [
        (r'src="html/static/', 'src="/static/'),
        (r'src="html/image/', 'src="/image/'),
        (r'src="/static/', 'src="/static/'),
        (r'src="/image/', 'src="/image/'),
    ]
    for pat, rep in rules:
        value = re.sub(pat, rep, value)
    return value


def sanitize_svg(svg):
    """删除 draw.io 的 content 元数据属性，避免数据库/图片体积爆炸。"""
    return SVG_CONTENT_ATTR_RE.sub('', svg)


def extract_svg(html, year, index, field, counter):
    """把内联 SVG 换成静态图片引用，返回替换后的 HTML。"""
    if not html:
        return html

    def repl(match):
        name = '%s_%s_%s_%d.svg' % (year, index, field, counter[0])
        counter[0] += 1
        svg = sanitize_svg(match.group(0))
        with open(os.path.join(STATIC_DIR, name), 'w', encoding='utf-8') as f:
            f.write(svg)
        return '<img src="/static/questions/%s" style="max-width:100%%;height:auto" />' % name

    return SVG_RE.sub(repl, html)


def clean_html(value, year, index, field, counter):
    value = rewrite_image_src(value)
    return extract_svg(value, year, index, field, counter)


def main():
    os.makedirs(DB_DIR, exist_ok=True)
    os.makedirs(STATIC_DIR, exist_ok=True)

    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    # 只重建题库类表，保留 users / progress，避免重跑迁移清空用户进度
    conn.executescript('''
    DROP TABLE IF EXISTS years;
    DROP TABLE IF EXISTS questions;
    DROP TABLE IF EXISTS enhanced_md;
    DROP TABLE IF EXISTS wrong_option_feedback;
    DROP TABLE IF EXISTS visual_lesson;
    ''')
    conn.executescript(SCHEMA)

    # 1) index.js -> years 表
    index_data, visual = None, {}
    for key, sub, value in parse_js(os.path.join(SRC, 'index.js')):
        if key == 'index':
            index_data = value
        elif key == 'visual':
            visual = value
    if not index_data:
        raise RuntimeError('index.js 缺少 P408.index')

    years = []
    for y in index_data.get('years', []):
        years.append((y['year'], y.get('count', 0), y.get('totalScore', 0),
                      json.dumps(y.get('bySubject', {}), ensure_ascii=False)))
    conn.executemany('INSERT INTO years(year,question_count,total_score,by_subject_json) VALUES(?,?,?,?)', years)

    # 2) 可视化题号 -> visual_lesson 表（固定路径规则）
    visual_rows = []
    for year, indices in visual.items():
        for idx in indices:
            lesson = 'html/lessons-v2/visual-analysis-20261026/%s/%02d/index.html' % (year, idx)
            visual_rows.append((int(year), idx, lesson))
    conn.executemany('INSERT OR IGNORE INTO visual_lesson(year,question_no,lesson_path) VALUES(?,?,?)', visual_rows)

    # 3) {year}.js -> questions 表
    year_files = sorted(f for f in os.listdir(SRC) if re.fullmatch(r'\d{4}\.js', f))
    question_total = 0
    for fn in year_files:
        year = int(fn[:-3])
        payloads = parse_js(os.path.join(SRC, fn))
        if not payloads:
            continue
        data = payloads[0][2]
        rows = []
        for q in data.get('questions', []):
            idx = q['index']
            counter = [0]
            stats = q.get('stats') or {}
            counts = stats.get('optionCounts') or {}
            rows.append((
                year, idx, q.get('id'), q.get('type'), q.get('typeName'),
                q.get('subject'), q.get('score'), q.get('answer'),
                q.get('hintFirst'), q.get('hintSecond'),
                json.dumps(q.get('knowledgePoints') or [], ensure_ascii=False),
                clean_html(q.get('stemHtml'), year, idx, 'stem', counter),
                json.dumps(q.get('options') or [], ensure_ascii=False),
                clean_html(q.get('answerHtml'), year, idx, 'answer', counter),
                clean_html(q.get('analysisHtml'), year, idx, 'analysis', counter),
                stats.get('avgDifficulty'),
                counts.get('A'), counts.get('B'), counts.get('C'), counts.get('D'),
            ))
        conn.executemany(INSERT_QUESTION, rows)
        question_total += len(rows)
        print('%s: %d 题' % (year, len(rows)))

    # 4) enhanced-{y}.js -> enhanced_md / wrong_option_feedback
    for fn in sorted(f for f in os.listdir(SRC) if f.startswith('enhanced-') and f.endswith('.js')):
        year = int(fn[len('enhanced-'):-3])
        payload = parse_js(os.path.join(SRC, fn))[0][2]
        md_rows = [(year, int(no), text) for no, text in (payload.get('md') or {}).items()]
        conn.executemany('INSERT OR REPLACE INTO enhanced_md(year,question_no,markdown) VALUES(?,?,?)', md_rows)

        wof_rows = []
        for no, choices in (payload.get('wof') or {}).items():
            for choice, item in choices.items():
                wof_rows.append((year, int(no), choice, item.get('title', ''), item.get('reason', ''),
                                 item.get('trap', ''), item.get('crowdHint', '')))
        conn.executemany(INSERT_WOF, wof_rows)

    conn.commit()
    conn.close()
    print('完成：%d 年 / %d 题 -> %s' % (len(years), question_total, DB_PATH))


SCHEMA = """
CREATE TABLE years(
  year INTEGER PRIMARY KEY,
  question_count INTEGER NOT NULL,
  total_score INTEGER NOT NULL,
  by_subject_json TEXT NOT NULL
);
CREATE TABLE questions(
  year INTEGER NOT NULL,
  question_no INTEGER NOT NULL,
  api_id INTEGER,
  type INTEGER,
  type_name TEXT,
  subject TEXT,
  score INTEGER,
  answer TEXT,
  hint_first TEXT,
  hint_second TEXT,
  knowledge_points_json TEXT NOT NULL,
  stem_html TEXT,
  options_json TEXT NOT NULL,
  answer_html TEXT,
  analysis_html TEXT,
  avg_difficulty REAL,
  option_a_count INTEGER,
  option_b_count INTEGER,
  option_c_count INTEGER,
  option_d_count INTEGER,
  PRIMARY KEY(year, question_no)
);
CREATE TABLE enhanced_md(
  year INTEGER NOT NULL,
  question_no INTEGER NOT NULL,
  markdown TEXT NOT NULL,
  PRIMARY KEY(year, question_no)
);
CREATE TABLE wrong_option_feedback(
  year INTEGER NOT NULL,
  question_no INTEGER NOT NULL,
  choice TEXT NOT NULL,
  title TEXT,
  reason TEXT,
  trap TEXT,
  crowd_hint TEXT,
  PRIMARY KEY(year, question_no, choice)
);
CREATE TABLE visual_lesson(
  year INTEGER NOT NULL,
  question_no INTEGER NOT NULL,
  lesson_path TEXT NOT NULL,
  PRIMARY KEY(year, question_no)
);
CREATE TABLE IF NOT EXISTS users(
  user_id TEXT PRIMARY KEY,
  openid TEXT UNIQUE NOT NULL,
  created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS progress(
  user_id TEXT NOT NULL,
  year INTEGER NOT NULL,
  question_no INTEGER NOT NULL,
  choice TEXT,
  correct INTEGER,
  viewed INTEGER NOT NULL DEFAULT 0,
  hint_level INTEGER NOT NULL DEFAULT 0,
  updated_at INTEGER NOT NULL,
  PRIMARY KEY(user_id, year, question_no)
);
CREATE INDEX IF NOT EXISTS idx_progress_user ON progress(user_id);
"""

INSERT_QUESTION = """INSERT OR REPLACE INTO questions(
  year,question_no,api_id,type,type_name,subject,score,answer,
  hint_first,hint_second,knowledge_points_json,stem_html,options_json,
  answer_html,analysis_html,avg_difficulty,
  option_a_count,option_b_count,option_c_count,option_d_count
) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""

INSERT_WOF = """INSERT OR REPLACE INTO wrong_option_feedback(
  year,question_no,choice,title,reason,trap,crowd_hint
) VALUES(?,?,?,?,?,?,?)"""


if __name__ == '__main__':
    main()
