"""Brighter ivory, soft facade/side-wall fill, and translucent white crystals."""
import bpy,json
from pathlib import Path
from mathutils import Vector
B=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(B.parent/'v04-pastel-palette/Boutique-final.blend'))
s=bpy.context.scene;colors=json.loads((B/'pastel-colors.json').read_text())
gold_before={m.name:[m.node_tree.nodes.get('Principled BSDF').inputs[k].default_value for k in ['Metallic','Roughness']] for m in bpy.data.materials if m.name.startswith(('04 |','05 |'))}
report={'version':'v05 luminous ivory; facade and outer-wall fill; softer shadows; white translucent crystal','materials':[]}
for key,color in colors.items():
 m=next(m for m in bpy.data.materials if m.name.startswith(key+' |'));p=m.node_tree.nodes.get('Principled BSDF')
 p.inputs['Base Color'].default_value=(*color,1);m.diffuse_color=(*color,1)
 report['materials'].append({'name':m.name,'linear_rgb':color})
for im in list(bpy.data.images):
 if not im.packed_file:continue
 path=B/'textures'/(im.name+'.png')
 if im.name in ['paint_01_basecolor','paint_02_basecolor','paint_03_basecolor','oyster_damask_basecolor']:
  replacement=bpy.data.images.load(str(path),check_existing=False);replacement.colorspace_settings.name='sRGB'
  for m in bpy.data.materials:
   if not m.use_nodes:continue
   for node in m.node_tree.nodes:
    if node.type=='TEX_IMAGE' and node.image==im:node.image=replacement
  old_name=im.name;bpy.data.images.remove(im);replacement.name=old_name;replacement.pack();replacement.filepath='//textures/'+path.name
 else:im.filepath='//textures/'+path.name
m=next(m for m in bpy.data.materials if m.name.startswith('15 |'));p=m.node_tree.nodes.get('Principled BSDF')
for k,v in {'Metallic':0,'Roughness':.14,'Transmission Weight':.25,'Alpha':.78,'IOR':1.45,'Coat Weight':.28,'Coat Roughness':.10,'Emission Strength':.035}.items():p.inputs[k].default_value=v
p.inputs['Emission Color'].default_value=(1,1,1,1);m.surface_render_method='DITHERED';m['web_role']='white_translucent_crystal';m['web_alpha']=.68
studio=bpy.data.collections['90_Studio']
def area(name,pos,target,energy,size):
 d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.color=(1,.98,.94);d.shape='DISK';d.size=size
 o=bpy.data.objects.new(name,d);studio.objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
area('facade broad soft fill',(0,-6,3.6),(0,.5,2.7),110,5)
area('left exterior soft fill',(-6,1.1,4),(-2.5,1.1,2.5),90,4)
area('right exterior soft fill',(6,1.1,4),(2.5,1.1,2.5),100,4)
for n in s.world.node_tree.nodes:
 if n.type=='BACKGROUND':n.inputs['Strength'].default_value=.30
for name,vals in gold_before.items():
 p=bpy.data.materials[name].node_tree.nodes.get('Principled BSDF');assert vals==[p.inputs[k].default_value for k in ['Metallic','Roughness']]
report['gold_reflection_properties_unchanged']=True;report['warm_practicals_preserved']=True
report['lights']=[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'color':list(o.data.color),'position':list(o.location)} for o in s.objects if o.type=='LIGHT']
report['crystal']={'color':[.98,.99,1],'metallic':0,'roughness':.14,'transmission':.25,'alpha':.78,'web_alpha':.68}
s['stage']='v05 luminous ivory, soft exterior/facade fill and white translucent crystal';s.camera=bpy.data.objects['01_Front']
bpy.ops.wm.save_as_mainfile(filepath=str(B/'Boutique-final.blend'))
(B/'palette-and-light-revision.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('LUMINOUS_SOURCE_SAVED',flush=True)
