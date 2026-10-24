"""Render saved source: Blender --background --python render_J001.py [-- --proof]."""
import bpy,sys
from pathlib import Path
BASE=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(BASE/'J001-source-v01.blend'))
scene=bpy.context.scene;proof='--proof' in sys.argv
names=['45deg','full'] if proof else ['front','side','back','45deg','full','preview']
for name in names:
 close=name in ['front','side','back','45deg']
 for o in bpy.data.collections['J001_PRODUCT_ONLY'].objects:
  if o.type=='MESH':o.hide_render=close and o.get('part')!='pendant'
 camname='CAM_PENDANT_'+name if close else ('CAM_FULL_RATIO' if name=='full' else 'CAM_FULL_DEFAULT')
 scene.camera=bpy.data.objects[camname];scene.cycles.samples=16 if proof else 48
 scene.render.resolution_x=(650 if close else 750) if proof else (850 if close else 1100)
 scene.render.resolution_y=scene.render.resolution_x if close else (950 if proof else 1400)
 scene.render.filepath=str(BASE/(f'proof-{name}.png' if proof else f'J001-{name}-v01.png'))
 bpy.ops.render.render(write_still=True);print('RENDER_COMPLETE',name,flush=True)
print('J001_RENDER_DONE',flush=True)
