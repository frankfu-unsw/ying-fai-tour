import pickle, numpy as np
from PIL import Image, ImageDraw
d=pickle.load(open('./vec.pkl','rb'))
def subpaths(path):
    subs=[]; cur=None
    for cmd in path:
        if cmd[0]=='m':
            if cur and len(cur)>1: subs.append((cur,False))
            cur=[cmd[1]]
        elif cmd[0]=='l': cur.append(cmd[1])
        elif cmd[0]=='c':
            p0=cur[-1]; p1,p2,p3=cmd[1],cmd[2],cmd[3]
            for i in range(1,9):
                t=i/8; a=(1-t)**3; b=3*(1-t)**2*t; c=3*(1-t)*t*t; e=t**3
                cur.append((a*p0[0]+b*p1[0]+c*p2[0]+e*p3[0], a*p0[1]+b*p1[1]+c*p2[1]+e*p3[1]))
        elif cmd[0]=='h':
            if cur and len(cur)>1: subs.append((cur,True))
            cur=[cur[0]] if cur else None
    if cur and len(cur)>1: subs.append((cur,False))
    return subs
BLACK=(0.0,0.0,0.0); GREEN=(0.851,0.928,0.854); TEAL=(0.557,0.826,0.814); RED=(0.937,0.248,0.273)
def cls(o):
    if o['fill'] and o['fc']==BLACK: return 'wall'
    if o['fill'] and o['fc']==GREEN: return 'green'
    if o['fill'] and o['fc']==TEAL: return 'teal'
    if o['fill'] and o['fc']==(1.0,1.0,1.0): return 'white'
    if o['stroke'] and o['sc']==BLACK: return 'line'
    if o['stroke'] and o['sc']==RED: return 'red'
    if o['stroke'] and o['sc'] in (GREEN,TEAL): return 'fillstroke'
    return 'other'
def render(pn, S, box, kinds, lw=1):
    x0,y0,x1,y1=box
    W=int((x1-x0)*S); H=int((y1-y0)*S)
    ims={k:Image.new('L',(W,H),0) for k in kinds}
    drs={k:ImageDraw.Draw(im) for k,im in ims.items()}
    for o in d[pn]['objs']:
        k=cls(o)
        if k=='fillstroke': k2=('green' if o['sc']==GREEN else 'teal')
        else: k2=k
        if k2 not in ims: continue
        for pts,closed in subpaths(o['path'] or []):
            q=[((x-x0)*S,(y-y0)*S) for x,y in pts]
            if k in ('wall','green','teal','white') and len(q)>=3:
                drs[k2].polygon(q,fill=255)
            elif k=='fillstroke':
                drs[k2].line(q+([q[0]] if closed else []),fill=255,width=max(1,int(round((o['lw'] or 0)*S))))
            else:
                drs[k2].line(q+([q[0]] if closed else []),fill=255,width=lw)
    return {k:np.array(im)>127 for k,im in ims.items()}
