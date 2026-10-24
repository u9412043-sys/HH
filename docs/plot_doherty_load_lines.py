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
 # Explicit DC resistor circuit example: VDD = Vds + Id*RD.
 # This is NOT the effective RF impedance of a Doherty combining network.
 vdd,rd=20.0,5.0
 load=(vdd-v)/rd
 ax.plot(v,load,color='#d32f2f',ls='--',lw=2.8,label='假設直流負載線：20 V、5 Ω')
 # Solve transistor/load intersection by bisection, without a grid artifact.
 lo,hi=0.0,vdd
 for _ in range(70):
  mid=(lo+hi)/2
  if float(model(ref,mid))-(vdd-mid)/rd>0:
   hi=mid
  else:
   lo=mid
 vq=(lo+hi)/2;iq=float(model(ref,vq))
 assert abs(iq-(vdd-vq)/rd)<1e-9
 ax.scatter([vq],[iq],color='#c62828',s=90,zorder=6)
 ax.annotate(f'此假設電路的交點 Q\nVgs = {ref} V\nVds ≈ {vq:.2f} V；Id ≈ {iq:.4f} A',
             xy=(vq,iq),xytext=(1.5,2.8 if ref==-2.79 else 1.2),
             fontproperties=font,fontsize=12,color='#b42318',
             arrowprops={'arrowstyle':'->','color':'#b42318'})
 ax.set_title(name,fontproperties=font,fontsize=19,pad=14)
 ax.set_xlabel('Vds（V，假設刻度）',fontproperties=font,fontsize=13)
 ax.set_ylabel('Id（A，假設刻度）',fontproperties=font,fontsize=13)
 ax.set_xlim(0,20);ax.set_ylim(-.08,4.3);ax.grid(alpha=.25)
 ax.legend(prop=font,loc='upper right')
fig.suptitle('Main／Peaking 輸出曲線＋假設直流電阻負載線',fontproperties=font,fontsize=23,y=.98)
fig.text(.5,.9,'假設每支路：VDD = 20 V、串聯 RD = 5 Ω。負載線 Id = (20 − Vds) / 5；斜率為 −1 / RD。',ha='center',fontproperties=font,fontsize=12)
fig.text(.5,.055,'紅虛線交點只適用於此直流串聯電阻示例；實際 PA 通常由扼流圈供電，不能把 RF 負載當成直流電阻。',ha='center',fontproperties=font,fontsize=14)
fig.text(.5,.015,'Doherty 的 RF 動態負載隨 Peaking 導通而變，不能用這條固定直流線代替；所有數值非實測、非安全設定。',ha='center',fontproperties=font,fontsize=12,color='#b42318')
fig.tight_layout(rect=[0,.12,1,.85])
fig.savefig(Path(__file__).with_name('doherty_load_lines.png'),dpi=160)
