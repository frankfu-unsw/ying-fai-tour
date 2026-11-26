# world-aligned rasters of one block's typical floor plan
import sys; sys.path.insert(0,'.')
from masks import d, subpaths, cls, GREEN, TEAL, BLACK
import numpy as np, json, cv2
from PIL import Image, ImageDraw
REG=json.load(open('./reg.json'))
PAGE={'A':26,'B':30}
BOX={'A':(-62,14,-37,27),'B':(-68,-15,-123,-40)}
R=100
def tf(blk):
    g=REG[blk]; o,ex,ey=g['o'],g['ex'],g['ey']
    return lambda px,py:(o[0]+px*ex[0]+py*ey[0], o[1]+px*ex[1]+py*ey[1])
def inv(blk):
    g=REG[blk]; o,ex,ey=g['o'],g['ex'],g['ey']
    M=np.array([[ex[0],ey[0]],[ex[1],ey[1]]]); Mi=np.linalg.inv(M)
    return lambda x,y:tuple(Mi@np.array([x-o[0],y-o[1]]))
class Grid:
    def __init__(s,blk):
        s.blk=blk; s.x0,s.x1,s.y0,s.y1=BOX[blk]; s.W=int((s.x1-s.x0)*R); s.H=int((s.y1-s.y0)*R)
    def px(s,x,y): return ((x-s.x0)*R,(s.y1-y)*R)
    def w(s,i,j): return (s.x0+(i+.5)/R, s.y1-(j+.5)/R)
def masks(blk):
    G=Grid(blk); T=tf(blk); pn=PAGE[blk]
    ims={k:Image.new('L',(G.W,G.H),0) for k in ('wall','green','teal','line','white')}
    dr={k:ImageDraw.Draw(v) for k,v in ims.items()}
    for o in d[pn]['objs']:
        k=cls(o)
        for pts,closed in subpaths(o['path'] or []):
            q=[G.px(*T(*p)) for p in pts]
            if k in ('wall','green','teal','white') and len(q)>=3: dr[k].polygon(q,fill=255)
            elif k=='fillstroke':
                kk='green' if o['sc']==GREEN else 'teal'
                dr[kk].line(q+([q[0]] if closed else []),fill=255,width=max(1,int(round((o['lw'] or .36)*R*0.0699))))
            elif k=='line':
                dr['line'].line(q+([q[0]] if closed else []),fill=255,width=2)
    m={k:np.array(v)>127 for k,v in ims.items()}
    return G,m
