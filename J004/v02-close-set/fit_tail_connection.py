import bpy,math,json,itertools
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from pathlib import Path
B=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(B/'J004-source-v02.blend'));dg=bpy.context.evaluated_depsgraph_get();objects=[o for o in bpy.data.collections['J004_PRODUCT_ONLY'].objects if o.type=='MESH'];geometry={};boxes={};trees={}
for o in objects:
 ev=o.evaluated_get(dg);m=ev.to_mesh();m.calc_loop_triangles();vs=[o.matrix_world@v.co for v in m.vertices];fs=[tuple(p.vertices) for p in m.loop_triangles];geometry[o.name]=(vs,fs);boxes[o.name]=([min(v[k] for v in vs) for k in range(3)],[max(v[k] for v in vs) for k in range(3)]);trees[o.name]=BVHTree.FromPolygons(vs,fs);ev.to_mesh_clear()
moving=[o.name for o in objects if o.name.startswith(('PENDING_Tail','TAIL49'))];fixed=[o.name for o in objects if o.name not in moving]
def centers(name):
 vs=geometry[name][0];return [sum(vs[i:i+10],Vector())/10 for i in range(0,len(vs),10)]
a=centers('PENDING_AdjustmentRing');b=centers('PENDING_TailLink_01')
def linking(delta):
 total=0
 for i in range(len(a)):
  u=a[(i+1)%len(a)]-a[i];p=(a[i]+a[(i+1)%len(a)])/2
  for j in range(len(b)):
   v=b[(j+1)%len(b)]-b[j];q=(b[j]+b[(j+1)%len(b)])/2+delta;r=p-q
   total+=r.dot(u.cross(v))/max(r.length**3,1e-30)
 return total/(4*math.pi)
vals=[i*.0001 for i in range(-5,6)];candidates=sorted(itertools.product(vals,repeat=3),key=lambda d:sum(x*x for x in d));best=None
for xyz in candidates:
 delta=Vector(xyz);lk=linking(delta)
 if abs(lk)<.75:continue
 collision=False
 for name in moving:
  lo,hi=boxes[name];potential=[n for n in fixed if all(lo[k]+delta[k]<=boxes[n][1][k] and boxes[n][0][k]<=hi[k]+delta[k] for k in range(3))]
  if not potential:continue
  vs,fs=geometry[name];tree=BVHTree.FromPolygons([v+delta for v in vs],fs)
  if any(tree.overlap(trees[n]) for n in potential):collision=True;break
 if not collision:best={'translation_mm':[x*1000 for x in delta],'linking_number_approx':lk};break
print('TAIL_FIT',best,flush=True);(B/'tail-fit.json').write_text(json.dumps(best,indent=2))
