# -*- coding: utf-8 -*-
"""后端接口冒烟测试：本地启动 FastAPI，用临时数据库验证接口，不污染真实进度。

用法（需先 pip install -r server/requirements.txt）：
    python scripts/smoke_test_backend.py
"""
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'server'))

TMP_DIR = tempfile.mkdtemp(prefix='p408-smoke-')
TMP_DB = os.path.join(TMP_DIR, 'questions.db')
shutil.copy2(os.path.join(ROOT, 'server', 'data', 'questions.db'), TMP_DB)
os.environ['P408_DB_PATH'] = TMP_DB

import uvicorn  # noqa: E402
from app.main import app  # noqa: E402

PORT = 8766
BASE = 'http://127.0.0.1:%d' % PORT
DEVICE_A = 'smoke-device-a'
DEVICE_B = 'smoke-device-b'


def call(path, method='GET', body=None, device=DEVICE_A):
    headers = {'content-type': 'application/json', 'X-Device-Id': device}
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode('utf-8') if body is not None else None,
        headers=headers,
        method=method
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode('utf-8'))


def main():
    config = uvicorn.Config(app, host='127.0.0.1', port=PORT, log_level='warning')
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(50):
        if server.started:
            break
        time.sleep(.1)
    if not server.started:
        raise SystemExit('服务启动失败')

    try:
        health = call('/api/health')
        years = call('/api/years')['data']
        qs = call('/api/years/2009/questions')['data']
        detail = call('/api/questions/2009/2')['data']

        call('/api/progress/answer', 'POST', {'year': 2009, 'index': 2, 'choice': 'C'})
        call('/api/progress/hint', 'POST', {'year': 2009, 'index': 2, 'level': 2})
        call('/api/progress/view', 'POST', {'year': 2009, 'index': 2})
        prog = call('/api/progress')['data']['records']
        other = call('/api/progress', device=DEVICE_B)['data']['records']
        call('/api/progress/clear', 'POST', {'year': 2009})
        cleared = call('/api/progress')['data']['records']

        record = prog.get('2009-2')
        assert health['data']['auth'] == 'device-id'
        assert len(years['years']) == 18 and years['total'] == 846
        assert len(qs['questions']) == 47 and qs['questions'][0]['hasOptions'] is True
        assert detail['question']['index'] == 2 and detail['enhanced']['md']
        assert record and record['choice'] == 'C' and record['correct'] is True
        assert record['hintLevel'] == 2 and record['viewed'] is True
        assert not other and '2009-2' not in cleared
        print('冒烟测试通过：设备ID隔离正常，题库与进度接口均可用')
    finally:
        server.should_exit = True
        thread.join(timeout=5)
        shutil.rmtree(TMP_DIR, ignore_errors=True)


if __name__ == '__main__':
    main()
