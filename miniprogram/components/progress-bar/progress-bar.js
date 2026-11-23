/* 进度条组件：按 done/count 显示百分比 */
Component({
  properties: {
    done: { type: Number, value: 0 },
    count: { type: Number, value: 0 }
  },
  observers: {
    'done, count': function (done, count) {
      this.setData({ percent: count > 0 ? Math.min(100, Math.round(done * 100 / count)) : 0 });
    }
  },
  data: { percent: 0 }
});
