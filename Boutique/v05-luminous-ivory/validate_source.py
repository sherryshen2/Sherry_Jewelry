import bpy,json
from pathlib import Path
B=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(B/'Boutique-final.blend'))
imgs=[]
for im in bpy.data.images:
 if im.name in ['Render Result','Viewer Node'] or im.users==0:continue
 assert len(im.pixels)>0 and im.packed_file,im.name
 imgs.append({'name':im.name,'packed':True,'size':list(im.size)})
assert bpy.context.scene.camera.name=='01_Front'
for n in ['01_Front','02_Left','03_Right']:assert bpy.data.objects[n].type=='CAMERA'
report={'source_reopens':True,'default_camera':'01_Front','editable_collections':[c.name for c in bpy.context.scene.collection.children if c.name.startswith('0')],'packed_images':imgs,'bytes':(B/'Boutique-final.blend').stat().st_size}
(B/'source-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('SOURCE_OK',json.dumps(report),flush=True)
