"""Render actual FreeCAD triangulation; no generated concept geometry."""
import json
import math
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent
G = json.loads((OUT / "preview_geometry.json").read_text(encoding="utf-8"))
im = Image.new("RGB", (1600, 1140), "#f5f6f8")
draw = ImageDraw.Draw(im)
font_path = "C:/Windows/Fonts/msyh.ttc"
font = ImageFont.truetype(font_path, 24)
small = ImageFont.truetype(font_path, 20)
title = ImageFont.truetype(font_path, 36)

def dot(a,b): return sum(x*y for x,y in zip(a,b))
def cross(a,b): return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]
def norm(v):
    size = math.sqrt(dot(v,v))
    return [x/size for x in v]

def scene(rect, cam, objects):
    cam = norm(cam)
    right = norm([-cam[1],cam[0],0])
    up = norm(cross(cam,right))
    if cam[2] < 0: up = [-x for x in up]
    faces, allpoints = [], []
    for geo, color, offset in objects:
        vertices = [[p[i]+offset[i] for i in range(3)] for p in geo["vertices"]]
        projected = [(dot(p,right), -dot(p,up)) for p in vertices]
        allpoints.extend(projected)
        for face in geo["faces"]:
            p = [vertices[i] for i in face]
            normal = norm(cross([p[1][i]-p[0][i] for i in range(3)],
                                [p[2][i]-p[0][i] for i in range(3)]))
            # Diffuse shading conveys the real mesh's surfaces.
            intensity = 0.63+0.37*abs(dot(normal,norm([1,-2,3])))
            fill = tuple(round(c*intensity) for c in color)
            faces.append(([dot(v,cam) for v in p],
                          [projected[i] for i in face],fill))
    xmin,ymin = min(p[0] for p in allpoints),min(p[1] for p in allpoints)
    xmax,ymax = max(p[0] for p in allpoints),max(p[1] for p in allpoints)
    x0,y0,x1,y1 = rect
    scale = min((x1-x0)/(xmax-xmin),(y1-y0)/(ymax-ymin))
    dx,dy = (x0+x1)/2-scale*(xmin+xmax)/2,(y0+y1)/2-scale*(ymin+ymax)/2
    # Per-pixel depth avoids painter-order artifacts across overlapping triangles.
    pixels = np.array(im)
    depth = np.full((im.height,im.width),-np.inf)
    for z,p,fill in faces:
        q = [(x*scale+dx,y*scale+dy) for x,y in p]
        lx=max(0,math.floor(min(v[0] for v in q)))
        rx=min(im.width-1,math.ceil(max(v[0] for v in q)))
        ly=max(0,math.floor(min(v[1] for v in q)))
        ry=min(im.height-1,math.ceil(max(v[1] for v in q)))
        (ax,ay),(bx,by),(cx,cy)=q
        denom=(by-cy)*(ax-cx)+(cx-bx)*(ay-cy)
        if abs(denom)<1e-8: continue
        yy,xx=np.mgrid[ly:ry+1,lx:rx+1]
        a=((by-cy)*(xx+0.5-cx)+(cx-bx)*(yy+0.5-cy))/denom
        b=((cy-ay)*(xx+0.5-cx)+(ax-cx)*(yy+0.5-cy))/denom
        c=1-a-b
        candidate=a*z[0]+b*z[1]+c*z[2]
        current=depth[ly:ry+1,lx:rx+1]
        visible=(a>=-1e-6)&(b>=-1e-6)&(c>=-1e-6)&(candidate>current)
        pixels[ly:ry+1,lx:rx+1][visible]=fill
        current[visible]=candidate[visible]
    im.paste(Image.fromarray(pixels))

draw.text((50,30),"富哥方案 · 产品1 / 滑轨固定屏幕 · V2",font=title,fill="#182b3a")
draw.text((50,86),"实际 CAD 模型预览　·　单位 mm　·　111 × 99 × 22.4",font=font,fill="#43586b")
for rect in [(40,140,790,650),(810,140,1560,650),(40,680,1560,1070)]:
    draw.rounded_rectangle(rect,radius=18,fill="white",outline="#d8dfe6",width=2)
draw.text((65,160),"正面：完整显示区，底部留排线空间",font=font,fill="#182b3a")
objects = [(G["front"],(215,225,235),(0,0,0)), (G["back"],(195,210,223),(0,0,0)),
           (G["gate"],(138,185,205),(0,0,0))]
for geo in G["hardware"]:
    objects.append((geo,(242,242,234) if geo["name"]=="ActiveArea" else (90,94,95),(0,0,0)))
scene((75,220,750,610),(1,-1,-2.6),objects)
draw.text((835,160),"两侧导槽＋上挡边，底部是滑入入口",font=font,fill="#182b3a")
scene((840,220,1530,610),(1,-1,2.6),[(G["front"],(215,225,235),(0,0,0))])
draw.text((65,700),"三个打印件：前框、后盖、底部挡条；仍用 4 颗 3×8 mm 自攻螺丝",font=font,fill="#182b3a")
scene((70,770,520,1015),(1,-1,2.6),[(G["front"],(215,225,235),(0,0,0))])
scene((580,770,1020,1015),(1,-1,2.6),[(G["back"],(195,210,223),(0,0,-20))])
scene((1080,810,1515,990),(1,-2,2.6),[(G["gate"],(138,185,205),(0,0,0))])
draw.text((240,1035),"前框",font=small,fill="#43586b")
draw.text((760,1035),"后盖 / 保留 Type-C 凹口",font=small,fill="#43586b",anchor="mm")
draw.text((1290,1035),"底部挡条 / 防止屏幕滑出",font=small,fill="#43586b",anchor="mm")
draw.text((50,1094),"已检查完整滑入路径和限位；导槽有装配间隙，尚未打印试装。",font=small,fill="#43586b")
im.save(OUT / "case-preview.png")

# A close-up of an actual rail cross section plus a partly inserted screen.
im = Image.new("RGB",(1600,900),"#f5f6f8")
draw = ImageDraw.Draw(im)
draw.text((50,30),"屏幕如何滑入与固定",font=title,fill="#182b3a")
draw.text((50,90),"先滑入屏幕，再从同一个底部入口推入挡条并锁螺丝",font=font,fill="#43586b")
for rect in [(40,145,790,790),(810,145,1560,790)]:
    draw.rounded_rectangle(rect,radius=18,fill="white",outline="#d8dfe6",width=2)
draw.text((65,168),"滑入途中：显示面朝前、排线端在后",font=font,fill="#182b3a")
objects=[(G["front"],(215,225,235),(0,0,0))]
for geo in G["hardware"]:
    objects.append((geo,(242,242,234) if geo["name"]=="ActiveArea" else (90,94,95),(0,-40,0)))
scene((75,235,745,740),(1,-1,2.8),objects)
draw.text((835,168),"左侧导槽截面（局部放大，实际 CAD）",font=font,fill="#182b3a")
objects=[(geo,(68,125,160) if geo["name"]=="glass" else (215,225,235),(0,0,0))
         for geo in G["rail_section"]]
scene((850,245,1515,670),(0,-1,0.001),objects)
draw.text((850,690),"蓝色：1.2 mm 屏幕玻璃的空白边缘",font=font,fill="#43586b")
draw.text((850,733),"导槽净高 2.0 mm，保留滑动间隙",font=font,fill="#43586b")
draw.text((50,828),"侧轨限制前后 / 左右移动；上挡边和底部挡条限制上下滑动。屏幕无需粘胶。",font=font,fill="#43586b")
im.save(OUT / "rail-detail.png")
print("CAD preview saved")
