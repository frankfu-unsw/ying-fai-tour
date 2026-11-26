import sys; sys.path.insert(0,'.')
from wmask import *
import pickle
from scipy import ndimage as ndi
FP='./'
def load(blk):
    g,m=pickle.load(open(FP+f'm_{blk}.pkl','rb')); G=Grid(blk); return G,m
DUP=(802.3,-36.5)
def _isdup(items,key):
    idx={}
    for it in items: idx.setdefault(it[key],[]).append(it)
    def f(it):
        for o in idx.get(it[key],[]):
            if abs(o['x0']-(it['x0']-DUP[0]))<1.0 and abs(o['top']-(it['top']-DUP[1]))<1.0: return True
        return False
    return f
def labels(blk,G):
    pn=PAGE[blk]; T=tf(blk); pw=d[pn]['w']; ph=d[pn]['h']
    dw=_isdup(d[pn]['words'],'text'); dc=_isdup(d[pn]['chars'],'text')
    nums={}; rooms=[]
    seen=set()
    for w in d[pn]['words']:
        if not (0<=w['x0']<=pw and 0<=w['top']<=ph) or dw(w): continue
        if w['text'].isdigit() and 14<w['size']<15.5:
            cx=(w['x0']+w['x1'])/2; cy=(w['top']+w['bottom'])/2
            key=(w['text'],round(cx),round(cy))
            if key in seen: continue
            seen.add(key)
            nums.setdefault(int(w['text']),[]).append(T(cx,cy))
    for c in d[pn]['chars']:
        if not (0<=c['x0']<=pw and 0<=c['top']<=ph) or dc(c): continue
        if c['text'] in ('廚','浴','客') and 4.5<c['size']<8:
            cx=(c['x0']+c['x1'])/2; cy=(c['top']+c['bottom'])/2
            key=(c['text'],round(cx,1),round(cy,1))
            if key in seen: continue
            seen.add(key)
            rooms.append(({'廚':'kit','浴':'bath','客':'liv'}[c['text']],T(cx,cy)))
    return nums,rooms
def segment(blk):
    G,m=load(blk)
    W=m['wall']; F=(m['green']|m['teal'])&~W; L=m['line']
    free=~(W|m['green']|m['teal']|L)
    lab,n=ndi.label(free)
    border=set(np.unique(np.concatenate([lab[0],lab[-1],lab[:,0],lab[:,-1]])))-{0}
    E=np.isin(lab,list(border))
    B=~E
    # main building: component of B containing the lift lobby / most fill
    bl,bn=ndi.label(B)
    sizes=ndi.sum(F,bl,range(1,bn+1)); main=1+int(np.argmax(sizes))
    B=bl==main
    return G,m,W,F,L,E,B
