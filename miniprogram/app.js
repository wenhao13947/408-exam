/* 小程序入口：初始化全局配置与设备标识 */
const auth = require('./utils/auth.js');

App({
  globalData: {
    // API 根地址：HTTPS 域名需在小程序后台加入 request 合法域名
    apiBase: 'https://408.wenhao.vip',
    // 设备标识：每台设备独立保存答题进度，不需要登录
    deviceId: '',
    // towxml 解析器，页面按需从本地 towxml/ 目录 require
    towxmlReady: false
  },

  onLaunch() {
    // 生成本地设备 ID，已存在则直接复用
    this.globalData.deviceId = auth.ensureDeviceId();
  }
});
