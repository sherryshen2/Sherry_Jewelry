import bpy
from pathlib import Path
from mathutils import Vector
B=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(B/'main-display-source.blend'))
s=bpy.context.scene
keep={'fitted soft shoulder necklace bust','necklace oval plinth','necklace gold plinth bead','necklace hidden rear retaining hook','studio floor'}
keep.update(o.name for o in bpy.data.objects['necklace_product'].children_recursive)
for o in s.objects:
 if o.type in {'MESH','CURVE'} and o.name not in keep:o.hide_render=True
target=Vector((-.052,.034,.219))
d=bpy.data.cameras.new('bust_detail_camera');d.type='ORTHO';d.ortho_scale=.213;d.clip_start=.001;d.clip_end=10
c=bpy.data.objects.new('bust_detail_camera',d);s.collection.objects.link(c);s.camera=c
s.render.resolution_x=760;s.render.resolution_y=1000;s.cycles.samples=24
for name,offset in [('04_Bust_Side',(0.5,0,0)),('05_Bust_Back',(0,.5,.06))]:
 c.location=target+Vector(offset);c.rotation_euler=(target-c.location).to_track_quat('-Z','Y').to_euler()
 s.render.filepath=str(B/(name+'.png'));bpy.ops.render.render(write_still=True)
 print('DETAIL_RENDERED',name,flush=True)
