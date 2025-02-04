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
    
    # 绘制用户折线图
    data_db_path = os.path.join(script_dir, "data.db")
    if os.path.exists(data_db_path):
        try:
            user_reality_timeline = calcUserRealityTimelineNew(data_db_path, its)
            if user_reality_timeline:
                # 创建折线图区域
                timeline_img = Image.new("RGBA", (200, 100), (0, 0, 0, 0))  # 200x100的透明背景
                timeline_dr = ImageDraw.Draw(timeline_img)

                # 画折线图
                timestamps = [datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S") for t, _ in user_reality_timeline]
                reality_values = [r for _, r in user_reality_timeline]

                min_time, max_time = min(timestamps), max(timestamps)
                min_reality, max_reality = min(reality_values), max(reality_values)

                def scale_x(time_point):
                    time_diff = (max_time - min_time).total_seconds()
                    if time_diff == 0:
                        return 0
                    return (time_point - min_time).total_seconds() / time_diff * 200

                def scale_y(reality_val):
                    return 100 - (reality_val - min_reality) / (max_reality - min_reality) * 100

                prev_xy = None
                for t, r in zip(timestamps, reality_values):
                    x, y = scale_x(t), scale_y(r)
                    if prev_xy:
                        timeline_dr.line([prev_xy, (x, y)], fill=(173, 216, 230, 128), width=3)  # 浅蓝色，半透明
                    prev_xy = (x, y)

                can.paste(timeline_img, (950, 10), timeline_img)  # 将折线图粘贴到指定位置 (950,10)

        except Exception as e:
            print(f"[ERROR] 绘制折线图失败: {e}")

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
    ureality = sum([score['singleRealityRaw'] for score in sorted(user_archive, key=lambda x: x['singleRealityRaw'], reverse=True)[:20]]) / 20
    e=[]
    sorted_history=history
    while sorted_history:
        sorted_history = sorted(sorted_history, key=lambda x: x['played_at'], reverse=True)
        #寻找最新位于b20中的历史记录
        b20 = sorted(user_archive, key=lambda x: x['singleRealityRaw'], reverse=True)[:20]
        i=-1
        lg_bn=None
        bn=None
        for lg_score in sorted_history:
            for bnn in b20:
                if (lg_score["name"] == bnn["name"] and lg_score["category"] == bnn["category"] and lg_score["score"] == bnn["bestScore"]):
                    bn=bnn;break
            if bn:lg_bn=lg_score;break
        if not bn:break
        t=lg_bn['played_at']
        sorted_history = [r for r in sorted_history if r['played_at'] <= t]
        sorted_history = sorted(sorted_history, key=lambda x: x['singleRealityRaw'], reverse=True)
        ii=0
        #寻找可进b的记录
        for idx in range(1, len(sorted_history)):
            record = sorted_history[idx]
            if (record["singleRealityRaw"] != bn["singleRealityRaw"]):ii=1
            elif (record["name"] != bn["name"] and record["category"] != bn["category"]):ii=1
            if ii==1:#防止重复
                for bnn in b20:
                    if not((record["name"] == bnn["name"] and record["category"] == bnn["category"] and record["score"] == bnn["bestScore"])):break
                    else:ii=0
            if ii==1:break
        user_archive.remove(bn)
        user_archive.append({"category":record['category'],"name":record['name'],"bestScore":record['score'],"singleRealityRaw":record['singleRealityRaw']})
        ureality = sum([score['singleRealityRaw'] for score in sorted(user_archive, key=lambda x: x['singleRealityRaw'], reverse=True)[:20]]) / 20
        e.append((t,ureality))
    return(e)




def calcUserRealityTimelineNew(db_path, user_archive):
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT chart_id, modifiers, grade, score, score_accuracy, score_exact_count, score_perfect_count, score_good_count, score_bad_count, score_miss_count, played_at FROM scores")
            rows = cursor.fetchall()
        if not rows:
            print("[WARN] 没有从 data.db 中读取到数据")
            return []

        history = []
        for r in rows:
            chart_id = str(r[0])
            modifiers = str(r[1])
            grade = str(r[2])
            score = int(r[3])
            score_accuracy = float(r[4])
            score_exact_count = int(r[5])
            score_perfect_count = int(r[6])
            score_good_count = int(r[7])
            score_bad_count = int(r[8])
            score_miss_count = int(r[9])
            played_at = str(r[10])

            constant = csts.get(chart_id, {}).get("constant", 0)
            category = csts.get(chart_id, {}).get("category", 0)
            name = csts.get(chart_id, {}).get("name", 0)
            rlt = reality(score) or 0
            singleRealityRaw = rlt + constant

            history.append({
                "chart_id": chart_id,
                "name": name,
                "category": category,
                "modifiers": modifiers,
                "grade": grade,
                "score": score,
                "score_accuracy": score_accuracy,
                "score_exact_count": score_exact_count,
                "score_perfect_count": score_perfect_count,
                "score_good_count": score_good_count,
                "score_bad_count": score_bad_count,
                "score_miss_count": score_miss_count,
                "constant": constant,
                "played_at": played_at,
                "singleRealityRaw": singleRealityRaw
            })

        print("\n[INFO] 读取 data.db 历史记录:")
        for record in sorted(history, key=lambda x: x["played_at"], reverse=True):
            print(f"Song: {record['name']}_{record['category']}, Played At: {record['played_at']}, "
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

def drawUserInfo(user_reality_timeline, uname, outPath):
    if not user_reality_timeline:
        print("[WARN] 用户 Reality 变化曲线数据为空")
        return

    W, H = 1200, 600
    can = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    dr = ImageDraw.Draw(can)

    # 加载字体
    font_path = os.path.join(script_dir, "fonts", "NotoSansCJK-Regular.ttc")
    f_title = ImageFont.truetype(font_path, 40, index=2)
    f_labels = ImageFont.truetype(font_path, 24, index=2)

    # 将时间戳字符串转换为 datetime 对象
    timestamps = [datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S") for t, _ in user_reality_timeline]
    reality_values = [r for _, r in user_reality_timeline]

    # 计算最小时间和最大时间，用于归一化
    min_time, max_time = min(timestamps), max(timestamps)
    min_reality, max_reality = min(reality_values), max(reality_values)

    # 如果时间差为零，直接退出绘制
    if min_time == max_time:
        print("[ERROR] 所有时间戳相同，无法绘制图表。")
        return

    # 设置边距和绘图区域的尺寸
    px_margin, py_margin = 100, 80
    plot_width, plot_height = W - 2 * px_margin, H - 2 * py_margin

    # 归一化时间戳和 Reality 值，使其适应绘图区域
    def scale_x(time_point):
        # 处理除零错误
        time_diff = (max_time - min_time).total_seconds()
        if time_diff == 0:
            return px_margin  # 如果时间差为零，返回左边距作为默认值
        return px_margin + (time_point - min_time).total_seconds() / time_diff * plot_width

    def scale_y(reality_val):
        return H - py_margin - (reality_val - min_reality) / (max_reality - min_reality) * plot_height

    # 绘制网格线
    grid_color = (100, 100, 100, 200)
    for i in range(6):
        y = H - py_margin - i * (plot_height // 5)
        dr.line([(px_margin, y), (W - px_margin, y)], fill=grid_color, width=1)

    # 绘制 Reality 变化的折线图
    prev_xy = None
    for t, r in zip(timestamps, reality_values):  # 使用转换后的时间戳
        x, y = scale_x(t), scale_y(r)
        dr.ellipse((x - 5, y - 5, x + 5, y + 5), fill=(255, 255, 255, 255))  # 绘制点
        if prev_xy:
            dr.line([prev_xy, (x, y)], fill=(0, 150, 255, 255), width=3)  # 绘制点与点之间的连线
        prev_xy = (x, y)

    # 添加标题和标签
    dr.text((W // 2 - 150, 20), f"User Reality Progression - {uname}", fill=(255, 255, 255), font=f_title)
    dr.text((px_margin - 60, py_margin - 10), f"{max_reality:.2f}", fill=(255, 255, 255), font=f_labels)
    dr.text((px_margin - 60, H - py_margin - 20), f"{min_reality:.2f}", fill=(255, 255, 255), font=f_labels)
    dr.text((W - px_margin - 80, H - py_margin + 10), max_time.strftime("%Y-%m-%d"), fill=(255, 255, 255), font=f_labels)
    dr.text((px_margin, H - py_margin + 10), min_time.strftime("%Y-%m-%d"), fill=(255, 255, 255), font=f_labels)

    # 保存生成的图片
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
