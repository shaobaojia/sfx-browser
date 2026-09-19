#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sfx-browser 冒烟测试（在 NAS 上运行: ssh nas python3 - < smoke_test.py）"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = 'http://127.0.0.1:8093'


def get(path, headers=None):
    req = urllib.request.Request(BASE + path, headers=headers or {})
    r = urllib.request.urlopen(req, timeout=60)
    return r.status, dict(r.headers), r.read()


def search(q):
    s, h, b = get('/api/search?q=' + urllib.parse.quote(q))
    return json.loads(b)


fails = []


def check(name, cond, info=''):
    print(('PASS ' if cond else 'FAIL ') + name + (' | ' + info if info else ''), flush=True)
    if not cond:
        fails.append(name)


fid = None
try:
    s, h, b = get('/api/stats')
    st = json.loads(b)
    check('stats', s == 200 and st['files'] > 100000,
          'files=%d bytes=%.1fGB mtime=%s' % (st['files'], st['bytes'] / 1e9, st['db_mtime']))
except Exception as e:
    check('stats', False, repr(e))

try:
    r = search('耳鸣')
    names = [x['name'] for x in r['results']]
    check('search 耳鸣(CN->EN桥)', r['total'] >= 3, 'total=%d first=%s' % (r['total'], names[:5]))
    check('result fields', all(k in r['results'][0] for k in ('id', 'rel', 'mtime', 'size')) if r['results'] else False)
    if r['results']:
        fid = r['results'][0]['id']
except Exception as e:
    check('search 耳鸣', False, repr(e))

try:
    r = search('tinnitus')
    check('search tinnitus', r['total'] >= 1, 'total=%d' % r['total'])
    r = search('wind')
    check('search wind', r['total'] >= 100, 'total=%d' % r['total'])
    r = search('金属 撞击(AND+扩展)')
    check('search 金属 撞击', r['total'] >= 1, 'total=%d' % r['total'])
    r = search('door slam')
    check('search door slam', r['total'] >= 1, 'total=%d' % r['total'])
except Exception as e:
    check('search set', False, repr(e))

try:
    def getj(path):
        s, h, b = get(path)
        return json.loads(b)

    r = getj('/api/dirs')
    tops = [k['name'] for k in r['kids']]
    check('dirs 顶层', '01_商业音效包' in tops and len(tops) >= 4, 'tops=%s' % tops)
    r = getj('/api/dirs?under=' + urllib.parse.quote('01_商业音效包'))
    ld = [k for k in r['kids'] if k['name'] == 'Lens Distortions']
    check('dirs 二级目录', len(r['kids']) >= 20 and bool(ld), 'kids=%d' % len(r['kids']))
    if ld:
        check('dirs LD 计数', ld[0]['n'] >= 2000 and ld[0]['s'] > 1e10,
              'n=%d s=%.1fG' % (ld[0]['n'], ld[0]['s'] / 1e9))
    d = urllib.parse.quote('01_商业音效包/Lens Distortions')
    r = getj('/api/search?dir=' + d + '&limit=300')
    check('browse 浏览模式', r['total'] >= 2000 and r['shown'] == 300,
          'total=%d shown=%d' % (r['total'], r['shown']))
    ids1 = set(x['id'] for x in r['results'])
    r2 = getj('/api/search?dir=' + d + '&limit=300&offset=300')
    ids2 = set(x['id'] for x in r2['results'])
    check('browse 分页无重叠', r2['total'] == r['total'] and len(r2['results']) == 300 and not (ids1 & ids2),
          'page2=%d' % len(r2['results']))
    r3 = getj('/api/search?dir=' + d + '&limit=50&sort=size')
    sizes = [x['size'] for x in r3['results']]
    check('browse 大小排序', sizes == sorted(sizes, reverse=True), 'top=%.1fM' % (sizes[0] / 1e6))
    r4 = getj('/api/search?q=dark&dir=' + d + '&limit=50')
    inside = all(x['rel'].startswith('01_商业音效包/Lens Distortions/') for x in r4['results'])
    check('目录内搜索', r4['total'] >= 1 and inside, 'total=%d' % r4['total'])
    r5 = getj('/api/search?dir=' + d + '&limit=10&sort=rand')
    check('browse 随机排序', len(r5['results']) == 10, 'n=%d' % len(r5['results']))
except Exception as e:
    check('dirs/browse', False, repr(e))

if fid:
    try:
        s, h, b = get('/api/wave?id=%d' % fid)
        check('wave png', b[:8] == b'\x89PNG\r\n\x1a\n', '%d bytes' % len(b))
    except Exception as e:
        check('wave', False, repr(e))
    try:
        s, h, b = get('/api/audio?id=%d' % fid)
        check('audio 200', s == 200 and len(b) > 1000, '%d bytes ct=%s' % (len(b), h.get('Content-Type')))
        s, h, b = get('/api/audio?id=%d' % fid, headers={'Range': 'bytes=100-199'})
        check('audio 206 range', s == 206 and len(b) == 100 and 'Content-Range' in h,
              'status=%s %s' % (s, h.get('Content-Range')))
    except Exception as e:
        check('audio', False, repr(e))

try:
    r = search('aiff')
    if r['results']:
        aid = r['results'][0]['id']
        t0 = time.time()
        s, h, b = get('/api/audio?id=%d' % aid)
        dt = time.time() - t0
        check('aiff 转码', s == 200 and b[:4] == b'RIFF',
              '%d bytes in %.1fs ct=%s' % (len(b), dt, h.get('Content-Type')))
        t0 = time.time()
        s, h, b = get('/api/audio?id=%d' % aid)
        dt = time.time() - t0
        check('aiff 缓存命中', b[:4] == b'RIFF' and dt < 0.6, '%.2fs' % dt)
    else:
        print('SKIP aiff（库里未找到 aiff 文件）')
except Exception as e:
    check('aiff', False, repr(e))

try:
    import io as _io
    import zipfile as _zfl
    r = search('耳鸣')
    top = r['results'][:2]
    ids = ','.join(str(x['id']) for x in top)
    s, h, b = get('/api/zip?ids=' + ids)
    ok = s == 200 and b[:2] == b'PK'
    names = []
    if ok:
        with _zfl.ZipFile(_io.BytesIO(b)) as z:
            names = z.namelist()
    check('basket zip 平铺', ok and len(names) == len(top)
          and all(('/' not in n and '\\' not in n) for n in names),
          'names=%s' % names)
except Exception as e:
    check('zip', False, repr(e))

try:
    import shutil as _sh
    test_dest = '/volume1/主目录/Hermes/read/Projects/sfx-browser/_smoke_export'
    _sh.rmtree(test_dest, ignore_errors=True)
    r = search('耳鸣')
    ids = [x['id'] for x in r['results'][:2]]

    def post_export(dest):
        req = urllib.request.Request(
            BASE + '/api/export',
            data=json.dumps({'ids': ids, 'dest': dest}).encode('utf-8'),
            headers={'Content-Type': 'application/json'}, method='POST')
        return json.loads(urllib.request.urlopen(req, timeout=60).read())

    j = post_export(test_dest)
    n_files = len(os.listdir(test_dest)) if os.path.isdir(test_dest) else 0
    check('export 导出到文件夹', j.get('copied') == 2 and n_files == 2,
          'copied=%s files=%d' % (j.get('copied'), n_files))
    j2 = post_export(test_dest)
    n_files2 = len(os.listdir(test_dest)) if os.path.isdir(test_dest) else 0
    check('export 重名加后缀', j2.get('copied') == 2 and j2.get('renamed', 0) >= 1 and n_files2 == 4,
          'renamed=%s files=%d' % (j2.get('renamed'), n_files2))
    try:
        post_export('/etc/should_be_blocked')
        check('export 拒绝库外目标', False, 'no error raised')
    except urllib.error.HTTPError as he:
        check('export 拒绝库外目标', he.code == 400, 'status=%s' % he.code)
    try:
        post_export('/volume1/主目录/Collection/素材&模板&音库/音效/_blocked')
        check('export 拒绝库内目标', False, 'no error raised')
    except urllib.error.HTTPError as he:
        check('export 拒绝库内目标', he.code == 400, 'status=%s' % he.code)
    _sh.rmtree(test_dest, ignore_errors=True)
except Exception as e:
    check('export', False, repr(e))

try:
    s, h, b = get('/')
    tb = b.decode('utf-8', 'ignore')
    check('index page', s == 200 and '音效库' in tb, '%d bytes' % len(b))
    check('index 注入状态', 'window.__STATE__' in tb, '')
except Exception as e:
    check('index', False, repr(e))

try:
    s, h, b = get('/api/state')
    st0 = json.loads(b)
    check('state 读取', s == 200 and isinstance(st0.get('state'), dict), 'keys=%d' % len(st0.get('state') or {}))

    def post_state(key, value):
        req = urllib.request.Request(
            BASE + '/api/state',
            data=json.dumps({'key': key, 'value': value}).encode('utf-8'),
            headers={'Content-Type': 'application/json'}, method='POST')
        return json.loads(urllib.request.urlopen(req, timeout=30).read())

    j = post_state('_smoke_t', '42')
    st1 = json.loads(get('/api/state')[2]).get('state') or {}
    check('state 写入', bool(j.get('ok')) and st1.get('_smoke_t') == '42', 'got=%r' % st1.get('_smoke_t'))
    post_state('_smoke_t', '7')
    st2 = json.loads(get('/api/state')[2]).get('state') or {}
    check('state 覆盖', st2.get('_smoke_t') == '7', 'got=%r' % st2.get('_smoke_t'))
except Exception as e:
    check('state', False, repr(e))

print()
print('FAILED: ' + (', '.join(fails) if fails else 'none — all good'))
sys.exit(1 if fails else 0)
