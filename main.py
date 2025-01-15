#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, re, json, base64, plistlib, math, datetime, urllib.parse
from xml.etree import ElementTree as ET
from PIL import Image, ImageDraw, ImageFont

# 加载常量
def load_c():
    d = {}
    try:
        with open("./beatmapid字典.txt","r",encoding="utf-8") as f:
            for ln in f:
                ln=ln.strip()
                if not ln or ln.startswith("#"):continue
                m=re.match(r'"([^"]+)":\s*\{\s*constant:\s*([-\d\.]+)\s+category:\s*"([^"]+)"\s+name:\s*"([^"]+)"\s*\},?',ln)
                if m:
                    d[m.group(1)]={"constant":float(m.group(2)),"category":m.group(3),"name":m.group(4)}
    except:pass
    return d
csts=load_c()

# 分数计算
def reality(score):
    if score>=1005000:return 1
    if score>=995000:return 1.4/(math.exp(-3.65*(score/10000-99.5))+1)-0.4
    if score>=980000:return((math.exp(3.1*(score-980000)/15000)-1)/(math.exp(3.1)-1))*0.8-0.5
    if score>=700000:return score/280000-4

# 尝试解析JSON
def tJ(s):
    try:return json.loads(s)
    except:return None

# 提取 reg
def regFile(s):
    m=re.search(r'"PlayerFile(?:_h\d+)?"\s*=\s*hex:((?:[0-9a-fA-F]{2},?[\s\\\n]*)+)',s)
    if m:
        hd=re.sub(r"[,\\\s\n]","",m.group(1))
        return "".join(chr(int(hd[i:i+2],16))for i in range(0,len(hd),2))
    return ""

# 处理 plist
def pPlist(b):
    try:
        pd=plistlib.loads(b)
        if "PlayerFile" in pd:
            d=pd["PlayerFile"]
            if isinstance(d,str):
                try:json.loads(d);return d
                except:pass
    except:pass
    return ""

# 处理 XML
def pXML(s):
    try:
        root=ET.fromstring(s)
        n=root.find(".//string[@name='PlayerFile']")
        if n is not None and n.text:return urllib.parse.unquote(n.text)
    except:pass
    return ""

# 处理 Prefs
def pPrefs(s):
    try:
        for n in ET.fromstring(s).iter("pref"):
            if n.get("name")=="PlayerFile"and n.get("type")=="string":
                return base64.b64decode(n.text or "").decode("utf-8","replace")
    except:pass
    return ""

# 判断新旧格式
def isNewF(d):
    return bool(re.match(r"^\[.*?\],\{.*?\}$",d.strip(),re.DOTALL))

# 解析数据
def pData(raw):
    if not raw.strip():return None,[]
    return pNew(raw) if isNewF(raw) else pOld(raw)

# 新格式
def pNew(s):
    try:
        m=re.match(r"^\[(.*?)\],\{(.*)\}$",s,re.DOTALL)
        if not m:return None,[]
        u=m.group(1)
        sd=m.group(2)
        its=[]
        for song in re.findall(r"\[.*?\]",sd,re.DOTALL):
            ps=psN(song)
            if ps:its.append(ps)
        return u,its
    except:return None,[]

# 处理单曲(新)
def psN(s):
    try:
        arr=s.strip("[]").split(",")
        if len(arr)<6:return
        t,c,co,sc,ac,l=arr
        co,sc,ac,l=float(co),int(sc),float(ac),int(l)
        r=reality(sc)
        sr=(r+co)if r else 0
        return{"name":t.strip(),"category":c.strip(),"constant":co,"bestScore":sc,
               "bestAccuracy":ac,"bestLevel":l,"singleRealityRaw":sr}
    except:return

# 旧格式
def pOld(s):
    i=s.find('{"UserName":')
    j=s.find("}]}",i)
    if i<0 or j<0:return None,[]
    j+=3
    d=tJ(s[i:j])
    if not d or"SongRecords"not in d:return None,[]
    u=d.get("UserName")
    its=[]
    for r in d["SongRecords"]:
        pr=psO(r)
        if pr:its.append(pr)
    return u,its

# 处理单曲(旧)
def psO(r):
    b=r.get("BeatmapID")
    if(not b)or(b not in csts):return
    c=csts[b]
    sc=r.get("BestScore",0)
    ac=r.get("BestAccuracy",0.0)
    lv=r.get("BestLevel",0)
    rr=reality(sc)
    return{"name":c["name"],"category":c["category"],"constant":c["constant"],
           "bestScore":sc,"bestAccuracy":ac,"bestLevel":lv,
           "singleRealityRaw":(rr+c["constant"]) if rr else 0}

# 计算平均Reality
def avgR(its):
    arr=sorted([x["singleRealityRaw"]for x in its if x["singleRealityRaw"]>0],reverse=True)
    return sum(arr[:20])/20 if arr[:20] else 0

# 处理文件
def hF(b,fn):
    fn=fn.lower()
    s=b.decode("utf-8","replace")
    if fn.endswith(".json"):
        i=s.find('{"UserName":')
        j=s.find("]}]",i)
        return s[: j+3]+"}" if (i>=0 and j>=0) else s
    elif fn.endswith(".xml"):return pXML(s)
    elif fn=="prefs":return pPrefs(s)
    elif fn.endswith(".plist"):return pPlist(b)
    elif fn.endswith(".reg"):return regFile(s)
    return s

# 绘图
def drawImg(its,uname,uR,outp,drawCount):
    sd=os.path.dirname(os.path.abspath(__file__))
    scale=1.3
    cardW,cardH=int(340*scale),int(100*scale)
    imgW,imgH=int(142*scale),int(80*scale)
    xOff,yOff=110,350
    colSp,rowSp=int(400*scale),int(125*scale)
    rows=(drawCount+1)//2
    baseRows=11
    # 若超出默认22则增加高度
    if drawCount<=22:H=2200
    else:H=2200+(rows-baseRows)*rowSp
    W=1200
    can=Image.new("RGBA",(W,H),(0,0,0,255))
    dr=ImageDraw.Draw(can)
    bgp=os.path.join(sd,"jpgs","查分图.jpg")
    if os.path.exists(bgp):
        bg=Image.open(bgp).convert("RGBA").resize((W,H))
        can.paste(bg,(0,0))
    else:dr.rectangle([(0,0),(W,H)],fill=(0,0,0,255))
    ov=Image.new("RGBA",(W,200),(128,128,128,int(0.3*255)))
    can.paste(ov,(0,50),ov)
    dr.line([(550,250),(650,50)],fill=(255,255,255,int(0.8*255)),width=3)
    fp=os.path.join(sd,"fonts","NotoSansCJK-Regular.ttc")
    f25=ImageFont.truetype(fp,25,index=2)
    f30=ImageFont.truetype(fp,30,index=2)
    f50=ImageFont.truetype(fp,50,index=2)
    dr.text((660,80),"Player: "+str(uname),fill=(255,255,255),font=f25)
    dr.text((660,130),"Reality: "+str(round(uR,4)),fill=(255,255,255),font=f25)
    dr.text((660,180),"Date: "+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            fill=(255,255,255),font=f25)
    dr.text((100,90),"Reality查分器v3.0",fill=(255,255,255),font=f50)
    dr.text((100,160),"http://k9.lv/c/",fill=(255,255,255),font=f30)
    cImgs=[]
    for i in range(drawCount):
        nm=its[i]["name"]
        ip=os.path.join(sd,"jpgs",nm+".jpg")
        if not os.path.exists(ip):ip=os.path.join(sd,"jpgs","NYA.jpg")
        try:cImgs.append(Image.open(ip).convert("RGBA"))
        except:cImgs.append(Image.new("RGBA",(142,80),(100,100,100,255)))
    fN=ImageFont.truetype(fp,int(13*scale),index=2)
    fS=ImageFont.truetype(fp,int(30*scale),index=2)
    fR=ImageFont.truetype(fp,int(15*scale),index=2)
    def draw_gradient_txt(cv,xy,txt,ft,tc,bc):
        d=ImageDraw.Draw(cv)
        bb=d.textbbox((0,0),txt,font=ft)
        tw,th=bb[2]-bb[0],bb[3]-bb[1]
        g=Image.new("RGBA",(tw,th))
        for y in range(th):
            r=int(tc[0]*(1-y/(th-1))+bc[0]*(y/(th-1)))if th>1 else tc[0]
            gg=int(tc[1]*(1-y/(th-1))+bc[1]*(y/(th-1)))if th>1 else tc[1]
            bbb=int(tc[2]*(1-y/(th-1))+bc[2]*(y/(th-1)))if th>1 else tc[2]
            for x in range(tw):g.putpixel((x,y),(r,gg,bbb,255))
        mk=Image.new("L",(tw,th),0)
        ImageDraw.Draw(mk).text((-bb[0],-bb[1]),txt,font=ft,fill=255)
        g.putalpha(mk)
        cv.alpha_composite(g,dest=(xy[0]-bb[0],xy[1]-bb[1]))
    def dtb(d,x,y,txt,ft,fl):
        b=d.textbbox((0,0),txt,font=ft)
        d.text((x,y-(b[3]-b[1])),txt,font=ft,fill=fl)
    for i in range(drawCount):
        x=xOff+(i%2)*colSp
        y=yOff+(i//2)*rowSp-(50 if i%2==0 else 0)
        bg=Image.new("RGBA",(cardW,cardH),(128,128,128,int(0.4*255)))
        can.paste(bg,(x,y),bg)
        numT="#"+str(i+1)
        nb=dr.textbbox((0,0),numT,font=fN)
        dr.text((x+cardW-10-(nb[2]-nb[0]),y+int(scale)),numT,
                fill=(250,250,250) if i<20 else (201,201,201),font=fN)
        scT=str(its[i]["bestScore"]).zfill(7)
        scPos=(int(x+160*scale),int(y+53*scale))
        lv=its[i]["bestLevel"]
        if lv<2:draw_gradient_txt(can,scPos,scT,fS,(0x99,0xC5,0xFB),(0xD8,0xC3,0xFA))
        else:dtb(dr,scPos[0],scPos[1],scT,fS,(144,202,239) if lv==2 else (255,255,255))
        sn=its[i]["name"]
        fw=int(19*scale)
        fSong=ImageFont.truetype(fp,fw,index=2)
        while dr.textbbox((0,0),sn,font=fSong)[2]>200 and fw>10:
            fw-=1;fSong=ImageFont.truetype(fp,fw,index=2)
        dtb(dr,int(x+163*scale),int(y+28*scale),sn,fSong,(255,255,255))
        rt="%s %.1f > %.2f   %.2f%%"%(its[i]['category'],its[i]['constant'],
                                      its[i]['singleRealityRaw'],its[i]['bestAccuracy']*100)
        dtb(dr,int(x+160*scale),int(y+80*scale),rt,fR,(255,255,255))
        ci=cImgs[i].resize((imgW,imgH))
        can.paste(ci,(int(x+10*scale),int(y+10*scale)))
    can.convert("RGB").save(outp,"PNG")

def main():
    sd=os.path.dirname(os.path.abspath(__file__))
    args=sys.argv[1:]
    # 默认配置
    drawCount=22
    savePath=os.path.join(sd,"save.json") if os.path.exists(os.path.join(sd,"save.json")) \
             else os.path.join(sd,"save.txt")
    outPath=os.path.join(sd,"output_py_%s.png"%datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
    
    # 第1参数若是数字，则作为drawCount
    idx=0
    if len(args)>0 and args[0].isdigit():
        drawCount=int(args[0]);idx=1
    
    # 第2参数若存在，则作为存档路径
    if len(args)>idx:
        sp=args[idx]
        if os.path.exists(sp):
            savePath=sp
        idx+=1

    # 第3参数若存在，则判断是目录还是文件
    if len(args)>idx:
        p=args[idx]
        if os.path.isdir(p):
            outPath=os.path.join(p,"output_py_%s.png"%datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
        else:
            # 上级目录不存在就不处理，默认逻辑
            dirp=os.path.dirname(p)
            if dirp=="" or os.path.isdir(dirp):
                outPath=p
    
    # 读文件并解析
    try:
        with open(savePath,"rb")as f:cont=f.read()
    except:
        print(f"[ERROR] 存档文件不存在: {savePath}")
        return
    raw=hF(cont,os.path.basename(savePath))
    uname,its=pData(raw)
    if not its:
        print("[ERROR] 无效数据");return
    its.sort(key=lambda x:x["singleRealityRaw"],reverse=True)
    uR=avgR(its)
    mI=min(drawCount,len(its))  # 实际要绘制的曲目数
    drawImg(its,uname,uR,outPath,mI)
    print("[OK] 完成，图像输出:",outPath)

if __name__=="__main__":
    main()
