# -*- coding: utf-8 -*-
"""题库接口：年份列表、题目列表、题目详情。"""
import json

from fastapi import APIRouter, Depends, HTTPException

from .. import auth, db

router = APIRouter(prefix='/api', tags=['questions'])


@router.get('/years')
def list_years(_user: str = Depends(auth.current_user)):
    conn = db.connect()
    rows = conn.execute('SELECT * FROM years ORDER BY year').fetchall()
    conn.close()
    years = []
    for r in rows:
        years.append({
            'year': r['year'],
            'count': r['question_count'],
            'totalScore': r['total_score'],
            'bySubject': json.loads(r['by_subject_json'])
        })
    return {'code': 0, 'data': {'total': sum(y['count'] for y in years), 'years': years}}


@router.get('/years/{year}/questions')
def list_questions(year: int, _user: str = Depends(auth.current_user)):
    conn = db.connect()
    rows = conn.execute('''SELECT question_no,type,type_name,subject,score
                           FROM questions WHERE year=? ORDER BY question_no''', (year,)).fetchall()
    conn.close()
    if not rows:
        raise HTTPException(status_code=404, detail='该年份没有题目')
    questions = [{
        'index': r['question_no'], 'type': r['type'], 'typeName': r['type_name'],
        'subject': r['subject'], 'score': r['score'],
        'hasOptions': bool(r['type'] == 1)
    } for r in rows]
    return {'code': 0, 'data': {'year': year, 'questions': questions}}


@router.get('/questions/{year}/{index}')
def get_question(year: int, index: int, user: str = Depends(auth.current_user)):
    conn = db.connect()
    q = conn.execute('SELECT * FROM questions WHERE year=? AND question_no=?', (year, index)).fetchone()
    if not q:
        conn.close()
        raise HTTPException(status_code=404, detail='题目不存在')
    md = conn.execute('SELECT markdown FROM enhanced_md WHERE year=? AND question_no=?',
                      (year, index)).fetchone()
    wof_rows = conn.execute('''SELECT choice,title,reason,trap,crowd_hint FROM wrong_option_feedback
                               WHERE year=? AND question_no=?''', (year, index)).fetchall()
    visual = conn.execute('SELECT lesson_path FROM visual_lesson WHERE year=? AND question_no=?',
                          (year, index)).fetchone()
    prog = conn.execute('''SELECT * FROM progress
                           WHERE user_id=? AND year=? AND question_no=?''', (user, year, index)).fetchone()
    prev_row = conn.execute('SELECT question_no FROM questions WHERE year=? AND question_no<? ORDER BY question_no DESC LIMIT 1',
                            (year, index)).fetchone()
    next_row = conn.execute('SELECT question_no FROM questions WHERE year=? AND question_no>? ORDER BY question_no LIMIT 1',
                            (year, index)).fetchone()
    conn.close()

    question = {
        'index': index,
        'type': q['type'],
        'typeName': q['type_name'],
        'subject': q['subject'],
        'score': q['score'],
        'answer': q['answer'],
        'hintFirst': q['hint_first'],
        'hintSecond': q['hint_second'],
        'knowledgePoints': json.loads(q['knowledge_points_json']),
        'stemHtml': q['stem_html'] or '',
        'options': json.loads(q['options_json']),
        'answerHtml': q['answer_html'] or '',
        'analysisHtml': q['analysis_html'] or '',
        'stats': {
            'avgDifficulty': q['avg_difficulty'],
            'optionCounts': {
                'A': q['option_a_count'], 'B': q['option_b_count'],
                'C': q['option_c_count'], 'D': q['option_d_count']
            }
        }
    }
    wof = {}
    for r in wof_rows:
        wof[r['choice']] = {'title': r['title'], 'reason': r['reason'],
                            'trap': r['trap'], 'crowdHint': r['crowd_hint']}

    return {'code': 0, 'data': {
        'question': question,
        'enhanced': {'md': md['markdown'] if md else '', 'wof': wof},
        'progress': db.row_to_progress(prog),
        'hasVisual': bool(visual),
        'prevIndex': prev_row['question_no'] if prev_row else None,
        'nextIndex': next_row['question_no'] if next_row else None
    }}
