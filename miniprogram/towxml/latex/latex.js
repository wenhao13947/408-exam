const config = require('../config');
Component({
	options: {
		styleIsolation: 'shared'
	},
	properties: {
		data: {
			type: Object,
			value: {}
		}
	},
	data: {
		attr:{
			src:'',
			class:''
		},
		size:{
			w:0,
			h:0
		},
		// 图片加载失败时改为显示 LaTeX 源码，避免出现空白
		fallback:'',
		failed:false
	},
	lifetimes:{
		attached:function(){
			const _ts = this;
			let dataAttr = this.data.data.attr;
			let tex = '';
			try {
				tex = decodeURIComponent(dataAttr.value || '');
			} catch (e) {
				tex = dataAttr.value || '';
			}

			// 设置公式图片
			_ts.setData({
				attr:{
					src:`${config.latex.api}=${dataAttr.value}&type=${dataAttr.type || 'line'}&theme=${global._theme || ''}`,
					class:`${dataAttr.class} ${dataAttr.class}--${dataAttr.type}`
				},
				fallback:tex,
				formulaScale:16 * 3
			});
		}
	},
	methods: {
		load:function(e){
			const _ts = this;

			// 公式图片按 3 倍像素生成，换算回 em 后与正文文字大小一致
			let scale = _ts.data.formulaScale || 16 * 3,
				w = e.detail.width / scale,
				h = e.detail.height /scale;

			_ts.setData({
				size:{
					w:w,
					h:h
				},
				failed:false
			});
		},

		// 图片加载失败（网络异常或公式不存在）时显示 LaTeX 源码，避免空白
		error:function(){
			this.setData({ failed:true, size:{ w:0, h:0 } });
		}
	}
})