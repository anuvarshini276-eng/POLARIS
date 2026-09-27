"""Generate truthful charts of synthetic values as reusable education media."""
import sys,io,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
os.environ.setdefault('MPLCONFIGDIR',str(Path(__file__).resolve().parents[1]/'data'/'matplotlib-cache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sqlalchemy import select
from app.models.database import SessionLocal,Resource,uid
from app.services.storage import storage
def seed_media():
    with SessionLocal() as db:
        if db.scalar(select(Resource).where(Resource.kind=='media')):return
        for region,title,values in [('Antarctic','A synthetic year at the Antarctic coast',[-4,-6,-12,-18,-23,-27,-29,-26,-21,-15,-9,-5]),('Arctic','A synthetic Arctic seasonal cycle',[-16,-17,-15,-10,-4,2,5,4,0,-6,-11,-15])]:
            plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12})
            fig,ax=plt.subplots(figsize=(10,6),dpi=150);fig.patch.set_facecolor('#edf5f8');ax.set_facecolor('#edf5f8')
            ax.plot(range(1,13),values,color='#167e95',lw=3,marker='o',ms=6)
            ax.fill_between(range(1,13),values,-35,color='#b1dadd',alpha=.55)
            ax.set(xticks=range(1,13),xticklabels=['J','F','M','A','M','J','J','A','S','O','N','D'],ylim=(-35,10),ylabel='Illustrative temperature (°C)')
            ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',alpha=.2)
            fig.suptitle(title,x=.12,ha='left',fontsize=19,fontweight='bold',color='#14384f')
            fig.text(.12,.9,'POLARIS EDUCATION  /  SYNTHETIC DATA',fontsize=10,color='#578397')
            fig.text(.12,.03,'Invented values for demonstration. Not observed measurements or scientific evidence.',fontsize=9,color='#617e8e')
            fig.subplots_adjust(top=.82,bottom=.15,left=.12,right=.94)
            buf=io.BytesIO();fig.savefig(buf,format='png');plt.close(fig);key=uid()+'.png';storage().put(key,buf.getvalue())
            db.add(Resource(kind='media',title=title,data={'description':'Educational chart generated from explicitly synthetic monthly temperatures. Download and reuse for demonstrations only.','region':region,'mime':'image/png','storage_key':key,'status':'PUBLISHED','demo':True}))
        db.commit()
if __name__=='__main__':seed_media()
