# 修复原型页增强解析图片引用（2026-11-26）

> 状态：待用户确认后实施

## 1. 目的与背景

用户反馈：打开 `408刷题原型.html#/y/2023/q/19`，「原解析」图片正常，「增强解析」图片引用错误。

根因已通过源码与数据核对确认（非浏览器、非素材缺失问题）：

1. `scripts/build_prototype.py` 的 `fix_src()` 只改写题目 HTML 中的 `<img src>`（例如把 `../../static/...` 改为 `html/static/...`），`build_enhanced()` 却把 Markdown 原文原样打包，没有改写 `![...](...)` 里的图片路径。
2. `408刷题原型.html` 的 `mdToHtml()` 没有 Markdown 图片语法分支，`![alt](url)` 会被当成普通文本原样显示，不会生成 `<img>`。
3. 因此 `prototype-data/enhanced-*.js` 中全部 73 处图片引用仍是源站路径 `/data/enhanced-analysis/assets/YYYY/NN/original-analysis-M.*`，在本地 HTML 中既不解析也不显示。
4. 以 2023#19 为例：原解析引用 `html/static/assets/exam/2023/2023_19_ans.jpg`（文件存在）；增强解析引用 `/data/enhanced-analysis/assets/2023/19/original-analysis-1.jpg`（文件不存在）。

## 2. 期望结果

- 2023#19「增强解析」的图片显示为 `html/static/assets/exam/2023/2023_19_ans.jpg`，与原解析一致。
- 同类问题一次性修复：原型数据中可对应真实素材的增强解析图片全部改为本地可访问路径并正常显示。
- 不改动 `html/data/enhanced-analysis/` 源 Markdown、不改动小程序与服务端数据，避免影响其他端。
- 5 处确实没有素材的引用保持原样，并在审计文档中列明，留待用户决策。

## 3. 核心逻辑

全库扫描结果：`html/data/enhanced-analysis/*/*.md` 共 73 处 `![...](/data/enhanced-analysis/assets/...)` 引用，按可对应素材分类：

| 分类 | 数量 | 解析规则 | 示例 |
|---|---:|---|---|
| A | 47 | 对应 `server/static/questions/{年}_{题}_analysis_{M-1}.svg` | `2009/06/original-analysis-1.svg` → `2009_6_analysis_0.svg` |
| B | 12 | 对应 `server/static/questions/{年}_{题}_analysis_{M}.svg`（M-1 不存在） | `2010/04/original-analysis-1.svg` → `2010_4_analysis_1.svg` |
| C | 9 | 对应原解析 HTML 中的 `<img>`，素材位于 `html/static/assets/exam/` | `2023/19/original-analysis-1.jpg` → `2023_19_ans.jpg` |
| D | 5 | 无任何素材，无法自动修复 | 2013#46、2020#47、2025#1（3 张） |

编号规则：Markdown 图片编号从 1 开始，服务端 SVG 编号从 0 开始，因此优先用 `M-1`，不存在时回退 `M`。

```mermaid
flowchart TD
    A[读取增强解析 Markdown] --> B[匹配 !...alt... 图片引用]
    B --> C{server SVG<br>{年}_{题}_analysis_{M-1} 存在?}
    C -- 是 --> D[改为 server/static/questions/...]
    C -- 否 --> E{server SVG<br>{年}_{题}_analysis_{M} 存在?}
    E -- 是 --> F[改为 server/static/questions/...]
    E -- 否 --> G{原解析 HTML 第 M 张图<br>存在且素材可用?}
    G -- 是 --> H[改为 html/static/assets/exam/...]
    G -- 否 --> I[保持原引用并记录待决策]
    D --> J[写入 prototype-data/enhanced-*.js]
    F --> J
    H --> J
    I --> J
    J --> K[mdToHtml 将图片语法转为 img 标签]
    K --> L[原型页按相对路径加载本地图片]
```

## 4. 实现方案

### 4.1 构建期改写：`scripts/build_prototype.py`

- 新增 Markdown 图片 URL 改写函数 `fix_md(md, year)`：用正则匹配 `![alt](/data/enhanced-analysis/assets/YYYY/NN/original-analysis-M.ext)`，按第 3 节 A→B→C→D 优先级解析目标路径，仅替换括号内的 URL，保留 alt 文本与其余 Markdown 内容。
- `build_enhanced()` 读取每个 md 后调用 `fix_md()`，再写入 `prototype-data/enhanced-{year}.js`。
- 复用现有 `fix_src()` 的替换规则处理「原解析 HTML 图片 URL → 本地 URL」，不新增第三方依赖。
- 不修改源 md 文件，因此小程序与服务端读取的数据不受影响。

### 4.2 渲染期显示：`408刷题原型.html`

- 在 `mdToHtml()` 的 `inline()` 中增加 Markdown 图片分支：`![alt](url)` → `<img src="url" alt="alt" loading="lazy">`，放在代码/粗体/斜体替换之前，并对 URL 做简单白名单校验（仅允许相对路径、`https://` 等安全协议）。
- 图片仍由现有 `.analysis img { max-width: 100%; }` 约束，不新增样式。

### 4.3 重新生成数据

- 运行 `python scripts/build_prototype.py`，重新生成 `prototype-data/enhanced-*.js`。
- 用 `git diff --stat` 核对：除 `enhanced-*.js` 外不应有其他 prototype-data 文件变化；若有，先排查原因再继续。

### 4.4 文档同步

- 更新 `docs/2026-11-26-image-defects-audit.md`：把 2023#19 从「非标准路径待决策」移到已修复，说明 68 处已在原型页修复，D 类 5 处仍待决策。

## 5. 涉及代码

| 文件 | 改动 |
|---|---|
| `scripts/build_prototype.py` | 新增 `fix_md()`；`build_enhanced()` 调用它 |
| `408刷题原型.html` | `mdToHtml()` 的 `inline()` 增加图片语法渲染 |
| `prototype-data/enhanced-2009.js` ~ `enhanced-2025.js` | 由构建脚本重新生成，68 处 URL 改写 |
| `docs/2026-11-26-image-defects-audit.md` | 同步修复状态与剩余待决策项 |

不改动：`html/data/enhanced-analysis/**/*.md`、`miniprogram/**`、`server/**`、`prototype-data/{year}.js`。

## 6. 潜在风险

1. **小程序现有映射可能有偏差**：`miniprogram/pages/question/question.js` 把 `original-analysis-N.svg` 直接映射到 `_analysis_N.svg`，未按 1→0 换算；本方案不改小程序，仅在验收说明中提示，是否单独修复由用户决定。
2. **D 类 5 处仍为破图**：无素材可用，不删除引用、不伪造图片，保持现状并登记。
3. **重新生成的副作用**：`build_prototype.py` 会重写所有 prototype-data 文件，需用 git diff 确认无额外变更；工作区已有其他未提交改动，不能整体回滚。
4. **图片语法误伤**：`inline()` 增加图片分支时，需避免把含 `![` 的普通文本或公式误转为图片；用严格正则并先于粗体/斜体替换。
5. **URL 安全**：只对白名单协议输出 `src`，避免数据里的异常 URL 注入。

## 7. 验收标准

1. 浏览器打开 `file:///F:/part/post-graduate/408-exam/408刷题原型.html#/y/2023/q/19`，查看答案与解析 → 增强解析，显示流水线阶段安排图，与「原解析」图片一致。
2. 抽查 2009#6（A 类）、2010#4（B 类）、2025#20（C 类）增强解析图片正常显示；2013#46（D 类）保持现状。
3. `prototype-data/enhanced-*.js` 中不再出现可修复的 `/data/enhanced-analysis/assets/` 引用；D 类 5 处仍保留。
4. `git diff` 仅包含本方案第 5 节列出的文件；源 md、小程序、服务端文件未被修改。
5. 刷新页面无需联网，本地图片均可加载。

## 8. 待用户确认的决策

1. 是否同意按「同类问题批量修复」处理全部 73 处引用（当前方案），而不是只改 2023#19 一处？
2. 是否同意只改原型页构建与渲染层，不改动源 Markdown、小程序和服务端？
3. D 类 5 处无素材引用是否保持原样（方案默认），还是删除引用改为纯文字？
