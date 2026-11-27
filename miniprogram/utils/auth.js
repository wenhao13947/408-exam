/* 设备标识管理：内部使用，不做登录鉴权。
 * 每台设备首次打开时生成一个随机 ID 并持久化，后续请求用它区分进度。 */
const DEVICE_KEY = 'p408_device_id_v1';

function ensureDeviceId() {
  try {
    const saved = wx.getStorageSync(DEVICE_KEY);
    if (saved) return saved;
  } catch (e) {
    // 存储不可用时退回内存态，当前会话仍可用
  }
  // 时间戳 + 随机串，保证同一时刻多台设备不冲突
  const id = 'dev-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 10);
  try {
    wx.setStorageSync(DEVICE_KEY, id);
  } catch (e) {}
  return id;
}

module.exports = { ensureDeviceId };
