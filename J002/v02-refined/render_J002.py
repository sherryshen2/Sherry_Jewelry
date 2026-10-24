import bpy,sys
from pathlib import Path
B=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(B/'J002-source-v02.blend'));s=bpy.context.scene
proof='--proof' in sys.argv
names=['single-side','single-45deg','pair-default'] if proof else ['single-front','single-side','single-back','single-45deg','single-bottom','pair-default','pair-front']
for name in names:
 single=name.startswith('single');camera='CAM_'+name.replace('-','_').replace('single','SINGLE').replace('pair','PAIR')
 for o in bpy.data.collections['J002_PRODUCT_ONLY'].objects:
  if o.type=='MESH':o.hide_render=single and o.parent.name.startswith('J002_B')
 s.camera=bpy.data.objects[camera];s.render.resolution_x=650 if proof else (900 if single else 1200);s.render.resolution_y=650 if proof else 900;s.cycles.samples=16 if proof else 64
 s.render.filepath=str(B/(('proof-' if proof else 'J002-')+name+('-v02' if not proof else '')+'.png'));bpy.ops.render.render(write_still=True);print('RENDER_DONE',name,flush=True)
print('J002_RENDER_COMPLETE',flush=True)

if not proof and '--full-only' not in sys.argv:
 from mathutils import Vector
 left=bpy.data.objects['J002_A_MASTER']
 for o in bpy.data.collections['J002_PRODUCT_ONLY'].objects:
  if o.type=='MESH':o.hide_render=o.parent.name.startswith('J002_B')
 for label,direction in [('side',(1,0,0)),('four-prong',(1,-1,.15))]:
  d=bpy.data.cameras.new('CLOSEUP_'+label);d.type='ORTHO';d.ortho_scale=.0047;d.clip_start=.0001;d.clip_end=1
  o=bpy.data.objects.new('CLOSEUP_'+label,d);s.collection.objects.link(o)
  target=left.matrix_world@Vector((0,-.00495,.00035));o.location=target+left.rotation_euler.to_matrix()@Vector(direction).normalized()*.07;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
  s.camera=o;s.render.resolution_x=1100;s.render.resolution_y=1100;s.cycles.samples=96;s.render.filepath=str(B/('J002-closeup-'+label+'-v02.png'));bpy.ops.render.render(write_still=True)
