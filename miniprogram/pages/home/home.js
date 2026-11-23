/* 首页：年份列表与总体进度 */
const api = require('../../utils/api.js');
const progressUtil = require('../../utils/progress.js');

Page({
  data: {
    years: [],
    total: 0,
    done: 0,
    ok: 0,
    rate: 0,
    loading: true,
    error: ''
  },

  onShow() { this.load(); },

  load() {
    this.setData({ loading: true, error: '' });
    Promise.all([api.getYears(), api.getMyProgress()])
      .then(([yearsData, progress]) => {
        const records = progress.records || {};
        const years = (yearsData.years || []).map(y => {
          const stat = progressUtil.summarize(pickYearRecords(records, y.year));
          const bySubject = y.bySubject || {};
          const bySubjectArr = Object.keys(bySubject).map(name => ({ name, count: bySubject[name] }));
          return Object.assign({}, y, { bySubjectArr, done: stat.done, ok: stat.ok, rate: stat.rate });
        });
        const all = progressUtil.summarize(records);
        this.setData({
          years,
          total: yearsData.total || years.reduce((s, y) => s + y.count, 0),
          done: all.done, ok: all.ok, rate: all.rate,
          loading: false
        });
      })
      .catch(err => this.setData({ loading: false, error: err.message }));
  },

  goYear(e) {
    wx.navigateTo({ url: '/pages/year/year?year=' + e.currentTarget.dataset.year });
  }
});

/* 进度接口返回 { "2009-1": {...} }，按年份前缀筛选 */
function pickYearRecords(records, year) {
  const out = {};
  Object.keys(records).forEach(k => {
    if (k.indexOf(year + '-') === 0) out[k] = records[k];
  });
  return out;
}
