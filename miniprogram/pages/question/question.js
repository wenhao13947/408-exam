/* 答题页：题干、选项、提交、两级提示、解析页签与翻页 */
const api = require('../../utils/api.js');

/* 把后端返回内容里的根相对图片路径补全为完整 URL。
   小程序会把 /static/... 当成包内文件而非网络图片，导致图不显示。 */
function resolveStaticImages(html) {
  if (!html) return html;
  const app = getApp();
  const base = app && app.globalData ? app.globalData.apiBase : '';
  if (!base) return html;
  // HTML 图片：同时兼容 src="/static/..." 与 src='/static/...'
  let result = html.replace(/src=(["'])\/static\//g, function (match, quote) {
    return 'src=' + quote + base + '/static/';
  });
  // 增强解析 markdown 图片：/data/enhanced-analysis/assets/YYYY/NN/original-analysis-N.svg
  // 数据里这些文件从未落地，实际对应的是服务端抽取好的原解析 SVG
  result = result.replace(/!\[([^\]]*)\]\(\/data\/enhanced-analysis\/assets\/(\d{4})\/(\d{1,2})\/original-analysis-(\d+)\.svg\)/g,
    function (match, alt, year, index, n) {
      const target = '/static/questions/' + year + '_' + parseInt(index, 10) + '_analysis_' + n + '.svg';
      return '![' + alt + '](' + base + target + ')';
    });
  return result;
}

let towxmlParser = null;
function getParser() {
  if (towxmlParser) return towxmlParser;
  // towxml 3.x 的 index.js 直接导出解析函数，包装成 parse 方法以兼容现有调用
  const toWxml = require('../../towxml/index.js');
  towxmlParser = { parse: (str, type) => toWxml(str, type) };
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
          stemNodes: parser.parse(resolveStaticImages(q.stemHtml || ''), 'html'),
          optionNodes: (q.options || []).map(o => parser.parse(resolveStaticImages(o.html || ''), 'html')),
          answerNodes: parser.parse(resolveStaticImages(q.answerHtml || ''), 'html'),
          originalNodes: parser.parse(resolveStaticImages(q.analysisHtml || ''), 'html'),
          enhancedNodes: parser.parse(resolveStaticImages((data.enhanced && data.enhanced.md) || ''), 'markdown'),
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
