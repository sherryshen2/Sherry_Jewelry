"""Rebuild display LOD, then check its actual generated link geometry and interlocking."""
import bpy,bmesh,runpy,sys,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
BASE=Path(__file__).resolve().parent
sys.argv=['blender','--','--display'];g=runpy.run_path(str(BASE/'build_J001.py'))
links=g['chain_links'];dg=bpy.context.evaluated_depsgraph_get();trees={};boxes={}
for o in links:
 me=o.evaluated_get(dg).to_mesh();bm=bmesh.new();bm.from_mesh(me);bm.transform(o.matrix_world)
 trees[o.name]=BVHTree.FromBMesh(bm);boxes[o.name]=([min(v.co[k] for v in bm.verts) for k in range(3)],[max(v.co[k] for v in bm.verts) for k in range(3)]);bm.free();o.evaluated_get(dg).to_mesh_clear()
intersections=[]
for i,a in enumerate(links):
 for b in links[i+1:]:
  x=boxes[a.name];y=boxes[b.name]
  if all(x[0][k]<=y[1][k] and y[0][k]<=x[1][k] for k in range(3)) and trees[a.name].overlap(trees[b.name]):intersections.append([a.name,b.name])
def line(o):return [o.matrix_world@(sum((o.data.vertices[i+j].co for j in range(6)),Vector())/6) for i in range(0,len(o.data.vertices),6)]
unlinked=[];checked=0
for side in ['L','R']:
 seq=sorted([o for o in links if o['sequence_side']==side],key=lambda o:o['sequence_index'])
 for a,b in zip(seq,seq[1:]):
  inv=a.matrix_world.inverted();pa=[inv@p for p in line(a)];pb=[inv@p for p in line(b)];rx=max(abs(p.x) for p in pa);rz=max(abs(p.z) for p in pa);inside=0
  for p,q in zip(pb,pb[1:]+pb[:1]):
   if (p.y<0<=q.y) or (q.y<0<=p.y):
    v=p.lerp(q,-p.y/(q.y-p.y));inside+=int((v.x/rx)**2+(v.z/rz)**2<1)
  checked+=1
  if inside!=1:unlinked.append([a.name,b.name])
r={'lod':'display','adjacent_pairs_checked':checked,'chain_mesh_intersections':intersections,'unlinked_adjacent_pairs':unlinked}
(BASE/'J001-display-chain-validation-v01.json').write_text(json.dumps(r,indent=2));print(json.dumps(r),flush=True)
