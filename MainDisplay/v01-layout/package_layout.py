from pathlib import Path
import json,hashlib,zipfile,shutil
B=Path(__file__).resolve().parent
assert json.loads((B/'resource-check.json').read_text())['pass']
assert json.loads((B/'browser-check.json').read_text())['pass']
assert json.loads((B/'assembly-check.json').read_text())['source_and_export_world_bounds_match']
shutil.copyfile(B/'01_Front.png',B/'main-display-hero.png')
names=['main-display-source.blend','main-display-scene.glb','necklace.glb','earrings.glb','ring.glb','bracelet.glb','01_Front.png','02_Left.png','03_Right.png','main-display-hero.png','web-front.png','web-left.png','web-right.png','web-mobile.png','product-placement.json','camera-and-lighting.json','product-audit.json','input-audit.json','assembly-check.json','browser-check.json','resource-check.json','scene-stats.json','首版说明.txt','preview.py','打开预览.command','render_display.py','export_scene.py','validate_resources.py','check_assembly.py']
files=[B/n for n in names]
for folder in ['textures','source-notes','viewer']:files+=sorted(p for p in (B/folder).rglob('*') if p.is_file())
assert all(p.is_file() and p.stat().st_size>0 for p in files)
manifest={'stage':'stage1 layout; approval pending','date':'2026-10-23','files':[{'file':str(p.relative_to(B)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]};(B/'file-manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
p=B.parent/'MainDisplay-stage1-preview.zip'
with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for f in files+[B/'file-manifest.json']:z.write(f,'MainDisplay-stage1/'+str(f.relative_to(B)))
with zipfile.ZipFile(p) as z:assert z.testzip() is None
report={'archive':str(p),'archive_bytes':p.stat().st_size,'blend_bytes':(B/'main-display-source.blend').stat().st_size,'glbs_bytes':sum((B/(n+'.glb')).stat().st_size for n in ['main-display-scene','necklace','earrings','ring','bracelet']),'files':len(files)+1};(B/'delivery-summary.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
