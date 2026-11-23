# 后端接口说明（新手版）

所有接口都在 `https://wenhao.vip` 下，统一返回结构：

- 成功：`{"code": 0, "data": {...}}`
- 失败：`{"code": 非0, "message": "可读的错误原因"}`

除登录和健康检查外，请求头都要带：`Authorization: Bearer <token>`。

## 0. 健康检查

`GET /api/health`

返回：`{"code":0,"data":{"status":"ok"}}`

用途：确认后端是否启动，不需要登录。

## 1. 登录

`POST /api/auth/login`

请求体：
```json
{ "code": "wx.login 返回的临时 code" }
```

返回：
```json
{ "code": 0, "data": { "token": "签名后的登录态", "expireAt": 1763880000000 } }
```

发生了什么：

1. 小程序调用 `wx.login` 拿到 `code`（5 分钟有效、只能用一次）。
2. 后端用 `code + appid + appsecret` 向微信换取 `openid`。
3. 后端按 openid 找到或创建用户，签发自定义 token。
4. `appsecret` 只在服务端环境变量 `WX_APPSECRET` 里，前端永远看不到。

## 2. 年份列表

`GET /api/years`

返回：
```json
{
  "code": 0,
  "data": {
    "total": 846,
    "years": [
      { "year": 2009, "count": 47, "totalScore": 100, "bySubject": { "数据结构": 12 } }
    ]
  }
}
```

## 3. 某年题目列表

`GET /api/years/{year}/questions`

返回：`data.questions` 是题目摘要数组，每项含 `index / type / typeName / subject / score / hasOptions`。`hasOptions` 表示是否为选择题，供年份页决定用绿色/红色还是蓝色标记；只返回摘要，避免一次传输大量题干。

## 4. 题目详情

`GET /api/questions/{year}/{index}`

返回关键字段：

| 字段 | 含义 |
|---|---|
| `question` | 题干 HTML、选项 HTML、答案、两级提示、知识点、原解析、统计 |
| `enhanced.md` | 增强解析 Markdown（towxml 渲染，支持表格与 KaTeX） |
| `enhanced.wof` | 按错误选项组织的反馈：`{ "A": { title, reason, trap } }` |
| `progress` | 当前用户该题进度；没有记录时为 `null` |
| `hasVisual` | 是否有可视化解析 |
| `prevIndex` / `nextIndex` | 上一题/下一题题号，没有则为 `null` |

## 5. 进度查询

- `GET /api/progress`：当前用户全部进度。
- `GET /api/progress/{year}`：当前用户某年进度。

返回的 `records` 结构与网页原型一致：

```json
{
  "2009-2": {
    "choice": "C",
    "correct": true,
    "viewed": true,
    "hintLevel": 2,
    "t": 1763880000000
  }
}
```

注意 `t` 是毫秒时间戳，与网页 localStorage 中 `Date.now()` 一致。

## 6. 提交答案

`POST /api/progress/answer`

```json
{ "year": 2009, "index": 2, "choice": "C" }
```

后端根据题库里的 `answer` 判定是否正确，不接受客户端传来的 `correct`，防止伪造成绩。已存在的 `viewed` 和 `hint_level` 会保留。

## 7. 记录提示

`POST /api/progress/hint`

```json
{ "year": 2009, "index": 2, "level": 1 }
```

`level` 只能是 1 或 2。后端取历史最大值，避免「进一步提示」被降级。

## 8. 记录已看解析

`POST /api/progress/view`

```json
{ "year": 2009, "index": 2 }
```

## 9. 清空某年进度

`POST /api/progress/clear`

```json
{ "year": 2009 }
```

只删除当前用户、指定年份的记录。

## 错误码

| HTTP 状态码 | 含义 |
|---|---|
| 400 | 参数错误（如选项不是 A/B/C/D） |
| 401 | 未登录、token 无效或过期；小程序会自动重新登录并重试一次 |
| 404 | 年份或题目不存在 |
| 500 | 服务端配置错误（例如未设置 `WX_APPSECRET`） |
