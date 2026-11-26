import pickle, json
FP='./'
X=pickle.load(open(FP+'export.pkl','rb'))
r2=lambda v:round(float(v),2); r3=lambda v:round(float(v),3)
out={}
for blk,B in X.items():
    fl={}
    for k,f in B['flats'].items():
        wins=[]; doors=[]
        wmeta={w['id']:w for w in f['wins']}
        for p in f['pieces']:
            if p[0]=='win':
                o=p[5]; m=wmeta[o['id']]
                wins.append([p[1],p[2],p[3],p[4],o['sill'],o['head'],o['out'],m['room'],m['dir']])
            elif p[0] in ('door','open'):
                doors.append([p[0][0],p[1],p[2],p[3],p[4],p[5]['head']])
        rooms=[[r['id'],r['type'][0],r['at'],r['rects']] for r in f['rooms']]
        e=f['entry']
        fl[str(k)]=dict(th=f['th'],O=f['O'],a=f['area'],lb=f['label'],c=f['color'][0],
            w=wins,d=doors,f=[[m[0][0]]+m[1:] for m in f['floors']],rm=rooms,lv=[l[:4]+[l[6][0]] for l in f['leaves']],
            e=[round(e['X']),round(e['Y'])] if e else None,cl=f['claimed'])
    out[blk]=dict(o=B['outline'],r=[[r3(a),r3(b),r3(c),r3(d),e,x] for a,b,c,d,e,x in B['rects']],fin=B['fins'],cw=B['cwins'],f=fl)
s=json.dumps(out,separators=(',',':'))
open(FP+'plan.json','w').write(s)
print(len(s))
