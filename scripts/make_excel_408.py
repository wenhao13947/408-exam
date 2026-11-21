# -*- coding: utf-8 -*-
"""生成 408 真题汇总 Excel：读取 data/*.json -> data/408真题汇总.xlsx"""
import json
import os
import re

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
OUT = os.path.join(DATA, '408真题汇总.xlsx')

HEADERS = ['年份', '题号', '科目', '题型', '分值', '答案', '知识点', '题干预览']


def plain_text(html, limit=60):
    txt = re.sub(r'<[^>]+>', '', html or '')
    txt = re.sub(r'\s+', ' ', txt).strip()
    return txt[:limit]


def write_rows(ws, questions):
    ws.append(HEADERS)
    for q in questions:
        ws.append([
            q['year'], q['index'], q['subject'] or '', q['typeName'],
            q['score'], q['answer'], '、'.join(q['knowledgePoints']),
            plain_text(q['stemHtml']),
        ])
    # 样式
    header_fill = PatternFill('solid', fgColor='DDEBF7')
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')
    widths = [8, 8, 16, 12, 8, 8, 36, 70]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = 'A2'
    ws.auto_filter.ref = f'A1:{get_column_letter(len(HEADERS))}{ws.max_row}'


def main():
    wb = Workbook()
    ws_all = wb.active
    ws_all.title = '全部题目'
    rows_all = []

    files = sorted(f for f in os.listdir(DATA) if re.match(r'^\d{4}\.json$', f))
    for fn in files:
        with open(os.path.join(DATA, fn), encoding='utf-8') as f:
            data = json.load(f)
        year = data['year']
        rows_all.extend(data['questions'])
        ws = wb.create_sheet(str(year))
        write_rows(ws, data['questions'])

    write_rows(ws_all, rows_all)
    wb.save(OUT)
    print(f'OK: {OUT}  共 {len(rows_all)} 题, {len(files) + 1} 个 Sheet')


if __name__ == '__main__':
    main()
