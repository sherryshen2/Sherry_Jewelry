"""Revise the approved source palette and practical lighting, preserving geometry."""
import bpy,json
from pathlib import Path
from mathutils import Vector
B=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(B.parent/'v02-final/Boutique-final.blend'))
s=bpy.context.scene
changes={
 '04 |':((.85,.53,.17),.80,.24),
 '05 |':((.95,.68,.26),.87,.20),
 '07 |':((.78,.36,.43),0,.53),
 '10 |':((.53,.24,.30),0,.82),
 '13 |':((.78,.30,.40),.18,.15),
 '18 |':((.84,.43,.48),0,.68),
}
report={'version':'v03 brighter gold / rose, illuminated warm practicals','materials':[],'lights':[]}
for prefix,(col,metal,rough) in changes.items():
 m=next(m for m in bpy.data.materials if m.name.startswith(prefix));p=m.node_tree.nodes.get('Principled BSDF')
 p.inputs['Base Color'].default_value=(*col,1);m.diffuse_color=(*col,1)
 p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 report['materials'].append({'name':m.name,'linear_rgb':col,'metallic':metal,'roughness':rough})
m=next(m for m in bpy.data.materials if m.name.startswith('20 |'));p=m.node_tree.nodes.get('Principled BSDF')
p.inputs['Base Color'].default_value=(1,.67,.29,1)
p.inputs['Emission Color'].default_value=(1,.52,.17,1);p.inputs['Emission Strength'].default_value=4.5
for o in s.objects:
 if o.type!='LIGHT':continue
 if o.name.startswith('chandelier practical'):o.data.energy=65;o.data.color=(1,.68,.36)
 if o.name.startswith('cabinet warm practical'):o.data.energy=20;o.data.color=(1,.72,.40)
 if o.name.startswith('cool front fill'):o.data.energy=190
 if o.name.startswith('overhead silk light'):o.data.energy=200
studio=bpy.data.collections['90_Studio']
def area(name,pos,target,energy,size):
 d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.color=(1,.71,.39);d.shape='RECTANGLE';d.size=size;d.size_y=.16
 o=bpy.data.objects.new(name,d);studio.objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
for x in [-1.91,1.91]:
 for z in [2.87,2.08]:area('warm shelf wash',(x,2.08,z),(x,2.30,z-.55),4.0,.64)
area('central counter warm wash',(0,.49,1.785),(0,.61,1.43),5.0,2.5)
for o in studio.objects:
 if o.type=='LIGHT':report['lights'].append({'name':o.name,'watts':o.data.energy,'color_linear':list(o.data.color)})
s.camera=bpy.data.objects['01_Front'];s['stage']='v03 final — brighter gold and pink, visible warm light'
s['web_lighting']='5 realtime lights; cabinet and chandelier warm illumination; retain COLOR_0 contact shading'
# Keep textures self-contained and resolve the editable external copies to this version.
for im in bpy.data.images:
 if im.packed_file:
  im.filepath='//textures/'+Path(im.filepath).name
bpy.ops.wm.save_as_mainfile(filepath=str(B/'Boutique-final.blend'))
(B/'palette-and-light-revision.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('PALETTE_LIGHT_REVISION_SAVED',flush=True)
