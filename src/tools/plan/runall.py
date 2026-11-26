import sys; sys.path.insert(0,'.')
from viz import *
import wmask
FP='./'
out={}
for blk in 'AB':
    D=pickle.load(open(FP+f'blk_{blk}.pkl','rb')); D['G']=wmask.Grid(blk)
    rects=pickle.load(open(FP+f'rects_{blk}.pkl','rb'))
    tiles=[]
    for k in sorted(D['FL']):
        th=frame_of(D,k,*rects); A=analyze_flat(D,k,rects,th)
        p=FP+f'fl_{blk}{k}.png'; viz(A,p)
        # keep only what the export needs (the full masks of every flat would not fit in memory)
        for kk in ('W','Fall','B','lab','gap'): A.pop(kk,None)
        out[(blk,k)]=A
        im=cv2.imread(p); h,w=im.shape[:2]; s=400/max(h,w); im=cv2.resize(im,(int(w*s),int(h*s)))
        canvas=np.full((410,410,3),255,np.uint8); canvas[:im.shape[0],:im.shape[1]]=im
        cv2.putText(canvas,f'{blk}{k} th{th}',(5,25),cv2.FONT_HERSHEY_SIMPLEX,.8,(0,0,255),2)
        tiles.append(canvas)
        print(blk,k,th,'doors',''.join(d['kind'][0] for d in A['doors']),'rooms',[(r['type'],round(r['area'],1)) for r in A['rooms']],'wins',len(A['wins']))
    rows=[np.hstack(tiles[i:i+6]+[np.full((410,410,3),255,np.uint8)]*(6-len(tiles[i:i+6]))) for i in range(0,len(tiles),6)]
    cv2.imwrite(FP+f'sheet_{blk}.png',np.vstack(rows))
    del D, rects, tiles, rows; import gc; gc.collect()
pickle.dump({k:{kk:vv for kk,vv in v.items()} for k,v in out.items()},open(FP+'flats_all.pkl','wb'))
