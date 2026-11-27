/**
 * 验证：用小程序实际使用的 towxml 解析器解析增强解析 md，
 * 取出所有 <latex> 节点的 value，检查映射表中是否存在对应图片。
 *
 * 这一步很关键：提取脚本用正则，towxml 用 markdown-it，
 * 两边对公式内容的截取口径可能有差异，必须实测确认。
 */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const ROOT = path.resolve(__dirname, '..');
const toWxml = require(path.join(ROOT, 'miniprogram', 'towxml', 'index.js'));
const map = JSON.parse(fs.readFileSync(
  path.join(ROOT, 'server', 'static', 'formulas', 'formula-map.json'), 'utf8'));
const mdRoot = path.join(ROOT, 'html', 'data', 'enhanced-analysis');

function normalize(tex) {
  return tex.replace(/\r\n/g, '\n').replace(/\r/g, '\n').trim();
}
function digest(tex, kind) {
  return crypto.createHash('md5').update(normalize(tex) + '|' + kind).digest('hex');
}

function walk(node, found) {
  if (!node || typeof node !== 'object') return;
  if (node.tag === 'latex' && node.attr && node.attr.value) {
    found.push({ tex: decodeURIComponent(node.attr.value), type: node.attr.type });
  }
  if (Array.isArray(node.child)) node.child.forEach(child => walk(child, found));
}

function collectMdFiles(dir) {
  const out = [];
  for (const name of fs.readdirSync(dir)) {
    const full = path.join(dir, name);
    const stat = fs.statSync(full);
    if (stat.isDirectory()) out.push(...collectMdFiles(full));
    else if (name.toLowerCase().endsWith('.md')) out.push(full);
  }
  return out;
}

const files = collectMdFiles(mdRoot);
let totalNodes = 0;
let missing = 0;
const samples = [];

for (const file of files) {
  const src = fs.readFileSync(file, 'utf8');
  let nodes;
  try {
    nodes = toWxml(src, 'markdown');
  } catch (e) {
    console.warn(`[解析失败] ${file}: ${e.message}`);
    continue;
  }
  const found = [];
  walk(nodes, found);
  for (const item of found) {
    totalNodes++;
    if (!map[digest(item.tex, item.type)]) {
      missing++;
      if (samples.length < 10) {
        samples.push({ file: path.relative(ROOT, file), type: item.type, tex: item.tex.slice(0, 100) });
      }
    }
  }
}

console.log(`解析 md 文件 ${files.length} 份，latex 节点 ${totalNodes} 个`);
console.log(`映射表缺失 ${missing} 个`);
if (samples.length) {
  console.log('缺失样本：');
  samples.forEach(s => console.log(`  ${s.file} [${s.type}] ${JSON.stringify(s.tex)}`));
}
process.exitCode = missing > 0 ? 1 : 0;
