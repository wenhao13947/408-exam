# 后端接口说明（新手版）

内部使用版本：**不做登录鉴权**。小程序在每台设备上生成一个随机 ID，通过请求头 `X-Device-Id` 传给后端，后端用它区分不同设备的进度。

所有接口都在 `https://408.wenhao.vip` 下，统一返回结构：

- 成功：`{"code": 0, "data": {...}}`
- 失败：`{"code": 非0, "message": "可读的错误原因"}`

除健康检查外，每个请求都要带请求头：`X-Device-Id: <设备ID>`。缺少时返回 400。

## 0. 健康检查

`GET /api/health`

返回：`{"code":0,"data":{"status":"ok","auth":"device-id"}}`

## 1. 年份列表

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

## 2. 某年题目列表

`GET /api/years/{year}/questions`

返回：`data.questions` 是题目摘要数组，每项含 `index / type / typeName / subject / score / hasOptions`。`hasOptions` 表示是否为选择题，供年份页决定颜色标记。

## 3. 题目详情

`GET /api/questions/{year}/{index}`

返回关键字段：

| 字段 | 含义 |
|---|---|
| `question` | 题干 HTML、选项 HTML、答案、两级提示、知识点、原解析、统计 |
| `enhanced.md` | 增强解析 Markdown（towxml 渲染，支持表格与 KaTeX） |
| `enhanced.wof` | 按错误选项组织的反馈：`{ "A": { title, reason, trap, crowdHint } }` |
| `progress` | 当前设备该题进度；没有记录时为 `null` |
| `hasVisual` | 是否有可视化解析 |
| `prevIndex` / `nextIndex` | 上一题/下一题题号，没有则为 `null` |

## 4. 进度查询

- `GET /api/progress`：当前设备全部进度。
- `GET /api/progress/{year}`：当前设备某年进度。

返回的 `records` 结构：

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

## 5. 提交答案

`POST /api/progress/answer`

```json
{ "year": 2009, "index": 2, "choice": "C" }
```

后端根据题库里的 `answer` 判定是否正确，不接受客户端传来的 `correct`。

## 6. 记录提示

`POST /api/progress/hint`

```json
{ "year": 2009, "index": 2, "level": 1 }
```

`level` 只能是 1 或 2；后端取历史最大值，避免「进一步提示」被降级。

## 7. 记录已看解析

`POST /api/progress/view`

```json
{ "year": 2009, "index": 2 }
```

## 8. 清空某年进度

`POST /api/progress/clear`

```json
{ "year": 2009 }
```

只删除当前设备、指定年份的记录。

## 错误码

| HTTP 状态码 | 含义 |
|---|---|
| 400 | 缺少设备标识或参数错误 |
| 404 | 年份或题目不存在 |
| 500 | 服务端内部错误 |
