import bpy,sys
from pathlib import Path
B=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(B/'main-display-source.blend'));s=bpy.context.scene
proof='--proof' in sys.argv
for name in (['01_Front'] if proof else ['01_Front','02_Left','03_Right']):
 s.camera=bpy.data.objects[name];s.cycles.samples=16 if proof else 20;s.render.resolution_x=960 if proof else 1200;s.render.resolution_y=880 if proof else 1100;s.render.filepath=str(B/('layout-proof.png' if proof else name+'.png'));bpy.ops.render.render(write_still=True);print('RENDER_DONE',name,flush=True)
