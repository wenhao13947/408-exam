/**
 * 清理不再被 formula-map.json 引用的旧 PNG（例如换用新提取口径后遗留的文件）。
 * 只删除映射表中没有引用的文件，避免误删当前有效图片。
 */
const fs = require('fs');
const path = require('path');

const DIR = path.resolve(__dirname, '..', 'server', 'static', 'formulas');
const map = JSON.parse(fs.readFileSync(path.join(DIR, 'formula-map.json'), 'utf8'));
const keep = new Set(Object.keys(map).map(h => h + '.png'));

let removed = 0;
for (const name of fs.readdirSync(DIR)) {
  if (!name.endsWith('.png')) continue;
  if (keep.has(name)) continue;
  fs.unlinkSync(path.join(DIR, name));
  removed++;
}
console.log(`清理旧图片 ${removed} 个，保留 ${keep.size} 个`);
