"""Colour-only revision of v03. Preserve lighting and all reflective properties."""
import bpy,json
from pathlib import Path
B=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(B.parent/'v03-brighter-warm/Boutique-final.blend'))
s=bpy.context.scene
colors=json.loads((B/'pastel-colors.json').read_text())
def lighting():
 return {o.name:{'matrix':[list(r) for r in o.matrix_world],'energy':o.data.energy,'color':list(o.data.color),'type':o.data.type,'size':getattr(o.data,'size',None)} for o in s.objects if o.type=='LIGHT'}
before=lighting();report={'version':'v04 pastel palette; v03 lighting and metallic response retained','materials':[]}
for key,color in colors.items():
 m=next(m for m in bpy.data.materials if m.name.startswith(key+' |'));p=m.node_tree.nodes.get('Principled BSDF')
 previous=list(p.inputs['Base Color'].default_value[:3]);metal=p.inputs['Metallic'].default_value;rough=p.inputs['Roughness'].default_value
 p.inputs['Base Color'].default_value=(*color,1);m.diffuse_color=(*color,1)
 assert p.inputs['Metallic'].default_value==metal and p.inputs['Roughness'].default_value==rough
 report['materials'].append({'name':m.name,'previous_linear_rgb':previous,'linear_rgb':color,'metallic':metal,'roughness':rough})
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
assert lighting()==before
report['lights_unchanged']=True;report['lights']=before;report['metallic_and_roughness_unchanged']=True
s['stage']='v04 pastel champagne, blush pink and ivory; v03 lighting and metallic reflection retained'
s.camera=bpy.data.objects['01_Front']
bpy.ops.wm.save_as_mainfile(filepath=str(B/'Boutique-final.blend'))
(B/'palette-and-light-revision.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('PASTEL_SOURCE_SAVED; LIGHTS_AND_REFLECTION_RETAINED',flush=True)
