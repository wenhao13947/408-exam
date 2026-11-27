# -*- coding: utf-8 -*-
"""配置读取：内部使用版本，不依赖微信登录密钥。"""
import os

TOKEN_TTL_SECONDS = int(os.environ.get('TOKEN_TTL_SECONDS', '86400'))

DB_PATH = os.environ.get('P408_DB_PATH', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'questions.db'))
