import bpy,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(p/'J003-source-v06.blend'));dg=bpy.context.evaluated_depsgraph_get();trees={};bounds={};prongs=[]
for o in bpy.data.collections['J003_PRODUCT_ONLY'].objects:
 if o.type!='MESH' or not o.data.materials[0].name.startswith('M01'):continue
 ev=o.evaluated_get(dg);m=ev.to_mesh();v=[o.matrix_world@x.co for x in m.vertices];f=[list(x.vertices) for x in m.polygons];trees[o.name]=BVHTree.FromPolygons(v,f);bounds[o.name]=([min(x[k] for x in v) for k in range(3)],[max(x[k] for x in v) for k in range(3)]);ev.to_mesh_clear()
 if 'MainProng' in o.name or 'Bead_' in o.name:prongs.append(o.name)
contacts={}
for name in prongs:
 a=bounds[name];contacts[name]=[]
 for other,t in trees.items():
  if name==other:continue
  b=bounds[other]
  if all(a[0][k]<=b[1][k] and b[0][k]<=a[1][k] for k in range(3)) and trees[name].overlap(t):contacts[name].append(other)
r={'prong_metal_contacts':contacts,'without_other_metal_contact':[n for n,c in contacts.items() if not c]};(p/'J003-prong-support-v06.json').write_text(json.dumps(r,indent=2));print('unsupported prongs',r['without_other_metal_contact'])
