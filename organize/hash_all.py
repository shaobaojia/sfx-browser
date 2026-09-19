#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""三根全量 md5：主库 + 两个邻居。按根分 CSV 落 hash3_20260919/，结束写 done.json。"""
import os, glob, hashlib, json, time

AMP = chr(38)
BASE = [x for x in glob.glob('/volume1/*/Collection/*/') if AMP in x][0].rstrip('/')
main = None
sibs = []
for name in sorted(os.listdir(BASE)):
    p = os.path.join(BASE, name)
    if not os.path.isdir(p):
        continue
    ks = os.listdir(p)
    if sum(1 for k in ks if k[:3] in ('01_', '02_', '03_', '99_')) >= 3:
        main = p
    elif '音' in name:
        sibs.append((name, p))

OUT = '/volume1/主目录/Hermes/read/Projects/sfx-browser/organize/hash3_20260919'
os.makedirs(OUT, exist_ok=True)
roots = [('main', main)] + [('sib_%d' % (i + 1), p) for i, (n, p) in enumerate(sibs)]
with open(os.path.join(OUT, 'meta.json'), 'w', encoding='utf-8') as f:
    json.dump({'roots': {k: v for k, v in roots}, 'sib_names': [n for n, _ in sibs],
               'started': time.strftime('%F %T')}, f, ensure_ascii=False, indent=1)

t_start = time.time()
CH = 1024 * 1024
for key, root in roots:
    csvp = os.path.join(OUT, key + '.tsv')
    n = 0
    byt = 0
    err = 0
    t0 = time.time()
    with open(csvp, 'w', encoding='utf-8') as out:
        for r, _, fs in os.walk(root):
            for fn in fs:
                fp = os.path.join(r, fn)
                try:
                    st = os.stat(fp)
                    h = hashlib.md5()
                    with open(fp, 'rb') as fh:
                        while True:
                            b = fh.read(CH)
                            if not b:
                                break
                            h.update(b)
                    rel = os.path.relpath(fp, root)
                    out.write('%d\t%s\t%s\n' % (st.st_size, h.hexdigest(), rel))
                    n += 1
                    byt += st.st_size
                    if n % 2000 == 0:
                        print('[%s] %d files %.1f GiB %.0fs' % (key, n, byt / 1024**3, time.time() - t0), flush=True)
                except OSError:
                    err += 1
    print('== [%s] DONE: %d files / %.1f GiB / %d errors / %.0fs' % (key, n, byt / 1024**3, err, time.time() - t0), flush=True)

with open(os.path.join(OUT, 'done.json'), 'w', encoding='utf-8') as f:
    json.dump({'finished': time.strftime('%F %T'), 'elapsed_s': round(time.time() - t_start)}, f)
print('ALLDONE', flush=True)
