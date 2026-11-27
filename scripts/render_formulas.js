/**
 * 把 formulas.json 里的 LaTeX 公式批量渲染为透明背景 PNG。
 *
 * 为什么需要浏览器截图：KaTeX 的 renderToString() 输出的是 HTML + CSS，
 * 依赖浏览器排版和字体文件才能显示。小程序 <image> 只能加载图片，
 * 所以这里用 Playwright 驱动本机 Edge，把排版结果截图为 PNG。
 *
 * 输出：
 *   server/static/formulas/<hash>.png
 *   server/static/formulas/formula-map.json
 */
const fs = require('fs');
const path = require('path');
const katex = require('katex');
const { chromium } = require('playwright-core');

const ROOT = path.resolve(__dirname, '..');
const LIST_FILE = path.join(__dirname, '.formula-build', 'formulas.json');
const OUT_DIR = path.join(ROOT, 'server', 'static', 'formulas');
const KATEX_DIR = path.join(ROOT, 'html', 'vendor', 'katex');

// 图片按 3 倍像素渲染，小程序端用 scale=48 还原（16px 基准 * 3）
const DEVICE_SCALE_FACTOR = 3;
const BASE_FONT_PX = 16;

// 常见 Windows 系统上的 Edge / Chrome 路径，按优先级尝试
const BROWSER_CANDIDATES = [
  'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
  'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
  'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe'
];

function findBrowser() {
  for (const candidate of BROWSER_CANDIDATES) {
    if (fs.existsSync(candidate)) return candidate;
  }
  throw new Error(
    '未找到 Edge 或 Chrome 浏览器。请安装 Microsoft Edge，或设置环境变量 EDGE_PATH 指向浏览器可执行文件。'
  );
}

function buildShellHtml() {
  let css = fs.readFileSync(path.join(KATEX_DIR, 'katex.min.css'), 'utf8');
  // KaTeX CSS 里的字体是相对路径 url(fonts/xxx)，改成绝对 file:// 路径，
  // 这样用 page.setContent() 时也能正确加载字体。
  const fontsUrl = 'file:///' + path.join(KATEX_DIR, 'fonts').replace(/\\/g, '/') + '/';
  css = css.replace(/url\(fonts\//g, `url(${fontsUrl}`);

  return `<!doctype html><html><head><meta charset="utf-8"><style>
html,body { margin:0; padding:0; background:transparent; }
body { font-size:${BASE_FONT_PX}px; font-family:"Microsoft YaHei","PingFang SC",sans-serif; }
#root { display:inline-block; padding:2px 3px; margin:0; }
${css}
</style></head><body><div id="root"></div></body></html>`;
}

async function main() {
  const limitArg = process.argv.indexOf('--limit');
  const limit = limitArg > -1 ? parseInt(process.argv[limitArg + 1], 10) : 0;
  const filterArg = process.argv.indexOf('--filter');
  const filter = filterArg > -1 ? process.argv[filterArg + 1] : '';

  if (!fs.existsSync(LIST_FILE)) {
    throw new Error('找不到公式清单，请先运行 python build_formula_images.py');
  }
  const payload = JSON.parse(fs.readFileSync(LIST_FILE, 'utf8'));
  let formulas = payload.formulas || [];
  if (filter) formulas = formulas.filter(x => x.tex.includes(filter));
  if (limit > 0) formulas = formulas.slice(0, limit);

  if (!fs.existsSync(OUT_DIR)) fs.mkdirSync(OUT_DIR, { recursive: true });

  const executablePath = process.env.EDGE_PATH || findBrowser();
  const browser = await chromium.launch({ executablePath, headless: true });
  const context = await browser.newContext({
    viewport: { width: 1400, height: 600 },
    deviceScaleFactor: DEVICE_SCALE_FACTOR
  });
  const page = await context.newPage();
  await page.setContent(buildShellHtml(), { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);

  const map = {};
  let ok = 0;
  let failed = 0;
  const startedAt = Date.now();

  for (let i = 0; i < formulas.length; i++) {
    const item = formulas[i];
    let html;
    try {
      html = katex.renderToString(item.tex, {
        displayMode: item.type === 'block',
        throwOnError: false,
        strict: false,
        trust: false,
        output: 'html'
      });
    } catch (e) {
      failed++;
      if (failed <= 10) console.warn(`[KaTeX 渲染失败] ${item.hash}: ${e.message}`);
      continue;
    }

    try {
      await page.evaluate((inner) => {
        document.getElementById('root').innerHTML = inner;
      }, html);

      const target = path.join(OUT_DIR, item.hash + '.png');
      const element = await page.$('#root');
      const buffer = await element.screenshot({ omitBackground: true });
      fs.writeFileSync(target, buffer);

      // 截图宽高是物理像素，除以倍率得到 CSS 像素，供服务端返回元数据
      const widthPx = Math.round(buffer.readUInt32BE(16) / DEVICE_SCALE_FACTOR);
      const heightPx = Math.round(buffer.readUInt32BE(20) / DEVICE_SCALE_FACTOR);

      map[item.hash] = {
        tex: item.tex,
        type: item.type,
        file: item.hash + '.png',
        width: widthPx,
        height: heightPx
      };
      ok++;

      if ((i + 1) % 200 === 0 || i + 1 === formulas.length) {
        const elapsed = ((Date.now() - startedAt) / 1000).toFixed(1);
        console.log(`进度 ${i + 1}/${formulas.length}，成功 ${ok}，失败 ${failed}，耗时 ${elapsed}s`);
      }
    } catch (e) {
      failed++;
      if (failed <= 10) console.warn(`[截图失败] ${item.hash}: ${e.message}`);
    }
  }

  // 过滤渲染属于验证用途，写入独立映射表，避免覆盖正式全量映射表
  const mapFile = filter
    ? path.join(__dirname, '.formula-build', 'formula-map-test.json')
    : path.join(OUT_DIR, 'formula-map.json');
  fs.writeFileSync(mapFile, JSON.stringify(map, null, 2), 'utf8');

  await browser.close();
  console.log(`完成：成功 ${ok}，失败 ${failed}，映射表 ${mapFile}`);
  if (failed > 0) process.exitCode = 1;
}

main().catch(e => {
  console.error(e);
  process.exitCode = 1;
});
