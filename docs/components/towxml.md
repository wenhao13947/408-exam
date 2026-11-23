# towxml 接入详解（新手版）

towxml 是一个把 HTML/Markdown 转成微信小程序 WXML 节点的工具。我们用它来显示题干、选项、原解析和增强解析，因为它能处理 KaTeX 公式，而小程序自带的 `rich-text` 不能。

## 1. 为什么需要「构建 npm」

前端写的是 `require('towxml')`，但小程序不能直接读取 `node_modules`。开发者工具的「构建 npm」会把依赖转换成 `miniprogram_npm/towxml/`，小程序才能引用。

步骤：

1. 在微信开发者工具打开项目根目录。
2. 菜单「工具 → 构建 npm」。
3. 确认生成了 `miniprogram_npm/towxml/index.js` 和 `style/main.wxss`。

代码里的引用路径：

```js
// miniprogram/pages/question/question.js
const parser = require('../../miniprogram_npm/towxml/index.js');
parser.parse(markdown或html字符串, 'md' 或 'html');
```

## 2. 数据是怎样变成页面的

```mermaid
flowchart LR
    A[后端返回 stemHtml / markdown] --> B[towxml.parse]
    B --> C[节点树 nodes]
    C --> D[<towxml nodes='{{...}}' />]
    D --> E[小程序页面显示]
```

`parse` 的第二个参数很关键：

- `'html'`：题干、选项、答案、原解析本来就是 HTML。
- `'md'`：增强解析是 Markdown，里面有 `$$...$$` 公式和表格。

第三个参数可以传配置项（例如主题），本项目使用默认值。

## 3. 页面里的四处调用

`miniprogram/pages/question/question.js` 的 `load()` 中：

| 字段 | 调用 | 用途 |
|---|---|---|
| `stemNodes` | `parse(q.stemHtml, 'html')` | 题干 |
| `optionNodes` | 对每个 `option.html` 调用 `parse(..., 'html')` | 选项 |
| `answerNodes` | `parse(q.answerHtml, 'html')` | 非选择题答案 |
| `originalNodes` | `parse(q.analysisHtml, 'html')` | 原解析 |
| `enhancedNodes` | `parse(enhanced.md, 'md')` | 增强解析（表格 + KaTeX） |

这些节点在 `load()` 时一次解析完，切换解析页签只改 `activeTab`，不重复解析，避免卡顿。

## 4. 样式覆盖

`miniprogram/app.wxss` 顶部引入 towxml 基础样式：

```css
@import "./miniprogram_npm/towxml/style/main.wxss";
```

后面自定义的 `.towxml` 规则负责：

- `table` 最小宽度 720rpx，外层 `.scroll-x` 可横向滚动。
- `img / svg` 最大宽度 100%，不超出卡片。
- `.katex / .katex-display` 最大宽度 100%，长公式横向滚动。

## 5. 已知限制

1. 题干里从 draw.io 抽出的 SVG 是静态文件；少数安卓机型可能显示不完整，必要时改成 PNG。
2. 增强解析 Markdown 中如果有图片，towxml 能渲染，但迁移脚本目前只改写了题干图片路径；图片显示异常时需补充路径映射。
3. 可视化解析原本是 iframe，小程序不能直接加载，页面里降级为提示文字。
4. 若未执行「构建 npm」，`app.wxss` 里的 `@import "./miniprogram_npm/towxml/style/main.wxss"` 会找不到文件，**整个小程序编译失败**，不只是答题页。构建 npm 必须是打开项目后的第一步。
5. 若 towxml 版本升级导致 API 变化，优先检查 `parse` 的参数顺序和组件路径 `/miniprogram_npm/towxml/index`。
