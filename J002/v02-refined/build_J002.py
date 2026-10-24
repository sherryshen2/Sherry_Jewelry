"""Blender 4.5 actual editable J002 closed-pair refinement. Params mm, geometry meters.
Run --display for the lightweight GLB. All hidden closure geometry remains PENDING.
"""
import bpy,bmesh,json,math,sys
from pathlib import Path
from mathutils import Vector,Matrix
from math import sin,cos,pi
B=Path(__file__).resolve().parent;P=json.loads((B/'J002-parameters-v02.json').read_text());Q=P['provisional'];A=P['appearance'];MM=.001
DETAIL='--display' not in sys.argv;MODE='detail' if DETAIL else 'display'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.unit_settings.system='METRIC';s.unit_settings.length_unit='MILLIMETERS';s.unit_settings.scale_length=1
prod=bpy.data.collections.new('J002_PRODUCT_ONLY');s.collection.children.link(prod)
review=bpy.data.collections.new('REVIEW_ONLY_CAMERAS_LIGHTS');s.collection.children.link(review)
root=bpy.data.objects.new('J002_ROOT',None);prod.objects.link(root);root['stage']=P['stage'];root['inner_diameter_mm']=8.;root['outer_diameter_mm']=11.;root['stones_each']=8;root['prongs_each_stone']=4;root['exposed_stone_side_height_mm']=.5
left=bpy.data.objects.new('J002_A_MASTER',None);prod.objects.link(left);left.parent=root;left['handedness']='same master provisionally, photo does not resolve left/right mechanical differences'
def mat(name,col,metal,rough,trans=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes.get('Principled BSDF');n.inputs['Base Color'].default_value=(*col,1);n.inputs['Metallic'].default_value=metal;n.inputs['Roughness'].default_value=rough;n.inputs['Transmission Weight'].default_value=trans;n.inputs['IOR'].default_value=2.15 if not metal else 1.45;m.diffuse_color=(*col,1);return m
silver=mat('M01_925Silver_appearance',A['silver_linear_rgb'],1,A['metal_roughness']);cz=mat('M02_ColorlessCZ_optics_EST',A['gem_linear_rgb'],0,A['gem_roughness'],A['gem_transmission'])
def mesh(name,vs,fs,material=silver,smooth=False,evidence='PENDING image-proportion estimate'):
 me=bpy.data.meshes.new(name+'_mesh');me.from_pydata([tuple(Vector(v)*MM) for v in vs],[],fs);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free()
 o=bpy.data.objects.new('A_'+name,me);prod.objects.link(o);o.parent=left;o.data.materials.append(material);o['evidence']=evidence
 for f in me.polygons:f.use_smooth=smooth
 return o

def frame(t):return Vector((0,-sin(t),cos(t))),Vector((0,-cos(t),-sin(t))),Vector((1,0,0))
def profile(thick,width,r):
 out=[];steps=4 if DETAIL else 2
 for a,b,start in [(thick/2-r,width/2-r,0),(-thick/2+r,width/2-r,90),(-thick/2+r,-width/2+r,180),(thick/2-r,-width/2+r,270)]:
  for k in range(steps+1):t=math.radians(start+90*k/steps);out.append((a+r*cos(t),b+r*sin(t)))
 return out

def arcbody(name,a,b,outer,taper=False):
 count=128 if DETAIL else 56;angles=[math.radians(a+(b-a)*i/count) for i in range(count+1)]
 for deg in [90,180,270]:
  if a<deg<b:angles.append(math.radians(deg))
 angles=sorted(set(angles));pf=profile(outer-4,Q['axial_width_mm'],Q['edge_round_mm']);n=len(pf);v=[];f=[]
 for t in angles:
  normal,_,_=frame(t);widthscale=1
  if taper:widthscale=1-.75*max(0,min(1,(math.degrees(t)-171)/8.6))
  for rr,xx in pf:v.append(normal*((outer+4)/2+rr)+Vector((xx*widthscale,0,0)))
 for i in range(len(angles)-1):
  for k in range(n):j=(k+1)%n;f.append((i*n+k,i*n+j,(i+1)*n+j,(i+1)*n+k))
 f.extend([tuple(reversed(range(n))),tuple((len(angles)-1)*n+k for k in range(n))])
 o=mesh(name,v,f,smooth=True,evidence='8 mm bore and 11 mm outer reference circle per user; axial width and section estimated')
 bevel=o.modifiers.new('Soft_terminal_edges','BEVEL');bevel.width=.000025;bevel.segments=3 if DETAIL else 2;bevel.limit_method='ANGLE';bevel.angle_limit=.65
 return o
front=arcbody('01_FrontStoneCarrier_EST',16,179.6,Q['front_metal_outer_radius_mm'],True)
rear=arcbody('02_RearSmoothHoop_EST',180.4,336,Q['rear_metal_outer_radius_mm'])

def tube(name,path,r,closed=False,segments=None,evidence='PENDING hidden joint geometry'):
 ns=segments or (14 if DETAIL else 8);pts=[Vector(p) for p in path];vs=[];fs=[]
 for i,p in enumerate(pts):
  prev=pts[(i-1)%len(pts)] if closed else pts[max(0,i-1)];nex=pts[(i+1)%len(pts)] if closed else pts[min(len(pts)-1,i+1)];t=(nex-prev).normalized();axis=Vector((1,0,0))
  if abs(t.dot(axis))>.9:axis=Vector((0,1,0))
  u=t.cross(axis).normalized();w=t.cross(u).normalized()
  for k in range(ns):vs.append(p+r*(u*cos(2*pi*k/ns)+w*sin(2*pi*k/ns)))
 for i in range(len(pts) if closed else len(pts)-1):
  j=(i+1)%len(pts)
  for k in range(ns):l=(k+1)%ns;fs.append((i*ns+k,i*ns+l,j*ns+l,j*ns+k))
 if not closed:fs.extend([tuple(reversed(range(ns))),tuple((len(pts)-1)*ns+k for k in range(ns))])
 return mesh(name,vs,fs,smooth=True,evidence=evidence)
def ball(name,pos,r):
 ns=16 if DETAIL else 10;nr=10 if DETAIL else 6;vs=[Vector(pos)+Vector((0,0,r))];fs=[]
 for j in range(1,nr):
  a=pi*j/nr
  for i in range(ns):t=2*pi*i/ns;vs.append(Vector(pos)+Vector((r*sin(a)*cos(t),r*sin(a)*sin(t),r*cos(a))))
 end=len(vs);vs.append(Vector(pos)-Vector((0,0,r)))
 for i in range(ns):fs.append((0,1+i,1+(i+1)%ns))
 for j in range(nr-2):
  for i in range(ns):a=1+j*ns+i;b=1+j*ns+(i+1)%ns;fs.append((a,b,b+ns,a+ns))
 for i in range(ns):fs.append((end,1+(nr-2)*ns+(i+1)%ns,1+(nr-2)*ns+i))
 return mesh(name,vs,fs,smooth=True)
def annular_axle(name,x0,x1,ro,ri):
 n=48 if DETAIL else 24;vs=[];fs=[]
 for x,r in [(x0,ro),(x1,ro),(x1,ri),(x0,ri)]:
  for i in range(n):a=2*pi*i/n;vs.append((x,r*cos(a),-4.75+r*sin(a)))
 for k in range(4):
  for i in range(n):j=(i+1)%n;l=(k+1)%4;fs.append((k*n+i,k*n+j,l*n+j,l*n+i))
 return mesh(name,vs,fs,smooth=True,evidence='Bottom hinge region visible; knuckle split and pin dimensions PENDING')
def boolean(o,cutter,label):
 mod=o.modifiers.new(label,'BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter;return mod
# Hidden editable cutter collection: not exported, renders or product geometry.
cutters=bpy.data.collections.new('PENDING_EDITABLE_CUTTERS_NOT_FOR_EXPORT');s.collection.children.link(cutters)
def move_cutter(o):
 for c in list(o.users_collection):c.objects.unlink(o)
 cutters.objects.link(o);o.hide_render=True;o.hide_set(True)
# Fork clearance in lower rear half, allowing the center front knuckle to occupy the axle.
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,.00040,-.00475));cut=bpy.context.object;cut.name='PENDING_RearClevisSlot';cut.dimensions=(.00054,.00140,.00135);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);cut.parent=left;move_cutter(cut);boolean(rear,cut,'PENDING_hinge_clevis_clearance')
annular_axle('PENDING_03_HingeFrontCenterKnuckle',-.20,.20,.49,.17)
annular_axle('PENDING_03_HingeRearKnuckle_L',-.76,-.30,.49,.17)
annular_axle('PENDING_03_HingeRearKnuckle_R',.30,.76,.49,.17)
tube('PENDING_03_HingeAxle',[(-.78,0,-4.75),(.78,0,-4.75)],.15,segments=24 if DETAIL else 12)
# Upper curved earwire, retained as a separate editable closed-pose part.
wirepath=[]
for i in range(49 if DETAIL else 25):
 t=math.radians(18-48*i/(48 if DETAIL else 24));wirepath.append(frame(t)[0]*Q['earwire_arc_radius_mm'])
wire=tube('PENDING_04_Earwire_CLOSED',wirepath,Q['earwire_diameter_mm']/2,evidence='Top curved earwire visible; exact diameter/length and engagement depth PENDING')
# Receiver bore follows only the engaged end of the earwire. No invented open animation.
slotpath=[frame(math.radians(-19-15*i/20))[0]*5.15 for i in range(21)]
slot=tube('PENDING_LockChannelCutter',slotpath,.365);move_cutter(slot);boolean(rear,slot,'PENDING_closed_receiver_channel')
# A tiny rounded lip near the receiver marks the locking region; spring internals not invented.
normal,tan,axis=frame(math.radians(335));lip=tube('PENDING_05_LockReceiverLip',[normal*5.28+axis*x for x in [-.55,.55]],.12)

def claw(name,normal,tan,axis,a,b,r):
 # One watertight rounded post with a gently inward bent tip. Four independent posts per stone.
 rings=[];ns=20 if DETAIL else 12
 for rr,xx,yy,rad in [(4.77,.54,.53,.06),(4.81,.54,.53,.115),(4.97,.54,.53,.115),(5.10,.53,.51,.115),(5.18,.50,.48,.118),(5.23,.48,.46,.105),(5.28,.48,.46,.065)]:
  rings.append((normal*rr+axis*(a*xx)+tan*(b*yy),rad))
 vs=[];fs=[]
 for c,rad in rings:
  for k in range(ns):
   theta=2*pi*k/ns;vs.append(c+axis*(rad*cos(theta))+tan*(rad*sin(theta)))
 for row in range(len(rings)-1):
  for k in range(ns):j=(k+1)%ns;fs.append((row*ns+k,row*ns+j,(row+1)*ns+j,(row+1)*ns+k))
 bottom=len(vs);vs.append(normal*4.75+axis*(a*.54)+tan*(b*.53))
 top=len(vs);vs.append(normal*5.30+axis*(a*.48)+tan*(b*.46))
 for k in range(ns):
  j=(k+1)%ns;fs.append((bottom,j,k));fs.append((top,(len(rings)-1)*ns+k,(len(rings)-1)*ns+j))
 return mesh(name,vs,fs,smooth=True,evidence='Four claws per stone confirmed by user; exact post profile and location estimated')

def gemstone(index,angle):
 normal,tan,axis=frame(math.radians(angle));c=normal*Q['stone_girdle_radius_mm'];r=Q['gem_diameter_mm']/2;n=24 if DETAIL else 16;vs=[];fs=[]
 # Offset crown and pavilion rings make distinct planar triangular facets, with no emissive material.
 rings=[(r*.47,.35,pi/n),(r*.77,.18,0),(r,.025,0),(r,-.025,0),(r*.42,-.31,pi/n)]
 for rr,z,phase in rings:
  for i in range(n):a=2*pi*i/n+phase;vs.append(c+axis*rr*cos(a)+tan*rr*sin(a)+normal*z)
 fs.append(tuple(range(n)))
 for row in range(len(rings)-1):
  for i in range(n):
   a=row*n+i;b=row*n+(i+1)%n;aa=a+n;bb=b+n
   if row==2:fs.append((a,b,bb,aa))
   else:fs.extend([(a,b,aa),(b,bb,aa)])
 tip=len(vs);vs.append(c-normal*.42)
 for i in range(n):fs.append(((len(rings)-1)*n+i,(len(rings)-1)*n+(i+1)%n,tip))
 stone=mesh(f'06_CZ_{index:02}',vs,fs,cz,evidence='Exactly 8 colorless CZ per earring and 0.5 mm exposed side height per user; diameter, spacing and cut estimated');stone['stone_index']=index;stone['angle_deg']=angle;stone['exposed_side_height_mm']=.5;stone['prongs']=4
 boolean(front,stone,'Fitted_gem_seat_%02d'%index)
 for a in [-1,1]:
  for b in [-1,1]:
   pr=claw(f'07_Prongs_{index:02}_{a}_{b}',normal,tan,axis,a,b,r);pr['stone_index']=index;pr['prong_count']=1
   boolean(pr,stone,'Fitted_crown_seat');w=pr.modifiers.new('Remove_tiny_seat_slivers','WELD');w.merge_threshold=.00000001
 return stone
stones=[gemstone(i+1,t) for i,t in enumerate(Q['stone_angles_deg'])]
# Retain axis/receiver/fixed front relation as custom metadata, without claiming functioning mechanics.
left['pose']='fixed closed';left['mechanism']='No animation; pin, barrels and receiver only reference-informed provisional geometry';left['stone_count']=8
# Make a second earring with shared mesh data and remapped Boolean cutters.
right=bpy.data.objects.new('J002_B_INSTANCE_PENDING_HANDEDNESS',None);prod.objects.link(right);right.parent=root;right['handedness']='Same master, orientation differs; not a verified handed pair'
originals=list(left.children);mapping={}
for o in originals:
 copy=o.copy();copy.name=o.name.replace('A_','B_',1) if o.name.startswith('A_') else 'B_'+o.name
 collection=cutters if o in list(cutters.objects) else prod;collection.objects.link(copy);copy.parent=right;mapping[o]=copy
 if collection==cutters:copy.hide_render=True;copy.hide_set(True)
for old,new in mapping.items():
 for m in new.modifiers:
  if m.type=='BOOLEAN' and m.object in mapping:m.object=mapping[m.object]
left.location=Vector(P['pair_pose']['left_position_mm'])*MM;left.rotation_euler.z=math.radians(P['pair_pose']['left_z_rotation_deg'])
right.location=Vector(P['pair_pose']['right_position_mm'])*MM;right.rotation_euler.z=math.radians(P['pair_pose']['right_z_rotation_deg'])
bpy.context.view_layer.update()
# Photography only: separate from glTF product.
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=64;s.cycles.use_denoising=True;s.cycles.max_bounces=8;s.cycles.transmission_bounces=6;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.world.use_nodes=True
s.world.node_tree.nodes['Background'].inputs[0].default_value=(*A['review_world_linear_rgb'],1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.6;s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast'
def area(name,pos,energy,size):
 d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);review.objects.link(o);o.location=pos;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
area('Key',(-.04,-.045,.055),.22,.020);area('Rim',(.045,.025,.04),.20,.012);area('FrontStrip',(.015,-.06,-.012),.06,.008);area('Rear',(-.02,.06,.005),.08,.02)
def cam(name,direction,target,scale):
 d=bpy.data.cameras.new(name);d.type='ORTHO';d.ortho_scale=scale;d.clip_start=.0001;d.clip_end=1;o=bpy.data.objects.new(name,d);review.objects.link(o);o.location=Vector(target)+Vector(direction).normalized()*.12;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
for label,direction in [('front',(0,-1,0)),('side',(1,0,0)),('back',(0,1,0)),('45deg',(1,-1,.25)),('bottom',(1,-1,-.8))]:
 cam('CAM_SINGLE_'+label,left.rotation_euler.to_matrix()@Vector(direction),left.location,.0155)
cam('CAM_PAIR_default',(0,-1,.25),(0,0,0),.027);cam('CAM_PAIR_front',(0,-1,0),(0,0,0),.027)
s.camera=bpy.data.objects['CAM_PAIR_default'];s.render.resolution_x=1200;s.render.resolution_y=900
for file in ['build_J002.py','J002-parameters-v02.json']:
 text=bpy.data.texts.new(file);text.write((B/file).read_text())
for screen in bpy.data.screens:
 for ar in screen.areas:
  if ar.type=='VIEW_3D':ar.spaces.active.clip_start=.0001;ar.spaces.active.clip_end=2;ar.spaces.active.region_3d.view_distance=.045
if DETAIL:bpy.ops.wm.save_as_mainfile(filepath=str(B/'J002-source-v02.blend'))
# Batch only final product geometry by material, preserving editable source separately.
dg=bpy.context.evaluated_depsgraph_get();parts=[o for o in prod.objects if o.type=='MESH'];points=[];triangles=0;singlepoints=[]
for o in parts:
 ev=o.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles();triangles+=len(me.loop_triangles);points.extend(o.matrix_world@v.co for v in me.vertices)
 if o.parent==left:singlepoints.extend(left.matrix_world.inverted()@o.matrix_world@v.co for v in me.vertices)
 ev.to_mesh_clear()
batches=[]
for material,label in [(silver,'Silver'),(cz,'CZ')]:
 bpy.ops.object.select_all(action='DESELECT');members=[o for o in parts if o.data.materials[0]==material];copies=[]
 for o in members:
  me=bpy.data.meshes.new_from_object(o.evaluated_get(dg),depsgraph=dg);copy=bpy.data.objects.new('export_'+o.name,me);s.collection.objects.link(copy);copy.matrix_world=o.matrix_world;copy.select_set(True);copies.append(copy)
 bpy.context.view_layer.objects.active=copies[0];bpy.ops.object.join();ob=bpy.context.object;ob.name='J002_'+label;ob.parent=root;batches.append(ob)
bpy.ops.object.select_all(action='DESELECT');root.select_set(True)
for o in batches:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(B/f'J002-{MODE}-v02.glb'),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_extras=True,export_cameras=False,export_lights=False)
for o in batches:bpy.data.objects.remove(o,do_unlink=True)
def bounds(ps):return [[min(v[k] for v in ps)*1000 for k in range(3)],[max(v[k] for v in ps)*1000 for k in range(3)]]
stats={'stage':P['stage'],'triangles':triangles,'source_mesh_objects':len(parts),'materials':2,'export_meshes':2,'stones_each':8,'stones_total':16,'bounds_mm':bounds(points),'single_local_bounds_mm':bounds(singlepoints),'files':{f.name:f.stat().st_size for f in B.glob('*.glb')}}
(B/f'J002-{MODE}-stats.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2));print('J002_BUILD_COMPLETE',json.dumps(stats),flush=True)
