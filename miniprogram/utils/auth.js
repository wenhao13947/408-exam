/* 登录态封装：wx.login -> 后端 code2session -> 自定义 token
 * 注意：appsecret 只存在于服务端环境变量，小程序端绝不保存。 */
const TOKEN_KEY = 'p408_token_v1';
const EXPIRE_KEY = 'p408_token_v1_expire';

function restoreToken(app) {
  try {
    const token = wx.getStorageSync(TOKEN_KEY) || '';
    const expireAt = Number(wx.getStorageSync(EXPIRE_KEY) || 0);
    if (token && expireAt && Date.now() < expireAt) {
      app.globalData.token = token;
    } else {
      app.globalData.token = null;
      clearToken(app);
    }
  } catch (e) {
    app.globalData.token = null;
  }
}

function saveToken(app, token, expireAt) {
  app.globalData.token = token || null;
  try {
    wx.setStorageSync(TOKEN_KEY, token || '');
    wx.setStorageSync(EXPIRE_KEY, expireAt || 0);
  } catch (e) {
    // 存储失败时保持内存态，不影响当前会话
  }
}

function clearToken(app) {
  app.globalData.token = null;
  try {
    wx.removeStorageSync(TOKEN_KEY);
    wx.removeStorageSync(EXPIRE_KEY);
  } catch (e) {}
}

/* 供 api.js 调用：确保有 token，没有则登录一次 */
function ensureLogin(app) {
  const api = require('./api.js');
  if (app.globalData.token) return Promise.resolve(app.globalData.token);
  return new Promise((resolve, reject) => {
    wx.login({
      success(res) {
        if (!res.code) return reject(new Error('wx.login 未返回 code'));
        api.post('/api/auth/login', { code: res.code }, false)
          .then(data => {
            const token = data && data.token;
            if (!token) return reject(new Error('后端未返回 token'));
            saveToken(app, token, data.expireAt);
            resolve(token);
          })
          .catch(reject);
      },
      fail: reject
    });
  });
}

module.exports = { restoreToken, saveToken, clearToken, ensureLogin };
