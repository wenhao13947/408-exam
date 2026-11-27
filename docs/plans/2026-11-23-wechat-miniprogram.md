# 微信小程序迁移实施设计（2026-11-23）

> 状态：服务端已部署并验证（2026-11-24）；2026-11-26 按用户要求去掉鉴权，改为设备 ID 模式并重新部署。

## 1. 目的与背景

参考 `408刷题原型.html`，开发微信小程序版本。由于 `prototype-data/` 约 32.8MB，超过小程序包体限制，题库必须放服务端。用户选择 towxml 渲染 Markdown + KaTeX，选择 Python 自建后端并用 SQLite 保存进度与登录态。

## 2. 期望结果

- 小程序三页面：首页年份列表、年份题目网格、答题页。
- 完整保留提交答案、两级提示、答错反馈、查看答案、原解析/增强解析页签、翻页。
- 增强解析支持表格与 KaTeX 公式；可视化解析降级。
- 服务端保存进度与登录态；不打包题库；不泄露密钥。

## 3. 核心逻辑

```mermaid
flowchart TD
    A[小程序提交 wx.login code] --> B[后端 code2session 换 openid]
    B --> C[签发自定义 token]
    C --> D[小程序带 token 请求题库/进度]
    D --> E[FastAPI 查 SQLite]
    E --> F[返回统一结构 code/data]
    F --> G[towxml 解析 HTML/Markdown]
    G --> H[页面显示与交互]
```

## 4. 实现方案

- 小程序原生框架，目录 `miniprogram/`，`app.json` 注册三页面。
- `utils/api.js` 统一请求，`utils/auth.js` 管理 token，`utils/progress.js` 换算状态。
- 答题页 `load()` 一次解析所有 towxml 节点，页签切换复用。
- Python FastAPI 后端，SQLite 存题库与进度；Nginx 处理 HTTPS 与静态图片。
- `scripts/import_prototype_data.py` 从原型 JS 迁移数据，抽取 SVG 为静态图片。

## 5. 涉及代码

新增：
- `project.config.json`
- `miniprogram/**`
- `server/**`
- `scripts/import_prototype_data.py`、`check_import.py`、`smoke_test_backend.py`
- `docker-compose.yml`、`nginx/**`、`env.example`
- `docs/miniprogram-architecture.md`、`api.md`、`deployment.md`、`components/**`

不修改：`408刷题原型.html`、`prototype-data/**`。

## 6. 风险与处理

| 风险 | 处理 |
|---|---|
| 密钥泄露 | appsecret/root 密码只走环境变量，不写文件 |
| 包体超限 | 题库放服务端，小程序只放 UI |
| towxml 未构建 | 文档强调开发者工具执行「构建 npm」 |
| SVG 兼容 | 去掉 draw.io content 元数据；必要时转 PNG |
| 可视化 iframe | 小程序降级为提示文字 |

## 7. 验收标准

- `python scripts/check_import.py` 通过：18 年、846 题、图片无缺失。
- 后端冒烟测试通过：健康、年份、题目、详情、答题/提示/解析/清空接口正常。
- 小程序可编译、可预览；三页面流程走通；增强解析公式与表格正常。
- 仓库中无明文密钥。

## 8. 实施偏差与变更日志

### 2026-11-23 偏差记录

1. **Context7 文档查询失败**：环境报 `fetch failed`，未能在线核对 towxml / FastAPI 最新版本用法。处理方式：采用已知稳定写法，并在 `docs/components/towxml.md` 中标注版本变化时检查 `parse` 参数与组件路径。
2. **requirements.txt 版本调整**：原写 `uvicorn[standard]==0.34.0`，当前软件源最高 0.33.0，安装失败。改为范围约束 `>=0.30,<0.34`，实测安装与冒烟测试通过。
3. **迁移筛选变量笔误**：`enhanced-*.js` 筛选初版误用外层变量 `fn`，导致增强解析 0 条；已修正为 `f`，现为 846 条。
4. **图片路径校验**：原型自带 `/static/questions/2023/38-official-diagram.png` 指向 html 目录而非迁移输出目录，校验脚本增加双路径回退，现图片引用 246 个、缺失 0。
5. **code-reviewer 审查后修复**：移除 `TOKEN_SECRET` 弱默认值（漏配直接拒绝启动）；年份页改用后端 `hasOptions` 判断选择题，避免摘要无 `options` 时崩溃；迁移改为只重建题库表、保留用户进度；SVG content 正则兼容双引号；校验脚本同时检查 `/image/`；80 端口补 ACME 目录与 HTTPS 跳转；SQLite 增加 busy_timeout 与原子创建用户；提示接口返回实际层级并修复无历史时变量未定义；token 过期检查与 401 单次重试；错误反馈限定答错时显示；冒烟测试改用临时库；文档修正构建 npm 与验证命令。
6. **服务器部署方式偏离原计划**：原计划用 `docker-compose.yml` 同时启动 API 与独立 Nginx。实际服务器已有 `wenhao-nginx` 占用 80/443，且已有 `408.wenhao.vip` 证书，因此改为只启动 `p408-api` 容器，并把 `/api/` 代理到该容器（加入 `backend_phone-control-network`，代理地址 `http://p408-api:8000`）。接口基地址为 `https://408.wenhao.vip`。`docker-compose.yml` 保留作为新环境部署参考。
7. **代理地址修正**：初次配置写成 `proxy_pass http://127.0.0.1:8767`，在 Nginx 容器内指向自身导致 502；改为同网容器名 `p408-api:8000` 后公网健康检查通过。
8. **appsecret 处理**：按安全约定未在服务器 `.env` 中填写 appsecret，登录接口需用户重置密钥后自行填入并重启容器；题库与进度接口已验证正常。
9. **2026-11-26 去掉鉴权（用户要求）**：小程序请求地址 404 的直接原因是 `apiBase` 写成 `https://wenhao.vip`（实际为 `https://408.wenhao.vip`），且登录依赖未填写的 appsecret。用户明确要求内部使用不做鉴权，选择「每台设备独立进度」。实现：小程序启动时生成本地 `deviceId` 并通过 `X-Device-Id` 请求头发送；后端 `current_user` 改为读取该请求头，删除 `code2session`/token/`auth/login` 路由及相关环境变量；文档、冒烟测试同步更新。冒烟测试验证两台设备进度互不干扰。
9. **towxml 接入方案重做（2026-11-26）**：原计划用 `package.json` 声明 `towxml@^4.0.0` + 开发者工具「构建 npm」，实际该版本在 npm 官方源不存在（最高 3.0.6），`npm install` 报 `ETARGET`，导致 `miniprogram_npm` 无法生成，开发者工具报组件找不到。进一步核对 3.0.6 包内容发现三个隐藏错误：组件入口是 `towxml.*` 而非 `index`、`parse` 类型只接受 `'markdown'` 而非 `'md'`、`index.js` 导出的是函数而非带 `.parse` 的对象；且包内 `decode.json` 用绝对路径 `/towxml/...` 要求整包放在 `miniprogram/towxml/`。实际改为本地目录接入：放置 `towxml@3.0.6` 到 `miniprogram/towxml/`，组件路径改 `/towxml/towxml`，`getParser()` 内包装导出函数为 `{ parse }`，类型改 `'markdown'`，样式改 `./towxml/style/main.wxss`，删除 package.json 依赖声明。详见 `docs/plans/2026-11-26-fix-towxml-component.md`。
