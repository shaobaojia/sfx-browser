#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""音效库结构整理：全库文件 → 4 桶结构。
--dry: 计算+校验+写 organize_plan.csv + 打印样例
无参 : 读取 plan 执行移动（可重跑，带断点续行）"""
import os, sys, json, csv, time, re
LIB = "/volume1/主目录/Collection/素材&模板&音库/音效"
ORG = "/volume1/主目录/Hermes/read/Projects/sfx-browser/organize"
PLAN = os.path.join(ORG, "organize_plan.csv")
MOVED = os.path.join(ORG, "organize_moved.csv")
DRYJ = os.path.join(ORG, "organize_dry.json")
CONF = os.path.join(ORG, "organize_conflicts.csv")
B1, B2, B3, B9 = "01_商业音效包", "02_中文音效合集", "03_项目素材", "99_待整理"
PSF = B1 + "/Pro Sound Effect"
RAW = B9 + "/_原始压缩包"

DEST = {}
def _add(names, dest):
    for n in names: DEST[n] = dest

_add(["[Blastwave.FX]Collection","Bluezone Corporation(76)","Boom Library - Close Combat Bundle",
      "Multiply Sound Film Score Bundle","Rock The Speakerbox - Broken",
      "[Tonsturm]01 Breaking Glass","[Tonsturm]02 Electricity",
      "A Sound Effect - Animal Hyperrealism Vol II","A Sound Effect - Rocks Momentum",
      "Sound Morph - Matter Mayhem","[Sound.Ideas]The SFX Kit For Game",
      "[Sound.Ideas]The Underwater Sound Effects Series","[Sound.Ideas]Thunder Sound Effects",
      "[Sound.Ideas]The Metropolis Science Fiction Toolkit","[Sound.Ideas]The Metropolis Science Fiction Toolkit Vol.2",
      "[Sound.Ideas]Drone Archeology","[Hollywood.Edge]The Edge Edition",
      "[Hollywood.Edge]The Eerie Edition Sound FX_可怕的","[Samplesourcer]Collecyion",
      "[WHO01]","[WHO02]","[WHO03]","[WHO04]","[WHO05]","[WHOBonus]"], B1)
_add(["26.Sci Fi,Beeps,Computers,Industry,Chemistry,Lab,Hospital","34.Airplane,Helicopter,Train,Boat,Car,Motorcycle",
"7 Cars","4 Water","27.Vehicles,Machines,Construction,Power Tools,Industry",
"21.Modern Aircraft,Helicopters,Airport Amb","15 Interior Crowds & Ambiences","1 Nature Backgrounds",
"31.Water","47.Traffic City Rural","49.Nature Ambiences","42.Recreation","48.Room Tone,Ambience,Industry",
"6 Planes & Trains","25.Household","5 Rain,Thunder,Fire,Bubbles","45.Airports,Travel",
"14 Crowds,Kids,Babies,Heartbeats","46.Rain,Wind","3 Wind","22.Historical Aircraft",
"19 Beeps,Bells,Buzzers,Rumbles,Tools","8 Traffic,Sirens,Motors,Busses","12 Sports & Boats",
"37.Crowd,Sports Crowds,Int","36.Air,Steam,Hiss,Whooshes,Industry Machines,Hand Tools",
"29.Automobiles,Motorcycles","30.Sports","41.Computers,Electronics",
"28.Crashes,Creak,Scraping,Impacts,Fire,Еxplosions,Footsteps","16 Household","17 Telephones,Cameras,Clocks",
"20 Electronic,Sci-Fi","32.Household","43.SciFi,Eerie,Horror","50.Designed Sounds","44.Scrapes & Scratches",
"38.Foley;Cloth,Nylon,Leather,Velcro,Zippers,Bag","23.Modern Military;Heavy Artillery,Gun",
"39.Human;Body Sounds","2 Birds & Animals","35.Wet Movement,Bubbles,Squeak,Impact,Crash,Pops",
"40.Pistol,Machine Gun,Bullet,Grenade","18 Doors,Squeaks,Creaks","24.Historical Military",
"13 Humans Coughs,Laughs,Grunts,Screams,Moans,Farts","33.Doors",
"9 Guns,Ricochets,Explosions,Fireworks","11 Crashes,Impacts & Swishes","10 Body Sounds",
"US01","US02","US03","US04","US05","wb04","wb05",
"Explosions","Explosions - 5.1 Surround","Hits & Tones","Impacts","Impacts & Destruction Sweeteners",
"Natural Elements","Period Combat","Period Devices","Period Vehicles","Period Backgrounds","Home & Office",
"Backgrounds","Vocals & Wallas","Vocals - Monster","Vocals - Humanoid",
"Sound Design - Sci-Fi","Sound Design - Fantasy","Sound Design - Horror",
"Ricochets - Hits - Whiz Bys","Title Sequence Effects","Thunder & Lightning",
"Weapons & Explosions","Weapons & Firearms","Hand To Hand Combat","Sports & Recreation",
"Electronics","Animals","Vehicles","Vintage Cartoon"], PSF)
_add(["魔法法术咒语技能释放音效","气氛音乐音效","布斯的音效库","电影级音效","电影音效",
"脚步声","脚步声02","飞机","飞机02","汽车","火","环境音","鸟，动物","欢呼、鼓掌","转场常用音效",
"卡通（华纳兄弟电影）","卡通（华纳兄弟电影） (2)","卡通（华纳兄弟电影） (3)"], B2)
_add(["LTT_V30All","预告"], B3)
_add(["临时"], B9)
DEST["Pro Sound Effect"] = B1  # Pro Sound Effect 本体 → 01桶下同名位置（即 PSF 路径）

JUNK = "\uf028\uf029"   # 下载工具残留的坏括号字符（私有区）
def clean(s):
    c = s.strip().strip(JUNK).strip()
    return c if c else s

def collapse(segs):
    out = []
    for s in segs:
        if not s: continue
        if out and out[-1] == s: continue
        out.append(s)
    return out

def T(rel, size=0):
    base = os.path.basename(rel)
    if base.lower().endswith(".zip") and size > 1_000_000_000:
        return RAW + "/" + base
    segs = rel.split("/")
    if segs[0] == "预告":
        if len(segs) >= 2 and segs[1].startswith("15. Sound Morph"):
            rest = segs[2:]
            if rest and rest[0].endswith(".zip"): return RAW + "/" + rest[0]
            if rest and rest[0] == "Sound Morph - Sinematic": rest = rest[1:]
            return "/".join(collapse([B3, "预告", "Sound Morph - Sinematic"] + rest))
        if len(segs) == 2 and base.endswith(".rar"):
            return B3 + "/预告/" + re.sub(r"\d{6,}(?=\.rar$)", "", base)
        return "/".join(collapse([B3, "预告"] + segs[1:]))
    if segs[0] == "Wind":
        if len(segs) >= 2 and clean(segs[1]) == "百万剪辑狮的音效库":
            return "/".join(collapse([B2, "百万剪辑狮的音效库"] + segs[2:]))
        if len(segs) == 1: return None
        return "/".join(collapse([B1, "Wind"] + segs[1:]))
    if segs[0] == "音效":
        if len(segs) == 2: return B9 + "/" + segs[1]
        r0 = clean(segs[1])
        if r0 == "音效":
            if len(segs) >= 3 and segs[2] == "BD音效库":
                return "/".join(collapse([B2, "BD音效库"] + segs[3:]))
            return None
        if r0 == "网络下载":
            return "/".join(collapse([B9, "网络下载"] + segs[2:]))
        if r0 in ("音效素材1", "音效素材2", "音效素材3"):
            return "/".join(collapse([B2, r0] + segs[2:]))
        d = DEST.get(r0)
        if d is None: return None
        return "/".join(collapse([d, r0] + segs[2:]))
    if len(segs) == 1: return B9 + "/" + segs[0]
    name = clean(segs[0])
    d = DEST.get(name)
    if d is None: return None
    return "/".join(collapse([d, name] + segs[1:]))

def dry():
    t0 = time.time()
    files = []
    for root, dirs, fns in os.walk(LIB):
        for fn in fns:
            p = os.path.join(root, fn)
            try: st = os.stat(p)
            except OSError: continue
            files.append((os.path.relpath(p, LIB), st.st_size))
    files.sort(); total = len(files)
    plan = []; unmatched = []; targets = {}
    for rel, size in files:
        nr = T(rel, size)
        if nr is None: unmatched.append(rel); continue
        plan.append((rel, nr)); targets.setdefault(nr, []).append(rel)
    conflicts = [nr for nr, srcs in targets.items() if len(srcs) > 1]
    checks = [
        ("音效/音效/BD音效库/AA免责声明AA.png", 0, "02_中文音效合集/BD音效库/AA免责声明AA.png"),
        ("音效/音效素材3/音效素材3/综合音效/x.wav", 0, "02_中文音效合集/音效素材3/综合音效/x.wav"),
        ("音效/音效/BD音效库/附赠音效库（转场+撞击+音效+环境音）/音效/音效/其他类/f.wav", 0,
         "02_中文音效合集/BD音效库/附赠音效库（转场+撞击+音效+环境音）/音效/其他类/f.wav"),
        ("13 Fast Whoosh A.wav", 0, "99_待整理/13 Fast Whoosh A.wav"),
        ("Rock The Speakerbox - Broken.zip", 2_000_000_000, "99_待整理/_原始压缩包/Rock The Speakerbox - Broken.zip"),
        ("临时/a.wav", 0, "99_待整理/临时/a.wav"),
        ("LTT_V30All/a.wav", 0, "03_项目素材/LTT_V30All/a.wav"),
        ("Pro Sound Effect/4 Water/x.wav", 0, "01_商业音效包/Pro Sound Effect/4 Water/x.wav"),
        ("26.Sci Fi,Beeps,Computers,Industry,Chemistry,Lab,Hospital/a.wav", 0,
         "01_商业音效包/Pro Sound Effect/26.Sci Fi,Beeps,Computers,Industry,Chemistry,Lab,Hospital/a.wav"),
        ("音效/Pro Sound Effect/x.wav", 0, "01_商业音效包/Pro Sound Effect/x.wav"),
        ("电影级音效/a.wav", 0, "02_中文音效合集/电影级音效/a.wav"),
        ("Wind/百万剪辑狮的音效库/x/a.wav", 0, "02_中文音效合集/百万剪辑狮的音效库/x/a.wav"),
        ("预告/Sound Morph - Sinematic/a.wav", 0, "03_项目素材/预告/Sound Morph - Sinematic/a.wav"),
        ("预告/Visual Tone - Essential Flow Sound Effects646051097078.rar", 0,
         "03_项目素材/预告/Visual Tone - Essential Flow Sound Effects.rar"),
        ("US01/a.wav", 0, "01_商业音效包/Pro Sound Effect/US01/a.wav"),
        ("卡通（华纳兄弟电影） (2)/x.wav", 0, "02_中文音效合集/卡通（华纳兄弟电影） (2)/x.wav"),
        ("音效/网络下载/x.wav", 0, "99_待整理/网络下载/x.wav"),
        ("A Sound Effect - Rocks Momentum\uf029/A Sound Effect - Glacier Ice/t.wav", 0,
         "01_商业音效包/A Sound Effect - Rocks Momentum/A Sound Effect - Glacier Ice/t.wav"),
    ]
    bad = [(a, T(a, s)) for a, s, b in checks if T(a, s) != b]
    if bad:
        print("ASSERT-FAIL:")
        for a, got in bad: print("  ", a, "->", got)
        json.dump({"guard_ok": False, "asserts": [str(x) for x in bad]}, open(DRYJ, "w"), ensure_ascii=False)
        sys.exit(2)
    print("== 计划样例（首/中/末）==")
    step = max(1, len(plan) // 3)
    for a, b in (plan[:12] + plan[step:step+12] + plan[-12:]):
        print("  %s\n     -> %s" % (a, b))
    print()
    print("DRY: total=%d planned=%d unmatched=%d target_dupes=%d" % (total, len(plan), len(unmatched), len(conflicts)))
    if unmatched:
        print("== 未匹配（需处理！）==")
        for u in unmatched[:40]: print("  ", u)
        with open(os.path.join(ORG, "organize_unmatched.txt"), "w", encoding="utf-8") as uf:
            uf.write("\n".join(unmatched))
    if conflicts:
        print("== 目标重名（将转冲突区）TOP15 ==")
        for c in conflicts[:15]: print("  ", c, "←", targets[c][:2])
    print()
    def lsdir(dp, n=40):
        try: xs = sorted(os.listdir(os.path.join(LIB, dp)))
        except OSError as e: return ["ERR:" + str(e)]
        return xs[:n] + (["…(%d总)" % len(xs)] if len(xs) > n else [])
    tops = sorted(os.listdir(LIB)); print("== 顶层项数: %d ==" % len(tops))
    with open(PLAN, "w", newline="", encoding="utf-8-sig") as f:
        wr = csv.writer(f); wr.writerow(["rel", "new_rel"])
        wr.writerows(plan)
    guard_ok = (len(unmatched) == 0)
    json.dump({"total": total, "planned": len(plan), "unmatched_count": len(unmatched),
               "conflict_count": len(conflicts), "guard_ok": guard_ok,
               "elapsed_s": round(time.time() - t0, 1)}, open(DRYJ, "w"), ensure_ascii=False)
    print()
    print("DRY-OK" if guard_ok else "DRY-FAIL", "| %.1fs" % (time.time() - t0))

def execute():
    rows = list(csv.reader(open(PLAN, encoding="utf-8-sig")))
    assert rows[0] == ["rel", "new_rel"], "plan 文件头异常"
    plan = [(r[0], r[1]) for r in rows[1:]]
    t0 = time.time(); ok = errs = cfl = 0; done = 0
    f = open(MOVED, "w", newline="", encoding="utf-8-sig"); wr = csv.writer(f)
    wr.writerow(["rel", "new_rel", "status"])
    cf = open(CONF, "w", newline="", encoding="utf-8-sig"); wc = csv.writer(cf)
    wc.writerow(["rel", "intended", "reason"])
    for rel, nr in plan:
        src = os.path.join(LIB, rel); dst = os.path.join(LIB, nr)
        done += 1
        if not os.path.exists(src) and os.path.exists(dst): ok += 1; continue
        if not os.path.exists(src): errs += 1; wr.writerow([rel, nr, "src-missing"]); continue
        if os.path.exists(dst):
            nrb, nre = os.path.splitext(nr)
            dst2rel = B9 + "/_命名冲突/" + nr
            dst2 = os.path.join(LIB, dst2rel)
            k2 = 2
            while os.path.exists(dst2):
                dst2rel = B9 + "/_命名冲突/" + "%s_%d%s" % (nrb, k2, nre)
                dst2 = os.path.join(LIB, dst2rel)
                k2 += 1
            try:
                os.makedirs(os.path.dirname(dst2), exist_ok=True)
                os.rename(src, dst2)
                wr.writerow([rel, dst2rel, "conflict"]); wc.writerow([rel, nr, "conflict"])
                cfl += 1
            except OSError as e:
                errs += 1; wr.writerow([rel, nr, "err:" + str(e)])
            continue
        try:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            os.rename(src, dst); wr.writerow([rel, nr, "moved"]); ok += 1
        except OSError as e:
            errs += 1; wr.writerow([rel, nr, "err:" + str(e)])
        if done % 20000 == 0:
            f.flush(); cf.flush()
            print("progress %d/%d ok=%d conflict=%d err=%d" % (done, len(plan), ok, cfl, errs), flush=True)
    f.close(); cf.close()
    pruned = 0
    for root, dirs, fns in os.walk(LIB, topdown=False):
        try:
            if not os.listdir(root): os.rmdir(root); pruned += 1
        except OSError: pass
    print("ORG-DONE " + json.dumps({"planned": len(plan), "ok": ok, "conflict": cfl,
          "errors": errs, "pruned_dirs": pruned, "elapsed_s": round(time.time() - t0, 1)}, ensure_ascii=False), flush=True)

if __name__ == "__main__":
    if "--dry" in sys.argv: dry()
    else: execute()
