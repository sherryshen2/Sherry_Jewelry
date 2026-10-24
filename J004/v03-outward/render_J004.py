import bpy,sys
from pathlib import Path
B=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(B/'J004-source-v03.blend'));s=bpy.context.scene;proof='--proof' in sys.argv
views=[('unit','CAM_UNIT'),('clasp','CAM_CLASP'),('top','CAM_TOP'),('default','CAM_DEFAULT')] if proof else [('unit','CAM_UNIT'),('unit-side','CAM_UNIT_SIDE'),('clasp','CAM_CLASP'),('top','CAM_TOP'),('side','CAM_SIDE'),('back','CAM_BACK'),('bottom','CAM_BOTTOM'),('default','CAM_DEFAULT')]
for label,cam in views:
 for o in bpy.data.collections['J004_PRODUCT_ONLY'].objects:
  if o.type=='MESH':o.hide_render=label.startswith('unit') and o.parent.name!='J004_UNIT_01_MASTER'
 s.camera=bpy.data.objects[cam];s.render.resolution_x=700 if proof else (1000 if label.startswith('unit') else 1300);s.render.resolution_y=700 if proof else (1000 if label.startswith('unit') else 1050);s.cycles.samples=16 if proof else 40
 s.render.filepath=str(B/(('proof-' if proof else 'J004-')+label+('' if proof else '-v03')+'.png'));bpy.ops.render.render(write_still=True);print('RENDER_DONE',label,flush=True)
