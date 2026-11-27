# -*- coding: utf-8 -*-
"""身份识别：内部使用，不做登录鉴权。

小程序在请求头 X-Device-Id 中携带本地生成的设备 ID，后端直接用它作为用户标识。
不同设备的进度彼此隔离；不保存 openid，不使用 appsecret。
"""
from fastapi import Header, HTTPException

DEVICE_HEADER = 'X-Device-Id'


def current_user(x_device_id: str = Header(default='', alias=DEVICE_HEADER)):
    device_id = (x_device_id or '').strip()
    if not device_id:
        raise HTTPException(status_code=400, detail='缺少设备标识 X-Device-Id')
    if len(device_id) > 64:
        raise HTTPException(status_code=400, detail='设备标识过长')
    return device_id
