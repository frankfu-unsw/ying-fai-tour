import numpy as np, cv2
def row_runs(row):
    d=np.diff(np.concatenate([[0],row.view(np.int8) if row.dtype==bool else row.astype(np.int8),[0]]))
    s=np.nonzero(d==1)[0]; e=np.nonzero(d==-1)[0]
    return list(zip(s.tolist(),e.tolist()))
def decompose(M,tol=2,minw=4):
    H,W=M.shape; active={}; out=[]
    M=M.astype(bool)
    for y in range(H+1):
        runs=row_runs(M[y]) if y<H else []
        new={}
        for x0,x1 in runs:
            m=None
            for (a0,a1) in active:
                if abs(a0-x0)<=tol and abs(a1-x1)<=tol: m=(a0,a1); break
            if m: new[m]=active.pop(m)
            else: new[(x0,x1)]=y
        for (a0,a1),y0 in active.items(): out.append([a0,a1,y0,y])
        active=new
    return [r for r in out if r[1]-r[0]>=minw and r[3]-r[2]>=minw]
def decompose2(M,tol=2,minw=5,keep=.8):
    H,W=M.shape; active=[]; out=[]
    M=M.astype(bool)
    for y in range(H+1):
        runs=row_runs(M[y]) if y<H else []
        new=[]; used=set()
        for x0,x1 in runs:
            m=None
            for idx,a in enumerate(active):
                if idx in used: continue
                if abs(a[3]-x0)<=tol and abs(a[4]-x1)<=tol:
                    c0=max(a[0],x0); c1=min(a[1],x1)
                    if c1-c0>=max(minw,keep*(a[1]-a[0])): m=idx; break
            if m is not None:
                a=active[m]; used.add(m); new.append([max(a[0],x0),min(a[1],x1),a[2],x0,x1])
            else: new.append([x0,x1,y,x0,x1])
        for idx,a in enumerate(active):
            if idx not in used: out.append([a[0],a[1],a[2],y])
        active=new
    return [r for r in out if r[1]-r[0]>=minw and r[3]-r[2]>=minw]
def cover(rects,shape):
    C=np.zeros(shape,np.uint8)
    for a0,a1,y0,y1 in rects: C[y0:y1,a0:a1]=1
    return C>0
# 45-degree canvas: rotate world image by 45deg about its centre into a larger canvas
def rot_mats(shape):
    H,W=shape; D=int(np.ceil(np.hypot(H,W)))+4
    c=np.sqrt(.5)
    # dst(u,v) -> src(i,j): src = Csrc + R*(dst - Cdst), R rotation by 45 deg
    Cs=np.array([W/2,H/2]); Cd=np.array([D/2,D/2])
    Rm=np.array([[c,-c],[c,c]])   # columns are images of u and v axes in src: u -> (c, c)?? see below
    M=np.zeros((2,3)); M[:,:2]=Rm; M[:,2]=Cs-Rm@Cd
    return M,(D,D)
def to_rot(img,M,size):
    return cv2.warpAffine(img.astype(np.uint8),M,size,flags=cv2.WARP_INVERSE_MAP|cv2.INTER_NEAREST)>0
def rot_pt(M,u,v):
    return M[:,:2]@np.array([u,v])+M[:,2]
def line_open(M,n=41):
    m=M.astype(np.uint8)
    h=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((1,n),np.uint8)); v=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((n,1),np.uint8))
    return (h|v)>0
def wall_rects(W,n=61):
    M,size=rot_mats(W.shape)
    Wr=to_rot(W,M,size); Wdr=line_open(Wr,n)
    # back to world
    Minv=cv2.invertAffineTransform(M)
    Wd=cv2.warpAffine(Wdr.astype(np.uint8),Minv,(W.shape[1],W.shape[0]),flags=cv2.WARP_INVERSE_MAP|cv2.INTER_NEAREST)>0
    Wo=line_open(W,n)&~(Wd&~line_open(W,n+40))
    r0=[r for r in decompose2(Wo,2,5) if (r[1]-r[0])*(r[3]-r[2])>=60]
    C0=cover(r0,W.shape)
    C0r=to_rot(cv2.dilate(C0.astype(np.uint8),np.ones((3,3),np.uint8)),M,size)
    r1=[r for r in decompose2(Wdr&~C0r,2,5) if (r[1]-r[0])*(r[3]-r[2])>=60]
    C1=np.zeros(W.shape,np.uint8)
    for a0,a1,y0,y1 in r1:
        pts=np.array([rot_pt(M,u,v) for u,v in ((a0,y0),(a1,y0),(a1,y1),(a0,y1))]).astype(np.int32)
        cv2.fillPoly(C1,[pts],1)
    rem=W&~C0&~(C1>0)
    rem=cv2.morphologyEx(rem.astype(np.uint8),cv2.MORPH_OPEN,np.ones((5,5),np.uint8))>0
    # leftovers: diagonal pieces first (in the rotated canvas), then orthogonal ones
    remr=to_rot(rem,M,size)
    remr=cv2.morphologyEx(remr.astype(np.uint8),cv2.MORPH_OPEN,np.ones((5,5),np.uint8))>0
    r1b=[r for r in decompose2(remr,2,6) if (r[1]-r[0])*(r[3]-r[2])>=150 and min(r[1]-r[0],r[3]-r[2])>=8]
    for a0,a1,y0,y1 in r1b:
        pts=np.array([rot_pt(M,u,v) for u,v in ((a0,y0),(a1,y0),(a1,y1),(a0,y1))]).astype(np.int32)
        cv2.fillPoly(C1,[pts],1)
    rem=W&~C0&~(C1>0)
    rem=cv2.morphologyEx(rem.astype(np.uint8),cv2.MORPH_OPEN,np.ones((5,5),np.uint8))>0
    r2=[r for r in decompose2(rem,2,5) if (r[1]-r[0])*(r[3]-r[2])>=40]
    return r0+r2,r1+r1b,M,(W&~C0&~(C1>0)&~cover(r2,W.shape))
