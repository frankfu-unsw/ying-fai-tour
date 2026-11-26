import sys; sys.path.insert(0,'.')
from seg import *
def flats_of(blk,G,m,W,B):
    nums,rooms=labels(blk,G)
    FL={}; lab_all=np.zeros(W.shape,np.int16)
    for col in ('green','teal'):
        Fc=m[col]&~W&B
        lab,n=ndi.label(Fc)
        for nn,v in nums.items():
            for (x,y) in v:
                i,j=map(int,G.px(x,y))
                if 0<=j<G.H and 0<=i<G.W and lab[j,i]>0:
                    k=lab[j,i]; msk=lab==k
                    if msk.sum()/R/R>5 and nn not in FL:
                        FL[nn]=dict(mask=msk,label=(x,y),color=col); lab_all[msk]=nn
    return FL,lab_all,rooms
def outline(B,W):
    k=int(.5*R)
    Bo=cv2.morphologyEx(B.astype(np.uint8),cv2.MORPH_OPEN,np.ones((k,k),np.uint8))>0
    Bo=ndi.binary_fill_holes(Bo)
    lab,n=ndi.label(Bo); sz=ndi.sum(Bo,lab,range(1,n+1)); Bo=lab==(1+int(np.argmax(sz)))
    cs,_=cv2.findContours(Bo.astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
    c=max(cs,key=cv2.contourArea)[:,0,:]
    poly=cv2.approxPolyDP(c.reshape(-1,1,2),2.0,True)[:,0,:]
    return Bo,c,poly
def facade(Bo,c,poly,W,B):
    """walk the outline; return list of edges [(p0,p1,kind,depth)], kind 'wall'/'win'; coords in px"""
    H,Wd=W.shape
    # orientation of contour: make inward normal consistent. cv2 external contours are CCW in image coords? test with area sign
    P=poly.astype(float); n=len(P)
    area=0.5*np.sum(P[:,0]*np.roll(P[:,1],-1)-np.roll(P[:,0],-1)*P[:,1])
    sgn=1 if area>0 else -1
    def isW(x,y):
        i,j=int(round(x)),int(round(y))
        return 0<=j<H and 0<=i<Wd and W[j,i]
    def inB(x,y):
        i,j=int(round(x)),int(round(y))
        return 0<=j<H and 0<=i<Wd and B[j,i]
    edges=[]
    for e in range(n):
        a=P[e]; b=P[(e+1)%n]; v=b-a; L=np.hypot(*v)
        if L<1: continue
        u=v/L; nrm=np.array([-u[1],u[0]])*sgn   # inward normal (image coords)
        # check inward by sampling B
        mid=(a+b)/2
        if not inB(*(mid+nrm*15)) and inB(*(mid-nrm*15)): nrm=-nrm
        ts=np.arange(0,L+1e-9,1.0)
        wall=[]
        for t in ts:
            p=a+u*t
            hits=sum(isW(*(p+nrm*dd)) for dd in (3,5,7,9,11))
            wall.append(hits>=3)
        wall=np.array(wall)
        # close tiny gaps (<=4px) in wall and tiny wall bits (<=3px) inside windows
        def runs(arr):
            out=[]; s=0
            for i in range(1,len(arr)+1):
                if i==len(arr) or arr[i]!=arr[s]: out.append([arr[s],s,i]); s=i
            return out
        rr=runs(wall)
        for r in rr:
            if not r[0] and (r[2]-r[1])<=6: wall[r[1]:r[2]]=True
        rr=runs(wall)
        for r in rr:
            if r[0] and (r[2]-r[1])<=3 and r[1]>0 and r[2]<len(wall): wall[r[1]:r[2]]=False
        def thick(t):
            p=a+u*t; k=0
            while k<60 and isW(*(p+nrm*(k+2))): k+=1
            return k+2
        for val,s,t in runs(wall):
            p0=a+u*ts[s]; p1=a+u*ts[t-1] if t-1<len(ts) else b
            if t==len(ts): p1=b
            if s==0: p0=a
            if val or (t-s)<20:
                edges.append(dict(p0=p0,p1=p1,kind='wall',n=nrm,depth=None))
            else:
                th=[thick(ts[s]-8)] if s>0 else []
                if t<len(ts): th.append(thick(ts[t-1]+8))
                th=[x for x in th if x>5]
                dep=float(np.median(th)) if th else 20.0
                edges.append(dict(p0=p0,p1=p1,kind='win',n=nrm,depth=dep))
    return edges
