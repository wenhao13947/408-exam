# -*- coding: utf-8 -*-
"""进度接口：所有写操作以 token 中的 user_id 为准，防止越权修改他人进度。"""
import time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .. import auth, db

router = APIRouter(prefix='/api/progress', tags=['progress'])


def key_of(year, index):
    return '%s-%s' % (year, index)


@router.get('')
def my_progress(user: str = Depends(auth.current_user)):
    conn = db.connect()
    rows = conn.execute('SELECT * FROM progress WHERE user_id=?', (user,)).fetchall()
    conn.close()
    records = {key_of(r['year'], r['question_no']): db.row_to_progress(r) for r in rows}
    return {'code': 0, 'data': {'records': records}}


@router.get('/{year}')
def year_progress(year: int, user: str = Depends(auth.current_user)):
    conn = db.connect()
    rows = conn.execute('SELECT * FROM progress WHERE user_id=? AND year=?', (user, year)).fetchall()
    conn.close()
    records = {key_of(r['year'], r['question_no']): db.row_to_progress(r) for r in rows}
    return {'code': 0, 'data': {'records': records}}


class AnswerIn(BaseModel):
    year: int
    index: int
    choice: str


@router.post('/answer')
def submit_answer(body: AnswerIn, user: str = Depends(auth.current_user)):
    if body.choice not in ('A', 'B', 'C', 'D'):
        raise HTTPException(status_code=400, detail='选项必须是 A/B/C/D')
    conn = db.connect()
    q = conn.execute('SELECT answer,type FROM questions WHERE year=? AND question_no=?',
                     (body.year, body.index)).fetchone()
    if not q:
        conn.close()
        raise HTTPException(status_code=404, detail='题目不存在')
    old = conn.execute('''SELECT viewed,hint_level FROM progress
                          WHERE user_id=? AND year=? AND question_no=?''',
                       (user, body.year, body.index)).fetchone()
    correct = 1 if body.choice == q['answer'] else 0
    viewed = old['viewed'] if old else 0
    hint_level = old['hint_level'] if old else 0
    conn.execute('''INSERT OR REPLACE INTO progress(
        user_id,year,question_no,choice,correct,viewed,hint_level,updated_at
    ) VALUES(?,?,?,?,?,?,?,?)''',
                 (user, body.year, body.index, body.choice, correct, viewed, hint_level, int(time.time())))
    conn.commit()
    conn.close()
    return {'code': 0, 'data': {'correct': bool(correct)}}


class HintIn(BaseModel):
    year: int
    index: int
    level: int


@router.post('/hint')
def set_hint(body: HintIn, user: str = Depends(auth.current_user)):
    if body.level not in (1, 2):
        raise HTTPException(status_code=400, detail='提示层级只能是 1 或 2')
    level = body.level
    conn = db.connect()
    old = conn.execute('''SELECT * FROM progress
                          WHERE user_id=? AND year=? AND question_no=?''',
                       (user, body.year, body.index)).fetchone()
    if old:
        level = max(old['hint_level'] or 0, body.level)
        conn.execute('''UPDATE progress SET hint_level=?,updated_at=?
                        WHERE user_id=? AND year=? AND question_no=?''',
                     (level, int(time.time()), user, body.year, body.index))
    else:
        conn.execute('''INSERT INTO progress(
            user_id,year,question_no,choice,correct,viewed,hint_level,updated_at
        ) VALUES(?,?,?,?,?,?,?,?)''',
                     (user, body.year, body.index, None, None, 0, body.level, int(time.time())))
    conn.commit()
    conn.close()
    return {'code': 0, 'data': {'hintLevel': level}}


class ViewIn(BaseModel):
    year: int
    index: int


@router.post('/view')
def view_analysis(body: ViewIn, user: str = Depends(auth.current_user)):
    conn = db.connect()
    old = conn.execute('''SELECT * FROM progress
                          WHERE user_id=? AND year=? AND question_no=?''',
                       (user, body.year, body.index)).fetchone()
    if old:
        conn.execute('UPDATE progress SET viewed=1,updated_at=? WHERE user_id=? AND year=? AND question_no=?',
                     (int(time.time()), user, body.year, body.index))
    else:
        conn.execute('''INSERT INTO progress(
            user_id,year,question_no,choice,correct,viewed,hint_level,updated_at
        ) VALUES(?,?,?,?,?,?,?,?)''',
                     (user, body.year, body.index, None, None, 1, 0, int(time.time())))
    conn.commit()
    conn.close()
    return {'code': 0, 'data': {'viewed': True}}


class ClearIn(BaseModel):
    year: int


@router.post('/clear')
def clear_year(body: ClearIn, user: str = Depends(auth.current_user)):
    conn = db.connect()
    conn.execute('DELETE FROM progress WHERE user_id=? AND year=?', (user, body.year))
    conn.commit()
    conn.close()
    return {'code': 0, 'data': {'cleared': body.year}}
