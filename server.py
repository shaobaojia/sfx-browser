#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SFX Browser — 音效库秒搜/试听服务（纯 stdlib 零依赖）
启动: python3 server.py        (默认 0.0.0.0:8093, SFX_PORT 可覆盖)
索引: python3 build_index.py   (重建 data/sfx.db，原子替换，无需重启)
导出: POST /api/export {ids:[], dest:"/volume1/主目录/..."}  篮子批量复制到目标文件夹
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import zipfile
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, quote

try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, 'data', 'sfx.db')
USER_DB = os.path.join(BASE, 'data', 'user.db')   # 用户状态独立小库（sfx.db 重建索引会被整库替换，不能混）
CACHE = os.path.join(BASE, 'cache')
WAVE_CACHE = os.path.join(CACHE, 'wave')
AUDIO_CACHE = os.path.join(CACHE, 'audio')
EXPORT_DIR = os.path.join(CACHE, 'exports')
PORT = int(os.environ.get('SFX_PORT', '8093'))
LIB = os.environ.get('SFX_LIB', '/volume1/主目录/Collection/素材&模板&音库/音效')
DEST_ROOT = '/volume1/主目录'   # 篮子导出允许的目标根（安全边界）

MIME = {'.wav': 'audio/wav', '.mp3': 'audio/mpeg', '.ogg': 'audio/ogg', '.oga': 'audio/ogg',
        '.flac': 'audio/flac', '.m4a': 'audio/mp4', '.aac': 'audio/aac', '.opus': 'audio/ogg'}
NEEDS_TRANSCODE = {'.aiff', '.aif', '.aifc', '.caf', '.wv', '.wma'}

# ---- 中英桥：中文词 -> 英文词（反向表自动生成，双向生效）----
SYN = {
    '耳鸣': ['tinnitus', 'ringing'],
    '爆炸': ['explosion', 'blast', 'boom', 'explode', 'detonate'],
    '枪': ['gun', 'gunshot', 'rifle', 'pistol'],
    '脚步': ['footstep', 'footsteps', 'walking'],
    '走路': ['footstep', 'walking', 'walk'],
    '跑': ['run', 'running', 'sprint'],
    '门': ['door', 'gate'],
    '敲门': ['knock'],
    '玻璃': ['glass', 'shatter'],
    '金属': ['metal', 'metallic', 'clank', 'clang'],
    '风': ['wind', 'breeze', 'gust'],
    '雨': ['rain', 'rainfall'],
    '雷': ['thunder', 'lightning'],
    '水': ['water', 'splash', 'drip', 'liquid'],
    '火': ['fire', 'flame', 'burn'],
    '海浪': ['wave', 'ocean', 'sea', 'surf'],
    '森林': ['forest', 'jungle'],
    '鸟': ['bird', 'birds', 'chirp'],
    '猫': ['cat', 'meow'],
    '狗': ['dog', 'bark'],
    '狼': ['wolf', 'howl'],
    '马': ['horse', 'gallop', 'neigh'],
    '昆虫': ['insect', 'bee', 'fly', 'bug'],
    '人群': ['crowd', 'people', 'chatter', 'murmur'],
    '笑': ['laugh', 'laughter', 'giggle'],
    '哭': ['cry', 'crying', 'sob', 'weep'],
    '尖叫': ['scream', 'shout', 'yell'],
    '呼吸': ['breath', 'breathe'],
    '心跳': ['heartbeat', 'heart'],
    '鼓掌': ['applause', 'clap'],
    '咳嗽': ['cough'],
    '喷嚏': ['sneeze'],
    '电话': ['phone', 'telephone'],
    '铃': ['bell', 'chime', 'ding'],
    '警报': ['alarm', 'siren', 'alert'],
    '钟': ['clock', 'bell', 'tick'],
    '打': ['hit', 'punch', 'slap', 'strike'],
    '锤': ['hammer', 'pound'],
    '碎': ['break', 'crack', 'smash', 'shatter', 'debris'],
    '撕裂': ['tear', 'rip', 'shred'],
    '撞': ['crash', 'collision', 'impact'],
    '刹车': ['brake', 'tire', 'screech', 'skid'],
    '汽车': ['car', 'vehicle', 'engine'],
    '摩托': ['motorcycle', 'motorbike'],
    '飞机': ['plane', 'airplane', 'jet', 'aircraft'],
    '船': ['boat', 'ship'],
    '火车': ['train', 'rail'],
    '引擎': ['engine', 'motor'],
    '机器': ['machine', 'mechanical', 'industrial'],
    '电流': ['electric', 'electricity', 'spark', 'zap'],
    '魔法': ['magic', 'magical', 'spell', 'witch', 'mystic'],
    '法术': ['magic', 'spell', 'sorcery'],
    '科幻': ['sci-fi', 'scifi', 'futuristic', 'space'],
    '太空': ['space', 'astronaut', 'sci-fi'],
    '激光': ['laser', 'beam', 'zap'],
    '机器人': ['robot', 'robotic', 'android'],
    '恐怖': ['horror', 'scary', 'eerie', 'creepy', 'dread'],
    '紧张': ['tension', 'tense', 'suspense', 'riser'],
    '悬念': ['suspense', 'riser', 'drone'],
    '气氛': ['ambience', 'atmosphere', 'ambient', 'drone'],
    '环境': ['ambience', 'ambient', 'atmosphere', 'room tone'],
    '低沉': ['low', 'deep', 'rumble', 'drone'],
    '轰鸣': ['rumble', 'roar', 'drone'],
    '嗡': ['hum', 'buzz', 'drone'],
    '噪音': ['noise', 'static'],
    '静电': ['static', 'crackle'],
    '冰': ['ice', 'freeze', 'frozen', 'frost'],
    '血': ['blood', 'gore', 'squish'],
    '骨头': ['bone', 'snap'],
    '摔': ['fall', 'drop', 'crash'],
    '弹跳': ['bounce', 'ball'],
    '欢呼': ['cheer', 'celebration'],
    '烟花': ['firework', 'firecracker'],
    '鞭炮': ['firecracker', 'firework'],
    '锣': ['gong'],
    '鼓': ['drum', 'percussion'],
    '风铃': ['wind chime', 'chime'],
    '婴儿': ['baby', 'infant'],
    '小孩': ['child', 'kid', 'baby'],
    '女人': ['woman', 'female'],
    '男人': ['man', 'male'],
    '怪兽': ['monster', 'creature', 'growl'],
    '恐龙': ['dinosaur', 'roar'],
    '龙': ['dragon', 'roar'],
    '气泡': ['bubble', 'pop'],
    '拉链': ['zipper'],
    '键盘': ['keyboard', 'typing', 'typewriter'],
    '打字': ['typing', 'typewriter'],
    '相机': ['camera', 'shutter'],
    '快门': ['shutter'],
    '转场': ['whoosh', 'swoosh', 'transition', 'swipe'],
    '嗖': ['whoosh', 'swoosh', 'swish'],
    '冲击': ['impact', 'strike'],
    '鼓点': ['drum', 'beat'],
    '电子': ['electronic', 'digital', 'synth'],
    '点击': ['click', 'tap', 'ui'],
    '提示': ['notification', 'alert', 'ding'],
    '错误': ['error', 'glitch', 'buzz'],
    '成功': ['success', 'win', 'chime'],
    '睡觉': ['sleep', 'snore'],
    '鼾': ['snore', 'snoring'],
    '吃饭': ['eat', 'eating', 'chew'],
    '喝水': ['drink', 'gulp'],
    '炒菜': ['cook', 'pan', 'sizzle'],
    '关门': ['door', 'close', 'slam'],
    '锁': ['lock', 'unlock', 'latch'],
    '钥匙': ['key', 'keys'],
    '硬币': ['coin', 'money'],
    '纸张': ['paper', 'pages'],
    '翻书': ['book', 'pages', 'paper'],
    '布料': ['cloth', 'fabric'],
    '皮革': ['leather'],
    '绳子': ['rope'],
    '木头': ['wood', 'wooden'],
    '石头': ['stone', 'rock'],
    '沙': ['sand'],
    '雪': ['snow'],
    '雾': ['fog', 'mist'],
    '派对': ['party', 'celebration'],
    '香槟': ['champagne', 'cork', 'pop'],
    '游戏': ['game', 'arcade', 'ui'],
    '升级': ['level up', 'upgrade', 'success'],
    '铃铛': ['bell', 'jingle'],
    '圣诞': ['christmas', 'jingle', 'bell'],
    '敲': ['knock', 'tap', 'rap'],
    '拍': ['clap', 'slap', 'pat'],
    '爆': ['explosion', 'blast', 'burst'],
    '击': ['hit', 'strike'],
    '碰撞': ['collision', 'impact'],
    '摩擦': ['friction', 'rub', 'scrape'],
    '飞': ['fly', 'flight', 'flying'],
}
SYN_REV = {}
for _cn, _ens in SYN.items():
    for _e in _ens:
        SYN_REV.setdefault(_e, []).append(_cn)


def expand_token(tok):
    """一个查询词 -> 同义扩展组（原文 + 中英互译 + 英文单复数 + 中文复合词拆子词）"""
    tok = tok.strip().lower()
    if not tok:
        return []
    out, seen = [], set()
    cand = [tok] + SYN.get(tok, []) + SYN_REV.get(tok, [])
    if not tok.isascii() and len(tok) > 1:
        # 复合中文词（如“撞击”“脚步声”）：命中其中的任何中文子词都带出英文扩展
        for k, ens in SYN.items():
            if k != tok and k in tok:
                cand.extend(ens)
    if tok.isascii():
        if tok.endswith('s'):
            cand.append(tok[:-1])
        else:
            cand.append(tok + 's')
    for c in cand:
        c = c.lower()
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out[:12]


def db():
    c = sqlite3.connect('file:%s?mode=ro' % DB, uri=True)
    c.row_factory = sqlite3.Row
    return c


_user_lock = threading.Lock()


def user_init():
    """用户状态库（收藏/篮子/视图/开关/导出目录；独立于 sfx.db，重建索引不受影响）"""
    os.makedirs(os.path.dirname(USER_DB), exist_ok=True)
    c = sqlite3.connect(USER_DB)
    c.execute('PRAGMA journal_mode=WAL')
    with c:
        c.execute('CREATE TABLE IF NOT EXISTS state(key TEXT PRIMARY KEY, value TEXT NOT NULL)')
    c.close()


def user_all():
    try:
        c = sqlite3.connect(USER_DB)
        rows = c.execute('SELECT key, value FROM state').fetchall()
        c.close()
        return {r[0]: r[1] for r in rows}
    except Exception:
        return {}


def user_set(key, value):
    with _user_lock:
        c = sqlite3.connect(USER_DB)
        with c:
            c.execute('INSERT OR REPLACE INTO state(key, value) VALUES(?, ?)', (key, value))
        c.close()


def like_pat(s):
    return '%' + s.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'


LIKE_REL = "rel LIKE ? ESCAPE '\\'"
LIKE_NAME = "name LIKE ? ESCAPE '\\'"


def pref_pat(s):
    return s.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '/%'


def _int(qs, key, default, lo=None, hi=None):
    """GET 参数安全取整数（带范围钳制；缺失/非法回退默认值）"""
    try:
        v = int(qs.get(key, [str(default)])[0])
    except (ValueError, TypeError):
        v = default
    if lo is not None:
        v = max(v, lo)
    if hi is not None:
        v = min(v, hi)
    return v


FMTS = {'wav': ('.wav',), 'mp3': ('.mp3',), 'wma': ('.wma',), 'aiff': ('.aif', '.aiff')}


def do_search(q, limit, offset=0, direc='', sort='', fmt=''):
    toks = [t for t in q.split() if t.strip()]
    conds, params = [], []
    if direc:
        conds.append("rel LIKE ? ESCAPE '\\'")
        params.append(pref_pat(direc))
    if fmt in FMTS:
        exts = FMTS[fmt]
        conds.append('ext IN (' + ','.join(['?'] * len(exts)) + ')')
        params += exts
    groups = []
    for t in toks:
        ex = expand_token(t)
        if not ex:
            continue
        groups.append('(' + ' OR '.join([LIKE_REL] * len(ex)) + ')')
        params += [like_pat(e) for e in ex]
    if toks and not groups:
        return 0, []
    if not conds and not groups:
        return 0, []
    if groups:
        conds.append(' AND '.join(groups))
    where = ' AND '.join(conds)
    if sort == 'size':
        order, oparams = 'size DESC, rel', []
    elif sort == 'mtime':
        order, oparams = 'mtime DESC, rel', []
    elif sort == 'rand':
        order, oparams = 'RANDOM()', []
    elif sort == 'name' or not toks:
        order, oparams = 'rel', []
    else:
        order = 'CASE WHEN ' + LIKE_NAME + ' THEN 0 ELSE 1 END, LENGTH(rel), id'
        oparams = [like_pat(toks[0])]
    sql = ('SELECT id, rel, name, dir, ext, size, mtime, COUNT(*) OVER () AS total '
           'FROM files WHERE ' + where + ' ORDER BY ' + order + ' LIMIT ? OFFSET ?')
    c = db()
    rows = c.execute(sql, params + oparams + [limit, offset]).fetchall()
    c.close()
    total = rows[0]['total'] if rows else 0
    return total, [dict(r) for r in rows]


_DIRS = {'mtime': 0, 'tree': None}


def dir_tree():
    """目录树（按 db mtime 缓存）：每个节点 = 该目录下递归音频数/体积 + 子目录"""
    try:
        mtime = int(os.path.getmtime(DB))
    except OSError:
        mtime = 0
    if _DIRS['tree'] is not None and _DIRS['mtime'] == mtime:
        return _DIRS['tree']
    c = db()
    rows = c.execute('SELECT dir, COUNT(*) n, COALESCE(SUM(size),0) s FROM files GROUP BY dir').fetchall()
    c.close()
    tree = {}

    def node(p):
        x = tree.get(p)
        if x is None:
            x = {'n': 0, 's': 0, 'kids': {}}
            tree[p] = x
        return x

    for r in rows:
        d = (r['dir'] or '').strip('/')
        if not d:
            continue
        cnt, sz = r['n'], r['s']
        parts = d.split('/')
        for i in range(1, len(parts) + 1):
            nd = node('/'.join(parts[:i]))
            nd['n'] += cnt
            nd['s'] += sz
        for i in range(len(parts)):
            nd = node('/'.join(parts[:i]))
            nd['kids'][parts[i]] = '/'.join(parts[:i + 1])
    _DIRS['mtime'] = mtime
    _DIRS['tree'] = tree
    return tree


def dir_kids(under):
    """某目录的子目录列表（名称 / 路径 / 递归数量 / 体积 / 有无下级）"""
    tree = dir_tree()
    nd = tree.get(under)
    kids = []
    if nd:
        for name in sorted(nd['kids']):
            full = nd['kids'][name]
            ch = tree.get(full) or {'n': 0, 's': 0, 'kids': {}}
            kids.append({'name': name, 'path': full, 'n': ch['n'], 's': ch['s'],
                         'has': bool(ch['kids'])})
    return kids


_WAVE_SEM = threading.Semaphore(2)   # 并发限流：最多 2 个 ffmpeg 同时跑（防"波形风暴"卡交互）


def _cached_media(cache_dir, key, suffix, cmd_fn, timeout, sem=None):
    """通用媒体缓存：命中直接返回；否则 mkstemp → ffmpeg → 原子替换"""
    dst = os.path.join(cache_dir, key)
    if os.path.exists(dst):
        return dst
    os.makedirs(cache_dir, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=cache_dir, suffix=suffix)
    os.close(fd)
    r = None
    try:
        if sem is None:
            r = subprocess.run(cmd_fn(tmp), timeout=timeout, capture_output=True)
        else:
            with sem:
                r = subprocess.run(cmd_fn(tmp), timeout=timeout, capture_output=True)
    except subprocess.TimeoutExpired:
        pass
    if r is None or r.returncode != 0 or not os.path.exists(tmp):
        try:
            os.remove(tmp)
        except Exception:
            pass
        return None
    os.replace(tmp, dst)
    return dst


def wave_for(fid, mtime, src):
    return _cached_media(
        WAVE_CACHE, '%d_%d_v960.png' % (fid, mtime), '.png',
        lambda tmp: ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-threads', '1', '-i', src,
                     '-filter_complex', 'showwavespic=s=960x96:colors=0x6ea8fe', '-frames:v', '1', tmp],
        90, sem=_WAVE_SEM)


def transcode(fid, mtime, src):
    return _cached_media(
        AUDIO_CACHE, '%d_%d.wav' % (fid, mtime), '.wav',
        lambda tmp: ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', src,
                     '-ac', '2', '-ar', '48000', '-c:a', 'pcm_s16le', tmp],
        180)


def make_zip(ids):
    """给一组 id 打包平铺 zip → (路径, None)；不可行时 (None, (错误信息, 状态码))"""
    c = db()
    rows = c.execute('SELECT id, rel, name, size FROM files WHERE id IN (%s)'
                     % ','.join('?' * len(ids)), ids).fetchall()
    c.close()
    rows = [r for r in rows if os.path.exists(os.path.join(LIB, r['rel']))]
    if not rows:
        return None, ('no valid files', 404)
    tot = sum(r['size'] for r in rows)
    if tot > 2_500_000_000:
        return None, ('选中的文件太大(%dMB)，请分批导出' % (tot // 10 ** 6), 400)
    os.makedirs(EXPORT_DIR, exist_ok=True)
    zpath = os.path.join(EXPORT_DIR, 'sfx_%d.zip' % int(time.time()))
    zf = zipfile.ZipFile(zpath, 'w', zipfile.ZIP_STORED)
    try:
        used = set()
        for r in rows:
            name = r['name']
            stem, ext = os.path.splitext(name)
            k = 2
            while name in used:
                name = '%s_%d%s' % (stem, k, ext)
                k += 1
            used.add(name)
            zf.write(os.path.join(LIB, r['rel']), arcname=name)
    finally:
        zf.close()
    return zpath, None


def parse_export_req(body):
    """解析导出请求体 → ((ids, dest), None) 或 (None, (错误信息, 状态码))"""
    try:
        data = json.loads(body.decode('utf-8'))
    except Exception:
        return None, ('bad json', 400)
    ids = []
    for x in (data.get('ids') or []):
        try:
            ids.append(int(x))
        except (TypeError, ValueError):
            pass
    ids = ids[:300]
    dest = (data.get('dest') or '').strip()
    if not ids:
        return None, ('篮子为空', 400)
    if not dest:
        return None, ('请填写目标文件夹', 400)
    return (ids, dest), None


def export_files(ids, dest):
    """把文件复制到 dest（限 DEST_ROOT 下且禁库内）→ (统计, None) 或 (None, (错误信息, 状态码))"""
    dest_norm = os.path.normpath(dest)
    root = os.path.normpath(DEST_ROOT)
    lib_norm = os.path.normpath(LIB)
    if not (dest_norm + os.sep).startswith(root + os.sep):
        return None, ('目标必须在 %s/ 下' % root, 400)
    if dest_norm == lib_norm or (dest_norm + os.sep).startswith(lib_norm + os.sep):
        return None, ('目标不能是音效库内部', 400)
    try:
        os.makedirs(dest_norm, exist_ok=True)
    except OSError as e:
        return None, ('无法创建目标目录: %s' % e, 500)
    c = db()
    rows = c.execute('SELECT id, rel, name FROM files WHERE id IN (%s)'
                     % ','.join('?' * len(ids)), ids).fetchall()
    c.close()
    got = {r['id']: r for r in rows}
    copied = renamed = missing = 0
    for i in ids:
        r = got.get(i)
        if not r:
            missing += 1
            continue
        src = os.path.join(LIB, r['rel'])
        if not os.path.exists(src):
            missing += 1
            continue
        stem, ext = os.path.splitext(r['name'])
        tgt = os.path.join(dest_norm, r['name'])
        k = 2
        while os.path.exists(tgt):
            tgt = os.path.join(dest_norm, '%s_%d%s' % (stem, k, ext))
            k += 1
        if os.path.basename(tgt) != r['name']:
            renamed += 1
        try:
            shutil.copy2(src, tgt)
            copied += 1
        except OSError:
            missing += 1
    print('export %d files -> %s (renamed %d, missing %d)' % (copied, dest_norm, renamed, missing))
    return {'copied': copied, 'renamed': renamed, 'missing': missing, 'dest': dest_norm}, None


class Handler(BaseHTTPRequestHandler):
    server_version = 'sfx-browser/1.5'
    protocol_version = 'HTTP/1.1'
    timeout = 60

    def log_message(self, *a):
        pass

    # ---------- helpers ----------
    def json(self, obj, status=200):
        b = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(b)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(b)

    def serve_path(self, fp, ctype, dl=False, fname=None, cache='no-cache'):
        size = os.path.getsize(fp)
        start, end, status = 0, size - 1, 200
        rng = self.headers.get('Range')
        if rng and rng.startswith('bytes='):
            spec = rng[6:].split(',')[0].strip()
            try:
                a, _, b = spec.partition('-')
                if a:
                    start = int(a)
                    end = int(b) if b else size - 1
                elif b:
                    start = max(0, size - int(b))
                    end = size - 1
                if 0 <= start <= end < size:
                    status = 206
                else:
                    start, end, status = 0, size - 1, 200
            except ValueError:
                start, end, status = 0, size - 1, 200
        length = end - start + 1
        self.send_response(status)
        self.send_header('Content-Type', ctype)
        self.send_header('Accept-Ranges', 'bytes')
        if status == 206:
            self.send_header('Content-Range', 'bytes %d-%d/%d' % (start, end, size))
        self.send_header('Content-Length', str(length))
        if dl and fname:
            self.send_header('Content-Disposition', "attachment; filename*=UTF-8''" + quote(fname))
        self.send_header('Cache-Control', cache)
        self.end_headers()
        with open(fp, 'rb') as f:
            f.seek(start)
            remain = length
            while remain > 0:
                chunk = f.read(min(262144, remain))
                if not chunk:
                    break
                self.wfile.write(chunk)
                remain -= len(chunk)

    def get_row(self, fid):
        c = db()
        r = c.execute('SELECT id, rel, name, ext, mtime FROM files WHERE id=?', (fid,)).fetchone()
        c.close()
        return r

    # ---------- routes ----------
    def do_GET(self):
        try:
            u = urlparse(self.path)
            path, qs = u.path, parse_qs(u.query)
            if path in ('/', '/index.html'):
                fp = os.path.join(BASE, 'index.html')
                try:
                    with open(fp, encoding='utf-8') as f:
                        t = f.read()
                except OSError:
                    return self.json({'error': 'index.html missing'}, 500)
                inject = '<script>window.__STATE__=%s;</script>\n' % \
                         json.dumps(user_all(), ensure_ascii=False).replace('</', '<\\/')
                t = t.replace('</head>', inject + '</head>', 1)
                b = t.encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(b)))
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                self.wfile.write(b)
                return
            if path == '/api/dirs':
                under = qs.get('under', [''])[0][:400].strip().strip('/')
                return self.json({'under': under, 'kids': dir_kids(under)})
            if path == '/api/search':
                q = qs.get('q', [''])[0][:200]
                direc = qs.get('dir', [''])[0][:400].strip().strip('/')
                sort = qs.get('sort', [''])[0]
                if sort not in ('name', 'size', 'mtime', 'rand'):
                    sort = ''
                fmt = qs.get('fmt', [''])[0]
                limit = _int(qs, 'limit', 300, 1, 1000)
                offset = _int(qs, 'offset', 0, 0)
                total, res = do_search(q, limit, offset, direc, sort, fmt)
                if q or direc:
                    print('search q=%r dir=%r -> %d (offset %d)' % (q, direc, total, offset))
                return self.json({'total': total, 'shown': len(res), 'offset': offset, 'results': res})
            if path == '/api/stats':
                c = db()
                row = c.execute('SELECT COUNT(*) n, COALESCE(SUM(size),0) sz FROM files').fetchone()
                c.close()
                mtime = int(os.path.getmtime(DB)) if os.path.exists(DB) else 0
                return self.json({'files': row['n'], 'bytes': row['sz'], 'db_mtime': mtime})
            if path == '/api/state':
                return self.json({'ok': True, 'state': user_all()})
            if path == '/api/wave':
                fid = _int(qs, 'id', 0)
                r = self.get_row(fid)
                if not r:
                    return self.json({'error': 'not found'}, 404)
                fp = wave_for(r['id'], r['mtime'], os.path.join(LIB, r['rel']))
                if not fp:
                    return self.json({'error': 'wave failed'}, 500)
                return self.serve_path(fp, 'image/png', cache='max-age=604800')
            if path == '/api/audio':
                fid = _int(qs, 'id', 0)
                r = self.get_row(fid)
                if not r:
                    return self.json({'error': 'not found'}, 404)
                src = os.path.join(LIB, r['rel'])
                if not os.path.exists(src):
                    return self.json({'error': 'file missing'}, 404)
                dl = qs.get('dl', ['0'])[0] == '1'
                if r['ext'] in NEEDS_TRANSCODE:
                    fp = transcode(r['id'], r['mtime'], src)
                    if not fp:
                        return self.json({'error': 'transcode failed'}, 500)
                    return self.serve_path(fp, 'audio/wav', dl=dl,
                                           fname=os.path.splitext(r['name'])[0] + '.wav',
                                           cache='max-age=3600')
                return self.serve_path(src, MIME.get(r['ext'], 'application/octet-stream'),
                                       dl=dl, fname=r['name'], cache='max-age=3600')
            if path == '/api/zip':
                ids = [int(x) for x in qs.get('ids', [''])[0].split(',') if x.strip().isdigit()][:300]
                if not ids:
                    return self.json({'error': 'empty ids'}, 400)
                zpath, err = make_zip(ids)
                if err:
                    return self.json({'error': err[0]}, err[1])
                try:
                    self.serve_path(zpath, 'application/zip', dl=True, fname='sfx_selection.zip')
                finally:
                    try:
                        os.remove(zpath)
                    except Exception:
                        pass
                return
            if path == '/favicon.ico':
                self.send_response(204)
                self.send_header('Content-Length', '0')
                self.end_headers()
                return
            return self.json({'error': 'not found'}, 404)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:
            import traceback
            traceback.print_exc()
            try:
                self.json({'error': str(e)}, 500)
            except Exception:
                pass

    def do_POST(self):
        try:
            u = urlparse(self.path)
            if u.path == '/api/state':
                try:
                    ln = int(self.headers.get('Content-Length') or 0)
                except ValueError:
                    ln = 0
                if ln > 2_000_000:
                    self.close_connection = True
                    return self.json({'error': 'payload too big'}, 413)
                body = self.rfile.read(ln) if ln else b''
                try:
                    data = json.loads(body.decode('utf-8'))
                    key = str(data.get('key') or '')
                    val = data.get('value')
                except Exception:
                    return self.json({'error': 'bad json'}, 400)
                if not (0 < len(key) <= 64):
                    return self.json({'error': 'bad key'}, 400)
                if not isinstance(val, str):
                    val = json.dumps(val, ensure_ascii=False)
                if len(val) > 1_900_000:
                    return self.json({'error': 'value too big'}, 400)
                user_set(key, val)
                return self.json({'ok': True})
            if u.path == '/api/export':
                try:
                    ln = int(self.headers.get('Content-Length') or 0)
                except ValueError:
                    ln = 0
                if ln > 1_000_000:
                    self.close_connection = True
                    return self.json({'error': 'payload too big'}, 413)
                body = self.rfile.read(ln) if ln else b''
                parsed, err = parse_export_req(body)
                if err:
                    return self.json({'error': err[0]}, err[1])
                ids, dest = parsed
                stats, err = export_files(ids, dest)
                if err:
                    return self.json({'error': err[0]}, err[1])
                return self.json(stats)
            return self.json({'error': 'not found'}, 404)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:
            import traceback
            traceback.print_exc()
            try:
                self.json({'error': str(e)}, 500)
            except Exception:
                pass


class Srv(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def main():
    user_init()
    os.makedirs(EXPORT_DIR, exist_ok=True)
    try:
        now = time.time()
        for fn in os.listdir(EXPORT_DIR):
            p = os.path.join(EXPORT_DIR, fn)
            if now - os.path.getmtime(p) > 3600:
                os.remove(p)
    except Exception:
        pass
    if not os.path.exists(DB):
        print('WARN: index not found (%s) — run build_index.py first' % DB, flush=True)
    srv = Srv(('0.0.0.0', PORT), Handler)
    print('sfx-browser serving on http://0.0.0.0:%d  (lib=%s)' % (PORT, LIB), flush=True)
    srv.serve_forever()


if __name__ == '__main__':
    main()
