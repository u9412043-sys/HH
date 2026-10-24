"""Generate illustrative bias charts, not measured PA specifications."""
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
fig,axes=plt.subplots(2,2,figsize=(15,10))
for col,(name,low,ref,cap,mid,width,rfadd) in enumerate([
 ('Main',-5,-2.79,1.6,3.66566,.45,.35),
 ('Peaking',-10,-4.978,.8,4.0982,.60,.25)]):
 v=np.linspace(low,-1,500)
 q=cap/(1+np.exp(-(v+mid)/width))
 ax=axes[0,col]
 ax.plot(v,q,color='#1565c0',lw=3,label='無 RF：靜態 Iddq（示意模型）')
 ax.plot(v,q+rfadd,color='#ef6c00',lw=3,label='有 RF：平均 Idd（固定輸入條件示意）')
 ax.axvline(ref,color='#777',ls='--',lw=1)
 qr=cap/(1+np.exp(-(ref+mid)/width))
 ax.scatter([ref],[qr],color='#1565c0',s=50,zorder=5)
 ax.annotate(f'參考 Vgs = {ref} V\n電流非實測',xy=(ref,qr),xytext=(low+.2,cap*.8),fontproperties=font,
             arrowprops=dict(arrowstyle='->',color='#444'))
 ax.set_ylim(0,2.2 if col==0 else 1.25)
 ax.set_title(name+'：Vgs 與汲極電流',fontproperties=font,fontsize=17)
 ax.set_ylabel('汲極電流（A，僅模型數值）',fontproperties=font,fontsize=12)
 ax.legend(prop=font,fontsize=10,loc='lower right')
 ax=axes[1,col]
 # Arbitrary gate leakage magnitude illustration; no device calibration.
 u=(v-low)/(-1-low)
 leakage=.08+.6*(1-u)**3
 ax.plot(v,leakage,color='#00897b',lw=3)
 ax.axvline(ref,color='#777',ls='--',lw=1)
 ax.set_ylim(0,1)
 ax.set_yticks([0,.5,1],['近零','較大','更大'],fontproperties=font)
 ax.set_title(name+'：|Igs| 閘極漏電示意',fontproperties=font,fontsize=17)
 ax.set_ylabel('|Igs| 相對大小（無安培刻度）',fontproperties=font,fontsize=12)
 ax.text(.04,.88,'只示意反向漏電可能隨負偏壓增加\n不代表你的 PA 走勢、量級或安全上限',
         transform=ax.transAxes,fontproperties=font,fontsize=12,color='#00695c',va='top')
 for r in range(2):
  axes[r,col].set_xlabel('Vgs（V）：較負 → 較不負',fontproperties=font,fontsize=12)
  axes[r,col].grid(alpha=.22)
fig.suptitle('Vgs、Idd、Igs 工作曲線：教學示意，非實測',fontproperties=font,fontsize=23)
fig.text(.5,.025,'固定 Vds 與溫度條件。上圖數值為任意模型；下圖未預測 Igs。RF 曲線不是固定輸出功率的校準模型。',
         ha='center',fontproperties=font,fontsize=12,color='#b42318')
fig.tight_layout(rect=[0,.065,1,.94],h_pad=3,w_pad=3)
out=Path(__file__).with_name('vgs_idd_igs.png')
fig.savefig(out,dpi=160)
print(out)
