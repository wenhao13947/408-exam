/* 小程序入口：初始化全局配置与登录态 */
const auth = require('./utils/auth.js');

App({
  globalData: {
    // API 根地址：HTTPS 域名需在小程序后台加入 request 合法域名
    apiBase: 'https://wenhao.vip',
    // 登录态 token，由 utils/auth.js 管理，不落库明文
    token: null,
    // towxml 解析器，构建 npm 后由页面按需 require
    towxmlReady: false
  },

  onLaunch() {
    // 启动时尝试恢复本地 token；失败时由具体页面触发重新登录
    auth.restoreToken(this);
  }
});
