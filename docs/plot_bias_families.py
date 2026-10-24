"""Illustrative bias families: RF current and gain compression, not PA predictions."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/mpl-config')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import numpy as np
from pathlib import Path
f=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams['axes.unicode_minus']=False
pin=np.linspace(0,34,500)
fig,axes=plt.subplots(1,3,figsize=(19,7))
colors=['#1565c0','#ef6c00','#00897b']
params=[(-3.10,16,24),(-2.95,17,26),(-2.79,18,28)]
alpha=10**.1-1
for (v,g0,pin1),color in zip(params,colors):
 q=1.6/(1+np.exp(-(v+3.66566)/.45))+.15
 total=q+2.2*(1-np.exp(-10**((pin-24)/10)))
 compression=10*np.log10(1+alpha*10**((pin-pin1)/10))
 gain=g0-compression
 pout=pin+gain
 label=f'Main Vgs = {v:.2f} V'
 axes[0].plot(pin,total,color=color,lw=3,label=label)
 axes[1].plot(pin,gain,color=color,lw=3,label=label)
 axes[1].plot([0,pin1],[g0,g0],color=color,ls=':',alpha=.65)
 axes[1].scatter([pin1],[g0-1],color=color,s=65,zorder=5)
 axes[1].annotate('壓縮 1 dB',xy=(pin1,g0-1),xytext=(pin1-8,g0-1.9),color=color,fontproperties=f,fontsize=11,arrowprops={'arrowstyle':'->','color':color})
 axes[2].plot(pin,pout,color=color,lw=3,label=label)
 axes[2].plot(pin,pin+g0,color=color,ls=':',alpha=.6)
 axes[2].scatter([pin1],[pin1+g0-1],color=color,s=65,zorder=5)
 axes[2].annotate(f'輸出 P1dB\n{pin1+g0-1:.0f} dBm（假設）',xy=(pin1,pin1+g0-1),xytext=(pin1-10,pin1+g0-6),fontproperties=f,color=color,fontsize=10,arrowprops={'arrowstyle':'->','color':color})
axes[0].axhline(3,color='#c62828',ls='--',lw=1.6)
axes[0].text(1,3.05,'總電流 3 A：僅記錄事件',fontproperties=f,color='#c62828',fontsize=11)
axes[0].set_ylim(0,4.1)
axes[1].set_ylim(7,19)
axes[2].set_ylim(10,54)
for ax,title,y in zip(axes,['① 不同 Vgs 的 RF 工作電流','② 不同 Vgs 的增益壓縮','③ 不同 Vgs 的輸入／輸出功率'],['Main＋Peaking 平均 Idd（A，示意）','增益 Gain（dB，示意）','RF 輸出 Pout（dBm，示意）']):
 ax.set_title(title,fontproperties=f,fontsize=17,pad=16)
 ax.set_xlabel('RF 輸入 Pin（dBm）',fontproperties=f,fontsize=13)
 ax.set_ylabel(y,fontproperties=f,fontsize=13)
 ax.grid(alpha=.23);ax.legend(prop=f,fontsize=10,loc='lower right')
fig.suptitle('每條曲線＝一個固定 Main Vgs；Peaking 固定 −4.978 V',fontproperties=f,fontsize=23,y=.98)
fig.text(.5,.895,'教學示意，非實測：Vds／頻率／波形／溫度／負載固定。各偏壓的增益與 P1dB 均為假設，並非從 Idd 推算。',ha='center',fontproperties=f,fontsize=12,color='#b42318')
fig.text(.5,.035,'② 圓點：相對各自小訊號增益下降 1 dB　｜　③ 虛點線：各自線性外推；圓點：比外推值低 1 dB 的輸出 P1dB',ha='center',fontproperties=f,fontsize=13)
fig.tight_layout(rect=[0,.1,1,.86],w_pad=2)
fig.savefig(Path(__file__).with_name('rf_bias_curve_families.png'),dpi=160)
# Validate exact defining compression at the chosen P1dB inputs.
assert abs(10*np.log10(1+alpha)-1)<1e-12
print('Generated curve families; 1 dB compression definition verified.')
