import bpy,sys
from pathlib import Path
B=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(B/'J002-source-v01.blend'));s=bpy.context.scene
proof='--proof' in sys.argv
names=['single-45deg','pair-default'] if proof else ['single-front','single-side','single-back','single-45deg','single-bottom','pair-default','pair-front']
for name in names:
 single=name.startswith('single');camera='CAM_'+name.replace('-','_').replace('single','SINGLE').replace('pair','PAIR')
 for o in bpy.data.collections['J002_PRODUCT_ONLY'].objects:
  if o.type=='MESH':o.hide_render=single and o.parent.name.startswith('J002_B')
 s.camera=bpy.data.objects[camera];s.render.resolution_x=650 if proof else (900 if single else 1200);s.render.resolution_y=650 if proof else 900;s.cycles.samples=16 if proof else 32
 s.render.filepath=str(B/(('proof-' if proof else 'J002-')+name+('-v01' if not proof else '')+'.png'));bpy.ops.render.render(write_still=True);print('RENDER_DONE',name,flush=True)
print('J002_RENDER_COMPLETE',flush=True)
