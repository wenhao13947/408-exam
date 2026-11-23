# -*- coding: utf-8 -*-
"""FastAPI 入口：注册路由、健康检查、统一返回结构。"""
import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from . import auth, config, db
from .routers import progress, questions

app = FastAPI(title='408 刷题小程序后端', version='1.0.0')


@app.on_event('startup')
def on_startup():
    db.init_db()


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code,
                        content={'code': exc.status_code, 'message': str(exc.detail)})


@app.get('/api/health')
def health():
    return {'code': 0, 'data': {'status': 'ok'}}


class LoginIn(BaseModel):
    code: str


@app.post('/api/auth/login')
def login(body: LoginIn):
    openid = auth.code2session(body.code)
    user_id = db.get_or_create_user(openid)
    token = auth.issue_token(user_id)
    expire_at = int(time.time() * 1000) + config.TOKEN_TTL_SECONDS * 1000
    return {'code': 0, 'data': {'token': token, 'expireAt': expire_at}}


app.include_router(questions.router)
app.include_router(progress.router)
