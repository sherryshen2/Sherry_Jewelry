import bpy,bmesh,json,math,struct
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
B=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(B/'J004-source-v01.blend'));s=bpy.context.scene;dg=bpy.context.evaluated_depsgraph_get();prod=bpy.data.collections['J004_PRODUCT_ONLY'];obs=[o for o in prod.objects if o.type=='MESH'];trees={};boxes={};issues=[];points=[];samples={};local={}
for o in obs:
 ev=o.evaluated_get(dg);m=ev.to_mesh();bm=bmesh.new();bm.from_mesh(m);bad=sum(not e.is_manifold for e in bm.edges);zero=sum(f.calc_area()<1e-17 for f in bm.faces);vol=bm.calc_volume(signed=True)
 if bad or zero or vol<=0:issues.append({'object':o.name,'nonmanifold':bad,'zeroarea':zero,'volume':vol})
 bm.free();m.calc_loop_triangles();vs=[o.matrix_world@v.co for v in m.vertices];fs=[tuple(p.vertices) for p in m.loop_triangles];trees[o.name]=BVHTree.FromPolygons(vs,fs);boxes[o.name]=([min(v[k] for v in vs) for k in range(3)],[max(v[k] for v in vs) for k in range(3)]);points.extend(vs)
 local[o.name]=[v.co.copy() for v in m.vertices]
 if 'Prongs' in o.name:samples[o.name]=vs+[sum((vs[i] for i in f),Vector())/3 for f in fs]
 ev.to_mesh_clear()
def bh(a,b):return all(boxes[a][0][k]<=boxes[b][1][k] and boxes[b][0][k]<=boxes[a][1][k] for k in range(3))
def hit(a,b):return bool(bh(a,b) and trees[a].overlap(trees[b]))
stones=[o for o in obs if o.get('stone_role')];metal=[o for o in obs if not o.get('stone_role')];contacts={};prongfits=[];unsupported=[]
for stone in stones:
 contacts[stone.name]=[o.name for o in metal if hit(stone.name,o.name)]
 for o in metal:
  if o.name not in samples or not bh(o.name,stone.name):continue
  worst=0
  for v in samples[o.name]:
   p,n,_,d=trees[stone.name].find_nearest(v)
   if p is not None and (v-p).dot(n)<-.000002:worst=max(worst,d*1000)
  if worst:prongfits.append({'prong':o.name,'stone':stone.name,'sample_depth_mm':worst})
for o in metal:
 if 'Prongs' in o.name and not any(x.parent==o.parent and 'Prongs' not in x.name and hit(o.name,x.name) for x in metal):unsupported.append(o.name)
nonown=[]
for stone in stones:
 for other in obs:
  if other.parent!=stone.parent and hit(stone.name,other.name):nonown.append([stone.name,other.name])
connectors=[o for o in obs if any(x in o.name for x in ['MainConnector_','Jump','Chain','TailLink','TailGemRing','AdjustmentRing'])]
linkcollisions=[]
for i,a in enumerate(connectors):
 for b in connectors[i+1:]:
  if hit(a.name,b.name):linkcollisions.append([a.name,b.name])
linkbody=[]
for a in connectors:
 for b in metal:
  if b in connectors:continue
  if hit(a.name,b.name):linkbody.append([a.name,b.name])
master=bpy.data.objects['J004_UNIT_01_MASTER'];v=[p for o in master.children if o.name in local for p in local[o.name]];unitdims=[(max(x[k] for x in v)-min(x[k] for x in v))*1000 for k in range(3)]
par=[o for o in prod.objects if o.type=='EMPTY' and o.name.startswith('J004_UNIT_')];centers=[o.location for o in sorted(par,key=lambda x:x['unit_index'])];spacing=[(centers[i+1]-centers[i]).length*1000 for i in range(47)]
guide=bpy.data.objects['PATH_CLOSED_160mm_NOT_PRODUCT'];p=[Vector(q.co[:3]) for q in guide.data.splines[0].points];perim=sum((p[(i+1)%len(p)]-p[i]).length for i in range(len(p)))*1000
framing={}
for cam in [o for o in s.objects if o.type=='CAMERA' and o.name not in ['CAM_UNIT','CAM_UNIT_SIDE','CAM_CLASP']]:
 s.render.resolution_x=1300;s.render.resolution_y=1050;co=[world_to_camera_view(s,cam,p) for p in points];framing[cam.name]=all(0<=v.x<=1 and 0<=v.y<=1 and v.z>0 for v in co)
r={'stage':'STRUCTURE_BLOCKOUT_AWAITING_CONFIRMATION','source_mesh_objects':len(obs),'mesh_issues':issues,'main_stones':sum(o['stone_role']=='main' for o in stones),'tail_stones':sum(o['stone_role']=='tail' for o in stones),'unit_dimensions_mm':unitdims,'unit_scales_one':all(max(abs(x-1) for x in o.scale)<1e-8 for o in par),'closed_centerline_length_mm':perim,'actual_center_chord_pitch_mm':[min(spacing),max(spacing)],'prongs_per_stone':{o.name:sum('Prongs' in x.name for x in o.parent.children) for o in stones},'stone_contacts':contacts,'unsupported_prongs':unsupported,'prong_intrusion_samples_over_0_002mm':prongfits,'stone_other_unit_or_closure_intersections':nonown,'link_link_surface_intersections':linkcollisions,'link_body_surface_intersections':linkbody,'full_camera_framing':framing,'lods':{},'limitations':['160 mm is closed wearing centerline. Tail excluded. Not a calibrated manufacturing flat end-to-end measurement.','Clasp, end rings, working-chain length and tail length are provisional','Side gallery windows visible; underside and hidden linkage construction provisional','Prong fit sampled vertices and triangle centers, tolerance 0.002 mm']}
for mode in ['detail','display']:
 path=B/f'J004-{mode}-v01.glb'
 if not path.exists():continue
 data=path.read_bytes();nn=struct.unpack_from('<I',data,12)[0];g=json.loads(data[20:20+nn]);[bpy.data.objects.remove(o,do_unlink=True) for o in list(bpy.data.objects)];bpy.ops.import_scene.gltf(filepath=str(path));vs=[];tri=0;bad=[]
 for o in s.objects:
  if o.type!='MESH':continue
  m=o.data;m.calc_loop_triangles();tri+=len(m.loop_triangles);vs.extend(o.matrix_world@v.co for v in m.vertices)
  if any(not math.isfinite(v.normal.length) or v.normal.length<.9 for v in m.vertices):bad.append(o.name)
 rt=bpy.data.objects.get('J004_ROOT');r['lods'][mode]={'bytes':len(data),'triangles':tri,'materials':len(g['materials']),'meshes':len(g['meshes']),'images':len(g.get('images',[])),'cameras':len(g.get('cameras',[])),'invalid_normals':bad,'bounds_mm':[[min(v[k] for v in vs)*1000 for k in range(3)],[max(v[k] for v in vs)*1000 for k in range(3)]],'root_location':list(rt.location) if rt else None,'root_scale':list(rt.scale) if rt else None,'extensions':g.get('extensionsUsed',[])}
 sp=B/f'J004-{mode}-stats.json';st=json.loads(sp.read_text());st.setdefault('source_evaluated_triangles',st['triangles']);st['triangles']=tri;st['files']={p.name:p.stat().st_size for p in B.glob('*.glb')};sp.write_text(json.dumps(st,ensure_ascii=False,indent=2))
(B/'J004-validation-v01.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));print(json.dumps(r,ensure_ascii=False,indent=2),flush=True)
