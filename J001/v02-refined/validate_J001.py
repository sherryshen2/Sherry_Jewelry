"""Validate actual saved meshes, link interlocking, and GLB round trips."""
import bpy,bmesh,json,math,struct
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
BASE=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(BASE/'J001-source-v02.blend'))
scene=bpy.context.scene;dg=bpy.context.evaluated_depsgraph_get()
objects=[o for o in bpy.data.collections['J001_PRODUCT_ONLY'].objects if o.type=='MESH']
issues=[];bvh={};bounds={};allverts=[]
for o in objects:
 ev=o.evaluated_get(dg);me=ev.to_mesh();bm=bmesh.new();bm.from_mesh(me)
 bad=sum(not e.is_manifold for e in bm.edges);zero=sum(f.calc_area()<1e-17 for f in bm.faces);vol=bm.calc_volume(signed=True)
 if bad or zero or vol<=0:issues.append({'object':o.name,'nonmanifold_edges':bad,'zero_area_faces':zero,'signed_volume':vol})
 bm.transform(o.matrix_world);coords=[v.co.copy() for v in bm.verts];allverts.extend(coords)
 bounds[o.name]=([min(v[k] for v in coords) for k in range(3)],[max(v[k] for v in coords) for k in range(3)])
 bvh[o.name]=BVHTree.FromBMesh(bm);bm.free();ev.to_mesh_clear()
def overlap_box(a,b):return all(a[0][k]<=b[1][k] and b[0][k]<=a[1][k] for k in range(3))
links=[o for o in objects if o.get('part')=='chain'];crossings=[]
for i,a in enumerate(links):
 for b in links[i+1:]:
  if overlap_box(bounds[a.name],bounds[b.name]) and bvh[a.name].overlap(bvh[b.name]):crossings.append([a.name,b.name])
def centerline(o):
 # Build template uses 36 centerline samples and 8 wire samples in detail mode.
 verts=o.data.vertices;wire=8
 return [o.matrix_world@(sum((verts[i+j].co for j in range(wire)),Vector())/wire) for i in range(0,len(verts),wire)]
def interlocked(a,b):
 pa=centerline(a);pb=centerline(b);inv=a.matrix_world.inverted();aa=[inv@p for p in pa];bb=[inv@p for p in pb]
 rx=max(abs(p.x) for p in aa);rz=max(abs(p.z) for p in aa);hits=[]
 for p,q in zip(bb,bb[1:]+bb[:1]):
  if (p.y<0 and q.y>=0) or (q.y<0 and p.y>=0):
   t=-p.y/(q.y-p.y);h=p.lerp(q,t);hits.append((h.x/rx)**2+(h.z/rz)**2<1)
 return sum(hits)==1,len(hits)
unlinked=[];pairs=0
for side in ['L','R']:
 ordered=sorted([o for o in links if o.get('sequence_side')==side],key=lambda o:o['sequence_index'])
 for a,b in zip(ordered,ordered[1:]):
  linked,hits=interlocked(a,b);pairs+=1
  if not linked:unlinked.append({'pair':[a.name,b.name],'plane_crossings':hits})
 mounts=[o for o in objects if o.name=='PENDING_SideMount_'+('-1' if side=='L' else '1')]
 if mounts:
  linked,hits=interlocked(mounts[0],ordered[0])
  if not linked:unlinked.append({'pair':[mounts[0].name,ordered[0].name],'plane_crossings':hits})
hardware_loop_intersections=[];hardware_loop_unlinked=[]
for an,bn in [('PENDING_ChainLink_L_109','PENDING_ClaspEndRing_L'),('PENDING_ChainLink_R_109','PENDING_ClaspEndRing_R'),('PENDING_ClaspEndRing_L','PENDING_LobsterLeftEye')]:
 a=bpy.data.objects[an];b=bpy.data.objects[bn]
 if bvh[an].overlap(bvh[bn]):hardware_loop_intersections.append([an,bn])
 linked,hits=interlocked(a,b)
 if not linked:hardware_loop_unlinked.append([an,bn])
stone=bpy.data.objects['02_RaisedPinkHeart_Cut_PENDING'];stone_contacts=[]
for o in objects:
 if o.data.materials[0].name.startswith('M01') and overlap_box(bounds[stone.name],bounds[o.name]) and bvh[stone.name].overlap(bvh[o.name]):stone_contacts.append(o.name)
pendant_connections={}
for o in objects:
 if o.get('part')!='pendant' or o==stone:continue
 pendant_connections[o.name]=[b.name for b in objects if b!=o and b.get('part')=='pendant' and overlap_box(bounds[o.name],bounds[b.name]) and bvh[o.name].overlap(bvh[b.name])]
body=[o for o in objects if o.get('part')=='pendant' and 'SideMount' not in o.name]
bodylo=[min(bounds[o.name][0][k] for o in body) for k in range(3)];bodyhi=[max(bounds[o.name][1][k] for o in body) for k in range(3)]
framing={}
for cam in [o for o in scene.objects if o.type=='CAMERA']:
 close='PENDANT' in cam.name;coords=[]
 for o in objects:
  if close and o.get('part')!='pendant':continue
  ev=o.evaluated_get(dg);me=ev.to_mesh();coords.extend(world_to_camera_view(scene,cam,o.matrix_world@v.co) for v in me.vertices);ev.to_mesh_clear()
 scene.render.resolution_x=850 if close else 1100;scene.render.resolution_y=850 if close else 1400
 # Re-evaluate after setting camera render aspect.
 coords=[]
 for o in objects:
  if close and o.get('part')!='pendant':continue
  for corner in o.evaluated_get(dg).bound_box:coords.append(world_to_camera_view(scene,cam,o.matrix_world@Vector(corner)))
 framing[cam.name]={'all_in_frame':all(0<=p.x<=1 and 0<=p.y<=1 and p.z>0 for p in coords),'min_xy':[min(p[k] for p in coords) for k in range(2)],'max_xy':[max(p[k] for p in coords) for k in range(2)]}
source_bounds=[[min(v[k] for v in allverts) for k in range(3)],[max(v[k] for v in allverts) for k in range(3)]]
result={'stage':'REFINED_REVIEW_PENDING','source_mesh_count':len(objects),'source_mesh_issues':issues,'chain_mesh_intersections':crossings,'hardware_loop_intersections':hardware_loop_intersections,'hardware_loop_unlinked':hardware_loop_unlinked,'adjacent_link_pairs_checked':pairs,'unlinked_adjacent_pairs':unlinked,'main_stone_metal_contacts':stone_contacts,'pendant_part_contacts':pendant_connections,'pendant_body_dimensions_mm':[(bodyhi[k]-bodylo[k])*1000 for k in range(3)],'chain_centerline_length_mm':bpy.data.objects['J001_ROOT']['centerline_length_mm'],'camera_framing':framing,'lods':{},'limitations':['Clasp mechanism, link dimensions and counts are provisional','Link interlock test checks loop topology, not physical gravity/contact simulation','Metal attachment parts may intentionally overlap','400 mm is centerline convention, not verified manufactured length']}
for mode in ['detail','display']:
 path=BASE/f'J001-{mode}-v02.glb'
 if not path.exists():continue
 data=path.read_bytes();jlen=struct.unpack_from('<I',data,12)[0];meta=json.loads(data[20:20+jlen])
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(path));verts=[];badnorm=[];tri=0
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  me=o.data;me.calc_loop_triangles();tri+=len(me.loop_triangles);verts.extend(o.matrix_world@v.co for v in me.vertices)
  if any(not math.isfinite(v.normal.length) or v.normal.length<.9 for v in me.vertices):badnorm.append(o.name)
 bb=[[min(v[k] for v in verts) for k in range(3)],[max(v[k] for v in verts) for k in range(3)]];rt=bpy.data.objects.get('J001_ROOT')
 result['lods'][mode]={'bytes':path.stat().st_size,'triangles':tri,'meshes':len(meta.get('meshes',[])),'materials':len(meta.get('materials',[])),'images':len(meta.get('images',[])),'camera_count':len(meta.get('cameras',[])),'extensions':meta.get('extensionsUsed',[]),'root_found':rt is not None,'root_scale':list(rt.scale) if rt else None,'invalid_normals':badnorm,'bounds_mm':[[p*1000 for p in row] for row in bb],'max_bound_error_vs_detail_mm':max(abs(bb[i][k]-source_bounds[i][k])*1000 for i in range(2) for k in range(3))}
(BASE/'J001-validation-v02.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
