"""Generic depletion FET DC output curves; not fitted to a particular PA."""
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
vd=np.linspace(0,20,600)
fig,ax=plt.subplots(figsize=(12,7.5))
colors=['#777777','#7b1fa2','#1565c0','#ef6c00','#00897b']
for vg,color in zip([-5,-4,-3,-2,-1],colors):
 ov=max(0,vg+4.5)
 # Arbitrary knee scaling and transconductance to illustrate qualitative regions.
 knee=2*ov
 ids=.30*ov**2*np.where(vd<knee,2*vd/max(knee,.001)-(vd/max(knee,.001))**2,1)*(1+.007*vd)
 ax.plot(vd,ids,color=color,lw=3,label=f'固定 Vgs = {vg} V')
 if ov:
  ik=.30*ov**2*(1+.007*knee)
  ax.scatter([knee],[ik],s=35,color=color)
ax.axvspan(0,2,color='#ffecb3',alpha=.3)
ax.text(.8,4.2,'低 Vds 線性／歐姆區\n電流明顯隨 Vds 增加',fontproperties=font,fontsize=13,color='#9c6500')
ax.text(10,4.2,'電流飽和區：固定 Vgs 時\nIdd 對 Vds 的變化較小',fontproperties=font,fontsize=14,color='#00695c')
ax.annotate('各曲線轉折位置不同\n主要由 Vgs 決定',xy=(5,1.94),xytext=(2,3.1),fontproperties=font,fontsize=12,arrowprops={'arrowstyle':'->'})
ax.annotate('截止：Vgs 足夠負，Idd 接近零',xy=(12,0),xytext=(8,.65),fontproperties=font,fontsize=13,color='#555',arrowprops={'arrowstyle':'->','color':'#555'})
ax.set_xlim(0,20);ax.set_ylim(-.08,4.8)
ax.set_xlabel('Vds：汲極－源極電壓（V，假設刻度）',fontproperties=font,fontsize=14)
ax.set_ylabel('Idd／Id：汲極電流（A，假設刻度）',fontproperties=font,fontsize=14)
ax.set_title('電晶體輸出特性曲線族：每條曲線固定一個 Vgs',fontproperties=font,fontsize=21,pad=22)
ax.legend(prop=font,loc='center right');ax.grid(alpha=.25)
fig.text(.5,.025,'僅為耗盡型 FET 原理示意，非 PA 實測；電壓、電流與轉折點不可作為安全設定或元件規格。',ha='center',fontproperties=font,fontsize=12,color='#b42318')
fig.tight_layout(rect=[0,.065,1,1])
fig.savefig(Path(__file__).with_name('transistor_output_characteristics.png'),dpi=170)
print('Generated generic fixed-Vgs DC output characteristic family.')
