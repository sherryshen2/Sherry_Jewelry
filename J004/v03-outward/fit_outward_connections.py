import bpy,math,json,itertools
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from pathlib import Path
B=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(B/'J004-source-v03.blend'));dg=bpy.context.evaluated_depsgraph_get();objects=[o for o in bpy.data.collections['J004_PRODUCT_ONLY'].objects if o.type=='MESH'];geometry={};boxes={};trees={}
for o in objects:
 ev=o.evaluated_get(dg);m=ev.to_mesh();m.calc_loop_triangles();vs=[o.matrix_world@v.co for v in m.vertices];fs=[tuple(p.vertices) for p in m.loop_triangles];geometry[o.name]=(vs,fs);boxes[o.name]=([min(v[k] for v in vs) for k in range(3)],[max(v[k] for v in vs) for k in range(3)]);trees[o.name]=BVHTree.FromPolygons(vs,fs);ev.to_mesh_clear()
def centers(name):
 vs=geometry[name][0];return [sum(vs[i:i+10],Vector())/10 for i in range(0,len(vs),10)]
def linking(a,b,delta):
 total=0
 for i in range(len(a)):
  u=a[(i+1)%len(a)]-a[i];p=(a[i]+a[(i+1)%len(a)])/2
  for j in range(len(b)):
   v=b[(j+1)%len(b)]-b[j];q=(b[j]+b[(j+1)%len(b)])/2+delta;r=p-q
   total+=r.dot(u.cross(v))/max(r.length**3,1e-30)
 return total/(4*math.pi)
def fit(moving,pairs,pin=None):
 fixed=[o.name for o in objects if o.name not in moving]
 vals=[i*.0001 for i in range(-5,6)];candidates=sorted(itertools.product(vals,repeat=3),key=lambda d:sum(x*x for x in d))
 clear_count=0;maxlink=0;maxcandidate=None
 for xyz in candidates:
  delta=Vector(xyz);collision=False
  for name in moving:
   lo,hi=boxes[name];potential=[n for n in fixed if all(lo[k]+delta[k]<=boxes[n][1][k] and boxes[n][0][k]<=hi[k]+delta[k] for k in range(3))]
   if not potential:continue
   vs,fs=geometry[name];tree=BVHTree.FromPolygons([v+delta for v in vs],fs)
   hits=[n for n in potential if tree.overlap(trees[n])]
   if xyz==(0.,0.,0.):print('ORIGIN HITS',hits,flush=True)
   if hits:collision=True;break
  if collision:continue
  clear_count+=1;lks=[linking(a,b,delta) for a,b in pairs]
  if abs(lks[0])>maxlink:maxlink=abs(lks[0]);maxcandidate=xyz
  if any(abs(x)<.75 for x in lks):continue
  if pin:
   # Transverse pin is vertical and must pass inside the translated horizontal ring.
   curve=centers(moving[0]);c=sum(curve,Vector())/len(curve);axis=(curve[0]-c).normalized();normal=Vector((-axis.y,axis.x,0));p=sum(geometry[pin][0],Vector())/len(geometry[pin][0]);v=p-c-delta
   if (v.dot(axis)/.00170)**2+(v.dot(normal)/.00030)**2>.85:continue
  return {'translation_mm':[x*1000 for x in delta],'linking_numbers_approx':lks}
 print('CLEAR',clear_count,'MAXLINK',maxlink,'CAND',maxcandidate,flush=True)
 return None
results={}
for sign,pin,other in [(-1,'UNIT48_PENDING_ConnectorPin_1','PENDING_ClaspAttachmentEye')]:
 name='PENDING_EndJump_'+str(sign);curve=centers(name);c=sum(curve,Vector())/len(curve);u=(curve[0]-c).normalized();v=Vector((-u.y,u.x,0));pp=sum(geometry[pin][0],Vector())/len(geometry[pin][0]);ee=sum(centers(other),Vector())/len(centers(other));print('INITIAL',linking(centers(other),curve,Vector()),'PIN',((pp-c).dot(u)*1000,(pp-c).dot(v)*1000),'EYE',((ee-c).dot(u)*1000,(ee-c).dot(v)*1000),flush=True);results[name]=fit([name],[(centers(other),centers(name))],None);print(name,results[name],flush=True)
(B/'outward-end-fit.json').write_text(json.dumps(results,indent=2))
