import bpy,json,math,struct
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
B=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(B/'main-display-source.blend'));bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
def bounds(root):
 pts=[o.matrix_world@v.co for o in root.children_recursive if o.type=='MESH' for v in o.data.vertices]
 return [[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]]
expected={k:bounds(bpy.data.objects[k+'_product']) for k in ['necklace','earrings','ring','bracelet']}
bust=bpy.data.objects['fitted soft shoulder necklace bust'];ev=bust.evaluated_get(dg);me=ev.to_mesh();bvh=BVHTree.FromPolygons([bust.matrix_world@v.co for v in me.vertices],[tuple(p.vertices) for p in me.polygons]);ev.to_mesh_clear()
penetrations=[];distances=[]
for o in bpy.data.objects['necklace_product'].children_recursive:
 if o.type!='MESH':continue
 for v in list(o.data.vertices)[::5]:
  p=o.matrix_world@v.co;q,n,ind,dist=bvh.find_nearest(p)
  signed=(p-q).dot(n);distances.append(signed)
  if signed<-.00015:penetrations.append({'point':list(p),'signed_mm':signed*1000})
fit={'necklace_sampled_vertices':len(distances),'bust_penetrations_over_0_15mm':len(penetrations),'max_signed_penetration_mm':min(distances)*1000,'penetration_examples':penetrations[:5],'note':'Signed nearest-surface check is a diagnostic, not a manufacturing fit certification.'}
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(B/'main-display-scene.glb'));fixed=list(bpy.context.scene.objects);anchors={k:bpy.data.objects[k+'_anchor'] for k in expected};actual={};checks={}
for k in expected:
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(B/(k+'.glb')));new=set(bpy.data.objects)-before;root=next(o for o in new if o.parent is None);root.parent=anchors[k];root.matrix_parent_inverse=Matrix.Identity(4);root.location=(0,0,0);root.rotation_euler=(0,0,0);root.scale=(1,1,1);bpy.context.view_layer.update();actual[k]=bounds(root);err=max(abs(expected[k][j][i]-actual[k][j][i]) for j in range(2) for i in range(3));assert err<1e-6,(k,err);checks[k]={'bounds_match_error_m':err,'bounds_blender_world_m':actual[k],'earring_children':[o.name for o in root.children] if k=='earrings' else None}
report={'reassembled_from_exported_files':True,'scene_only_fixed_geometry_and_anchors':not any('product' in o.name for o in fixed),'source_and_export_world_bounds_match':True,'products':checks,'fit_diagnostics':fit,'known_review_items':['v02 revised bust, necklace drape and enlarged backdrop.','Existing jewelry dimensions and optical approximations remain as source notes.','Rigid product animation only; no flexible chain deformation.']};(B/'assembly-check.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
