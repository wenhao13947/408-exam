# 部署说明（新手版）

目标：在服务器上用 Docker 跑起后端，让小程序能通过 HTTPS 访问接口。

## 实际部署记录（2026-11-24，已生效）

服务器上已有 `wenhao-nginx` 容器占用 80/443，并已为 `408.wenhao.vip` 配置证书。因此**没有另起 Nginx**，而是复用现有站点：

| 项目 | 实际值 |
|---|---|
| 接口基地址 | `https://408.wenhao.vip` |
| 健康检查 | `https://408.wenhao.vip/api/health` |
| API 容器 | `p408-api`（镜像 `p408-api:latest`，基于 `python:3.12-slim`） |
| API 容器内端口 | 8000；宿主机 `127.0.0.1:8767` 仅用于调试 |
| Nginx 代理 | `location /api/ { proxy_pass http://p408-api:8000; }` |
| Docker 网络 | API 容器已加入 `backend_phone-control-network`，与 Nginx 同网 |
| 项目目录 | `/root/projects/408mini` |
| 静态图片 | `/MyDocument/Data/nginx/html/p408-api/`（挂载进 Nginx 容器的 `/usr/share/nginx/html/p408-api/`） |
| Nginx 配置备份 | `/MyDocument/Data/nginx/conf/conf.d/408.conf.bak.p408-final` |

验证结果：健康检查返回 `{"code":0,"data":{"status":"ok"}}`；年份接口返回 18 年 / 846 题；题目详情、进度接口正常；静态 SVG 返回 200。

**鉴权已移除（2026-11-26）**：改为设备 ID 模式，不再需要 `WX_APPID` / `WX_APPSECRET` / `TOKEN_SECRET`。小程序请求头带 `X-Device-Id` 即可，不同设备进度隔离。登录接口 `/api/auth/login` 已删除。

重新部署命令（修改代码后）：

```bash
cd /root/projects/408mini
docker rm -f p408-api
docker build -t p408-api:latest server
docker run -d --name p408-api --restart unless-stopped -p 127.0.0.1:8767:8000 --env-file .env p408-api:latest
docker network connect backend_phone-control-network p408-api 2>/dev/null || true
curl -H 'X-Device-Id: test-device' https://408.wenhao.vip/api/health
```

小程序端需在微信公众平台把 request 合法域名设为 `https://408.wenhao.vip`。

以下为通用部署方案（新建独立 Nginx 时参考），当前服务器未采用。

## 1. 一次性准备

1. 在微信公众平台确认小程序的 AppID 是 `wxf07a6cf3c283a0aa`，并重置泄露过的 AppSecret。
2. 确认 `wenhao.vip` 的 DNS 已解析到服务器，且域名已备案（微信小程序要求 request 域名必须备案）。
3. 准备 HTTPS 证书。可用 Let's Encrypt，证书文件放到项目根目录的 `certs/`：
   - `certs/fullchain.pem`
   - `certs/privkey.pem`
4. 在微信公众平台「开发管理 → 服务器域名 → request 合法域名」加入 `https://wenhao.vip`。

## 2. 环境变量

复制样例：

```bash
cp env.example .env
```

然后用编辑器填写：

| 变量 | 说明 |
|---|---|
| `WX_APPID` | 小程序 AppID |
| `WX_APPSECRET` | 小程序 AppSecret（重置后的新值），只写在这里，不写进代码或文档 |
| `TOKEN_SECRET` | 自定义的一串随机字符串，用来给登录 token 签名 |
| `TOKEN_TTL_SECONDS` | token 有效秒数，默认 86400（一天） |
| `P408_DB_PATH` | 容器内数据库路径，保持 `/app/data/questions.db` |

`.env` 不要提交到 Git。仓库里只保留 `env.example`。

## 3. 题库迁移

在本地或服务器上执行一次：

```bash
python scripts/import_prototype_data.py
python scripts/check_import.py
```

第一个命令生成 `server/data/questions.db` 和 `server/static/questions/*.svg`；第二个命令校验 18 年、846 题、图片引用完整。

## 4. 启动服务

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f api
```

- API 容器内部监听 8000，不直接暴露到公网。
- Nginx 容器监听 80/443，负责 HTTPS 和 `/api/` 转发。
- 静态图片通过 `/static/`、`/image/`、`/static/questions/` 三个路径分发。

## 5. 验证

```bash
curl https://wenhao.vip/api/health
```

期望返回：`{"code":0,"data":{"status":"ok"}}`

## 6. 小程序端配置

1. 用微信开发者工具打开项目根目录（有 `project.config.json` 的那一层）。
2. 在开发者工具里执行「工具 → 构建 npm」，生成 `miniprogram_npm/towxml`。没有这一步，答题页会报找不到组件。
3. 在「详情 → 本地设置」确认已勾选 ES6 转 ES5 等选项。
4. 点击「预览」扫码在手机上测试；真机请求域名必须已在白名单。

## 7. 常见问题

| 现象 | 原因与处理 |
|---|---|
| 小程序提示 `url not in domain list` | request 合法域名没配或协议不是 HTTPS |
| 答题页空白/编译报找不到 towxml | 没有执行「构建 npm」 |
| 后端日志显示未配置 appid/appsecret | `.env` 没写或 docker compose 没重新创建容器，执行 `docker compose up -d --force-recreate` |
| 题目图片 404 | `server/static` 或 `html/static` 没挂载进 nginx 容器，检查 docker-compose.yml 的 volumes |
| 登录接口 401 | code 过期或 appsecret 错误；code 只能用一次，重新 `wx.login` |

## 8. 安全提醒

- 不要把 AppSecret、服务器密码写进任何代码、文档、Git 提交或聊天记录。
- `.env` 和 `certs/` 建议加入 `.gitignore`。
- 日志中不记录 token、openid、密钥原文。
