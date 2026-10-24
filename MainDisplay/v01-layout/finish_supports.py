import bpy,math
from pathlib import Path
B=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(B/'main-display-source.blend'))
o=bpy.data.objects['fitted soft shoulder necklace bust'];nx,ny,nz=(-.052,.022,.220)
for v in o.data.vertices:
 z=v.co.z-nz
 if z>.063:
  t=max(0,min(1,(z-.063)/.008));a=math.atan2((v.co.y-ny-.010)/.012,(v.co.x-nx)/.022)
  # A slim continuous neck replaces the upper flare; shoulder width is preserved below.
  xx=nx+.016*math.cos(a);yy=ny+.010+.008*math.sin(a)
  v.co.x=v.co.x*(1-t)+xx*t;v.co.y=v.co.y*(1-t)+yy*t
pad=bpy.data.objects['ring raised cushion'];pad.scale.z=1.42
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(B/'main-display-source.blend'),compress=True)
print('SUPPORTS_FINISHED',flush=True)
