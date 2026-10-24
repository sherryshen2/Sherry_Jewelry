import bpy,json
from pathlib import Path
from mathutils import Vector
B=Path(__file__).resolve().parent; W=B.parent.parent
bpy.ops.wm.open_mainfile(filepath=str(W/'Boutique/v06-soft-front/Boutique-final.blend'))
report={'boutique':{}}
for cn in ['02_Counter','04_Mirror','05_Textiles','08_Flowers_and_gifts']:
 report['boutique'][cn]=[{'name':o.name,'location':list(o.location),'dimensions':list(o.dimensions)} for o in bpy.data.collections[cn].objects]
products={'necklace':'J001/v02-refined/J001-display-v02.glb','earrings':'J002/v02-refined/J002-display-v02.glb','ring':'J003/v06-prong-gold/J003-display-v06.glb','bracelet':'J004/v02-close-set/J004-display-v02.glb'}
report['products']={}
for key,rel in products.items():
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(W/rel));bpy.context.view_layer.update()
 obs=list(bpy.context.scene.objects);pts=[o.matrix_world@Vector(c) for o in obs if o.type=='MESH' for c in o.bound_box]
 lo=[min(p[i] for p in pts) for i in range(3)];hi=[max(p[i] for p in pts) for i in range(3)]
 report['products'][key]={'source':rel,'bounds_blender_m':[lo,hi],'dimensions_mm':[(hi[i]-lo[i])*1000 for i in range(3)],'roots':[{'name':o.name,'matrix':[list(row) for row in o.matrix_world]} for o in obs if not o.parent],'objects':[{'name':o.name,'parent':o.parent.name if o.parent else None,'type':o.type,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale)} for o in obs],'materials':[m.name for m in bpy.data.materials]}
(B/'input-audit.json').write_text(json.dumps(report,indent=2));print('AUDIT_DONE')
