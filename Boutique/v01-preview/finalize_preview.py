import bpy,json
from pathlib import Path
B=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(B/'Boutique-stage1.blend'))
s=bpy.context.scene;s.camera=bpy.data.objects['01_Front'];s.render.filepath='//01_Front.png'
issues=[]
for im in bpy.data.images:
    if im.name in ['Render Result','Viewer Node']:continue
    # Blender loads external image pixels lazily after opening a .blend.
    if im.source=='FILE' and not im.packed_file:
        assert Path(bpy.path.abspath(im.filepath)).is_file(),im.filepath
        im.reload()
    pixel_count=len(im.pixels)
    if not im.has_data or not pixel_count:issues.append('Image has no pixels: '+im.name)
    if im.has_data and not im.packed_file:im.pack()
for o in bpy.data.objects:
    if o.type=='MESH' and any(f.material_index>=len(o.data.materials) for f in o.data.polygons):issues.append('Missing material: '+o.name)
assert not issues,issues
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(B/'Boutique-stage1.blend'))
p=B/'preview-audit.json';d=json.loads(p.read_text());d['validation']={'blender_reopen':True,'image_pixel_data_present':True,'images_packed':True,'face_material_slots_valid':True,'default_camera':'01_Front','three_rendered_views':[str(x) for x in ['01_Front.png','02_Left.png','03_Right.png']],'glb_export':'Deferred until user approves stage 1, per requested workflow'}
d['files']={x.name:x.stat().st_size for x in B.glob('*') if x.suffix in ['.blend','.png','.json'] and not x.name.startswith('proof-') and x.name not in ['preview-audit.json','package-manifest.json']};p.write_text(json.dumps(d,indent=2,ensure_ascii=False))
print('FINALIZED',json.dumps(d,ensure_ascii=False),flush=True)
