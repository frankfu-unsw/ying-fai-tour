import sys, os; sys.path.insert(0,".")
from masks import *
import numpy as np, cv2, re, json
K=14.17323  # pt per m at 1:200 on A3
src=open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','index.src.html')).read()
def pieces(name):
    s=src[src.index('const '+name+' = ['):]
    s=s[:s.index('\n];')+3]
    rows=re.findall(r"\['(wall|win|mull|door|open)', (-?\d+), (-?\d+), (-?\d+), (-?\d+)",s)
    return [(k,int(a),int(b),int(c),int(d)) for k,a,b,c,d in rows]
FL={'A2':(0,5.3375,-1),'A3':(0,-8.3375,1),'B9':(-22.6,-73.638,-1),'B10':(-22.6,-85.462,1)}
def worldrects(fid,typ):
    ox,oy,sy=FL[fid]; out=[]
    for k,X0,X1,Y0,Y1 in pieces('PIECES_'+typ):
        if k!='wall': continue
        xa,xb=ox+(X0-8115)/1000,ox+(X1-8115)/1000; ya,yb=oy+sy*Y0/1000,oy+sy*Y1/1000
        out.append((min(xa,xb),max(xa,xb),min(ya,yb),max(ya,yb)))
    return out
PXM=60  # px per metre for registration
def raster_rects(rects,box):
    x0,x1,y0,y1=box; W=int((x1-x0)*PXM); H=int((y1-y0)*PXM); im=np.zeros((H,W),np.uint8)
    for a,b,c,d in rects:
        cv2.rectangle(im,(int((a-x0)*PXM),int((y1-d)*PXM)),(int((b-x0)*PXM)-1,int((y1-c)*PXM)-1),255,-1)
    return im
def raster_walls(pn,tf,box):
    # tf maps page pt (px,py) -> world (x,y)
    x0,x1,y0,y1=box; W=int((x1-x0)*PXM); H=int((y1-y0)*PXM); im=Image.new('L',(W,H),0); dr=ImageDraw.Draw(im)
    for o in d[pn]['objs']:
        if cls(o)!='wall': continue
        for pts,cl in subpaths(o['path'] or []):
            q=[]
            for p in pts:
                x,y=tf(*p); q.append(((x-x0)*PXM,(y1-y)*PXM))
            if len(q)>=3: dr.polygon(q,fill=255)
    return np.array(im)
if __name__=='__main__':
    res={}
    for blk,pn,fids,box,guess in (('A',26,('A2','A3'),(-12,3,-19,9),(1034.3,292.2-5.3375*K+60)),('B',30,('B9','B10'),(-35,-19,-98,-62),None)):
        ref=raster_rects(worldrects(fids[0],blk)+worldrects(fids[1],blk),box)
        if blk=='A':
            xa,ya=guess
            tf=lambda px,py:((px-xa)/K,(ya-py)/K)
        else:
            # flat 10 label near (723,915)/100dpi*0.72 ; east face of B9/10 at x=-22.6: page bottom.. guess from fill later
            xb,yb=750*0.72+0, 0
            # find flats 9/10 fills: use label positions from words
            ws=[w for w in d[pn]['words'] if w['size']>14 and w['text'] in ('9','10')]
            print([(w['text'],w['x0'],w['top']) for w in ws])
            w9=[w for w in ws if w['text']=='9'][0]; w10=[w for w in ws if w['text']=='10'][0]
            # B9 label world approx (-25,-76.5)? use midpoint of 9/10 labels ~ (-26.5,-79.55)
            mx=(w9['x0']+w10['x0'])/2+4; my=(w9['top']+w10['top'])/2+6
            yb=my-(-26.5+0)*K*0  # placeholder
            xa_,ya_=mx,my
            tf=lambda px,py:(-26.5+(py-ya_)/K, -79.55+(px-xa_)/K)
        best=None
        for it in range(2):
            img=raster_walls(pn,tf,box)
            # phase correlation via matchTemplate on padded
            pad=3*PXM
            refp=cv2.copyMakeBorder(ref,pad,pad,pad,pad,cv2.BORDER_CONSTANT,0)
            r=cv2.matchTemplate(refp.astype(np.float32),img.astype(np.float32),cv2.TM_CCORR_NORMED)
            _,mv,_,ml=cv2.minMaxLoc(r)
            dx=(ml[0]-pad)/PXM; dy=-(ml[1]-pad)/PXM
            print(blk,'iter',it,'score',round(mv,4),'shift m',dx,dy)
            f0=tf
            tf=(lambda f0,dx,dy:(lambda px,py:(f0(px,py)[0]+dx,f0(px,py)[1]+dy)))(f0,dx,dy)
        # report final params: world of page origin
        o=tf(0,0); ex=tf(1,0); ey=tf(0,1)
        res[blk]=dict(o=o,ex=(ex[0]-o[0],ex[1]-o[1]),ey=(ey[0]-o[0],ey[1]-o[1]))
        img=raster_walls(pn,tf,box)
        vis=np.zeros(ref.shape+(3,),np.uint8); vis[...,2]=ref; vis[...,1]=img
        cv2.imwrite(f'./reg_{blk}.png',vis)
    json.dump(res,open('./reg.json','w'),indent=1)
    print(res)
