# -*- coding: utf-8 -*-
"""FastAPI 入口：注册路由、健康检查、统一返回结构。"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from . import db
from .routers import latex, progress, questions

app = FastAPI(title='408 刷题小程序后端', version='1.1.0')


@app.on_event('startup')
def on_startup():
    db.init_db()


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code,
                        content={'code': exc.status_code, 'message': str(exc.detail)})


@app.get('/api/health')
def health():
    return {'code': 0, 'data': {'status': 'ok', 'auth': 'device-id'}}


app.include_router(questions.router)
app.include_router(progress.router)
app.include_router(latex.router)
