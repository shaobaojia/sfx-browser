#!/usr/bin/env python3
# Multiply Sound 2 个 rar 验收：成员 CRC32 与已解压目录逐件对档（字节级）
import subprocess, os, glob, json, zlib, time

AMP = chr(38)
BASE = [x for x in glob.glob('/volume1/*/Collection/*/') if AMP in x][0].rstrip('/')
YX = BASE + '/音效/04_音乐/Multiply Sound@影采'
ORG = '/volume1/主目录/Hermes/read/Projects/sfx-browser/organize'
OUT = ORG + '/rar_audit_result.json'


def crc32_file(fp):
    crc = 0
    with open(fp, 'rb') as f:
        while True:
            b = f.read(4 * 1024 * 1024)
            if not b:
                break
            crc = zlib.crc32(b, crc)
    return crc % 0x100000000


def unrar_members(rar):
    r = subprocess.run(['unrar', 'lt', '-p-', rar], capture_output=True, text=True,
                       timeout=7200, errors='replace')
    members = []
    cur = None
    for ln in r.stdout.splitlines():
        s = ln.strip()
        if s.startswith('Name: '):
            if cur and cur.get('s') is not None:
                members.append(cur)
            cur = {'n': s[6:], 's': None, 'c': None, 'd': False}
        elif cur is not None:
            if s.startswith('Type: '):
                cur['d'] = s[6:].lower().startswith('dir')
            elif s.startswith('Size: ') and cur['s'] is None:
                try:
                    cur['s'] = int(s[6:])
                except ValueError:
                    pass
            elif (s.startswith('CRC32: ') or s.startswith('CRC: ')) and cur['c'] is None:
                cur['c'] = s.split(':', 1)[1].strip().lower()
    if cur and cur.get('s') is not None:
        members.append(cur)
    return [m for m in members if not m['d']]


def build_index(root):
    idx = {}
    n = tot = 0
    for r, dd, fs in os.walk(root):
        for f in fs:
            fp = os.path.join(r, f)
            try:
                sz = os.path.getsize(fp)
                crc = crc32_file(fp)
            except OSError:
                continue
            idx.setdefault((f, sz), []).append((os.path.relpath(fp, root), crc))
            n += 1
            tot += sz
    return idx, n, tot


tasks = [
    ('Vol3', YX + '/Multiply Sound Film Score Collection Vol.3.rar',
     YX + '/Multiply Sound Film Score Collection Vol.3'),
    ('CHPTRS', YX + '/3.CHPTRS Film Score Collection/3.CHPTRS Film Score Collection.rar',
     YX + '/3.CHPTRS Film Score Collection/3.CHPTRS Film Score Collection'),
]

report = {}
t0 = time.time()
for tag, rar, folder in tasks:
    ms = unrar_members(rar)
    print('%s: 成员 %d' % (tag, len(ms)), flush=True)
    idx, n, tot = build_index(folder)
    print('%s: 已解压 %d 件 / %.1f GiB (CRC 算完 t=%.0fs)' % (tag, n, tot / 1024**3, time.time() - t0), flush=True)
    matched = 0
    unmatched = []
    no_crc = []
    used = {}
    for m in ms:
        base = m['n'].split('/')[-1]
        if m['c'] in (None, '--------', '00000000'):
            no_crc.append(m['n'][:120])
            continue
        cand = idx.get((base, m['s']), [])
        hit = None
        for rel, crc in cand:
            if '%08x' % crc == m['c'].zfill(8):
                hit = rel
                break
        if hit:
            matched += 1
            k = (base, m['s'])
            used[k] = used.get(k, 0) + 1
        else:
            unmatched.append((m['n'], m['s'], m['c']))
    extra = []
    for k, lst in idx.items():
        c = used.get(k, 0)
        if len(lst) > c:
            for rel, crc in lst[c:]:
                extra.append(rel)
    pct = 100.0 * matched / max(1, len(ms))
    print('%s: 对齐 %d/%d (%.2f%%) | 无CRC成员 %d | 未对上 %d | 目录多出 %d'
          % (tag, matched, len(ms), pct, len(no_crc), len(unmatched), len(extra)), flush=True)
    for u in unmatched[:12]:
        print('   未对上:', u[0][:140], u[1], u[2], flush=True)
    for e in extra[:6]:
        print('   目录多出:', e[:140], flush=True)
    report[tag] = {'members': len(ms), 'extracted': n, 'matched': matched, 'pct': pct,
                   'no_crc': no_crc, 'unmatched': [list(u) for u in unmatched],
                   'extracted_only_count': len(extra), 'extracted_only_sample': extra[:50]}

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=1)
print('RAR-AUDIT-DONE %.0fs' % (time.time() - t0))
