/**
 * 扫描增强解析 Markdown，提取全部 LaTeX 公式，生成待渲染清单。
 *
 * 关键：必须使用与小程序完全相同的 towxml 解析器来提取，
 * 不能用正则近似。实测正则会漏掉跨行行内公式，也会与块公式的
 * 截取口径不一致，导致小程序端请求到不存在的图片而继续空白。
 *
 * 输出：scripts/.formula-build/formulas.json
 * 每个条目：{"hash": md5, "tex": 公式源码, "type": "line"|"block"}
 *
 * hash 口径：md5( normalize(tex) + "|" + type )
 * normalize：CRLF/CR 统一成 LF，并去掉首尾空白。
 */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const ROOT = path.resolve(__dirname, '..');
const MD_ROOT = path.join(ROOT, 'html', 'data', 'enhanced-analysis');
const OUT_DIR = path.join(__dirname, '.formula-build');
const OUT_FILE = path.join(OUT_DIR, 'formulas.json');
const toWxml = require(path.join(ROOT, 'miniprogram', 'towxml', 'index.js'));

function normalize(tex) {
  return tex.replace(/\r\n/g, '\n').replace(/\r/g, '\n').trim();
}
function makeHash(tex, kind) {
  return crypto.createHash('md5').update(normalize(tex) + '|' + kind).digest('hex');
}

function walk(node, found) {
  if (!node || typeof node !== 'object') return;
  if (node.tag === 'latex' && node.attr && node.attr.value !== undefined) {
    let tex = '';
    try {
      tex = decodeURIComponent(node.attr.value);
    } catch (e) {
      tex = node.attr.value;
    }
    found.push({ tex, type: node.attr.type || 'line' });
  }
  if (Array.isArray(node.child)) node.child.forEach(child => walk(child, found));
}

function collectMdFiles(dir) {
  const out = [];
  for (const name of fs.readdirSync(dir)) {
    const full = path.join(dir, name);
    if (fs.statSync(full).isDirectory()) out.push(...collectMdFiles(full));
    else if (name.toLowerCase().endsWith('.md')) out.push(full);
  }
  return out;
}

function main() {
  if (!fs.existsSync(MD_ROOT)) throw new Error('找不到增强解析目录：' + MD_ROOT);
  const files = collectMdFiles(MD_ROOT);
  const unique = {};
  let fileCount = 0;
  let total = 0;

  for (const file of files) {
    const src = fs.readFileSync(file, 'utf8');
    let nodes;
    try {
      nodes = toWxml(src, 'markdown');
    } catch (e) {
      console.warn(`[解析失败] ${path.relative(ROOT, file)}: ${e.message}`);
      continue;
    }
    const found = [];
    walk(nodes, found);
    if (!found.length) continue;
    fileCount++;
    total += found.length;
    for (const item of found) {
      const norm = normalize(item.tex);
      if (!norm) continue;
      const digest = makeHash(item.tex, item.type);
      if (!unique[digest]) {
        unique[digest] = { hash: digest, tex: norm, type: item.type };
      }
    }
  }

  if (!fs.existsSync(OUT_DIR)) fs.mkdirSync(OUT_DIR, { recursive: true });
  const payload = {
    summary: {
      mdFilesTotal: files.length,
      mdFilesWithFormulas: fileCount,
      rawFormulaCount: total,
      uniqueFormulaCount: Object.keys(unique).length
    },
    formulas: Object.keys(unique).sort().map(k => unique[k])
  };
  fs.writeFileSync(OUT_FILE, JSON.stringify(payload, null, 2), 'utf8');

  console.log(`扫描完成：${files.length} 个 md 文件，${fileCount} 个含公式，` +
    `原始节点 ${total} 个，去重后 ${Object.keys(unique).length} 个`);
  console.log('清单已写入：' + OUT_FILE);
}

main();
