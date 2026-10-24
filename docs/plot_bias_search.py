"""Illustrate static bias search with the current uncalibrated simulation model."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/mpl-config')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import numpy as np
from pathlib import Path
font=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams['axes.unicode_minus']=False
m=np.linspace(-5,-1,161);p=np.linspace(-10,-1,181)
M,P=np.meshgrid(m,p)
def main(v):return 1.6/(1+np.exp(-(v+3.66566)/.45))
def peak(v):return .8/(1+np.exp(-(v+4.0982)/.6))
I=main(M)+peak(P)
fig,axes=plt.subplots(1,2,figsize=(15,7))
a=axes[0]
im=a.pcolormesh(M,P,I,shading='auto',cmap='viridis',vmin=0,vmax=2.4)
c=a.contour(M,P,I,levels=[.5,1,1.5,2],colors='white',linewidths=.8)
a.clabel(c,fmt='%.1f A',fontsize=10)
cb=fig.colorbar(im,ax=a);cb.set_label('總 Iddq（A，模擬）',fontproperties=font)
a.scatter([-2.79],[-4.978],s=180,marker='*',color='#ff5252',edgecolor='white',zorder=5)
a.annotate('目前參考偏壓\n不是最佳點',xy=(-2.79,-4.978),xytext=(-4.8,-2),fontproperties=font,fontsize=13,color='white',arrowprops={'arrowstyle':'->','color':'white'})
a.set_title('① 偏壓地圖：每個位置是一組 Vgs',fontproperties=font,fontsize=17)
a.set_xlabel('Main Vgs（V）',fontproperties=font,fontsize=13);a.set_ylabel('Peaking Vgs（V）',fontproperties=font,fontsize=13)
a=axes[1]
for fixed,color in [(-6,'#1565c0'),(-4.978,'#ef6c00'),(-4,'#00897b')]:
 a.plot(m,main(m)+peak(fixed),color=color,lw=3,label=f'Peaking 固定 {fixed} V')
a.scatter([-2.79],[main(-2.79)+peak(-4.978)],color='#d32f2f',s=90,zorder=5)
a.axvline(-2.79,color='#777',ls=':',lw=1)
a.set_title('② 地圖切片：固定 Peaking，掃描 Main',fontproperties=font,fontsize=17)
a.set_xlabel('Main Vgs（V）',fontproperties=font,fontsize=13);a.set_ylabel('總 Iddq（A，模擬）',fontproperties=font,fontsize=13)
a.legend(prop=font);a.grid(alpha=.25)
fig.suptitle('工作點搜尋：先建立靜態偏壓地圖，再進行 RF 驗證',fontproperties=font,fontsize=22)
fig.text(.5,.035,'僅為現有模型的模擬資料；低電流區不代表 RF 性能合格。尚無實測 P1dB／ACLR，不能標示最佳工作點。',ha='center',fontproperties=font,fontsize=12,color='#b42318')
fig.tight_layout(rect=[0,.09,1,.92])
fig.savefig(Path(__file__).with_name('bias_search_map.png'),dpi=170)
