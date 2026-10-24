import bpy
from pathlib import Path
BASE=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(BASE/'J003-source-v06.blend'))
s=bpy.context.scene
views={'front':'CAM_01_FRONT_heart_face','side':'CAM_02_SIDE_profile','back':'CAM_03_BACK_ring_plane','45deg':'CAM_04_45DEG_default','underside':'CAM_05_UNDERSIDE_review','preview':'CAM_04_45DEG_default'}
for name,cam in views.items():
 s.camera=bpy.data.objects[cam];s.render.resolution_x=s.render.resolution_y=1000 if name=='preview' else 900;s.cycles.samples=32 if name=='preview' else 24
 s.render.filepath=str(BASE/f'J003-{name}-v06.png');bpy.ops.render.render(write_still=True)
# Isolated magnified head inspection; same real product, camera change only.
from mathutils import Vector
s.camera=bpy.data.objects['CAM_01_FRONT_heart_face'];s.camera.data.ortho_scale=.009;s.render.resolution_x=s.render.resolution_y=1000;s.cycles.samples=24
s.render.filepath=str(BASE/'J003-prong-closeup-v06.png');bpy.ops.render.render(write_still=True)
print('ALL_RENDERS_DONE',flush=True)
