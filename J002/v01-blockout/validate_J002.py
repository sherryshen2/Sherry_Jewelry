"""Read actual Blender/GLB geometry. Tolerances in report; hidden closure remains provisional."""
import bpy,bmesh,json,math,struct
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
B=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(B/'J002-source-v01.blend'));s=bpy.context.scene;dg=bpy.context.evaluated_depsgraph_get();prod=bpy.data.collections['J002_PRODUCT_ONLY'];left=bpy.data.objects['J002_A_MASTER'];objects=[o for o in prod.objects if o.type=='MESH'];issues=[];trees={};boxes={};pts=[];samples={};single=[]
for o in objects:
 ev=o.evaluated_get(dg);me=ev.to_mesh();bm=bmesh.new();bm.from_mesh(me);bad=sum(not e.is_manifold for e in bm.edges);zero=sum(f.calc_area()<1e-17 for f in bm.faces);vol=bm.calc_volume(signed=True)
 if bad or zero or vol<=0:issues.append({'name':o.name,'nonmanifold':bad,'zero_area':zero,'signed_volume':vol})
 bm.free();vs=[o.matrix_world@v.co for v in me.vertices];me.calc_loop_triangles();fs=[tuple(p.vertices) for p in me.loop_triangles];trees[o.name]=BVHTree.FromPolygons(vs,fs);boxes[o.name]=([min(v[k] for v in vs) for k in range(3)],[max(v[k] for v in vs) for k in range(3)]);pts.extend(vs)
 if o.parent==left:single.extend(left.matrix_world.inverted()@v for v in vs)
 if 'Prongs_' in o.name:samples[o.name]=vs+[sum((vs[i] for i in f),Vector())/3 for f in fs]
 ev.to_mesh_clear()
def boxhit(a,b):return all(a[0][k]<=b[1][k] and b[0][k]<=a[1][k] for k in range(3))
stones=[o for o in objects if '_06_CZ_' in o.name];metal=[o for o in objects if o.data.materials[0].name.startswith('M01')]
stonecollisions=[]
for i,a in enumerate(stones):
 for b in stones[i+1:]:
  if boxhit(boxes[a.name],boxes[b.name]) and trees[a.name].overlap(trees[b.name]):stonecollisions.append([a.name,b.name])
contacts={}
for a in stones:contacts[a.name]=[b.name for b in metal if boxhit(boxes[a.name],boxes[b.name]) and trees[a.name].overlap(trees[b.name])]
prong_support={};intrusions=[]
for name,vs in samples.items():
 prong_support[name]=[b.name for b in metal if b.name!=name and boxhit(boxes[name],boxes[b.name]) and trees[name].overlap(trees[b.name])]
 for stone in stones:
  if not boxhit(boxes[name],boxes[stone.name]):continue
  ds=[]
  for v in vs:
   p,n,_,d=trees[stone.name].find_nearest(v)
   if p is not None and (v-p).dot(n)<-.000002:ds.append(d*1000)
  if ds:intrusions.append({'prong':name,'stone':stone.name,'max_sample_depth_mm':max(ds)})
# Distinct front/back pose parts are not welded; hinge axis intentionally has small radial clearance.
mechanism={}
for key in ['A','B']:
 pin=key+'_PENDING_03_HingeAxle';barrels=[o.name for o in objects if o.name.startswith(key+'_PENDING_03_Hinge') and o.name!=pin]
 mechanism[key]={'axle_barrel_surface_intersections':[x for x in barrels if trees[pin].overlap(trees[x])],'earwire_and_receiver_present':all(any(o.name==key+'_'+label for o in objects) for label in ['PENDING_04_Earwire_CLOSED','PENDING_05_LockReceiverLip'])}
# Verify unchanged identical mesh templates and separate opposite poses.
sharing=[]
for a in [o for o in objects if o.parent==left]:
 b=bpy.data.objects.get(a.name.replace('A_','B_',1));sharing.append(bool(b and b.data==a.data))
front=bpy.data.objects['A_01_FrontStoneCarrier_EST'];rear=bpy.data.objects['A_02_RearSmoothHoop_EST'];inner=min(math.hypot(v.co.y,v.co.z) for o in [front,rear] for v in o.data.vertices)*2000
framing={}
for cam in [o for o in s.objects if o.type=='CAMERA']:
 is_single='SINGLE' in cam.name;s.render.resolution_x=900 if is_single else 1200;s.render.resolution_y=900;coords=[]
 for o in objects:
  if is_single and o.parent!=left:continue
  ev=o.evaluated_get(dg);me=ev.to_mesh();coords.extend(world_to_camera_view(s,cam,o.matrix_world@v.co) for v in me.vertices);ev.to_mesh_clear()
 framing[cam.name]={'all_in_frame':all(0<=p.x<=1 and 0<=p.y<=1 and p.z>0 for p in coords)}
source_bounds=[[min(v[k] for v in pts)*1000 for k in range(3)],[max(v[k] for v in pts)*1000 for k in range(3)]]
r={'stage':'STRUCTURE_BLOCKOUT_AWAITING_CONFIRMATION','mesh_objects':len(objects),'source_mesh_issues':issues,'stones_A':sum(o.parent==left for o in stones),'stones_B':sum(o.parent!=left for o in stones),'stone_intersections':stonecollisions,'stone_contacts':contacts,'stones_without_contact':[n for n,c in contacts.items() if not c],'prongs_without_metal_connection':[n for n,c in prong_support.items() if not c],'prong_penetration_samples_over_0_002mm':intrusions,'bore_diameter_mm':inner,'single_outer_reference_circle_diameter_mm':2*max(math.hypot(v.y,v.z) for v in single)*1000,'single_local_dimensions_mm':[(max(v[k] for v in single)-min(v[k] for v in single))*1000 for k in range(3)],'source_bounds_mm':source_bounds,'same_master_meshes':all(sharing),'mechanism_checks':mechanism,'camera_framing':framing,'lods':{},'limitations':['No open reference; internal latch and hinge geometry are provisional','No opening animation or mechanical fit simulation','Prong penetration checks sample vertices and triangle centers; tolerance 0.002 mm','8 mm bore is body reference cylinder, 11 mm outer is reference circle including wire and rear body','Pair identical structure is unconfirmed inference']}
for mode in ['detail','display']:
 path=B/f'J002-{mode}-v01.glb'
 if not path.exists():continue
 data=path.read_bytes();n=struct.unpack_from('<I',data,12)[0];g=json.loads(data[20:20+n]);bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(path));vertices=[];tri=0;badnormal=[]
 for o in s.objects:
  if o.type!='MESH':continue
  m=o.data;m.calc_loop_triangles();tri+=len(m.loop_triangles);vertices.extend(o.matrix_world@v.co for v in m.vertices)
  if any(not math.isfinite(v.normal.length) or v.normal.length<.9 for v in m.vertices):badnormal.append(o.name)
 bb=[[min(v[k] for v in vertices)*1000 for k in range(3)],[max(v[k] for v in vertices)*1000 for k in range(3)]];rt=bpy.data.objects.get('J002_ROOT')
 r['lods'][mode]={'bytes':len(data),'triangles':tri,'meshes':len(g['meshes']),'materials':len(g['materials']),'images':len(g.get('images',[])),'cameras':len(g.get('cameras',[])),'root_found':rt is not None,'root_location':list(rt.location) if rt else None,'root_scale':list(rt.scale) if rt else None,'bounds_mm':bb,'max_bound_difference_vs_detail_source_mm':max(abs(bb[a][k]-source_bounds[a][k]) for a in range(2) for k in range(3)),'invalid_normals':badnormal,'extensions':g.get('extensionsUsed',[])}
(B/'J002-validation-v01.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));print(json.dumps(r,ensure_ascii=False,indent=2),flush=True)

# Viewer statistics use actual GLB triangle counts after exporter tessellation.
for mode,result in r['lods'].items():
 path=B/f'J002-{mode}-stats.json'
 if path.exists():
  stats=json.loads(path.read_text());stats.setdefault('source_evaluated_triangles',stats['triangles']);stats['triangles']=result['triangles'];stats['files']={x.name:x.stat().st_size for x in B.glob('*.glb')};path.write_text(json.dumps(stats,ensure_ascii=False,indent=2))
