/* 答题页：题干、选项、提交、两级提示、解析页签与翻页 */
const api = require('../../utils/api.js');

let towxmlParser = null;
function getParser() {
  if (towxmlParser) return towxmlParser;
  // 构建 npm 后由微信开发者工具生成 miniprogram_npm/towxml
  towxmlParser = require('../../miniprogram_npm/towxml/index.js');
  return towxmlParser;
}

Page({
  data: {
    year: 0, index: 0,
    q: null, enhanced: null, progress: null,
    stemNodes: null, optionNodes: [], answerNodes: null, originalNodes: null, enhancedNodes: null,
    tabs: [], activeTab: 'original', hasVisual: false, visualTip: '',
    picked: null, submitted: false, showAns: false, hintLevel: 0,
    wof: null, verdict: '',
    prevIndex: null, nextIndex: null,
    loading: true, error: ''
  },

  onLoad(query) {
    this.setData({ year: Number(query.year) || 0, index: Number(query.index) || 0 });
  },

  onShow() { this.load(); },

  load() {
    const { year, index } = this.data;
    this.setData({ loading: true, error: '' });
    api.getQuestion(year, index)
      .then(data => {
        const q = data.question || {};
        const progress = data.progress || null;
        const isChoice = q.type === 1 && (q.options || []).length > 0;
        const submitted = !!(progress && progress.choice);
        const showAns = !!(progress && progress.viewed);
        const hintLevel = progress ? (progress.hintLevel || 0) : 0;
        const parser = getParser();

        const tabs = [{ key: 'original', label: '原解析' }, { key: 'enhanced', label: '增强解析' }];
        if (data.hasVisual) tabs.push({ key: 'visual', label: '可视化解析' });

        const wofMap = (data.enhanced && data.enhanced.wof) || {};
        const picked = progress ? progress.choice : null;
        const wof = submitted && progress.correct === false && picked && wofMap[picked] ? wofMap[picked] : null;

        let verdict = '';
        if (submitted && isChoice) {
          verdict = progress.correct
            ? '✓ 回答正确 · 你的答案 ' + picked
            : '✗ 回答错误 · 你的答案 ' + picked + ' · 正确答案 ' + q.answer;
        }

        this.setData({
          q,
          enhanced: data.enhanced,
          progress,
          stemNodes: parser.parse(q.stemHtml || '', 'html'),
          optionNodes: (q.options || []).map(o => parser.parse(o.html || '', 'html')),
          answerNodes: parser.parse(q.answerHtml || '', 'html'),
          originalNodes: parser.parse(q.analysisHtml || '', 'html'),
          enhancedNodes: parser.parse((data.enhanced && data.enhanced.md) || '', 'md'),
          tabs,
          activeTab: 'original',
          hasVisual: !!data.hasVisual,
          visualTip: data.hasVisual ? '可视化解析需要网页版 iframe，小程序中暂不支持，请在网页版查看。' : '',
          picked, submitted, showAns, hintLevel, wof, verdict,
          prevIndex: data.prevIndex, nextIndex: data.nextIndex,
          loading: false
        });
        wx.setNavigationBarTitle({ title: year + ' · 第 ' + index + ' 题' });
      })
      .catch(err => this.setData({ loading: false, error: err.message }));
  },

  pickOption(e) {
    if (this.data.submitted) return;
    this.setData({ picked: e.currentTarget.dataset.label });
  },

  submitAnswer() {
    const { year, index, picked } = this.data;
    if (!picked) return;
    api.submitAnswer(year, index, picked)
      .then(() => this.load())
      .catch(err => wx.showToast({ title: err.message, icon: 'none' }));
  },

  showHint() {
    const { year, index } = this.data;
    api.setHint(year, index, 1)
      .then(() => this.load())
      .catch(err => wx.showToast({ title: err.message, icon: 'none' }));
  },

  showMoreHint() {
    const { year, index } = this.data;
    api.setHint(year, index, 2)
      .then(() => this.load())
      .catch(err => wx.showToast({ title: err.message, icon: 'none' }));
  },

  viewAnalysis() {
    const { year, index, submitted, picked } = this.data;
    api.viewAnalysis(year, index)
      .then(() => { if (!submitted) this.setData({ picked: null }); return this.load(); })
      .catch(err => wx.showToast({ title: err.message, icon: 'none' }));
  },

  switchTab(e) { this.setData({ activeTab: e.currentTarget.dataset.key }); },

  goQuestion(e) {
    const idx = e.currentTarget.dataset.index;
    if (!idx) return;
    wx.redirectTo({ url: '/pages/question/question?year=' + this.data.year + '&index=' + idx });
  }
});
