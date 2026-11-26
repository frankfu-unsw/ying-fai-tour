import sys; sys.path.insert(0,'.')
from flats import *
import wmask, json
FP='./'
ALL=pickle.load(open(FP+'flats_all.pkl','rb'))
r3=lambda v:round(float(v),3)
def snap(v): return int(round(v/5.0))*5
def compass(dx,dy):
    a=(math.degrees(math.atan2(dx,dy))+360)%360
    return ['N','NE','E','SE','S','SW','W','NW'][int((a+22.5)//45)%8], a
def block_rects(D,rects):
    G=D['G']; r0,r1,M=rects; out=[]
    for a0,a1,y0,y1 in r0:
        out.append(dict(fam=0,cx=G.x0+(a0+a1)/2/R, cy=G.y1-(y0+y1)/2/R, lx=(a1-a0)/R, ly=(y1-y0)/R, ang=0,
                        corners=[(G.x0+a/R,G.y1-b/R) for a,b in ((a0,y0),(a1,y0),(a1,y1),(a0,y1))]))
    for a0,a1,y0,y1 in r1:
        c=rot_pt(M,(a0+a1)/2,(y0+y1)/2); cs=[rot_pt(M,u,v) for u,v in ((a0,y0),(a1,y0),(a1,y1),(a0,y1))]
        out.append(dict(fam=45,cx=G.x0+c[0]/R, cy=G.y1-c[1]/R, lx=(a1-a0)/R, ly=(y1-y0)/R, ang=-45,
                        corners=[(G.x0+p[0]/R,G.y1-p[1]/R) for p in cs]))
    return out
def export_block(blk):
    D=pickle.load(open(FP+f'blk_{blk}.pkl','rb')); G=wmask.Grid(blk); D['G']=G
    rects=pickle.load(open(FP+f'rects_{blk}.pkl','rb'))
    BR=block_rects(D,rects)
    E=~D['B']; Edil=cv2.dilate(E.astype(np.uint8),np.ones((61,61),np.uint8))>0
    for r in BR:
        i,j=img_of_world(G,r['cx'],r['cy']); i,j=int(i),int(j)
        pts=np.array([img_of_world(G,*p) for p in r['corners']]).astype(np.int32)
        m=np.zeros((80,80),np.uint8)  # cheap test: any corner near exterior
        r['ext']=any(Edil[min(max(int(q[1]),0),Edil.shape[0]-1),min(max(int(q[0]),0),Edil.shape[1]-1)] for q in pts) or bool(Edil[j,i])
    flats={}
    for k in sorted(D['FL']):
        A=ALL[(blk,k)]; LF=A['LF']; th=LF['th']; ex=np.array(LF['ex']); ey=np.array(LF['ey'])
        # world of local px (u,v)
        def w_of(u,v):
            i,j=img_of_local(LF,u,v); return np.array(world_of_img(G,i,j))
        O=w_of(MARG,MARG)
        mmX=lambda u:snap((u-MARG)*10); mmY=lambda v:snap((v-MARG)*10)
        def loc(p):  # world -> local mm
            d=np.array(p)-O; return (d@ex*1000, d@ey*1000)
        Fk=A['Fk']; H,Wd=Fk.shape
        Fkd=cv2.dilate(Fk.astype(np.uint8),np.ones((9,9),np.uint8))>0
        pieces=[]; claimed=[]
        for ri,r in enumerate(BR):
            if r['fam']!=th: continue
            cs=[loc(p) for p in r['corners']]
            X0=min(c[0] for c in cs); X1=max(c[0] for c in cs); Y0=min(c[1] for c in cs); Y1=max(c[1] for c in cs)
            u0=int(MARG+X0/10); u1=int(math.ceil(MARG+X1/10)); v0=int(MARG+Y0/10); v1=int(math.ceil(MARG+Y1/10))
            uu0,uu1,vv0,vv1=max(u0,0),min(u1,Wd),max(v0,0),min(v1,H)
            if uu1<=uu0 or vv1<=vv0: continue
            if not Fkd[vv0:vv1,uu0:uu1].any(): continue
            claimed.append(ri)
            pieces.append(['wall',snap(X0),snap(X1),snap(Y0),snap(Y1),{'r':ri}])
        rooms=A['rooms']
        names={'liv':'Living & dining','kit':'Kitchen','bath':'Bathroom'}
        # room ids
        nliv=0
        for i,r in enumerate(rooms):
            if r['type']=='liv':
                r['id']='living' if nliv==0 else 'bay'; nliv+=1
            else: r['id']={'kit':'kitchen','bath':'bath'}[r['type']]
        # windows
        wins=[]; zones=[]
        for w in A['wins']:
            side=w['side']; du,dv=DIRS[side]; sgn=dv if dv else du
            c0=w['line']+sgn*w['b0']; c1=w['line']+sgn*w['b1']; c0,c1=min(c0,c1),max(c0,c1)
            if dv: u0,u1,v0,v1=w['a0'],w['a1'],c0,c1
            else: u0,u1,v0,v1=c0,c1,w['a0'],w['a1']
            L_=(w['a1']-w['a0'])*10
            rt=rooms[w['room']]['type'] if 0<=w['room']<len(rooms) else 'liv'
            rid=rooms[w['room']]['id'] if 0<=w['room']<len(rooms) else 'living'
            if rt=='bath': sill,head=1.5,2.2
            elif rt=='kit': sill,head=1.05,2.2
            else: sill,head=(.55 if L_>=1500 else .9),2.3
            wid=f'w{len(wins)+1}'
            # outward direction in world
            od=np.array([du,dv],float); wd=od[0]*ex+od[1]*ey; cname,az=compass(*wd)
            wins.append(dict(id=wid,room=rid,len=L_,out=side,dir=cname,az=round(az,1),zone=(u0,u1,v0,v1)))
            pieces.append(['win',mmX(u0),mmX(u1),mmY(v0),mmY(v1),{'sill':sill,'head':head,'id':wid,'out':side}])
            zones.append((u0,u1,v0,v1,w['room']))
        # doors
        leaves=[]; entry=None
        L=A['L']
        for d in A['doors']:
            u0,u1,v0,v1=d['u0'],d['u1'],d['v0'],d['v1']; along=(u1-u0) if d['horiz'] else (v1-v0)
            X0,X1,Y0,Y1=mmX(u0),mmX(u1),mmY(v0),mmY(v1)
            # which side is the flat (for the entrance) / swing side and hinge from the drawn arc
            if d['horiz']:
                sa=np.zeros_like(Fk); sa[max(0,v0-along):v0,u0:u1]=1; sb=np.zeros_like(Fk); sb[v1:v1+along,u0:u1]=1
            else:
                sa=np.zeros_like(Fk); sa[v0:v1,max(0,u0-along):u0]=1; sb=np.zeros_like(Fk); sb[v0:v1,u1:u1+along]=1
            if d['kind']=='entry':
                fa=(sa.astype(bool)&Fk).sum(); fb=(sb.astype(bool)&Fk).sum()
                inner=-1 if fa>fb else 1      # -1: flat on the low side
                pieces.append(['door',X0,X1,Y0,Y1,{'head':2.1}])
                if d['horiz']:
                    yy=Y0 if inner<0 else Y1; leaves.append([X0,X1,(yy-45 if inner<0 else yy),(yy if inner<0 else yy+45),0,2.1,'door'])
                    entry=dict(X=(X0+X1)/2,Y=(yy-700*1 if inner<0 else yy+700),inX=0,inY=inner)
                else:
                    xx=X0 if inner<0 else X1; leaves.append([(xx-45 if inner<0 else xx),(xx if inner<0 else xx+45),Y0,Y1,0,2.1,'door'])
                    entry=dict(X=(xx-700 if inner<0 else xx+700),Y=(Y0+Y1)/2,inX=inner,inY=0)
                continue
            if along>105:
                pieces.append(['open',X0,X1,Y0,Y1,{'head':2.3}]); continue
            pieces.append(['door',X0,X1,Y0,Y1,{'head':2.05}])
            la=(sa.astype(bool)&L).sum(); lb=(sb.astype(bool)&L).sum()
            side=-1 if la>lb else 1
            sq=sa if side<0 else sb
            if d['horiz']:
                e0=(L[:, u0:u0+7]&sq[:, u0:u0+7].astype(bool)).sum(); e1=(L[:, u1-7:u1]&sq[:, u1-7:u1].astype(bool)).sum()
                hu=u0 if e0>=e1 else u1
                Xh=mmX(hu); a=(Xh,Xh+40) if hu==u0 else (Xh-40,Xh)
                b=(Y0-along*10,Y0) if side<0 else (Y1,Y1+along*10)
                leaves.append([a[0],a[1],b[0],b[1],0,2.05,'white'])
            else:
                e0=(L[v0:v0+7,:]&sq[v0:v0+7,:].astype(bool)).sum(); e1=(L[v1-7:v1,:]&sq[v1-7:v1,:].astype(bool)).sum()
                hv=v0 if e0>=e1 else v1
                Yh=mmY(hv); a=(Yh,Yh+40) if hv==v0 else (Yh-40,Yh)
                b=(X0-along*10,X0) if side<0 else (X1,X1+along*10)
                leaves.append([b[0],b[1],a[0],a[1],0,2.05,'white'])
        # floors: one labelled mask (rooms + door gaps + window zones), each label split into rectangles
        fl=A['roomlab'].copy().astype(np.int16)
        for d in A['doors']:
            sl=(slice(d['v0'],d['v1']),slice(d['u0'],d['u1']))
            nb=A['roomlab'][max(0,d['v0']-3):d['v1']+3,max(0,d['u0']-3):d['u1']+3]; nb=nb[nb>0]
            fl[sl]=np.bincount(nb).argmax() if nb.size else 1
        for (u0,u1,v0,v1,ri) in zones: fl[v0:v1,u0:u1]=ri+1 if ri>=0 else 1
        floors=[]; roomrects={}
        for i,r in enumerate(rooms):
            mk=(fl==i+1)
            mk=cv2.morphologyEx(mk.astype(np.uint8),cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))>0
            rr=decompose2(mk,3,6)
            mat={'kit':'kit','bath':'bath'}.get(r['type'],'main')
            for a0,a1,y0,y1 in rr:
                if (a1-a0)*(y1-y0)<150: continue
                floors.append([mat,mmX(a0),mmX(a1),mmY(y0),mmY(y1)])
            rr2=[q for q in decompose2(r['mask'],3,8) if (q[1]-q[0])*(q[3]-q[2])>=2500]
            roomrects[i]=[[mmX(a0),mmX(a1),mmY(y0),mmY(y1)] for a0,a1,y0,y1 in rr2]
        rout=[]
        for i,r in enumerate(rooms):
            rs=roomrects[i]
            if not rs: continue
            if r['chars']:
                t,u,v=r['chars'][0]; at=[mmX(u),mmY(v)]
            else:
                big=max(rs,key=lambda q:(q[1]-q[0])*(q[3]-q[2])); at=[(big[0]+big[1])//2,(big[2]+big[3])//2]
            rout.append(dict(id=r['id'],type=r['type'],rects=rs,at=at,area=round(r['area'],1),wins=[w['id'] for w in wins if w['room']==r['id']]))
        lab=D['FL'][k]['label']
        flats[k]=dict(no=k,th=th,O=[r3(O[0]),r3(O[1])],area=round(float(Fk.sum())/R/R,1),label=[r3(lab[0]),r3(lab[1])],color=D['FL'][k]['color'],
                      pieces=pieces,floors=floors,rooms=rout,wins=wins,leaves=leaves,entry=entry,claimed=claimed)
    # common windows (corridor ends) from the outline walk, in world metres
    cw=[]
    for e in D['edges']:
        if e['kind']=='win' and e['flat']==0:
            p0=world_of_img(G,*e['p0']); p1=world_of_img(G,*e['p1']); cw.append([r3(p0[0]),r3(p0[1]),r3(p1[0]),r3(p1[1])])
    outline=[[r3(world_of_img(G,*p)[0]),r3(world_of_img(G,*p)[1])] for p in D['poly']]
    fins=[[[r3(world_of_img(G,*p)[0]),r3(world_of_img(G,*p)[1])] for p in poly] for poly in D['fins']]
    rects_out=[[r3(r['cx']),r3(r['cy']),r3(r['lx']),r3(r['ly']),r['ang'],1 if r['ext'] else 0] for r in BR]
    return dict(outline=outline,rects=rects_out,fins=fins,cwins=cw,flats=flats)
if __name__=='__main__':
    res={}
    for blk in 'AB':
        res[blk]=export_block(blk)
        f=res[blk]['flats']
        print(blk,'rects',len(res[blk]['rects']),'ext',sum(r[5] for r in res[blk]['rects']),'flats',len(f),'pieces',sum(len(v['pieces']) for v in f.values()))
    pickle.dump(res,open(FP+'export.pkl','wb'))
