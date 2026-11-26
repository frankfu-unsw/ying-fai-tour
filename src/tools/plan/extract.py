import pdfplumber, pickle, sys
PDF='brochure.pdf'
pdf=pdfplumber.open(PDF)
out={}
for pn in (26,30):
    p=pdf.pages[pn-1]
    objs=[]
    for o in p.curves+p.lines+p.rects:
        path=o.get('path')
        objs.append(dict(t=o['object_type'],fill=o['fill'],stroke=o['stroke'],fc=o['non_stroking_color'],sc=o['stroking_color'],lw=o.get('linewidth'),pts=o.get('pts'),path=path,x0=o['x0'],x1=o['x1'],top=o['top'],bottom=o['bottom'],evenodd=o.get('evenodd')))
    words=p.extract_words(extra_attrs=['size','fontname','non_stroking_color'])
    chars=[dict(text=c['text'],x0=c['x0'],x1=c['x1'],top=c['top'],bottom=c['bottom'],size=c['size'],color=c.get('non_stroking_color')) for c in p.chars]
    out[pn]=dict(objs=objs,words=words,chars=chars,w=p.width,h=p.height)
pickle.dump(out,open(sys.argv[1],'wb'))
print('ok')
