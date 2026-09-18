#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重建音效库索引: 扫描 LIB -> data/sfx.db（先写 .building 再原子替换，服务无需重启）"""
import os
import sqlite3
import sys
import time

LIB = os.environ.get('SFX_LIB', '/volume1/主目录/Collection/素材&模板&音库/音效')
BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, 'data', 'sfx.db')
AUDIO_EXT = {'.wav', '.mp3', '.aiff', '.aif', '.aifc', '.caf', '.ogg', '.oga', '.flac',
             '.m4a', '.aac', '.opus', '.wv', '.wma'}


def main():
    if not os.path.isdir(LIB):
        print('ERROR: lib dir not found: %s' % LIB)
        sys.exit(2)
    t0 = time.time()
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    tmp = DB + '.building'
    if os.path.exists(tmp):
        os.remove(tmp)
    conn = sqlite3.connect(tmp)
    conn.execute('PRAGMA journal_mode=OFF')
    conn.execute('PRAGMA synchronous=OFF')
    conn.execute('CREATE TABLE files(id INTEGER PRIMARY KEY, rel TEXT, name TEXT, '
                 'dir TEXT, ext TEXT, size INTEGER, mtime INTEGER)')
    n = 0
    batch = []

    def flush():
        conn.executemany('INSERT INTO files(rel,name,dir,ext,size,mtime) VALUES(?,?,?,?,?,?)', batch)
        batch.clear()

    for root, dirs, files in os.walk(LIB):
        for fn in files:
            ext = os.path.splitext(fn)[1].lower()
            if ext not in AUDIO_EXT:
                continue
            full = os.path.join(root, fn)
            try:
                st = os.stat(full)
            except OSError:
                continue
            rel = os.path.relpath(full, LIB)
            batch.append((rel, fn, os.path.dirname(rel), ext, st.st_size, int(st.st_mtime)))
            n += 1
            if len(batch) >= 5000:
                flush()
                print('scanned %d ...' % n, flush=True)
    flush()
    conn.commit()
    cnt = conn.execute('SELECT COUNT(*) FROM files').fetchone()[0]
    conn.close()
    os.replace(tmp, DB)
    print('OK indexed %d files in %.1fs -> %s (%.1fMB)'
          % (cnt, time.time() - t0, DB, os.path.getsize(DB) / 1e6), flush=True)


if __name__ == '__main__':
    main()
