# -*- coding: utf-8 -*-
"""SQLite 连接与用户/进度表初始化（题库表由迁移脚本创建）。"""
import os
import sqlite3
import time

from . import config


def connect():
    conn = sqlite3.connect(config.DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    # 多用户同时写进度时等待锁，避免直接 database is locked
    conn.execute('PRAGMA busy_timeout = 5000')
    return conn


def init_db():
    os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
    conn = connect()
    conn.executescript('''
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
    ''')
    conn.commit()
    conn.close()


def get_or_create_user(openid):
    import hashlib
    conn = connect()
    user_id = hashlib.sha256((openid + '|p408').encode('utf-8')).hexdigest()[:24]
    # 原子插入：并发首次登录同一 openid 时不会因 UNIQUE 冲突报错
    conn.execute('INSERT OR IGNORE INTO users(user_id,openid,created_at) VALUES(?,?,?)',
                 (user_id, openid, int(time.time())))
    conn.commit()
    row = conn.execute('SELECT user_id FROM users WHERE openid=?', (openid,)).fetchone()
    conn.close()
    return row['user_id']


def row_to_progress(row):
    if not row:
        return None
    return {
        'choice': row['choice'],
        'correct': bool(row['correct']) if row['correct'] is not None else None,
        'viewed': bool(row['viewed']),
        'hintLevel': row['hint_level'] or 0,
        't': row['updated_at'] * 1000
    }
