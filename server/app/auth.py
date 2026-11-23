# -*- coding: utf-8 -*-
"""登录鉴权：code2session 由服务端完成，appsecret 只从环境变量读取。

token 格式：base64url(payload).hmac_sha256(payload, TOKEN_SECRET)
payload 含 user_id 与 exp（Unix 秒），不记录 openid 原文到日志。
"""
import base64
import hashlib
import hmac
import json
import time
import urllib.parse
import urllib.request

from fastapi import Header, HTTPException

from . import config, db


def code2session(code):
    if not config.WX_APPID or not config.WX_APPSECRET:
        raise HTTPException(status_code=500, detail='服务端未配置微信 appid/appsecret 环境变量')
    params = urllib.parse.urlencode({
        'appid': config.WX_APPID,
        'secret': config.WX_APPSECRET,
        'js_code': code,
        'grant_type': 'authorization_code'
    })
    url = 'https://api.weixin.qq.com/sns/jscode2session?' + params
    with urllib.request.urlopen(url, timeout=10) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    if 'openid' not in data:
        raise HTTPException(status_code=401, detail='微信登录失败：' + str(data.get('errmsg', '未知错误')))
    return data['openid']


def b64url_encode(raw):
    return base64.urlsafe_b64encode(raw).decode('ascii').rstrip('=')


def b64url_decode(text):
    return base64.urlsafe_b64decode(text + '=' * (-len(text) % 4))


def sign(payload_bytes):
    return b64url_encode(hmac.new(config.TOKEN_SECRET.encode('utf-8'), payload_bytes, hashlib.sha256).digest())


def issue_token(user_id):
    payload = json.dumps({'uid': user_id, 'exp': int(time.time()) + config.TOKEN_TTL_SECONDS},
                         separators=(',', ':')).encode('utf-8')
    body = b64url_encode(payload)
    return body + '.' + sign(payload)


def verify_token(token):
    if not token or '.' not in token:
        raise HTTPException(status_code=401, detail='缺少或无效的登录态')
    body, sig = token.rsplit('.', 1)
    try:
        payload_bytes = b64url_decode(body)
    except Exception:
        raise HTTPException(status_code=401, detail='登录态格式错误')
    if not hmac.compare_digest(sign(payload_bytes), sig):
        raise HTTPException(status_code=401, detail='登录态校验失败')
    try:
        payload = json.loads(payload_bytes)
    except Exception:
        raise HTTPException(status_code=401, detail='登录态内容错误')
    if payload.get('exp', 0) < int(time.time()):
        raise HTTPException(status_code=401, detail='登录态已过期')
    return payload['uid']


def current_user(authorization: str = Header(default='')):
    token = authorization[7:] if authorization.startswith('Bearer ') else authorization
    return verify_token(token)
