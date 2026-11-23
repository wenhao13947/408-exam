/* 统一请求封装：注入 token、解析统一返回结构、401 自动重登一次 */
const appInstance = () => getApp();

function request(path, method, data, needAuth = true, retried = false) {
  const app = appInstance();
  const url = app.globalData.apiBase + path;
  const header = { 'content-type': 'application/json' };
  if (needAuth && app.globalData.token) header.Authorization = 'Bearer ' + app.globalData.token;

  return new Promise((resolve, reject) => {
    wx.request({
      url,
      method,
      data: data || {},
      header,
      timeout: 15000,
      success(res) {
        const body = res.data || {};
        if (res.statusCode === 401 && needAuth && !retried) {
          const auth = require('./auth.js');
          auth.clearToken(app);
          auth.ensureLogin(app)
            .then(() => request(path, method, data, true, true))
            .then(resolve)
            .catch(reject);
          return;
        }
        if (res.statusCode >= 200 && res.statusCode < 300 && body.code === 0) {
          resolve(body.data);
        } else {
          reject(new Error(body.message || ('请求失败：HTTP ' + res.statusCode)));
        }
      },
      fail(err) { reject(new Error(err.errMsg || '网络请求失败')); }
    });
  });
}

function get(path, data, needAuth = true) { return request(path, 'GET', data, needAuth); }
function post(path, data, needAuth = true) { return request(path, 'POST', data, needAuth); }

/* 业务接口 */
function ensureReady() { return require('./auth.js').ensureLogin(appInstance()); }

function getYears() { return ensureReady().then(() => get('/api/years')); }
function getQuestions(year) { return ensureReady().then(() => get('/api/years/' + year + '/questions')); }
function getQuestion(year, index) { return ensureReady().then(() => get('/api/questions/' + year + '/' + index)); }
function getMyProgress() { return ensureReady().then(() => get('/api/progress')); }
function getYearProgress(year) { return ensureReady().then(() => get('/api/progress/' + year)); }
function submitAnswer(year, index, choice) { return post('/api/progress/answer', { year, index, choice }); }
function setHint(year, index, level) { return post('/api/progress/hint', { year, index, level }); }
function viewAnalysis(year, index) { return post('/api/progress/view', { year, index }); }
function clearYear(year) { return post('/api/progress/clear', { year }); }

module.exports = {
  request, get, post,
  getYears, getQuestions, getQuestion,
  getMyProgress, getYearProgress,
  submitAnswer, setHint, viewAnalysis, clearYear
};
