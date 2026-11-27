# 408 真题刷题 · 微信小程序版

参考 `408刷题原型.html` 移植的微信小程序。小程序只放界面，全部题库与进度放在自建 Python 服务端。

## 快速开始

### 1. 迁移题库（本地执行一次）

```bash
python scripts/import_prototype_data.py
python scripts/check_import.py
```

应看到：18 年 / 846 题 / 增强解析 846 / 图片缺失 0。

### 2. 服务端

接口已部署在 `https://408.wenhao.vip`，内部使用版本**不做登录鉴权**：每台设备本地生成 ID，通过请求头 `X-Device-Id` 区分进度。

服务器管理命令见 `docs/deployment.md`。环境变量样例见 `env.example`（不再需要微信密钥）。

### 3. 打开小程序

用微信开发者工具打开本目录（`project.config.json` 所在层），执行「工具 → 构建 npm」，然后点「预览」。

request 合法域名需设为 `https://408.wenhao.vip`。

## 验证命令

```bash
python scripts/check_import.py
pip install -r server/requirements.txt
python scripts/smoke_test_backend.py
```

## 目录速览

- `miniprogram/`：小程序三个页面与工具代码。
- `server/`：FastAPI 后端与 SQLite 数据库。
- `scripts/`：题库迁移、校验、后端冒烟测试。
- `nginx/`：HTTPS 与反向代理（服务器复用现有 Nginx，见部署文档）。
- `docs/`：架构、接口、部署、组件详解。

详细文档从 `docs/miniprogram-architecture.md` 开始。
