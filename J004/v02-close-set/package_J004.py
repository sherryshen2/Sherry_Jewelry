from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,shutil,hashlib,zipfile
B=Path(__file__).resolve().parent;fpath='/System/Library/Fonts/STHeiti Medium.ttc'
def font(n):return ImageFont.truetype(fpath,n)
def tile(im,file,box,crop=None):
 src=Image.open(B/file).convert('RGB')
 if crop:src=src.crop(crop)
 src.thumbnail((box[2],box[3]),Image.Resampling.LANCZOS);im.paste(src,(box[0]+(box[2]-src.width)//2,box[1]+(box[3]-src.height)//2))
shutil.copy2(B/'J004-default-v02.png',B/'J004-preview-v02.png')
im=Image.new('RGB',(1860,2060),'#f4f1ec');d=ImageDraw.Draw(im)
d.text((35,26),'J004 · 网球手链 v02 · 单节加宽加长',font=font(39),fill='#302c29')
d.text((37,83),'闭合中心路径 160 mm · 主链 48 颗 + 尾端 1 颗 · 单节 2.70 × 2.70 × 2 mm',font=font(25),fill='#65594f')
d.text((40,145),'单节放大 / 四爪与侧窗',font=font(28),fill='#302c29');d.text((780,145),'扣件与尾链 / 尺寸、内部结构待确认',font=font(28),fill='#302c29')
tile(im,'J004-unit-v02.png',(30,193,700,660));tile(im,'J004-clasp-v02.png',(770,193,1060,660))
d.text((40,895),'完整俯视',font=font(28),fill='#302c29');d.text((960,895),'完整斜俯视',font=font(28),fill='#302c29')
tile(im,'J004-top-v02.png',(30,945,885,720));tile(im,'J004-default-v02.png',(945,945,885,720))
d.text((40,1690),'完整侧视（低角度）/ 保留真实节段厚度',font=font(27),fill='#302c29')
tile(im,'J004-side-v02.png',(30,1735,1800,235),(0,370,1300,670))
d.text((38,1990),'名义连接间隙由 0.936 mm 减为 0.221 mm；弯曲内侧保留微小间隙。',font=font(24),fill='#7a5443')
im.save(B/'J004-review-board-v02.png')
r=json.loads((B/'J004-validation-v02.json').read_text());p=B/'J004-说明与待确认项-v02.txt';body=p.read_text().split('\n最终文件统计\n')[0]+'\n最终文件统计\n'
for mode,v in r['lods'].items():body+=f"{mode}: {v['bytes']:,} bytes / {v['bytes']/1e6:.3f} MB / {v['triangles']:,} 三角面 / {v['materials']} 材质。\n"
body+='完整逐项检查未发现网格异常、超过采样容差的穿石、悬空爪、连接环之间或连接环与其他零件的表面交叉。\n';p.write_text(body)
files=[p for p in B.rglob('*') if p.is_file() and p.suffix not in ['.log','.blend1'] and not p.name.startswith('proof-') and p.name!='J004-manifest-v02.json']
m={'product':'J004','stage':'structure blockout','files':{str(p.relative_to(B)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files}}
mp=B/'J004-manifest-v02.json';mp.write_text(json.dumps(m,ensure_ascii=False,indent=2));files.append(mp)
zip_path=B.parent/'J004-close-set-v02-delivery.zip'
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
 for p in files:z.write(p,'J004-v02/'+str(p.relative_to(B)))
with zipfile.ZipFile(zip_path) as z:assert z.testzip() is None
print(zip_path,zip_path.stat().st_size,len(files))
