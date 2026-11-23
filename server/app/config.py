# -*- coding: utf-8 -*-
"""配置读取：所有敏感值只从环境变量读取，不写入代码或仓库。

变量说明见根目录 env.example（只含变量名，不含值）。
"""
import os

WX_APPID = os.environ.get('WX_APPID', '')
WX_APPSECRET = os.environ.get('WX_APPSECRET', '')

# 不使用弱默认密钥：漏配时直接拒绝启动，避免任何人伪造登录态
TOKEN_SECRET = os.environ.get('TOKEN_SECRET', '')
if len(TOKEN_SECRET) < 16:
    raise RuntimeError('请在环境变量 TOKEN_SECRET 中设置至少 16 位的随机字符串（见 env.example）')

TOKEN_TTL_SECONDS = int(os.environ.get('TOKEN_TTL_SECONDS', '86400'))

DB_PATH = os.environ.get('P408_DB_PATH', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'questions.db'))
