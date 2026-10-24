from pathlib import Path
import zipfile,json,hashlib,gzip
B=Path(__file__).resolve().parent
for name,flag in [('browser-check.json','pass'),('blender-reimport-check.json','import_success'),('source-check.json','source_reopens'),('glb-check.json','valid_glb_header_and_buffers')]:
 assert json.loads((B/name).read_text())[flag],name
names=['Boutique-final.blend','Boutique-web.glb','Boutique-hero.png','02_Left.png','03_Right.png','web-front.png','web-left.png','web-right.png','web-mobile.png','camera-and-web-settings.json','web-stats.json','glb-check.json','blender-reimport-check.json','browser-check.json','source-check.json','交付说明.txt','preview.py','打开预览.command','export_web.py','render_final.py','validate_glb.py','reimport_check.py','palette-and-light-revision.json','palette-export-check.json','pastel-colors.json','front-light-revision.json']
files=[B/x for x in names]+sorted((B/'textures').glob('*.png'))+sorted(p for p in (B/'viewer').rglob('*') if p.is_file())
assert all(p.is_file() and p.stat().st_size for p in files)
manifest={'date':'2026-10-23','stage':'v06-soft-front','files':[{'path':str(p.relative_to(B)),'bytes':p.stat().st_size,'megabytes_decimal':round(p.stat().st_size/1e6,3),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]}
(B/'file-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
archive=B.parent/'Boutique-v06-soft-front.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=7) as z:
 for p in files+[B/'file-manifest.json']:z.write(p,'Boutique-v06/'+str(p.relative_to(B)))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
report={'archive':str(archive),'archive_bytes':archive.stat().st_size,'blend_bytes':(B/'Boutique-final.blend').stat().st_size,'glb_bytes':(B/'Boutique-web.glb').stat().st_size,'hero_bytes':(B/'Boutique-hero.png').stat().st_size,'files_in_archive':len(files)+1}
(B/'delivery-summary.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,ensure_ascii=False))
