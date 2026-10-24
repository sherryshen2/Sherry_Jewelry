from pathlib import Path
import json,shutil,zipfile,hashlib
from PIL import Image,ImageDraw,ImageFont
B=Path(__file__).resolve().parent
font='/System/Library/Fonts/STHeiti Medium.ttc'
def f(n):return ImageFont.truetype(font,n)
def tile(board,path,box):
 im=Image.open(B/path).convert('RGB');im.thumbnail((box[2],box[3]),Image.Resampling.LANCZOS);board.paste(im,(box[0]+(box[2]-im.width)//2,box[1]+(box[3]-im.height)//2))
shutil.copy2(B/'J002-pair-default-v02.png',B/'J002-preview-v02.png')
im=Image.new('RGB',(1860,1600),'#f4f1ec');d=ImageDraw.Draw(im)
d.text((38,24),'J002 · 四爪精修 v02',font=f(38),fill='#302c29')
d.text((40,78),'每只 8 颗锆石 · 每颗 4 爪 · 内径 8 mm / 外径 11 mm · 侧面露石 0.5 mm',font=f(24),fill='#665b51')
tile(im,'J002-pair-default-v02.png',(30,122,1190,840));tile(im,'J002-single-bottom-v02.png',(1230,122,600,790));d.text((1250,905),'底部 / 铰链内部仍待确认',font=f(25),fill='#665b51')
for i,(label,name) in enumerate([('正面','front'),('侧面','side'),('背面','back'),('45°','45deg')]):
 x=30+i*460;d.text((x+12,995),label,font=f(28),fill='#302c29');tile(im,f'J002-single-{name}-v02.png',(x,1040,440,440))
d.text((40,1530),'完整闭合姿态。侧宽、耳针尺寸、锁合内部及左右差异保留待确认。',font=f(24),fill='#665b51')
im.save(B/'J002-review-board-v02.png')
im=Image.new('RGB',(1860,1135),'#f4f1ec');d=ImageDraw.Draw(im);d.text((36,24),'J002 · 露石与四爪局部核对',font=f(38),fill='#302c29')
for x,label,name in [(30,'侧面：露石 0.5 mm','side'),(945,'斜前方：四根独立镶爪','four-prong')]:
 d.text((x+8,90),label,font=f(27),fill='#665b51');tile(im,f'J002-closeup-{name}-v02.png',(x,140,885,885))
d.text((38,1056),'0.5 mm 沿石的径向测量，由金属侧墙外包络至石台面。近景有意裁切。',font=f(24),fill='#665b51');im.save(B/'J002-prong-review-v02.png')
r=json.loads((B/'J002-validation-v02.json').read_text());report=B/'J002-说明与待确认项-v02.txt'
with report.open('a') as out:
 out.write('\n最终文件统计\n')
 for mode,st in r['lods'].items():out.write(f"{mode}: {st['bytes']:,} bytes / {st['bytes']/1e6:.3f} MB / {st['triangles']:,} 三角面 / {st['materials']} 材质。\n")
 out.write('详情文件小于 2 MB，不需要为达到 2–5 MB 目标而人为增大文件。\n顶部耳针与第一颗宝石的重叠已修复；两只耳针均与前圈连接。\n')
paths=[p for p in B.rglob('*') if p.is_file() and p.suffix not in ['.log','.blend1'] and not p.name.startswith('proof-') and p.name!='J002-manifest-v02.json']
manifest={'product':'J002','version':'v02','files':{str(p.relative_to(B)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths}}
mp=B/'J002-manifest-v02.json';mp.write_text(json.dumps(manifest,ensure_ascii=False,indent=2));paths.append(mp)
zipfile_path=B.parent/'J002-refined-v02-delivery.zip'
with zipfile.ZipFile(zipfile_path,'w',zipfile.ZIP_DEFLATED) as z:
 for p in paths:z.write(p,'J002-v02/'+str(p.relative_to(B)))
with zipfile.ZipFile(zipfile_path) as z:assert z.testzip() is None
print(zipfile_path,zipfile_path.stat().st_size,len(paths))
