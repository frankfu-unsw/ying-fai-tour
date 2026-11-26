import sys; sys.path.insert(0,'.')
from flats import *
def viz(A,path):
    img=np.full(A['W'].shape+(3,),255,np.uint8); img[A['B']]=(225,225,225); img[A['Fall']]=(200,200,200)
    cols=[(190,230,190),(230,200,150),(150,200,240),(200,160,230),(160,160,240)]
    for i,r in enumerate(A['rooms']):
        img[r['mask']]=cols[i%5]
        ys,xs=np.nonzero(r['mask']); cv2.putText(img,r['type'],(int(xs.mean())-20,int(ys.mean())),cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,0),2)
    img[A['L']]=(150,100,100); img[A['W']]=(0,0,0)
    for d in A['doors']: cv2.rectangle(img,(d['u0'],d['v0']),(d['u1']-1,d['v1']-1),(0,0,255) if d['kind']=='entry' else (255,0,255),3)
    for w in A['wins']:
        if w['side'] in ('Y0','Y1'):
            sg=-1 if w['side']=='Y0' else 1
            cv2.rectangle(img,(w['a0'],w['line']+sg*w['b0']),(w['a1'],w['line']+sg*w['b1']),(255,120,0),3)
        else:
            sg=-1 if w['side']=='X0' else 1
            cv2.rectangle(img,(w['line']+sg*w['b0'],w['a0']),(w['line']+sg*w['b1'],w['a1']),(255,120,0),3)
    cv2.imwrite(path,img)
