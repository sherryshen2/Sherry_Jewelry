from pathlib import Path
import zipfile,json,hashlib
B=Path(__file__).resolve().parent
names=['Boutique-stage1.blend','01_Front.png','02_Left.png','03_Right.png','camera-preview.json','preview-audit.json','阶段说明.txt']
files=[B/x for x in names]+list((B/'textures').glob('*.png'))
for p in files:
    assert p.is_file() and p.stat().st_size>0,p
manifest={'stage':'01 preview; user style confirmation pending','files':[{'path':str(p.relative_to(B)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]}
(B/'package-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
out=B.parent/'Boutique-stage1-preview.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in files+[B/'package-manifest.json']:z.write(p,'Boutique-stage1/'+str(p.relative_to(B)))
with zipfile.ZipFile(out) as z:
    assert z.testzip() is None
print(json.dumps({'archive':str(out),'bytes':out.stat().st_size,'blend_bytes':(B/'Boutique-stage1.blend').stat().st_size,'entries':len(files)+1},ensure_ascii=False))
