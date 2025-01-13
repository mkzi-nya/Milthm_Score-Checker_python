#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, re, json, base64, plistlib, math, datetime
from xml.etree import ElementTree as ET
from PIL import Image, ImageDraw, ImageFont

# 从文件加载常量字典
def load_constants():
    d = {}
    try:
        with open("./beatmapid字典.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"): continue
                m = re.match(r'"([^"]+)":\s*\{\s*constant:\s*([-\d\.]+)\s+category:\s*"([^"]+)"\s+name:\s*"([^"]+)"\s*\},?', line)
                if m:
                    key = m.group(1)
                    d[key] = {"constant": float(m.group(2)),
                              "category": m.group(3),
                              "name": m.group(4)}
    except Exception as e:
        print(f"[ERROR] 加载常量失败: {e}")
    return d

constants = load_constants()

# 分数计算
def reality(score: int):
    if score >= 1005000: return 1
    if score >= 995000: return 1.4/(math.exp(-3.65*(score/10000-99.5))+1)-0.4
    if score >= 980000: return ((math.exp(3.1*(score-980000)/15000)-1)/(math.exp(3.1)-1))*0.8-0.5
    if score >= 700000: return score/280000-4
    return None

# 存档解析函数
def tryParseJSON(data: str): 
    try: return json.loads(data)
    except: return None
def processRegFile(s: str):
    m = re.search(r'"PlayerFile(_h\d+)?"\s*=\s*hex:((?:[0-9a-fA-F]{2}[,\s\\\n]*)+)', s)
    if not m: 
        print("[DEBUG] 未找到 PlayerFile 字段"); return ""
    hexStr = re.sub(r'[,\s\\\n]', '', m.group(2))
    return "".join(chr(int(hexStr[i:i+2],16)) for i in range(0,len(hexStr),2))
def processPlistFile(content: str):
    try:
        data = plistlib.loads(content.encode("utf-8")) if content.startswith("<?xml") else plistlib.loads(content)
        return base64.b64decode(data["PlayerFile"]).decode("utf-8","replace") if "PlayerFile" in data else (print("[DEBUG] plist 文件中未找到 PlayerFile 字段") or "")
    except Exception as e:
        print(f"[ERROR] 解析 plist 文件失败: {e}")
    return ""
def processXMLFile(s: str):
    try:
        for node in ET.fromstring(s).iter("string"):
            if node.get("name")=="PlayerFile": return node.text or ""
    except: pass
    return ""
def processPrefsFile(s: str):
    try:
        for node in ET.fromstring(s).iter("pref"):
            if node.get("name")=="PlayerFile" and node.get("type")=="string":
                return base64.b64decode(node.text or "").decode("utf-8","replace")
    except: pass
    return ""
def isNewFormat(data: str) -> bool: return bool(re.match(r"^\[.*\],\{.*\}$",data))
def processData(raw: str): return processNewFormat(raw) if isNewFormat(raw) else processOldFormat(raw)
def processNewFormat(s: str):
    m = re.match(r"^\[(.*?)\],\{(.*)\}$", s)
    if not m: return ("", [])
    username, sd = m.group(1), m.group(2)
    items = [processSong(x) for x in sd.split("],[") if processSong(x)]
    return username, items
def processOldFormat(s: str):
    i = s.find('{"UserName":')
    j = s.find('}]}',i)
    if i<0 or j<0: return ("", [])
    j += 3
    data = tryParseJSON(s[i:j])
    if not data or "SongRecords" not in data: return ("", [])
    return data.get("UserName",""), [processSongOld(r) for r in data["SongRecords"] if processSongOld(r)]
def processSong(s: str):
    arr = s.strip("[]").split(",")
    if len(arr) < 6: return None
    try:
        title, cat = arr[0].strip(), arr[1].strip()
        cst, scr, acc, lvl = float(arr[2]), int(arr[3]), float(arr[4]), int(arr[5])
    except: return None
    r = reality(scr)
    return {"name": title, "category": cat, "constant": cst, "bestScore": scr, "bestAccuracy": acc, "bestLevel": lvl,
            "singleRealityRaw": (r+cst) if r is not None else 0.0}
def processSongOld(rec: dict):
    bID = rec.get("BeatmapID")
    if not bID or bID not in constants: return None
    cdef = constants[bID]
    scr, acc, lvl = rec.get("BestScore",0), rec.get("BestAccuracy",0.0), rec.get("BestLevel",0)
    r = reality(scr)
    return {"name": cdef["name"], "category": cdef["category"], "constant": cdef["constant"],
            "bestScore": scr, "bestAccuracy": acc, "bestLevel": lvl,
            "singleRealityRaw": (r+cdef["constant"]) if r is not None else 0.0}
def extractJSON(s: str):
    i = s.find('{"UserName":')
    j = s.find(']}]',i)
    return None if i<0 or j<0 else s[:j+3]+"}"
def calculateAverageReality(items):
    arr = sorted([it["singleRealityRaw"] for it in items if it["singleRealityRaw"]>0], reverse=True)
    return sum(arr[:20])/20 if arr[:20] else 0.0
def handleFile(content: str, base: str):
    fn = base.lower()
    if fn.endswith(".json"):
        extr = extractJSON(content); return extr if extr else content
    if fn.endswith(".xml"): return processXMLFile(content) or content
    if fn=="prefs": return processPrefsFile(content) or content
    if fn.endswith(".plist"): return processPlistFile(content) or content
    if fn.endswith(".reg"): return processRegFile(content) or content
    return content

# 绘图辅助函数
def draw_text_bottom_left(draw_obj, pos, text, font, fill):
    bbox = draw_obj.textbbox((0,0), text, font=font)
    draw_obj.text((pos[0], pos[1]-(bbox[3]-bbox[1])), text, font=font, fill=fill)
def draw_gradient_text_bottom_left(canvas, pos, text, font, top_color, bottom_color):
    draw_obj = ImageDraw.Draw(canvas)
    bbox = draw_obj.textbbox((0,0), text, font=font); tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    gradient = Image.new("RGBA", (tw,th))
    for y in range(th):
        ratio = y/(th-1) if th>1 else 0
        r = int(top_color[0]*(1-ratio)+bottom_color[0]*ratio)
        g = int(top_color[1]*(1-ratio)+bottom_color[1]*ratio)
        b = int(top_color[2]*(1-ratio)+bottom_color[2]*ratio)
        for x in range(tw): gradient.putpixel((x,y),(r,g,b,255))
    mask = Image.new("L", (tw,th), 0); ImageDraw.Draw(mask).text((-bbox[0], -bbox[1]), text, font=font, fill=255)
    gradient.putalpha(mask)
    canvas.alpha_composite(gradient, dest=(pos[0]-bbox[0], pos[1]-bbox[1]))

# 绘图函数
def drawImage(items, username, userReality, output_path):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    W, H = 1200, 2200; canvas = Image.new("RGBA",(W,H),(0,0,0,255)); draw = ImageDraw.Draw(canvas)
    bg_path = os.path.join(script_dir,"jpgs","查分图.jpg")
    if os.path.exists(bg_path):
        bg = Image.open(bg_path).convert("RGBA").resize((W,H)); canvas.paste(bg,(0,0))
    else: draw.rectangle([(0,0),(W,H)], fill=(0,0,0,255))
    overlay = Image.new("RGBA",(W,200),(128,128,128,int(0.3*255)))
    canvas.paste(overlay,(0,50),overlay)
    draw.line([(550,250),(650,50)], fill=(255,255,255,int(0.8*255)), width=3)
    font_path = os.path.join(script_dir,"fonts","NotoSansCJK-Regular.ttc")
    f25 = ImageFont.truetype(font_path,25,index=2); f30 = ImageFont.truetype(font_path,30,index=2); f50 = ImageFont.truetype(font_path,50,index=2)
    draw_text_bottom_left(draw, (660,100), f"Player: {username}", f25, (255,255,255))
    draw_text_bottom_left(draw, (660,150), f"Reality: {round(userReality,4)}", f25, (255,255,255))
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    draw_text_bottom_left(draw, (660,200), f"Date: {now_str}", f25, (255,255,255))
    draw_text_bottom_left(draw, (100,130), "Reality查分器v3.0", f50, (255,255,255))
    draw_text_bottom_left(draw, (100,180), "http://k9.lv/c/", f30, (255,255,255))
    maxItems = min(22, len(items)); card_images = []
    for i in range(maxItems):
        nm = items[i]["name"]
        img_path = os.path.join(script_dir,"jpgs",f"{nm}.jpg")
        if not os.path.exists(img_path): img_path = os.path.join(script_dir,"jpgs","NYA.jpg")
        try: card_images.append(Image.open(img_path).convert("RGBA"))
        except Exception as e:
            print(f"[DEBUG] 读取图片失败: {img_path}，错误: {e}")
            card_images.append(Image.new("RGBA",(142,80),(100,100,100,255)))
    scale = 1.3; cardW, cardH = int(340*scale), int(100*scale); imgW, imgH = int(142*scale), int(80*scale)
    xOffset, yOffset = 110,350; colSpace, rowSpace = int(400*scale), int(125*scale)
    f_num = ImageFont.truetype(font_path, int(13*scale), index=2)
    f_score = ImageFont.truetype(font_path, int(30*scale), index=2)
    f_reality = ImageFont.truetype(font_path, int(15*scale), index=2)
    for i in range(maxItems):
        x = xOffset + (i%2)*colSpace; y = yOffset + (i//2)*rowSpace - (50 if i%2==0 else 0)
        card_bg = Image.new("RGBA",(cardW,cardH),(128,128,128,int(0.4*255)))
        canvas.paste(card_bg,(x,y),card_bg)
        num_text = f"#{i+1}"
        bbox = draw.textbbox((0,0),num_text,font=f_num); w_num = bbox[2]-bbox[0]
        draw.text((x+cardW-10-w_num,y+int(scale)), num_text, fill=(250,250,250) if i<20 else (201,201,201), font=f_num)
        score_text = str(items[i]["bestScore"]).zfill(7)
        score_pos = (int(x+160*scale), int(y+53*scale)); bLevel = items[i]["bestLevel"]
        if bLevel < 2:
            draw_gradient_text_bottom_left(canvas, score_pos, score_text, f_score, (0x99,0xC5,0xFB), (0xD8,0xC3,0xFA))
        else:
            draw_text_bottom_left(draw, score_pos, score_text, f_score, (144,202,239) if bLevel==2 else (255,255,255))
        song_name = items[i]["name"]; maxTextWidth = 200; font_size = int(19*scale)
        font_song = ImageFont.truetype(font_path, font_size, index=2)
        while (draw.textbbox((0,0),song_name,font=font_song)[2]-draw.textbbox((0,0),song_name,font=font_song)[0] > maxTextWidth) and (font_size>10):
            font_size -= 1; font_song = ImageFont.truetype(font_path, font_size, index=2)
        draw_text_bottom_left(draw, (int(x+163*scale), int(y+28*scale)), song_name, font_song, (255,255,255))
        reality_text = f"{items[i]['category']} {float(items[i]['constant']):.1f} > {float(items[i]['singleRealityRaw']):.2f}   {(float(items[i]['bestAccuracy'])*100):.2f}%"
        draw_text_bottom_left(draw, (int(x+160*scale), int(y+80*scale)), reality_text, f_reality, (255,255,255))
        card_img = card_images[i].resize((imgW,imgH))
        canvas.paste(card_img,(int(x+10*scale), int(y+10*scale)))
    canvas.convert("RGB").save(output_path, "PNG")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    args = sys.argv[1:]
    save_path = args[0] if args else (os.path.join(script_dir,"save.json") if os.path.exists(os.path.join(script_dir,"save.json")) else os.path.join(script_dir,"save.txt"))
    if not os.path.exists(save_path):
        print(f"[ERROR] 存档文件不存在: {save_path}")
        return
    output_path = args[1] if len(args)>1 else os.path.join(script_dir, f"output_py_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
    with open(save_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    raw_data = handleFile(content, os.path.basename(save_path))
    username, items = processData(raw_data)
    userReality = calculateAverageReality(items)
    items.sort(key=lambda x: x["singleRealityRaw"], reverse=True)
    drawImage(items, username, userReality, output_path)
    print(f"[OK] 已完成，图像输出到: {output_path}")

if __name__=="__main__":
    main()
