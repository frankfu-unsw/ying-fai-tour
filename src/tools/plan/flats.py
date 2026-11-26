import sys; sys.path.insert(0,'.')
from rects import *
import pickle, math, json
from scipy import ndimage as ndi
R=100; MARG=150
C45=math.sqrt(.5)
def frame_of(D,k,r0,r1,M):
    """0 or 45 by wall family touching the flat"""
    Fk=D['FL'][k]['mask']; ys,xs=np.nonzero(Fk)
    cnt,_=cv2.findContours(Fk.astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
    c=max(cnt,key=cv2.contourArea)[:,0,:].astype(float)
    d=np.diff(np.vstack([c,c[:1]]),axis=0)
    diag=np.sum((d[:,0]!=0)&(d[:,1]!=0)); orth=np.sum((d[:,0]==0)^(d[:,1]==0))
    return 45 if diag>orth*0.5 else 0
def img_axes(th):
    # world ex=(cos,sin), ey=(sin,-cos); image coords flip y
    t=math.radians(th); ex=(math.cos(t),math.sin(t)); ey=(math.sin(t),-math.cos(t))
    return np.array([ex[0],-ex[1]]),np.array([ey[0],-ey[1]]),ex,ey
def local_frame(D,k,th):
    Fk=D['FL'][k]['mask']; ys,xs=np.nonzero(Fk)
    exi,eyi,ex,ey=img_axes(th)
    P=np.stack([xs,ys],1).astype(float)
    u=P@exi; v=P@eyi
    u0,u1,v0,v1=u.min(),u.max()+1,v.min(),v.max()+1
    C=(u0-MARG)*exi+(v0-MARG)*eyi       # image point of local pixel (0,0)
    Wl=int(u1-u0+2*MARG); Hl=int(v1-v0+2*MARG)
    Ma=np.array([[exi[0],eyi[0],C[0]],[exi[1],eyi[1],C[1]]])   # local(u,v)->image(i,j)
    return dict(Ma=Ma,size=(Wl,Hl),th=th,exi=exi,eyi=eyi,ex=ex,ey=ey,C=C)
def warp(Mimg,LF):
    return cv2.warpAffine(Mimg.astype(np.uint8),LF['Ma'],LF['size'],flags=cv2.WARP_INVERSE_MAP|cv2.INTER_NEAREST)>0
def warp_lab(lab,LF):
    return cv2.warpAffine(lab.astype(np.float32),LF['Ma'],LF['size'],flags=cv2.WARP_INVERSE_MAP|cv2.INTER_NEAREST).astype(np.int32)
def img_of_local(LF,u,v): return LF['Ma'][:,:2]@np.array([u,v])+LF['Ma'][:,2]
def local_of_img(LF,i,j):
    A=LF['Ma'][:,:2]; return np.linalg.solve(A,np.array([i,j])-LF['Ma'][:,2])
def world_of_img(G,i,j): return (G.x0+i/R, G.y1-j/R)
def img_of_world(G,x,y): return ((x-G.x0)*R,(G.y1-y)*R)
DIRS={'Y0':(0,-1),'Y1':(0,1),'X0':(-1,0),'X1':(1,0)}
def comps(mask):
    lab,n=ndi.label(mask); sl=ndi.find_objects(lab); return lab,n,sl
def fracs(reg,Fk,Fother,corrBig,E):
    n=max(1,reg.sum())
    return dict(f=(reg&Fk).sum()/n,o=(reg&Fother).sum()/n,c=(reg&corrBig).sum()/n,e=(reg&E).sum()/n)
def side_class(reg,Fk,Fall,corrBig,E,W):
    n=reg.sum()
    if n==0: return 'none'
    f=(reg&Fk).sum()/n; o=(reg&Fall&~Fk).sum()/n; c=(reg&corrBig).sum()/n; e=(reg&E).sum()/n; w=(reg&W).sum()/n
    best=max((f,'flat'),(o,'other'),(c,'corr'),(e,'ext'),(w,'wall'))
    return best[1] if best[0]>.4 else 'mix'
def analyze_flat(D,k,rects,th):
    G=D['G']; r0,r1,M=rects
    LF=local_frame(D,k,th)
    lab=warp_lab(D['lab_all'],LF); W=warp(D['W'],LF); B=warp(D['B'],LF); L=warp(D['L'],LF)
    H,Wd=W.shape
    Fk=cv2.morphologyEx((lab==k).astype(np.uint8),cv2.MORPH_OPEN,np.ones((5,5),np.uint8))>0; Fother=(lab>0)&(lab!=k); Fall=Fother|Fk; E=~B
    free=B&~Fall&~W
    fl,fn,_=comps(free); areas=ndi.sum(free,fl,range(1,fn+1))/R/R
    corrBig=np.isin(fl,[i+1 for i,a in enumerate(areas) if a>2.5])
    # ---- door gaps: runs between wall ends in each column (gaps in vertical walls) and each row (horizontal walls)
    doors=[]; gapmask=np.zeros_like(W)
    for horiz in (True,False):
        Wt=W if not horiz else W.T     # scan columns of Wt: for horiz walls scan rows of W
        Bt=B if not horiz else B.T
        cands={}
        for u in range(Wt.shape[1]):
            col=Wt[:,u]; rr=row_runs(col)
            for (a0,a1),(b0,b1) in zip(rr,rr[1:]):
                g0,g1=a1,b0; L_=g1-g0
                if 45<=L_<=118 and Bt[g0:g1,u].all(): cands.setdefault(u,[]).append((g0,g1))
        # group consecutive columns with matching gaps
        used=set(); 
        for u in sorted(cands):
            for (g0,g1) in cands[u]:
                if (u,g0,g1) in used: continue
                us=[u]; uu=u+1
                while uu in cands:
                    m=[q for q in cands[uu] if abs(q[0]-g0)<=3 and abs(q[1]-g1)<=3 and (uu,)+q not in used]
                    if not m: break
                    used.add((uu,)+m[0]); us.append(uu); uu+=1
                used.add((u,g0,g1))
                w=len(us)
                if not (5<=w<=36): continue
                # rect in W coords
                if horiz: u0,u1,v0,v1=g0,g1,us[0],us[-1]+1
                else: u0,u1,v0,v1=us[0],us[-1]+1,g0,g1
                # sides: across the wall
                if horiz:
                    A=np.zeros_like(W); A[max(0,v0-30):v0,u0+5:u1-5]=1
                    Bb=np.zeros_like(W); Bb[v1:v1+30,u0+5:u1-5]=1
                else:
                    A=np.zeros_like(W); A[v0+5:v1-5,max(0,u0-30):u0]=1
                    Bb=np.zeros_like(W); Bb[v0+5:v1-5,u1:u1+30]=1
                fa=fracs(A>0,Fk,Fother,corrBig,E); fb=fracs(Bb>0,Fk,Fother,corrBig,E)
                ca,cb=fa,fb
                if (fa['c']>=.25 and fb['f']>=.4) or (fb['c']>=.25 and fa['f']>=.4): kind='entry'
                elif fa['f']>=.6 and fb['f']>=.6 and fa['c']<.1 and fb['c']<.1: kind='int'
                else: continue
                # merge with an adjacent gap found on the neighbouring rows/cols
                mg=[d for d in doors if d['horiz']==horiz and abs(d['u0']-u0)<=4 and abs(d['u1']-u1)<=4 and abs(d['v0']-v0)<=4 and abs(d['v1']-v1)<=4]
                if not mg and horiz: mg=[d for d in doors if d['horiz'] and abs(d['u0']-u0)<=6 and abs(d['u1']-u1)<=6 and (abs(d['v1']-v0)<=2 or abs(v1-d['v0'])<=2)]
                if not mg and not horiz: mg=[d for d in doors if not d['horiz'] and abs(d['v0']-v0)<=6 and abs(d['v1']-v1)<=6 and (abs(d['u1']-u0)<=2 or abs(u1-d['u0'])<=2)]
                if mg:
                    d=mg[0]; d['u0']=min(d['u0'],u0); d['u1']=max(d['u1'],u1); d['v0']=min(d['v0'],v0); d['v1']=max(d['v1'],v1)
                    if kind=='entry': d['kind']='entry'
                    gapmask[v0:v1,u0:u1]=1; continue
                gapmask[v0:v1,u0:u1]=1
                doors.append(dict(kind=kind,u0=u0,u1=u1,v0=v0,v1=v1,horiz=horiz,sides=(ca,cb)))
    # ---- rooms
    intg=np.zeros_like(W)
    for d in doors:
        if d['kind']=='int': intg[d['v0']:d['v1'],d['u0']:d['u1']]=1
    rl,rn,rs=comps(Fk&~cv2.dilate(intg.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool))
    rooms=[]
    # room label chars -> local px
    chars=[]
    for t,(x,y) in D['rooms']:
        i,j=img_of_world(G,x,y); u,v=local_of_img(LF,i,j)
        if 0<=u<Wd and 0<=v<H and Fk[int(v),int(u)]: chars.append((t,u,v))
    for i in range(rn):
        mk=rl==i+1; a=mk.sum()/R/R
        if a<0.4: continue
        ts=[t for t,u,v in chars if rl[int(v),int(u)]==i+1]
        typ=ts[0] if ts else None
        rooms.append(dict(mask=mk,area=a,type=typ,chars=[(t,u,v) for t,u,v in chars if rl[int(v),int(u)]==i+1]))
    # untyped rooms: biggest -> liv, small with toilet... -> guess by size
    rooms.sort(key=lambda r:-r['area'])
    for r in rooms:
        if r['type'] is None:
            r['type']='liv' if r is rooms[0] else ('bath' if r['area']<2.6 and not any(q['type']=='bath' for q in rooms) else ('kit' if not any(q['type']=='kit' for q in rooms) else 'liv'))
    roomlab=np.zeros((H,Wd),np.int16)
    for i,r in enumerate(rooms): roomlab[r['mask']]=i+1
    # ---- windows: walk the flat's boundary outward
    wins=[]
    for side,(du,dv) in DIRS.items():
        sh=np.roll(Fk,(-dv,-du),axis=(0,1))
        bnd=Fk&~sh
        vs,us=np.nonzero(bnd)
        res={}
        for u,v in zip(us,vs):
            out=None
            for t in range(1,110):
                uu=u+du*t; vv=v+dv*t
                if not (0<=uu<Wd and 0<=vv<H): break
                if W[vv,uu]: out='wall'; break
                if Fother[vv,uu]: out='other'; break
                if E[vv,uu]: out='ext'; break
            line=v if dv else u; pos=u if dv else v
            res.setdefault(line,{})[pos]=out
        for line,dd in res.items():
            ps=sorted(dd)
            run=[]
            def flush(run):
                if len(run)<30: return
                a0,a1=run[0],run[-1]+1
                # wall stubs just beyond the run ends: their across extent (absolute) is the wall line
                sgn=dv if dv else du
                acr=[]
                for e in (a0-4,a1+3):
                    cs=[]
                    for t in range(-30,60):
                        c=line+sgn*t
                        uu,vv=((e,c) if dv else (c,e))
                        if 0<=uu<Wd and 0<=vv<H and W[vv,uu]: cs.append(t)
                    if cs:
                        # the contiguous run of wall nearest the boundary line
                        cs=sorted(cs); best=None; run_=[cs[0]]
                        groups=[]
                        for t in cs[1:]:
                            if t-run_[-1]<=1: run_.append(t)
                            else: groups.append(run_); run_=[t]
                        groups.append(run_)
                        g=min(groups,key=lambda g:min(abs(g[0]),abs(g[-1])))
                        if g[-1]-g[0]>=5: acr.append((g[0],g[-1]+1))
                acr=[q for q in acr if q[1]-q[0]<=32]
                if acr: b0,b1=min(acr,key=lambda q:q[1]-q[0])
                else: b0,b1=0,20
                # room at the inner side
                uu,vv=((run[len(run)//2],line-dv*4) if dv else (line-du*4,run[len(run)//2]))
                rid=roomlab[vv,uu] if (0<=uu<Wd and 0<=vv<H) else 0
                wins.append(dict(side=side,line=line,a0=a0,a1=a1,b0=b0,b1=b1,room=int(rid)-1))
            for p in ps:
                if dd[p]=='ext' and (not run or p-run[-1]<=3): run.append(p)
                else:
                    flush(run); run=[p] if dd[p]=='ext' else []
            flush(run)
    return dict(LF=LF,W=W,Fk=Fk,Fall=Fall,B=B,L=L,lab=lab,doors=doors,rooms=rooms,roomlab=roomlab,wins=wins,gap=gapmask)
