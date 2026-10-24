import bpy,json
from pathlib import Path
B=Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(B/'Boutique-web.glb'))
objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];tri=0
for o in objects:o.data.calc_loop_triangles();tri+=len(o.data.loop_triangles)
images=[]
for im in bpy.data.images:
 pixels=len(im.pixels);assert pixels>0 and im.has_data
 images.append({'name':im.name,'size':list(im.size),'loaded':True})
expected=json.loads((B/'web-stats.json').read_text());assert tri==expected['triangles']
report={'import_success':True,'triangles':tri,'mesh_objects':len(objects),'materials':len(bpy.data.materials),'images':images,'triangle_count_preserved':True}
(B/'blender-reimport-check.json').write_text(json.dumps(report,indent=2));print('REIMPORT_OK',json.dumps(report),flush=True)
