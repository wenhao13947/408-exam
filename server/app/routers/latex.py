# -*- coding: utf-8 -*-
"""公式图片接口：按 LaTeX 源码的 hash 返回预渲染 PNG。

小程序端的 <image> 组件无法携带请求头，所以本接口不要求设备标识；
公式内容是公开的题目解析，不涉及隐私。

图片由 scripts/build_formula_images.py + scripts/render_formulas.js 预生成，
映射表与图片位于 server/static/formulas/，随 Docker 镜像一起发布。
"""
import hashlib
import json
import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix='/api', tags=['latex'])

# latex.py 位于 server/app/routers/，向上三级才是 server/
SERVER_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FORMULA_DIR = os.path.join(SERVER_DIR, 'static', 'formulas')
MAP_FILE = os.path.join(FORMULA_DIR, 'formula-map.json')

_formula_map = None


def get_formula_map():
    """懒加载映射表：首次请求时读取一次，之后复用内存中的字典。"""
    global _formula_map
    if _formula_map is None:
        if not os.path.isfile(MAP_FILE):
            raise HTTPException(status_code=503, detail='公式映射表尚未生成')
        with open(MAP_FILE, 'r', encoding='utf-8') as f:
            _formula_map = json.load(f)
    return _formula_map


def normalize(tex):
    """统一换行并去首尾空白，必须与提取脚本的口径完全一致。"""
    return tex.replace('\r\n', '\n').replace('\r', '\n').strip()


def formula_hash(tex, kind):
    return hashlib.md5((normalize(tex) + '|' + kind).encode('utf-8')).hexdigest()


@router.get('/latex')
def latex_image(tex: str = '', type: str = 'line'):
    """返回公式 PNG。

    参数：
      tex  —— LaTeX 源码（URL 编码，框架自动解码）
      type —— line 行内公式 / block 独立成行公式

    异常路径：
      - 空公式、未知公式、映射表缺文件：统一返回 404，
        小程序端捕获后降级显示 LaTeX 源码，避免出现空白。
    """
    kind = type if type in ('line', 'block') else 'line'
    norm = normalize(tex)
    if not norm:
        raise HTTPException(status_code=404, detail='公式为空')

    digest = formula_hash(norm, kind)
    entry = get_formula_map().get(digest)
    if not entry:
        raise HTTPException(status_code=404, detail='公式图片不存在')

    image_path = os.path.join(FORMULA_DIR, entry['file'])
    if not os.path.isfile(image_path):
        raise HTTPException(status_code=404, detail='公式图片文件缺失')

    return FileResponse(
        image_path,
        media_type='image/png',
        headers={'Cache-Control': 'public, max-age=31536000, immutable'}
    )
