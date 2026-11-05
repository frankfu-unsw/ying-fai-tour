"""Build the three Ying Fai pages from the page sources and the shared runtime.

  common.js.html   the shared <script> block (window.YF: language, places, roads, buildings)
  *.src.html       each page with %%COMMON%% where the shared block goes
Writes full documents to ../ying-fai-tour/ and the artifact copies to site/artifact/
(the artifact's main page is a fragment: the host adds <html>, <head> and <body>).
"""
import os, re
HERE = os.path.dirname(os.path.abspath(__file__))
# run from the repo's src/ folder, the pages go one level up; run from a working copy beside the repo, into it
REPO = os.path.join(HERE, '..') if os.path.exists(os.path.join(HERE, '..', 'CNAME')) else os.path.join(HERE, '..', 'ying-fai-tour')
ART = os.path.join(HERE, 'site', 'artifact')
os.makedirs(ART, exist_ok=True)
common = open(os.path.join(HERE, 'common.js.html')).read()
for f in ['index.html', 'block-a.html', 'block-b.html']:
    s = open(os.path.join(HERE, f.replace('.html', '.src.html'))).read()
    assert s.count('%%COMMON%%') == 1
    doc = s.replace('%%COMMON%%', common)
    open(os.path.join(REPO, f), 'w').write(doc)
    if f == 'index.html':
        head = re.match(r'<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport"[^>]*>\n<meta name="description"[^>]*>\n', doc)
        assert head, 'unexpected document head'
        frag = doc[head.end():]
        frag = frag.replace('\n</head>\n<body>', '', 1)
        assert frag.endswith('\n</body>\n</html>\n')
        frag = frag[:-len('\n</body>\n</html>\n')]
        open(os.path.join(ART, f), 'w').write(frag)
    else:
        open(os.path.join(ART, f), 'w').write(doc)
    print(f, len(doc))
