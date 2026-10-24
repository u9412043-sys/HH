"""Illustrate identical-device Main/Peaking output curves with different bias."""
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
v=np.linspace(0,20,600)
def model(g,vd):
 ov=max(0,g+5)
 knee=2*ov
 z=np.minimum(np.asarray(vd)/max(knee,1e-9),1)
 return .35*ov**2*(2*z-z*z)*(1+.005*np.asarray(vd))
fig,axes=plt.subplots(1,2,figsize=(16,7.7))
colors=['#777','#7b1fa2','#1565c0','#ef6c00','#00897b']
for ax,name,ref in zip(axes,['Main：常見 Class AB 偏壓','Peaking：常見 Class C 偏壓'],[-2.79,-4.978]):
 for g,c in zip([-5.5,-4.978,-4,-2.79,-2],colors):
  ax.plot(v,model(g,v),color=c,lw=3 if g==ref else 1.8,alpha=1 if g==ref else .65,label=f'固定 Vgs = {g} V')
 ax.axvline(10,color='#555',ls='--',lw=1)
 iq=float(model(ref,10))
 ax.scatter([10],[iq],color='#c62828',s=90,zorder=6)
 ax.annotate(f'無 RF 偏壓點 Q\nVgs = {ref} V\nIddq 為示意值',xy=(10,iq),xytext=(4,2.8 if ref==-2.79 else 1.2),fontproperties=font,fontsize=13,color='#b42318',arrowprops={'arrowstyle':'->','color':'#b42318'})
 ax.set_title(name,fontproperties=font,fontsize=19,pad=14)
 ax.set_xlabel('Vds（V，假設刻度）',fontproperties=font,fontsize=13)
 ax.set_ylabel('Id（A，假設刻度）',fontproperties=font,fontsize=13)
 ax.set_xlim(0,20);ax.set_ylim(-.08,3.8);ax.grid(alpha=.25)
 ax.legend(prop=font,loc='upper right')
fig.suptitle('Doherty Main／Peaking 的電晶體輸出曲線族',fontproperties=font,fontsize=23,y=.98)
fig.text(.5,.9,'示例假設兩支路使用相同電晶體：曲線族相同，選用的靜態偏壓點不同。Vds = 10 V 僅為標示用假設。',ha='center',fontproperties=font,fontsize=12)
fig.text(.5,.055,'Main：無 RF 時已有 Iddq；Peaking：無 RF 時接近截止，RF 閘極擺幅足夠時才導通。',ha='center',fontproperties=font,fontsize=14)
fig.text(.5,.015,'非實測、非元件規格。不能僅憑 −2.79 V／−4.978 V 判定你的 PA 電流或導通類別；RF 下 Vds 也會擺動。',ha='center',fontproperties=font,fontsize=12,color='#b42318')
fig.tight_layout(rect=[0,.12,1,.85])
fig.savefig(Path(__file__).with_name('doherty_main_peaking_output.png'),dpi=160)
