# -*- coding: utf-8 -*-
"""把 API 部署到服务器并接入现有 408.wenhao.vip 的 Nginx。

安全约定：SSH 密码只从环境变量 P408_SSH_PASSWORD 读取，绝不写入脚本或仓库。
用法：
    $env:P408_SSH_PASSWORD='...'
    python scripts/deploy_server.py
"""
import os
import secrets
import tempfile

import paramiko

HOST = 'wenhao.vip'
PORT = 22
USER = 'root'
PASSWORD = os.environ.get('P408_SSH_PASSWORD', '')
if not PASSWORD:
    raise SystemExit('请通过环境变量 P408_SSH_PASSWORD 提供服务器密码')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REMOTE_APP = '/root/projects/408mini'
REMOTE_NGINX_STATIC = '/MyDocument/Data/nginx/html/p408-api'
NGINX_CONF = '/MyDocument/Data/nginx/conf/conf.d/408.conf'
APPID = 'wxf07a6cf3c283a0aa'
API_PORT = 8767

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, PORT, USER, PASSWORD, timeout=30)
sftp = ssh.open_sftp()


def run(cmd, timeout=180):
    _in, out, err = ssh.exec_command(cmd, timeout=timeout)
    o = out.read().decode('utf-8', 'replace')
    e = err.read().decode('utf-8', 'replace')
    code = out.channel.recv_exit_status()
    if code != 0:
        raise RuntimeError('命令失败(%d): %s\n%s\n%s' % (code, cmd, o, e[-2000:]))
    return o.strip()


def mkdir_p(path):
    run('mkdir -p ' + path)


def ensure_remote_dir(path):
    parts = [p for p in path.split('/') if p]
    cur = ''
    for p in parts:
        cur += '/' + p
        try:
            sftp.stat(cur)
        except IOError:
            sftp.mkdir(cur)


def upload_file(local, remote):
    ensure_remote_dir(os.path.dirname(remote))
    sftp.put(local, remote)


def upload_tree(local_root, remote_root, skip=()):
    for dirpath, dirnames, filenames in os.walk(local_root):
        dirnames[:] = [d for d in dirnames if d not in skip]
        rel = os.path.relpath(dirpath, local_root)
        remote_dir = remote_root if rel == '.' else remote_root + '/' + rel.replace('\\', '/')
        ensure_remote_dir(remote_dir)
        for name in filenames:
            sftp.put(os.path.join(dirpath, name), remote_dir + '/' + name)


print('1/7 创建远程目录')
for d in [REMOTE_APP, REMOTE_APP + '/server/data', REMOTE_APP + '/server/static/questions',
          REMOTE_NGINX_STATIC + '/static/questions', REMOTE_NGINX_STATIC + '/static',
          REMOTE_NGINX_STATIC + '/image']:
    mkdir_p(d)

print('2/7 上传后端代码与数据库')
upload_tree(os.path.join(ROOT, 'server', 'app'), REMOTE_APP + '/server/app')
upload_file(os.path.join(ROOT, 'server', 'requirements.txt'), REMOTE_APP + '/server/requirements.txt')
upload_file(os.path.join(ROOT, 'server', 'Dockerfile'), REMOTE_APP + '/server/Dockerfile')
upload_file(os.path.join(ROOT, 'server', 'data', 'questions.db'), REMOTE_APP + '/server/data/questions.db')
upload_tree(os.path.join(ROOT, 'server', 'static', 'questions'), REMOTE_APP + '/server/static/questions')

print('3/7 上传题目静态图片（Nginx 可直接读取的目录）')
upload_tree(os.path.join(ROOT, 'server', 'static', 'questions'), REMOTE_NGINX_STATIC + '/static/questions')
upload_tree(os.path.join(ROOT, 'html', 'static'), REMOTE_NGINX_STATIC + '/static', skip=('questions',))
upload_tree(os.path.join(ROOT, 'html', 'image'), REMOTE_NGINX_STATIC + '/image')

print('4/7 写入 .env（appsecret 留空，需你重置后自行填写）')
token_secret = os.environ.get('P408_TOKEN_SECRET') or secrets.token_urlsafe(32)
# 本地临时保存，供部署后生成测试 token；任务结束后删除，不入库
with open(os.path.join(ROOT, 'server', '.token_secret_local'), 'w', encoding='utf-8') as f:
    f.write(token_secret)
tmp_env = tempfile.NamedTemporaryFile('w', delete=False, encoding='utf-8')
tmp_env.write('WX_APPID=%s\n' % APPID)
tmp_env.write('WX_APPSECRET=\n')
tmp_env.write('TOKEN_SECRET=%s\n' % token_secret)
tmp_env.write('TOKEN_TTL_SECONDS=86400\n')
tmp_env.write('P408_DB_PATH=/app/data/questions.db\n')
tmp_env.close()
upload_file(tmp_env.name, REMOTE_APP + '/.env')
os.unlink(tmp_env.name)
run('chmod 600 ' + REMOTE_APP + '/.env')

print('5/7 构建并启动 API 容器')
run('docker rm -f p408-api 2>/dev/null || true')
run('cd ' + REMOTE_APP + ' && docker build -t p408-api:latest server', timeout=600)
run('cd ' + REMOTE_APP + ' && docker run -d --name p408-api --restart unless-stopped '
    '-p 127.0.0.1:%d:8000 --env-file .env p408-api:latest' % API_PORT, timeout=180)
run('sleep 3 && curl -fsS http://127.0.0.1:%d/api/health' % API_PORT)

print('6/7 把 /api/ 与静态路径挂到现有 408.wenhao.vip 配置')
with sftp.open(NGINX_CONF, 'r') as f:
    conf = f.read().decode('utf-8')
if 'proxy_pass http://127.0.0.1:%d' % API_PORT not in conf:
    backup = NGINX_CONF + '.bak.p408'
    with sftp.open(backup, 'w') as f:
        f.write(conf.encode('utf-8'))
    block = '''
    # ===== 408 刷题小程序 API（由 deploy_server.py 添加）=====
    location /api/ {
        proxy_pass http://127.0.0.1:%d;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    location /static/questions/ {
        alias /usr/share/nginx/html/p408-api/static/questions/;
        add_header Cache-Control "public, max-age=86400";
    }
    location /static/ {
        alias /usr/share/nginx/html/p408-api/static/;
        add_header Cache-Control "public, max-age=86400";
    }
    location /image/ {
        alias /usr/share/nginx/html/p408-api/image/;
        add_header Cache-Control "public, max-age=86400";
    }
''' % API_PORT
    head, sep, tail = conf.rpartition('}')
    conf = head + block + sep + tail
    with sftp.open(NGINX_CONF, 'w') as f:
        f.write(conf.encode('utf-8'))
    print('   已备份原配置到 ' + backup)
run('docker exec wenhao-nginx nginx -t')
run('docker exec wenhao-nginx nginx -s reload')

print('7/7 从公网验证')
print(run('curl -fsS --max-time 10 https://408.wenhao.vip/api/health'))
print('部署完成。API 基地址：https://408.wenhao.vip')

sftp.close()
ssh.close()
