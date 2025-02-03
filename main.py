#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, re, json, base64, plistlib, math, datetime, urllib.parse,sqlite3,requests;from functools import partial;from xml.etree import ElementTree as ET;from PIL import Image, ImageDraw, ImageFont
script_dir = os.getenv("dir", os.path.dirname(os.path.abspath(__file__)));csts={}
dict_path = os.path.join(script_dir, "beatmapid字典.txt")
try:
    with open(dict_path, "r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln or ln.startswith("#"):continue
            m = re.match(r'"([^"]+)":\s*\{\s*constant:\s*([-\d\.]+)\s+category:\s*"([^"]+)"\s+name:\s*"([^"]+)"\s*\},?', ln)
            if m:csts[m.group(1)] = {"constant": float(m.group(2)),"category": m.group(3),"name": m.group(4)}
except:pass
def reality(score):
    if score >= 1005000: return 1
    if score >= 995000: return 1.4/(math.exp(-3.65*(score/10000-99.5))+1)-0.4
    if score >= 980000: return ((math.exp(3.1*(score-980000)/15000)-1)/(math.exp(3.1)-1))*0.8-0.5
    if score >= 700000: return score/280000 - 4
def regFile(s):
    m = re.search(r'"PlayerFile(?:_h\d+)?"\s*=\s*hex:((?:[0-9a-fA-F]{2},?[\s\\\n]*)+)', s)
    if m:
        hd = re.sub(r"[,\\\s\n]", "", m.group(1))
        return "".join(chr(int(hd[i:i+2], 16)) for i in range(0, len(hd), 2))
    return ""
def pPlist(b):
    try:
        pd = plistlib.loads(b)
        if "PlayerFile" in pd:
            d = pd["PlayerFile"]
            if isinstance(d, str):
                try:json.loads(d);return d
                except:pass
    except:pass
    return ""
def pXML(s):
    try:
        n = ET.fromstring(s).find(".//string[@name='PlayerFile']")
        if n is not None and n.text:
            return urllib.parse.unquote(n.text)
    except:pass
    return ""
def pPrefs(s):
    try:
        for n in ET.fromstring(s).iter("pref"):
            if n.get("name") == "PlayerFile" and n.get("type") == "string":
                return base64.b64decode(n.text or "").decode("utf-8", "replace")
    except:pass
    return ""
def pdb(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM kv WHERE key='PlayerFile'")
        row = cursor.fetchone()
        conn.close()
        if row:return pOld(row[0])
        else:return None, []
    except Exception as e:
        print(f"[ERROR] 解析数据库失败: {e}")
        return None, []
def pData(raw):
    if not raw.strip():return None,[]
    return pNew(raw) if bool(re.match(r"^\[.*?\],\{.*?\}$", raw.strip(), re.DOTALL)) else pOld(raw)
def pNew(s):
    try:
        m = re.match(r"^\[(.*?)\],\{(.*)\}$", s, re.DOTALL)
        if not m: return None,[]
        its=[]
        for song in re.findall(r"\[.*?\]", m.group(2), re.DOTALL):
            if (ps := psN(song)): its.append(ps)
        return m.group(1),its
    except:return None,[]
def psN(s):
    try:
        arr = s.strip("[]").split(",")
        if len(arr) < 6: return
        t,c,co,sc,ac,l = arr
        co, sc, ac, l = float(co), int(sc), float(ac), int(l)
        r = reality(sc)
        sr = (r + co) if r else 0
        return {
            "name": t.strip(),
            "category": c.strip(),
            "constant": co,
            "bestScore": sc,
            "bestAccuracy": ac,
            "bestLevel": l,
            "singleRealityRaw": sr
        }
    except:
        return
def pOld(s):
    if (i:= s.find('{"UserName":'))<0 or (j:=s.find("}]}", i))<0: return None,[]
    j += 3
    try:d = json.loads(s[i:j])
    except:d = None
    if not d or "SongRecords" not in d: return None,[]
    its=[]
    for r in d["SongRecords"]:
        if (pr:=psO(r)): its.append(pr)
    return d.get("UserName"),its
def psO(r):
    if not (b := r.get("BeatmapID")) or b not in csts: return
    c, sc, ac, lv, rr = csts[b], r.get("BestScore", 0), r.get("BestAccuracy", 0.0), r.get("BestLevel", 0), reality(r.get("BestScore", 0))
    return {**c, "bestScore": sc, "bestAccuracy": ac, "bestLevel": lv, "singleRealityRaw": (rr + c["constant"]) if rr else 0}

def drawImg(its, uname, uR, outp, drawCount, drawLevel):
    rows = (drawCount+1)//2
    if drawCount<=22:H=2200
    else:H = 2200 + (rows-11)*162
    W = 1200
    can=Image.new("RGBA",(W,H),(0,0,0,255))
    dr=ImageDraw.Draw(can)
    bgp = os.path.join(script_dir, "jpgs", "查分图.jpg")
    if os.path.exists(bgp):bg = Image.open(bgp).convert("RGBA").resize((W,H));can.paste(bg, (0,0))
    else:dr.rectangle([(0,0),(W,H)], fill=(0,0,0,255))
    ov=Image.new("RGBA",(W,200),(128,128,128,int(0.2*255)))
    can.paste(ov,(0,50),ov)
    dr.line([(550,250),(650,50)], fill=(255,255,255,int(0.8*255)), width=3)
    fp=os.path.join(script_dir,"fonts","NotoSansCJK-Regular.ttc")
    f25=ImageFont.truetype(fp,25,index=2)
    dr.text((660,80), "Player: "+str(uname), fill=(255,255,255), font=f25)
    dr.text((660,130),"Reality: "+str(math.floor(uR*10000)/10000), fill=(255,255,255), font=f25)
    dr.text((660,180),"Date: "+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),fill=(255,255,255), font=f25)
    dr.text((100,90),"Reality查分器v1.2", fill=(255,255,255), font=ImageFont.truetype(fp,50,index=2))
    dr.text((100,160),"http://k9.lv/c/", fill=(255,255,255), font=ImageFont.truetype(fp,30,index=2))
    cImgs=[]
    for i in range(drawCount):
        if not os.path.exists(ip:=os.path.join(script_dir, "jpgs", its[i]["name"]+".jpg")):ip=os.path.join(script_dir, "jpgs", "NYA.jpg")
        try:cImgs.append(Image.open(ip).convert("RGBA"))
        except:cImgs.append(Image.new("RGBA",(142,80),(100,100,100,255)))
    def draw_gradient_txt(cv,xy,txt,ft,tc,bc):
        bb=ImageDraw.Draw(cv).textbbox((0,0),txt,font=ft)
        tw,th=bb[2]-bb[0],bb[3]-bb[1]
        g=Image.new("RGBA",(tw,th))
        for yy in range(th):
            ratio=yy/(th-1) if th>1 else 0
            for xx in range(tw):
                g.putpixel((xx,yy),(int(tc[0]*(1-ratio)+bc[0]*ratio),int(tc[1]*(1-ratio)+bc[1]*ratio),int(tc[2]*(1-ratio)+bc[2]*ratio),255))
        ImageDraw.Draw(mk:=Image.new("L",(tw,th),0)).text((-bb[0],-bb[1]),txt,font=ft,fill=255)
        g.putalpha(mk)
        cv.alpha_composite(g,dest=(xy[0]-bb[0],xy[1]-bb[1]))
    def dtb(d,x,y,txt,ft,fl):
        b=d.textbbox((0,0),txt,font=ft)
        d.text((x,y-(b[3]-b[1])),txt,font=ft,fill=fl)
    for i in range(drawCount):
        x=110+(i%2)*520
        y=350+(i//2)*162-(50 if i%2==0 else 0)
        bg=Image.new("RGBA",(442,130),(128,128,128,int(0.3*255)))
        can.paste(bg,(x,y),bg)
        numT="#"+str(i+1)
        nb=dr.textbbox((0,0),numT,font=ImageFont.truetype(fp,16,index=2))
        dr.text((x+442-10-(nb[2]-nb[0]),y+int(1.3)),
                numT, fill=(250,250,250) if i<20 else (201,201,201), font=ImageFont.truetype(fp,16,index=2))
        scT=str(its[i]["bestScore"]).zfill(7)
        scPos=(int(x+160*1.3),int(y+53*1.3))
        lv=its[i]["bestLevel"]
        if lv<2:draw_gradient_txt(can, scPos, scT, ImageFont.truetype(fp,39,index=2), (0x99,0xC5,0xFB), (0xE8,0xD3,0xFF))
        else:dtb(dr, scPos[0], scPos[1]-5, scT, ImageFont.truetype(fp,39,index=2), (154,218,250) if lv==2 else (255,255,255))
        fw=24
        fSong=ImageFont.truetype(fp,fw,index=2)
        while dr.textbbox((0,0),sn:=its[i]["name"],font=fSong)[2]>200 and fw>10:
            fw-=1
            fSong=ImageFont.truetype(fp,fw,index=2)
        dtb(dr,int(x+163*1.3),int(y+24*1.3),sn,fSong,(255,255,255))
        rt="%s %.1f > %.2f   %.2f%%"%(its[i]['category'],its[i]['constant'],its[i]['singleRealityRaw'],its[i]['bestAccuracy']*100)
        dtb(dr,int(x+160*1.3),int(y+80*1.3),rt,ImageFont.truetype(fp,19,index=2),(255,255,255))
        ci=cImgs[i].resize((185,104))
        can.paste(ci,(int(x+10*1.3),int(y+10*1.3)), ci)
        if drawLevel==1:
            if lv>=6:levelFile="6.png"
            elif lv<=0:levelFile="0.png"
            elif lv in [1,2,3,4,5]:levelFile=f"{lv}.png"
            else:levelFile=None
            if levelFile:
                lvlPath=os.path.join(script_dir,"jpgs",levelFile)
                if os.path.exists(lvlPath):
                    lvl=Image.open(lvlPath).convert("RGBA")
                    lw=lh=75
                    lx=x+442-80
                    ly=scPos[1]-lh+35
                    lvl=lvl.resize((lw,lh))
                    can.alpha_composite(lvl,(lx,ly))
    can.convert("RGB").save(outp,"PNG")
def load_links(txt_path=None):
    if not txt_path:txt_path = os.path.join(script_dir, "links.txt")
    lm={}
    if not os.path.isfile(txt_path):
        print(f"[ERROR] 文件不存在: {txt_path}")
        return lm
    with open(txt_path,"r",encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if not line or line.startswith("#"):continue
            m=re.match(r'^"([^"]+)"\s*:\s*"([^"]+)"\s*,?$',line)
            if m:lm[m.group(1).strip()]=m.group(2).strip()
    return lm
def download_with_progress(url, out_path):
    r=requests.get(url,stream=True);r.raise_for_status()
    total=int(total) if total else 0
    downloaded=0
    with open(out_path,"wb")as f:
        for c in r.iter_content(chunk_size=8192):
            if c:
                f.write(c)
                downloaded+=len(c)
                if total>0:
                    pct=downloaded/total*100
                    print(f"\r下载进度: {downloaded}/{total} ({pct:.2f}%)",end="")
                else:print(f"\r已下载 {downloaded} 字节",end="")
    print()
def download_one(task, jpg_dir, show_progress):
    song_name, url = task
    op = os.path.join(jpg_dir, f"{song_name}.jpg")
    if os.path.exists(op):return None
    tmp = op + ".tmp"
    try:
        if show_progress:
            print(f"\n[INFO] 开始下载: {song_name} -> {url}")
            download_with_progress(url, tmp)
        else:
            requests.get(url, stream=True).raise_for_status(); open(tmp, "wb").write(requests.get(url, stream=True).content)
        im = Image.open(tmp).convert("RGB")
        im.save(op,"JPEG")
        im.close()
        os.remove(tmp)
        return song_name+".jpg"
    except Exception as e:
        if os.path.exists(tmp):os.remove(tmp)
        return f"[ERR]{song_name}: {e}"
def download_all_parallel(links_map):
    jpg_dir = os.path.join(script_dir, "jpgs")
    os.makedirs(jpg_dir,exist_ok=True)
    tasks = list(links_map.items())
    if not tasks:return
    sentinel = os.path.join(script_dir, ".first_download_done")
    show_progress = not os.path.exists(sentinel)
    done_cnt = 0
    from concurrent.futures import ProcessPoolExecutor, as_completed
    with ProcessPoolExecutor() as exe:
        func = partial(download_one, jpg_dir=jpg_dir, show_progress=show_progress)
        fut_map = {exe.submit(func, t):t for t in tasks}
        for fut in as_completed(fut_map):
            if fut.result():
                done_cnt += 1
                if show_progress:print("[OK]", fut.result())
    if done_cnt>0 and show_progress:
        with open(sentinel,"w") as f:
            f.write("downloaded.\n")
def calcUserRealityTimeline(user_archive, history):
    """
    1. 遍历用户存档，按“曲名||难度”去重，取最高成绩并按 singleRealityRaw 降序排序，取前20个为 b20，20之后的为 b21。
    2. 遍历历史记录并计算单曲 Reality，查找与 b20 内曲目匹配的成绩，逐步更新 b20。
    3. 最终生成多个时间点和 user reality 值。
    """
    # ① 用户存档去重：根据曲名和难度生成唯一标识，取最高成绩。
    user_best = {}
    for rec in user_archive:
        key = rec["name"] + "||" + rec["category"]
        if key not in user_best or rec["singleRealityRaw"] > user_best[key]["singleRealityRaw"]:
            user_best[key] = rec
    sorted_user = sorted(user_best.values(), key=lambda r: r["singleRealityRaw"], reverse=True)
    # b20为前20，若不足20则补空（以 None 表示，空成绩视为 0）
    b20 = sorted_user[:20]
    if len(b20) < 20:
        b20.extend([None]*(20 - len(b20)))
    candidate_b21 = sorted_user[20] if len(sorted_user) > 20 else None

    # ② 历史记录：根据 chart_id 生成曲目名称并计算 reality
    for rec in history:
        song_name = csts.get(rec["chart_id"], {}).get("name", rec["chart_id"])
        rec["song"] = song_name
        rec["singleRealityRaw"] = rec.get("singleRealityRaw", 0) + csts.get(rec["chart_id"], {}).get("constant", 0)

    history_backup = sorted(history, key=lambda r: r["singleRealityRaw"], reverse=True)

    timeline = []
    while True:
        # 查找 b20 内的曲目，并从历史记录中找到与之对应的最高成绩
        b20_songs = {rec["name"] for rec in b20 if rec is not None}
        bn = None
        bn_index = None
        for idx, rec in enumerate(history_backup):
            if rec["song"] in b20_songs:
                bn = rec
                bn_index = idx
                break
        if bn is None:
            break  # 没有更多的记录可以替换

        # 找到对应的 b20 曲目
        bn_pos = None
        for i, rec in enumerate(b20):
            if rec is not None and rec["name"] == bn["song"]:
                bn_pos = i
                break
        if bn_pos is None:
            # 若没找到（理论上不该发生），继续扫描下一条记录
            history_backup = history_backup[:bn_index]
            continue

        # 获取该记录后的下一条历史记录（如果有）
        rec2 = history_backup[bn_index + 1] if bn_index + 1 < len(history_backup) else None

        # 判断替换规则
        replacement = None
        if rec2 is not None and rec2["song"] not in b20_songs and rec2["singleRealityRaw"] != bn["singleRealityRaw"]:
            if candidate_b21 is not None:
                replacement = candidate_b21 if candidate_b21["singleRealityRaw"] >= rec2["singleRealityRaw"] else rec2
            else:
                replacement = rec2
        else:
            if candidate_b21 is not None:
                replacement = candidate_b21
            else:
                replacement = None

        # 替换操作
        if replacement is None:
            # 直接将该位置置为 None
            b20[bn_pos] = None
            # 更新当前的 reality，并保存时间点
            current_total = sum(rec["singleRealityRaw"] if rec is not None else 0 for rec in b20)
            current_reality = current_total / 20.0
            timeline.append((bn["played_at"], current_reality))
        else:
            # 替换为新记录
            b20[bn_pos] = replacement
            current_total = sum(rec["singleRealityRaw"] if rec is not None else 0 for rec in b20)
            current_reality = current_total / 20.0
            timeline.append((replacement["played_at"], current_reality))
            # 如果使用了候补 b21，则更新候补为下一个
            if replacement == candidate_b21:
                try:
                    idx_candidate = sorted_user.index(candidate_b21)
                    candidate_b21 = sorted_user[idx_candidate + 1]
                except:
                    candidate_b21 = None

        # 删除 bn 及其之后的历史记录
        history_backup = history_backup[:bn_index]

    # 按时间升序排序时间点
    timeline.sort(key=lambda t: t[0])
    return timeline


# ----------------------------
# 计算用户的 Reality 变化时间线
def calcUserRealityTimelineNew(db_path, user_archive):
    """
    读取 data.db 中历史记录，计算每条记录的 singleRealityRaw，并生成用户的 Reality 变化时间线
    """
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT chart_id, score, played_at FROM scores")
            rows = cursor.fetchall()
        if not rows:
            print("[WARN] 没有从 data.db 中读取到数据")
            return []
        history = []
        for r in rows:
            chart_id = str(r[0])
            score = int(r[1]) if r[1] is not None else 0
            played_at = str(r[2]) if r[2] is not None else "Unknown"
            try:
                played_at_dt = datetime.datetime.strptime(played_at, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                print(f"[ERROR] 时间格式错误: {played_at}")
                continue
            constant = csts.get(chart_id, {}).get("constant", 0)
            rlt = reality(score) or 0
            singleRealityRaw = rlt + constant
            history.append({
                "chart_id": chart_id,
                "played_at": played_at_dt,
                "score": score,
                "constant": constant,
                "singleRealityRaw": singleRealityRaw
            })
        print("\n[INFO] 读取 data.db 历史记录:")
        for record in sorted(history, key=lambda x: x["played_at"], reverse=True):
            print(f"Song: {record['song']}, Played At: {record['played_at']}, "
                  f"Score: {record['score']}, Constant: {record['constant']}, "
                  f"Reality: {record['singleRealityRaw']}")
        # 使用历史记录和用户存档生成 Reality 变化时间线
        timeline = calcUserRealityTimeline(user_archive, history)
        for t, r in timeline:
            print(f"Time: {t}, Reality: {r:.4f}")
        return timeline
    except sqlite3.Error as e:
        print(f"[ERROR] Database error: {e}")
    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")
    return []

# ----------------------------
# 绘制用户 Reality 变化折线图
def drawUserInfo(user_reality_timeline, uname, outPath):
    if not user_reality_timeline:
        print("[WARN] 用户 Reality 变化曲线数据为空")
        return
    W, H = 1200, 600
    can = Image.new("RGBA", (W, H), (0,0,0,255))
    dr = ImageDraw.Draw(can)
    font_path = os.path.join(script_dir, "fonts", "NotoSansCJK-Regular.ttc")
    f_title = ImageFont.truetype(font_path, 40, index=2)
    f_labels = ImageFont.truetype(font_path, 24, index=2)
    timestamps = [t for t, _ in user_reality_timeline]
    reality_values = [r for _, r in user_reality_timeline]
    min_time, max_time = min(timestamps), max(timestamps)
    min_reality, max_reality = min(reality_values), max(reality_values)
    px_margin, py_margin = 100, 80
    plot_width, plot_height = W - 2*px_margin, H - 2*py_margin
    def scale_x(time_point):
        return px_margin + (time_point - min_time).total_seconds() / (max_time - min_time).total_seconds() * plot_width
    def scale_y(reality_val):
        return H - py_margin - (reality_val - min_reality) / (max_reality - min_reality) * plot_height
    grid_color = (100,100,100,200)
    for i in range(6):
        y = H - py_margin - i*(plot_height//5)
        dr.line([(px_margin, y), (W-px_margin, y)], fill=grid_color, width=1)
    prev_xy = None
    for t, r in user_reality_timeline:
        x, y = scale_x(t), scale_y(r)
        dr.ellipse((x-5, y-5, x+5, y+5), fill=(255,255,255,255))
        if prev_xy:
            dr.line([prev_xy, (x, y)], fill=(0,150,255,255), width=3)
        prev_xy = (x, y)
    dr.text((W//2-150, 20), f"User Reality Progression - {uname}", fill=(255,255,255), font=f_title)
    dr.text((px_margin-60, py_margin-10), f"{max_reality:.2f}", fill=(255,255,255), font=f_labels)
    dr.text((px_margin-60, H-py_margin-20), f"{min_reality:.2f}", fill=(255,255,255), font=f_labels)
    dr.text((W-px_margin-80, H-py_margin+10), max_time.strftime("%Y-%m-%d"), fill=(255,255,255), font=f_labels)
    dr.text((px_margin, H-py_margin+10), min_time.strftime("%Y-%m-%d"), fill=(255,255,255), font=f_labels)
    can.convert("RGB").save(outPath, "PNG")
def download_with_progress(url, out_path):
    r=requests.get(url,stream=True);r.raise_for_status()
    total=int(total) if total else 0
    downloaded=0
    with open(out_path,"wb")as f:
        for c in r.iter_content(chunk_size=8192):
            if c:
                f.write(c)
                downloaded+=len(c)
                if total>0:
                    pct=downloaded/total*100
                    print(f"\r下载进度: {downloaded}/{total} ({pct:.2f}%)",end="")
                else:print(f"\r已下载 {downloaded} 字节",end="")
    print()
def download_one(task, jpg_dir, show_progress):
    song_name, url = task
    op = os.path.join(jpg_dir, f"{song_name}.jpg")
    if os.path.exists(op):return None
    tmp = op + ".tmp"
    try:
        if show_progress:
            print(f"\n[INFO] 开始下载: {song_name} -> {url}")
            download_with_progress(url, tmp)
        else:
            requests.get(url, stream=True).raise_for_status(); open(tmp, "wb").write(requests.get(url, stream=True).content)
        im = Image.open(tmp).convert("RGB")
        im.save(op,"JPEG")
        im.close()
        os.remove(tmp)
        return song_name+".jpg"
    except Exception as e:
        if os.path.exists(tmp):os.remove(tmp)
        return f"[ERR]{song_name}: {e}"
def main():
    args = sys.argv[1:]
    # 第一个数字参数为 drawLevel
    drawLevel = int(args.pop(0)) if args and args[0].isdigit() else 0
    # 第二个数字参数为 drawCount
    drawCount = int(args.pop(0)) if args and args[0].isdigit() else 22
    save_json_path = os.path.join(script_dir, "save.json")
    save_txt_path  = os.path.join(script_dir, "save.txt")
    save_db_path   = os.path.join(script_dir, "saves.db")
    user_specified_path = args[0] if args else None
    download_all_parallel(load_links())
    # 依次尝试读取存档文件（用户指定、saves.db、save.txt、save.json）
    paths = [p for p in [user_specified_path, save_db_path, save_txt_path, save_json_path] if p]
    its, uname = None, None
    for path in paths:
        if its or not os.path.exists(path):
            continue
        try:
            fn = os.path.basename(path).lower()
            if fn.endswith(".db"):
                uname, its = pdb(path)
            else:
                with open(path, "rb") as f:
                    cont = f.read()
                s = cont.decode("utf-8", "replace")
                if fn.endswith(".json"):
                    i = s.find('{"UserName":')
                    j = s.find("]}]", i)
                    raw = s[:j+3] + "}" if (i >= 0 and j >= 0) else s
                elif fn.endswith(".xml"):
                    raw = pXML(s)
                elif fn == "prefs":
                    raw = pPrefs(s)
                elif fn.endswith(".plist"):
                    raw = pPlist(cont)
                elif fn.endswith(".reg"):
                    raw = regFile(s)
                else:
                    raw = s
                uname, its = pData(raw)
            if its:
                break
        except Exception as e:
            print(f"[ERROR] 解析 {os.path.splitext(os.path.basename(path))[1].upper()} 存档文件失败: {e}")
    if not its:
        print("[ERROR] 无法解析存档数据")
        return
    its.sort(key=lambda x: x["singleRealityRaw"], reverse=True)
    valid = [x["singleRealityRaw"] for x in its if x["singleRealityRaw"] > 0]
    user_reality = (sum(sorted(valid, reverse=True)[:20]) / 20) if len(valid) >= 20 else 0
    # 如果用户指定的存档为 .db，则同目录下存在 data.db 时调用新算法生成历史曲线
    if user_specified_path and user_specified_path.endswith(".db"):
        data_db_path = os.path.join(os.path.dirname(user_specified_path), "data.db")
        if os.path.exists(data_db_path):
            user_reality_timeline = calcUserRealityTimelineNew(data_db_path, its)
            if user_reality_timeline:
                user_info_outPath = os.path.join(script_dir, f"user_info_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                drawUserInfo(user_reality_timeline, uname, user_info_outPath)
                print("[OK] 用户 Reality 变化曲线已生成:", user_info_outPath)
    outPath = os.path.join(script_dir, "output_py_%s.png" % datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    drawImg(its, uname, user_reality, outPath, min(drawCount, len(its)), drawLevel)
    print("[OK] 完成，图像输出:", outPath)

if __name__ == "__main__":
    main()
