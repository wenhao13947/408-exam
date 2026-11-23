# 408 真题刷题 · 微信小程序版

参考 `408刷题原型.html` 移植的微信小程序。小程序只放界面，全部题库与进度放在自建 Python 服务端。

## 快速开始

### 1. 迁移题库（本地执行一次）

```bash
python scripts/import_prototype_data.py
python scripts/check_import.py
```

应看到：18 年 / 846 题 / 增强解析 846 / 图片缺失 0。

### 2. 配置服务端

```bash
cp env.example .env
# 编辑 .env，填写 WX_APPID / WX_APPSECRET / TOKEN_SECRET
docker compose up -d --build
curl https://wenhao.vip/api/health
```

### 3. 打开小程序

用微信开发者工具打开本目录（`project.config.json` 所在层），执行「工具 → 构建 npm」，然后点「预览」扫码。

## 目录速览

- `miniprogram/`：小程序三个页面与工具代码。
- `server/`：FastAPI 后端与 SQLite 数据库。
- `scripts/`：题库迁移、校验、后端冒烟测试。
- `nginx/`：HTTPS 与反向代理。
- `docs/`：架构、接口、部署、组件详解。

## 验证命令

```bash
python scripts/check_import.py
pip install -r server/requirements.txt
python scripts/smoke_test_backend.py
```

## 重要提醒

- `appsecret` 和服务器密码不要写进代码、文档或聊天记录；只用环境变量。
- 微信小程序的 request 合法域名必须配置为 `https://wenhao.vip`。
- 可视化解析在小程序中降级为提示文字，完整效果请看网页原型。

详细文档从 `docs/miniprogram-architecture.md` 开始。
