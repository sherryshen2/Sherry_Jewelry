import bpy,json,bmesh
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
BASE=Path(__file__).resolve().parent
results={}
for label,path in [('v05_before',BASE.parent/'v05-richer-color/J003-source-v05.blend'),('v06_after',BASE/'J003-source-v06.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(path));dg=bpy.context.evaluated_depsgraph_get()
 objects=[o for o in bpy.data.collections['J003_PRODUCT_ONLY'].objects if o.type=='MESH']
 trees={};boxes={};prongs={}
 for o in objects:
  ev=o.evaluated_get(dg);me=ev.to_mesh();vs=[o.matrix_world@v.co for v in me.vertices];me.calc_loop_triangles();polys=[tuple(p.vertices) for p in me.loop_triangles]
  trees[o.name]=BVHTree.FromPolygons(vs,polys);boxes[o.name]=([min(v[k] for v in vs) for k in range(3)],[max(v[k] for v in vs) for k in range(3)])
  if 'MainProng' in o.name or 'Bead_' in o.name:
   prongs[o.name]=vs+[sum((vs[i] for i in f),Vector())/len(f) for f in polys]
  ev.to_mesh_clear()
 gems=[o.name for o in objects if o.data.materials[0].name.startswith(('M02','M03'))]
 penetrations=[];maxdepth=0;mainmax=0;nearcontacts={}
 for name,pts in prongs.items():
  nearcontacts[name]=[]
  for stone in gems:
   a=boxes[name];b=boxes[stone]
   if not all(a[0][k]<=b[1][k]+.000002 and b[0][k]<=a[1][k]+.000002 for k in range(3)):continue
   tree=trees[stone];depths=[];nearest=1
   for p in pts:
    loc,n,idx,d=tree.find_nearest(p)
    if loc is None:continue
    nearest=min(nearest,d)
    if (p-loc).dot(n)<-.000002:depths.append(d*1000)
   if nearest<=.000002:nearcontacts[name].append(stone)
   if depths:
    depth=max(depths);maxdepth=max(maxdepth,depth)
    if 'MainProng' in name:mainmax=max(mainmax,depth)
    penetrations.append({'prong':name,'stone':stone,'sampled_depth_mm':depth,'sample_count':len(depths)})
 results[label]={'sampled_internal_prong_points_over_0_002mm':penetrations,'max_depth_mm':maxdepth,'main_prong_max_depth_mm':mainmax,'contact_within_0_002mm':nearcontacts}
results['method']='Evaluated meshes; nearest oriented stone surface at prong vertices and triangulated face centers. 0.002 mm tolerance. This sampling check is not an exhaustive solid-intersection proof; editable exact Boolean seats separately remove stone volume.'
(BASE/'J003-prong-fit-check-v06.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
print(json.dumps({k:{x:y for x,y in v.items() if x in ['max_depth_mm','main_prong_max_depth_mm']} for k,v in results.items() if isinstance(v,dict)},indent=2))
