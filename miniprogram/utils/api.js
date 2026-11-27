/* 统一请求封装：注入设备标识、解析统一返回结构。内部使用，不做登录鉴权。 */
const appInstance = () => getApp();

function request(path, method, data) {
  const app = appInstance();
  const url = app.globalData.apiBase + path;
  const deviceId = app.globalData.deviceId || require('./auth.js').ensureDeviceId();
  const header = {
    'content-type': 'application/json',
    'X-Device-Id': deviceId
  };

  return new Promise((resolve, reject) => {
    wx.request({
      url,
      method,
      data: data || {},
      header,
      timeout: 15000,
      success(res) {
        const body = res.data || {};
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

function get(path, data) { return request(path, 'GET', data); }
function post(path, data) { return request(path, 'POST', data); }

/* 业务接口：不再需要登录准备步骤 */
function getYears() { return get('/api/years'); }
function getQuestions(year) { return get('/api/years/' + year + '/questions'); }
function getQuestion(year, index) { return get('/api/questions/' + year + '/' + index); }
function getMyProgress() { return get('/api/progress'); }
function getYearProgress(year) { return get('/api/progress/' + year); }
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
