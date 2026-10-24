"""Editable J004 blockout. Run with Blender 4.5, optional -- --display. Units mm -> meters."""
import bpy,bmesh,json,math,sys,bisect
from pathlib import Path
from mathutils import Vector,Matrix
from math import sin,cos,pi
B=Path(__file__).resolve().parent;P=json.loads((B/'J004-parameters-v02.json').read_text());Q=P['provisional'];C=P['confirmed'];A=P['appearance'];MM=.001;L=C['closed_wear_length_mm']
DETAIL='--display' not in sys.argv;MODE='detail' if DETAIL else 'display'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.unit_settings.system='METRIC';s.unit_settings.length_unit='MILLIMETERS'
prod=bpy.data.collections.new('J004_PRODUCT_ONLY');s.collection.children.link(prod)
review=bpy.data.collections.new('REVIEW_ONLY');s.collection.children.link(review)
paths=bpy.data.collections.new('EDITABLE_PATHS_NOT_FOR_EXPORT');s.collection.children.link(paths)
root=bpy.data.objects.new('J004_ROOT',None);prod.objects.link(root);root['stage']=P['stage'];root['closed_wear_length_mm']=L;root['main_stones']=C['main_stones'];root['tail_stones']=C['tail_stones']
parent=root

def material(name,col,metal,rough,trans=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes.get('Principled BSDF');n.inputs['Base Color'].default_value=(*col,1);n.inputs['Metallic'].default_value=metal;n.inputs['Roughness'].default_value=rough;n.inputs['Transmission Weight'].default_value=trans;n.inputs['IOR'].default_value=2.15 if not metal else 1.45;m.diffuse_color=(*col,1);return m
silver=material('M01_925Silver',A['silver_linear_rgb'],1,A['metal_roughness']);cz=material('M02_ColorlessCZ_EST',A['gem_linear_rgb'],0,A['gem_roughness'],A['gem_transmission'])
def mesh(name,vs,fs,mat=silver,smooth=False,evidence='PENDING reference-proportion geometry'):
 me=bpy.data.meshes.new(name+'_mesh');me.from_pydata([tuple(Vector(v)*MM) for v in vs],[],fs);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free()
 o=bpy.data.objects.new(name,me);prod.objects.link(o);o.parent=parent;o.data.materials.append(mat);o['evidence']=evidence
 for f in me.polygons:f.use_smooth=smooth
 return o

def tube(name,points,r,closed=False,ns=None):
 ns=ns or (10 if DETAIL else 6);ps=[Vector(p) for p in points];v=[];f=[]
 for i,p in enumerate(ps):
  prev=ps[(i-1)%len(ps)] if closed else ps[max(0,i-1)];nex=ps[(i+1)%len(ps)] if closed else ps[min(len(ps)-1,i+1)];t=(nex-prev).normalized();ref=Vector((0,0,1))
  if abs(t.dot(ref))>.9:ref=Vector((0,1,0))
  u=t.cross(ref).normalized();w=t.cross(u).normalized()
  for k in range(ns):a=2*pi*k/ns;v.append(p+r*(u*cos(a)+w*sin(a)))
 for i in range(len(ps) if closed else len(ps)-1):
  j=(i+1)%len(ps)
  for k in range(ns):l=(k+1)%ns;f.append((i*ns+k,i*ns+l,j*ns+l,j*ns+k))
 if not closed:f.extend([tuple(reversed(range(ns))),tuple((len(ps)-1)*ns+k for k in range(ns))])
 return mesh(name,v,f,smooth=True)
def ellipse_link(name,center,long,short,axis1,axis2,wire):
 n=32 if DETAIL else 20;c=Vector(center);u=Vector(axis1);v=Vector(axis2)
 return tube(name,[c+u*(long*cos(2*pi*i/n))+v*(short*sin(2*pi*i/n)) for i in range(n)],wire,True)
def rrpath(a,b,r,z):
 out=[];n=5 if DETAIL else 3
 for x,y,start in [(a-r,b-r,0),(-a+r,b-r,90),(-a+r,-b+r,180),(a-r,-b+r,270)]:
  for i in range(n):t=math.radians(start+90*i/(n-1));out.append((x+r*cos(t),y+r*sin(t),z))
 return out
def difference(o,c,label):
 m=o.modifiers.new(label,'BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=c

def empty(name):
 o=bpy.data.objects.new(name,None);prod.objects.link(o);o.parent=root;return o
# Local master coordinates: length X, width Y, bottom 0, table near Z=2 mm.
master=empty('J004_UNIT_01_MASTER');parent=master
sx_unit=Q['setting_length_mm']/2;sy_unit=Q['setting_width_mm']/2
n=24 if DETAIL else 16;r=Q['stone_diameter_mm']/(2*sx_unit);v=[];f=[]
rings=[(r*.45,1.96,pi/n),(r*.78,1.72,0),(r,1.52,0),(r,1.48,0),(r*.43,.87,pi/n)]
for rad,z,phase in rings:
 for i in range(n):t=2*pi*i/n+phase;v.append((rad*cos(t),rad*sin(t),z))
f.append(tuple(range(n)))
for row in range(4):
 for i in range(n):a=row*n+i;b=row*n+(i+1)%n;aa=a+n;bb=b+n;f.extend([(a,b,aa),(b,bb,aa)])
end=len(v);v.append((0,0,.52))
for i in range(n):f.append((4*n+i,4*n+(i+1)%n,end))
gem=mesh('UNIT01_CZ',v,f,cz,evidence='Round colorless CZ visible; 48 main plus one tail per user; diameter/cut estimated');gem['stone_role']='main'
base=tube('UNIT01_PENDING_BaseRing',rrpath(.82,.82,.20,.15),.15,True);base['evidence']='Side lower rail visible; underside opening provisional'
rail=tube('UNIT01_GalleryUpperRail',rrpath(.80,.80,.18,1.10),.12,True);difference(rail,gem,'Fitted_pavilion_seat')
for ax in [-1,1]:
 for ay in [-1,1]:
  vs=[];fs=[];ns=12 if DETAIL else 8
  levels=[(.08,.81,.15),(.22,.81,.19),(1.16,.81,.19),(1.36,.72,.19),(1.55,.62,.18),(1.78,.51,.17),(1.90,.45,.13),(1.97,.43,.065)]
  for z,xy,rad in levels:
   for i in range(ns):a=2*pi*i/ns;vs.append((ax*xy+rad*cos(a),ay*xy+rad*sin(a),z))
  for j in range(len(levels)-1):
   for i in range(ns):k=(i+1)%ns;fs.append((j*ns+i,j*ns+k,(j+1)*ns+k,(j+1)*ns+i))
  bottom=len(vs);vs.append((ax*.81,ay*.81,0));top=len(vs);vs.append((ax*.43,ay*.43,2.0))
  for i in range(ns):k=(i+1)%ns;fs.append((bottom,k,i));fs.append((top,(len(levels)-1)*ns+i,(len(levels)-1)*ns+k))
  claw=mesh(f'UNIT01_Prongs_{ax}_{ay}',vs,fs,smooth=True,evidence='Four rounded corner prongs and side-window basket visible; profile estimated');difference(claw,gem,'Fitted_gem_seat');m=claw.modifiers.new('Weld_numeric_slivers','WELD');m.merge_threshold=1e-8
# Provisional transverse pins, visible through side windows, captured by the connector loops.
for sx in [-1,1]:
 tube('UNIT01_PENDING_ConnectorPin_'+str(sx),[(sx*.65,-.81,.64),(sx*.65,.81,.64)],.05,ns=10 if DETAIL else 6)
# Requested wider/longer unit: bake XY dimensions into editable master meshes; height stays 2 mm.
for ob in master.children:
 if ob.type=='MESH':
  for vert in ob.data.vertices:vert.co.x*=sx_unit;vert.co.y*=sy_unit
  ob.data.update()
# Arc-length lookup: rigid units are positioned and rotated, never stretched.
N=24000;ratio=Q['ellipse_ratio'];raw=[Vector((ratio*sin(2*pi*i/N),cos(2*pi*i/N),0)) for i in range(N+1)];cum=[0.]
for i in range(N):cum.append(cum[-1]+(raw[i+1]-raw[i]).length)
scale=C['closed_wear_length_mm']/cum[-1];a=ratio*scale;b=scale;cum=[x*scale for x in cum]
def at(distance):
 d=distance%L;i=min(N-1,bisect.bisect_right(cum,d)-1);u=(d-cum[i])/(cum[i+1]-cum[i]);theta=2*pi*(i+u)/N
 pos=Vector((a*sin(theta),b*cos(theta),0));tan=Vector((a*cos(theta),-b*sin(theta),0)).normalized();return pos,tan
# Saved editable centerline curve carries the 160 mm closed reference path.
cu=bpy.data.curves.new('CLOSED_160mm_CENTERLINE','CURVE');cu.dimensions='3D';sp=cu.splines.new('POLY');sp.points.add(2399)
for i,p in enumerate(sp.points):q,_=at(L*i/2400);p.co=(*tuple(q*MM),1)
sp.use_cyclic_u=True;guide=bpy.data.objects.new('PATH_CLOSED_160mm_NOT_PRODUCT',cu);paths.objects.link(guide);guide.hide_render=True;guide.hide_set(True);guide['length_mm']=L;guide['ellipse_semiaxes_mm']=[a,b]
main_count=C['main_stones'];closure=Q['closure_zone_mm'];step=(L-closure-Q['setting_length_mm'])/(main_count-1);distances=[closure/2+Q['setting_length_mm']/2+i*step for i in range(main_count)]
source=list(master.children);units=[master]
for idx in range(2,main_count+1):
 par=empty(f'J004_UNIT_{idx:02}');mapping={}
 for old in source:
  o=old.copy();o.name=old.name.replace('UNIT01',f'UNIT{idx:02}');prod.objects.link(o);o.parent=par;mapping[old]=o
 for old,o in mapping.items():
  for m in o.modifiers:
   if m.type=='BOOLEAN' and m.object in mapping:m.object=mapping[m.object]
 units.append(par)
for i,(par,dist) in enumerate(zip(units,distances)):
 p,t=at(dist);par.location=p*MM;par.rotation_euler.z=math.atan2(t.y,t.x);par['unit_index']=i+1;par['path_distance_mm']=dist;par['body_dimensions_mm']=[Q['setting_length_mm'],Q['setting_width_mm'],C['setting_total_height_mm']];par['center_pitch_mm']=step
# Each connector is a separate interposed oblong loop in the XZ plane, passing through basket windows.
parent=root
for i in range(main_count-1):
 p,t=at((distances[i]+distances[i+1])/2);p.z=.64
 link=ellipse_link(f'PENDING_MainConnector_{i+1:02}',p,(step-1.30*sx_unit)/2+.30,.23,t,(0,0,1),Q['connector_wire_radius_mm']);link['evidence']='Connector between visible separate baskets; internal lug and exact shape pending'
# End rings and working adjustable chain, all independently editable.
for sign in [-1,1]:
 p,t=at(sign*9.15);p.z=.64
 ellipse_link('PENDING_EndJump_'+str(sign),p,1.60,.25,t,(0,0,1),.08)
# Lobster clasp: estimated outline from reference, solid rounded body, hollow hook, separate visible gate/lever.
clasp=empty('J004_PENDING_LOBSTER_CLASP');parent=clasp
cp,ct=at(-4.55);clasp.location=cp*MM;clasp.rotation_euler.z=math.atan2(ct.y,ct.x)+pi
outline=[(-3.8,0),(-3.65,.72),(-3.12,1.20),(-2.30,1.42),(-1.42,1.32),(-.60,.94),(.30,.59),(1.65,.40),(2.65,.30),(3.25,.05),(2.65,-.42),(1.20,-.69),(-.40,-1.00),(-1.70,-1.28),(-2.75,-1.12),(-3.45,-.65)]
# Scale 7.05 mm outline length to specified 7.2 mm.
outline=[(min(x*7.2/7.05,2.4),y) for x,y in outline]
vs=[(x,y,z) for z in [0,.95] for x,y in outline];nn=len(outline);fs=[tuple(reversed(range(nn))),tuple(nn+i for i in range(nn))]+[(i,(i+1)%nn,(i+1)%nn+nn,i+nn) for i in range(nn)]
body=mesh('PENDING_ClaspBody',vs,fs,smooth=True,evidence='Lobster clasp silhouette visible; dimensions and internal mechanism provisional')
bev=body.modifiers.new('Rounded_clasp_edges','BEVEL');bev.width=.00014;bev.segments=3 if DETAIL else 2
# Cutters are retained separately and omitted from export.
def hide_cutter(o):
 for col in list(o.users_collection):col.objects.unlink(o)
 paths.objects.link(o);o.hide_render=True;o.hide_set(True)
# Elliptical opening through the large hook end.
vs=[];fs=[];nn=48 if DETAIL else 24
for z in [-1,2]:
 for i in range(nn):t=2*pi*i/nn;vs.append((-2.12+1.05*cos(t),.03+.78*sin(t),z))
fs=[tuple(reversed(range(nn))),tuple(nn+i for i in range(nn))]+[(i,(i+1)%nn,(i+1)%nn+nn,i+nn) for i in range(nn)]
cut=mesh('PENDING_ClaspOpeningCutter',vs,fs);hide_cutter(cut);difference(body,cut,'Hook_opening')
# Visible closed gate seam: slender separate curved tongue near upper lip (not a functioning spring).
gate=tube('PENDING_ClaspClosedGate',[(-1.75,1.20,.54),(-1.10,1.02,.54),(-.45,.76,.54)],.18,ns=12 if DETAIL else 8)
lever=tube('PENDING_ClaspLever',[(-.05,-.82,.32),(.8,-1.04,.32),(1.45,-.85,.32)],.17)
ellipse_link('PENDING_ClaspAttachmentEye',(3.0,0,.64),.95,.55,(1,0,0),(0,1,0),.10)
parent=root
# Large receiving/adjustment ring intersects the hook opening, with clearance to its walls.
recv,rt=at(-.65);recv.z=.48
ellipse_link('PENDING_AdjustmentRing',recv,1.30,.90,rt,(0,0,1),.12)
for i,d in enumerate([1.1,2.7,4.3,5.9,7.5]):
 p,t=at(d);p.z=.64
 v=Vector((-t.y,t.x,0)) if i%2==0 else Vector((0,0,1))
 ellipse_link(f'PENDING_WorkingChain_{i+1:02}',p,1.02,.43,t,v,.10)
# Tail branches outward from the adjustment ring; length and link count provisional.
tail_start=recv-rt*.50+Vector((0,-.5,.77));tail_direction=Vector((-.06,1,0)).normalized();tail_positions=[]
for i in range(Q['tail_link_count']):
 dist=1.1+i*Q['tail_link_pitch_mm'];p=tail_start+tail_direction*dist;p.x+=.018*dist*dist;p.z=1.25
 tan=Vector((tail_direction.x+.036*dist,tail_direction.y,0)).normalized();v=Vector((-tan.y,tan.x,0)) if i%2==0 else Vector((0,0,1))
 ellipse_link(f'PENDING_TailLink_{i+1:02}',p,.98,(.80 if i==0 else .40),tan,v,.10);tail_positions.append(p)
tail_direction=tan
p=tail_positions[-1]+tail_direction*1.5;p.z=1.25
ellipse_link('PENDING_TailGemRing',p,1.12,.25,tail_direction,(0,0,1),.10)
tail=empty('J004_TAIL_STONE_49');tail.location=(p+tail_direction*(1.47+.65*(sx_unit-1))-Vector((0,0,.64)))*MM;tail.rotation_euler.z=math.atan2(tail_direction.y,tail_direction.x)
mapping={}
for old in source:
 o=old.copy();o.name=old.name.replace('UNIT01','TAIL49');prod.objects.link(o);o.parent=tail;mapping[old]=o
 if o.get('stone_role'):o['stone_role']='tail'
for old,o in mapping.items():
 for m in o.modifiers:
  if m.type=='BOOLEAN' and m.object in mapping:m.object=mapping[m.object]
# Small clearance adjustment preserves interlocking topology at the tail attachment.
for o in list(root.children):
 if o.name.startswith(('PENDING_TailLink','PENDING_TailGemRing','J004_TAIL_STONE')):o.location+=Vector(Q['tail_pose_translation_mm'])*MM
# Source-backed photography; never part of GLB.
bpy.context.view_layer.update();parent=root
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=32;s.cycles.use_denoising=True;s.cycles.max_bounces=8;s.cycles.transmission_bounces=6;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.10,.10,.10,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.6;s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast'
def area(name,loc,energy,size):
 d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);review.objects.link(o);o.location=loc;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
area('Key',(-.08,-.07,.11),2.5,.07);area('Strip',(.09,.03,.06),2.0,.025);area('Rim',(-.03,.10,.04),1.5,.04)
def camera(name,target,direction,ortho):
 d=bpy.data.cameras.new(name);d.type='ORTHO';d.ortho_scale=ortho;d.clip_start=.0001;d.clip_end=2;o=bpy.data.objects.new(name,d);review.objects.link(o);o.location=Vector(target)+Vector(direction).normalized()*.2;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
center=Vector((0,.005,.001));camera('CAM_TOP',center,(0,0,1),.084);camera('CAM_SIDE',center,(0,-1,.10),.084);camera('CAM_BACK',center,(0,1,.35),.084);camera('CAM_BOTTOM',center,(0,0,-1),.084);camera('CAM_DEFAULT',center,(.35,-.75,1.0),.084)
camera('CAM_UNIT',master.location+Vector((0,0,.001)),master.rotation_euler.to_matrix()@Vector((1,-1,1)),.0055)
camera('CAM_UNIT_SIDE',master.location+Vector((0,0,.001)),master.rotation_euler.to_matrix()@Vector((0,-1,.05)),.0048)
camera('CAM_CLASP',Vector((0,b*.001,.001)),(0,-.7,1),.032)
s.camera=bpy.data.objects['CAM_DEFAULT'];s.render.resolution_x=1200;s.render.resolution_y=1000
for name in ['build_J004.py','J004-parameters-v02.json']:
 txt=bpy.data.texts.new(name);txt.write((B/name).read_text())
for screen in bpy.data.screens:
 for ar in screen.areas:
  if ar.type=='VIEW_3D':ar.spaces.active.clip_start=.0001;ar.spaces.active.clip_end=2;ar.spaces.active.region_3d.view_distance=.12
if DETAIL:bpy.ops.wm.save_as_mainfile(filepath=str(B/'J004-source-v02.blend'))
# Evaluate repeated units only for export; source retains shared editable meshes and curve.
dg=bpy.context.evaluated_depsgraph_get();parts=[o for o in prod.objects if o.type=='MESH'];points=[];tris=0
for o in parts:
 ev=o.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles();tris+=len(me.loop_triangles);points.extend(o.matrix_world@v.co for v in me.vertices);ev.to_mesh_clear()
batches=[]
for mat,label in [(silver,'Silver'),(cz,'CZ')]:
 bpy.ops.object.select_all(action='DESELECT');copies=[]
 for o in parts:
  if o.data.materials[0]!=mat:continue
  me=bpy.data.meshes.new_from_object(o.evaluated_get(dg),depsgraph=dg);cp=bpy.data.objects.new('export_'+o.name,me);s.collection.objects.link(cp);cp.matrix_world=o.matrix_world;cp.select_set(True);copies.append(cp)
 bpy.context.view_layer.objects.active=copies[0];bpy.ops.object.join();ob=bpy.context.object;ob.name='J004_'+label;ob.parent=root;batches.append(ob)
bpy.ops.object.select_all(action='DESELECT');root.select_set(True)
for o in batches:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(B/f'J004-{MODE}-v02.glb'),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_extras=True,export_cameras=False,export_lights=False)
bb=[[min(v[k] for v in points)*1000 for k in range(3)],[max(v[k] for v in points)*1000 for k in range(3)]]
stats={'stage':P['stage'],'triangles':tris,'materials':2,'source_mesh_objects':len(parts),'stones_main':C['main_stones'],'stones_tail':C['tail_stones'],'bounds_mm':bb,'closed_path_length_mm':L,'ellipse_semiaxes_mm':[a,b],'main_center_pitch_mm':step,'straight_tangent_gap_mm':step-Q['setting_length_mm'],'closure_zone_mm':closure,'files':{p.name:p.stat().st_size for p in B.glob('*.glb')}}
(B/f'J004-{MODE}-stats.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2));print('J004_BUILD_COMPLETE',json.dumps(stats),flush=True)
