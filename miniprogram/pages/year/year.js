/* 年份页：题目网格与年度统计 */
const api = require('../../utils/api.js');
const progressUtil = require('../../utils/progress.js');

Page({
  data: { year: 0, questions: [], done: 0, ok: 0, rate: 0, loading: true, error: '' },

  onLoad(query) {
    this.setData({ year: Number(query.year) || 0 });
  },

  onShow() { this.load(); },

  load() {
    const year = this.data.year;
    this.setData({ loading: true, error: '' });
    Promise.all([api.getQuestions(year), api.getYearProgress(year)])
      .then(([list, prog]) => {
        const records = prog.records || {};
        const questions = (list.questions || []).map(q => {
          const r = records[progressUtil.key(year, q.index)];
          const isChoice = q.hasOptions === true || (q.type === 1 && (q.options || []).length > 0);
          return Object.assign({}, q, { status: progressUtil.statusOf(r, isChoice) });
        });
        const stat = progressUtil.summarize(records);
        this.setData({ questions, done: stat.done, ok: stat.ok, rate: stat.rate, loading: false });
        wx.setNavigationBarTitle({ title: year + ' 年 · ' + questions.length + ' 题' });
      })
      .catch(err => this.setData({ loading: false, error: err.message }));
  },

  goQuestion(e) {
    wx.navigateTo({ url: '/pages/question/question?year=' + this.data.year + '&index=' + e.currentTarget.dataset.index });
  },

  clearYear() {
    const year = this.data.year;
    wx.showModal({
      title: '清空进度',
      content: '确定清空 ' + year + ' 年的做题进度？此操作不可恢复。',
      success: res => {
        if (!res.confirm) return;
        api.clearYear(year).then(() => this.load()).catch(err => wx.showToast({ title: err.message, icon: 'none' }));
      }
    });
  }
});
