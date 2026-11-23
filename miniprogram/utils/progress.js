/* 进度展示辅助：把后端记录映射为页面状态，路由跳转与统计都在这里集中处理 */

function statusOf(record, isChoice) {
  if (!record) return 'todo';
  if (isChoice && record.choice) return record.correct ? 'right' : 'wrong';
  return 'viewed';
}

function summarize(records) {
  let done = 0, ok = 0;
  Object.keys(records || {}).forEach(k => {
    const r = records[k];
    if (!r) return;
    done += 1;
    if (r.correct) ok += 1;
  });
  return { done, ok, rate: done ? Math.round(ok * 100 / done) : 0 };
}

function key(year, index) { return year + '-' + index; }

module.exports = { statusOf, summarize, key };
