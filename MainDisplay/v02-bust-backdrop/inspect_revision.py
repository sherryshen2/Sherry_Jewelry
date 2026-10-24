import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
B=Path(__file__).resolve().parent
def appearance():
 return {m.name:{n.name:{i.name:list(i.default_value) if hasattr(i.default_value,'__len__') else i.default_value for i in n.inputs if hasattr(i,'default_value') and (isinstance(i.default_value,(float,int)) or hasattr(i.default_value,'__len__'))} for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'} for m in bpy.data.materials if m.use_nodes}
def unchanged():
 result={}
 for col in bpy.data.collections:
  if not col.name.startswith(('01_Fixed_Counter','04_Fixed_Decor','90_Lighting','91_Cameras')):continue
  for o in col.objects:
   result[o.name]=[list(row) for row in o.matrix_world]
 for name in ['earrings_anchor','ring_anchor','bracelet_anchor']:
  result[name]=[list(row) for row in bpy.data.objects[name].matrix_world]
 return result
bpy.ops.wm.open_mainfile(filepath=str(B.parent/'v01-layout/main-display-source.blend'));baseline=unchanged();materials=appearance()
bpy.ops.wm.open_mainfile(filepath=str(B/'main-display-source.blend'));bpy.context.view_layer.update()
current=unchanged();ma=appearance();changes=[n for n,v in baseline.items() if current[n]!=v]
material_changes=[n for n,v in materials.items() if n in ma and ma[n]!=v]
assert not changes,changes
assert not material_changes,material_changes
root=bpy.data.objects['necklace_product'];stone=next(o for o in root.children_recursive if o.name.startswith('02_RaisedPinkHeart'))
stonepts=[stone.matrix_world@v.co for v in stone.data.vertices]
center=[(min(v[i] for v in stonepts)+max(v[i] for v in stonepts))/2 for i in range(3)]
assert abs(center[0]+.052)<.001
assert .215<center[2]<.223,center
bust=bpy.data.objects['fitted soft shoulder necklace bust'];dg=bpy.context.evaluated_depsgraph_get();ev=bust.evaluated_get(dg);mesh=ev.to_mesh()
bvh=BVHTree.FromPolygons([bust.matrix_world@v.co for v in mesh.vertices],[tuple(p.vertices) for p in mesh.polygons]);ev.to_mesh_clear()
minimum=1;bad=[];sample_count=0
for o in root.children_recursive:
 if o.type!='MESH':continue
 for v in list(o.data.vertices)[::7]:
  p=o.matrix_world@v.co;q,n,_,d=bvh.find_nearest(p);signed=(p-q).dot(n);minimum=min(minimum,signed);sample_count+=1
  if signed<-.00015:bad.append({'object':o.name,'signed_mm':signed*1000})
report={'unchanged_scene_transforms':not changes,'unchanged_original_material_settings':not material_changes,'pendant_gem_center_world_m':center,'necklace_fit_sample_count':sample_count,'minimum_signed_fabric_clearance_mm':minimum*1000,'penetrations_over_0_15mm':len(bad),'examples':bad[:12]}
(B/'revision-check.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
