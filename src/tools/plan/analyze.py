import sys; sys.path.insert(0,'.')
from outline import *
import pickle, math
def runs(arr):
    out=[]; s=0
    for i in range(1,len(arr)+1):
        if i==len(arr) or arr[i]!=arr[s]: out.append([bool(arr[s]),s,i]); s=i
    return out
def facade2(poly,W,B,Fall,lab_all):
    H,Wd=W.shape
    P=poly.astype(float); n=len(P)
    get=lambda M,x,y:(lambda i,j:0<=j<H and 0<=i<Wd and M[j,i])(int(round(x)),int(round(y)))
    edges=[]
    for e in range(n):
        a=P[e]; b=P[(e+1)%n]; v=b-a; L=np.hypot(*v)
        if L<1: continue
        u=v/L; nrm=np.array([-u[1],u[0]])
        mid=(a+b)/2
        sc=sum(get(B,*(mid+nrm*k)) for k in (4,8,12))-sum(get(B,*(mid-nrm*k)) for k in (4,8,12))
        if sc<0: nrm=-nrm
        ts=np.arange(0,L+1e-9,1.0)
        wall=np.array([sum(get(W,*(a+u*t+nrm*dd)) for dd in (3,5,7,9,11))>=3 for t in ts])
        for r in runs(wall):
            if not r[0] and (r[2]-r[1])<=6: wall[r[1]:r[2]]=True
        for r in runs(wall):
            if r[0] and (r[2]-r[1])<=3 and r[1]>0 and r[2]<len(wall): wall[r[1]:r[2]]=False
        for val,s,t in runs(wall):
            p0=a+u*ts[s] if s>0 else a; p1=(a+u*ts[t-1]) if t<len(ts) else b
            kind='wall'; dep=None; flat=0
            if not val and (t-s)>=20:
                # march inward at samples: distance to fill (flat) or to a free corridor pixel
                ds=[]; fl=[]; outc=[]
                for f in np.linspace(.15,.85,7):
                    p=a+u*(ts[s]+(ts[t-1]-ts[s])*f); k=0; hit=('free',80)
                    while k<80:
                        q=p+nrm*k
                        if get(Fall,*q): hit=('f',k); break
                        if get(W,*q) and k>2: hit=('w',k); break
                        if not get(B,*q) and k>5: hit=('out',k); break
                        k+=1
                    outc.append(hit[0])
                    if hit[0]=='f':
                        ds.append(hit[1]); qq=p+nrm*(hit[1]+3); fl.append(int(lab_all[int(round(qq[1])),int(round(qq[0]))]))
                maj=max(set(outc),key=outc.count)
                if maj=='f' and fl:
                    dep=float(np.median(ds)); flat=int(max(set(fl),key=fl.count))
                    kind='win' if dep<=48 else 'wall'
                elif maj=='free' and (t-s)>=60:
                    kind='win'; dep=20.0; flat=0
            edges.append(dict(p0=p0,p1=p1,kind=kind,n=nrm,depth=dep,flat=flat))
    return edges
def block(blk):
    G,m,W,F,L,E,B=segment(blk)
    FL,lab_all,rooms=flats_of(blk,G,m,W,B)
    Fall=lab_all>0
    Bo,c,poly=outline(B,W)
    ed=facade2(poly,W,B,Fall,lab_all)
    fins=W&~Bo
    lab,n=ndi.label(fins)
    near=cv2.dilate(Bo.astype(np.uint8),np.ones((9,9),np.uint8))>0
    finpolys=[]
    for k in range(1,n+1):
        mk=lab==k
        if mk.sum()<0.03*R*R or not (mk&near).any(): continue
        cs,_=cv2.findContours(mk.astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        cc=max(cs,key=cv2.contourArea); pp=cv2.approxPolyDP(cc,1.5,True)[:,0,:]
        finpolys.append(pp)
    return dict(G=G,m=m,W=W,L=L,E=E,B=B,FL=FL,lab_all=lab_all,rooms=rooms,Bo=Bo,poly=poly,edges=ed,fins=finpolys)
if __name__=='__main__':
    for blk in 'AB':
        D=block(blk); G=D['G']
        pickle.dump({k:v for k,v in D.items() if k not in ('m',)},open(f'blk_{blk}.pkl','wb'))
        ed=D['edges']; wins=[e for e in ed if e['kind']=='win']
        print(blk,'wins',len(wins),'flats',len(D['FL']),'fins',len(D['fins']),'common wins',sum(1 for e in wins if e['flat']==0))
        img=np.full((G.H,G.W,3),255,np.uint8); img[D['B']]=(225,225,225); img[D['lab_all']>0]=(190,230,190); img[D['W']]=(0,0,0)
        for e in ed:
            col=(0,150,0) if e['kind']=='wall' else ((255,60,0) if e['flat'] else (0,0,255))
            cv2.line(img,tuple(map(int,e['p0'])),tuple(map(int,e['p1'])),col,6 if e['kind']=='win' else 2)
            if e['kind']=='win':
                q=(e['p0']+e['p1'])/2+e['n']*e['depth']; cv2.line(img,tuple(map(int,(e['p0']+e['p1'])/2)),tuple(map(int,q)),(255,0,255),3)
        for p in D['fins']: cv2.polylines(img,[p.reshape(-1,1,2)],True,(0,0,255),4)
        cv2.imwrite(f'fac_{blk}.png',cv2.resize(img,(G.W//4,G.H//4),interpolation=cv2.INTER_AREA))
        cv2.imwrite(f'facz_{blk}.png',img[1800:3400,4500:7000] if blk=='A' else img[300:2200,1400:3600])
