"""Blender 4.5: --background --factory-startup --python build_J001.py -- --render
Use --display for the low LOD. Source remains a review blockout with named pending parts.
All construction dimensions are mm; Blender coordinates and glTF exports are meters.
"""
import bpy,bmesh,json,math,sys
from pathlib import Path
from mathutils import Vector,Matrix
from math import sin,cos,pi

BASE=Path(__file__).resolve().parent
P=json.loads((BASE/'J001-parameters-v01.json').read_text())
Q=P['provisional'];E=P['pendant_estimates_mm'];A=P['appearance']
DETAIL='--display' not in sys.argv;MODE='detail' if DETAIL else 'display';MM=.001
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.length_unit='MILLIMETERS';scene.unit_settings.scale_length=1
product=bpy.data.collections.new('J001_PRODUCT_ONLY');scene.collection.children.link(product)
guides=bpy.data.collections.new('EDITABLE_PATHS_NOT_FOR_EXPORT');scene.collection.children.link(guides)
review=bpy.data.collections.new('REVIEW_ONLY_CAMERAS_LIGHTS');scene.collection.children.link(review)
root=bpy.data.objects.new('J001_ROOT',None);product.objects.link(root);root.empty_display_size=.008
root['stage']='结构草模；链节尺寸、数量、微爪、隐藏穿接细节待确认'
root['chain_length_mm']=P['chain_length_mm'];root['length_convention']=P['length_convention_pending']

def material(name,col,metal=0,rough=.2,trans=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;s=m.node_tree.nodes.get('Principled BSDF')
 s.inputs['Base Color'].default_value=(*col,1);s.inputs['Metallic'].default_value=metal;s.inputs['Roughness'].default_value=rough
 s.inputs['Transmission Weight'].default_value=trans;s.inputs['IOR'].default_value=A['ior_approximation'] if not metal else 1.45
 m.diffuse_color=(*col,1);return m
silver=material('M01_Silver_user_spec',A['silver_base_linear'],1,A['silver_roughness'])
pink=material('M02_PinkZircon_reference_approx',A['pink_base_linear'],0,A['pink_roughness'],A['pink_transmission'])
clear=material('PENDING_M03_ClaspCharm_light_stone',(.80,.84,.89),0,.035,.60)

def mesh(name,verts,faces,mat=silver,part='pendant',evidence='图片比例草稿',smooth=False):
 me=bpy.data.meshes.new(name+'_mesh');me.from_pydata([tuple(Vector(v)*MM) for v in verts],[],faces);me.update()
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free()
 o=bpy.data.objects.new(name,me);product.objects.link(o);o.parent=root;o.data.materials.append(mat)
 o['part']=part;o['evidence']=evidence
 for p in me.polygons:p.use_smooth=smooth
 return o

def face_xyz(p,d):return (p[0],-d,p[1])
segments=[((0,1.85),(.4,2.5),(.9,2.65),(1.3,2.55)),((1.3,2.55),(1.95,2.5),(2.55,2.1),(2.45,1.45)),((2.45,1.45),(2.6,0),(.9,-1.9),(0,-2.55)),((0,-2.55),(-.9,-1.9),(-2.6,0),(-2.45,1.45)),((-2.45,1.45),(-2.55,2.1),(-1.95,2.5),(-1.3,2.55)),((-1.3,2.55),(-.9,2.65),(-.4,2.5),(0,1.85))]
raw=[]
for seg in segments:
 for i in range(100):
  t=i/100;u=1-t;raw.append(Vector(tuple(u**3*seg[0][k]+3*u*u*t*seg[1][k]+3*u*t*t*seg[2][k]+t**3*seg[3][k] for k in range(2))))
xm=max(abs(p.x) for p in raw);ym=min(p.y for p in raw);yM=max(p.y for p in raw)
raw=[Vector((p.x/(2*xm),(p.y-(ym+yM)/2)/(yM-ym))) for p in raw]

def resample(points,n,closed=True):
 seq=points+[points[0]] if closed else points
 lens=[0]
 for a,b in zip(seq,seq[1:]):lens.append(lens[-1]+(b-a).length)
 result=[];j=0
 for i in range(n):
  d=lens[-1]*i/(n if closed else n-1)
  while j<len(lens)-2 and lens[j+1]<d:j+=1
  f=(d-lens[j])/max(lens[j+1]-lens[j],1e-12);result.append(seq[j].lerp(seq[j+1],f))
 return result
def heart(w,h,n=96):return [Vector((p.x*w,p.y*h)) for p in resample(raw,n)]
outline=heart(10,12,96)
def annulus(name,loops,depths,part='pendant'):
 n=len(loops[0]);v=[];f=[]
 for loop,d in zip(loops,depths):v.extend(face_xyz(p,d) for p in loop)
 for i in range(n):
  j=(i+1)%n
  for a,b in [(0,1),(1,2),(2,3),(3,0)]:f.append((a*n+i,a*n+j,b*n+j,b*n+i))
 o=mesh(name,v,f,part=part,evidence='背面心形开孔有图片依据；壁厚与内侧过渡按比例暂定',smooth=True)
 bevel=o.modifiers.new('Editable_edge_radius_0.08mm','BEVEL');bevel.width=.00008;bevel.segments=2 if DETAIL else 1
 return o
gallery=annulus('01_HeartCarrier_BackHeartWindow_EST',[[p*.98 for p in outline],[p*.57 for p in outline],[p*.78 for p in outline],outline],[-4,-4,1.1,1.1])

def heartgem():
 out=heart(E['stone_width'],E['stone_height'],48);v=[];f=[];N=48;M=12
 for i in range(M):v.append(face_xyz(out[4*i]*.43,4))
 for i in range(M):v.append(face_xyz(out[4*i+2]*.74,3.4))
 G=len(v)
 for d in [1.49,1.41]:v.extend(face_xyz(p,d) for p in out)
 PV=len(v)
 for i in range(24):v.append(face_xyz(out[2*i]*.45,-1.4))
 f.append(tuple(range(M)))
 for i in range(M):
  a=i;b=(i+1)%M;s=M+i;g=[G+(4*i+j)%N for j in range(5)]
  f.extend([(a,b,s),(a,s,g[2]),(a,g[2],g[1]),(a,g[1],g[0]),(b,g[4],g[3]),(b,g[3],g[2]),(b,g[2],s)])
 for i in range(N):f.append((G+i,G+(i+1)%N,G+N+(i+1)%N,G+N+i))
 for i in range(24):
  a=PV+i;b=PV+(i+1)%24;g0=G+N+2*i;g1=G+N+(2*i+1)%N;g2=G+N+(2*i+2)%N
  f.extend([(a,g0,g1),(a,g1,b),(b,g1,g2)])
 tip=len(v);v.append(face_xyz((0,-.25),-2.8))
 for i in range(24):f.append((PV+i,PV+(i+1)%24,tip))
 return mesh('02_RaisedPinkHeart_Cut_PENDING',v,f,pink,evidence='单颗凸出粉色心形石及朝向有参考；切割图近似')
stone=heartgem()

def ball(name,center,r,part='pendant',mat=silver):
 ns=12 if DETAIL else 8;nr=8 if DETAIL else 6;v=[Vector(center)+Vector((0,0,r))];f=[]
 for j in range(1,nr):
  a=pi*j/nr
  for i in range(ns):
   t=2*pi*i/ns;v.append(Vector(center)+Vector((r*sin(a)*cos(t),r*sin(a)*sin(t),r*cos(a))))
 bottom=len(v);v.append(Vector(center)+Vector((0,0,-r)))
 for i in range(ns):f.append((0,1+i,1+(i+1)%ns))
 for j in range(nr-2):
  for i in range(ns):
   a=1+j*ns+i;b=1+j*ns+(i+1)%ns;f.append((a,b,b+ns,a+ns))
 for i in range(ns):f.append((bottom,1+(nr-2)*ns+(i+1)%ns,1+(nr-2)*ns+i))
 return mesh(name,v,f,mat,part,'数量与布置待确认；银色金属珠按用户规格',True)
for i,p in enumerate(heart(9,10.8,Q['metal_bead_count'])):ball(f'PENDING_SilverRimBead_{i+1:02}',face_xyz(p,1.25),E['bead_radius'])

def tube(name,points,r,part='pendant',mat=silver,closed=False,ns=None):
 ns=ns or (10 if DETAIL else 6);v=[];f=[];points=[Vector(p) for p in points]
 for i,p in enumerate(points):
  prev=points[(i-1)%len(points)] if closed else points[max(i-1,0)]
  nex=points[(i+1)%len(points)] if closed else points[min(i+1,len(points)-1)]
  t=(nex-prev).normalized();axis=Vector((0,1,0))
  if abs(t.dot(axis))>.9:axis=Vector((1,0,0))
  u=t.cross(axis).normalized();w=t.cross(u).normalized()
  for k in range(ns):v.append(p+r*(u*cos(2*pi*k/ns)+w*sin(2*pi*k/ns)))
 for i in range(len(points) if closed else len(points)-1):
  j=(i+1)%len(points)
  for k in range(ns):f.append((i*ns+k,i*ns+(k+1)%ns,j*ns+(k+1)%ns,j*ns+k))
 if not closed:f.extend([tuple(reversed(range(ns))),tuple((len(points)-1)*ns+k for k in range(ns))])
 return mesh(name,v,f,mat,part,'可见结构的比例草稿；隐藏几何待确认',True)
for i,(x,z) in enumerate([(-2.4,3.4),(2.4,3.4),(0,-4.35)]):
 path=[(x,-.9,z),(x,-1.8,z),(x*.96,-2.5,z*.96),(x*.91,-2.7,z*.93)]
 tube(f'PENDING_MainProng_{i+1}',path,.24);ball(f'PENDING_MainProngCap_{i+1}',path[-1],.26)

def oval_data(a,b,r,name):
 n=36 if DETAIL else 24;ns=8 if DETAIL else 6;v=[];f=[]
 for i in range(n):
  t=2*pi*i/n;p=Vector((b*sin(t),0,a*cos(t)));normal=Vector((sin(t)/b,0,cos(t)/a)).normalized()
  for j in range(ns):
   u=2*pi*j/ns;v.append(p+r*(normal*cos(u)+Vector((0,1,0))*sin(u)))
 for i in range(n):
  for j in range(ns):f.append((i*ns+j,i*ns+(j+1)%ns,((i+1)%n)*ns+(j+1)%ns,((i+1)%n)*ns+j))
 o=mesh(name,v,f,part='chain',smooth=True);me=o.data;bpy.data.objects.remove(o,do_unlink=True);return me
def instance_link(name,data,pos,tangent,twist,part='chain'):
 t=Vector(tangent).normalized();normal=Vector((0,1,0));u=normal.cross(t).normalized();v=t.cross(u).normalized()
 ux=u*cos(twist)+v*sin(twist);vy=-u*sin(twist)+v*cos(twist)
 o=bpy.data.objects.new(name,data);product.objects.link(o);o.parent=root;o.location=Vector(pos)*MM
 o.rotation_euler=Matrix((ux,vy,t)).transposed().to_euler();o['part']=part;o['evidence']='链节为交替穿接的实体椭圆环；截面、数量与隐藏连接待确认'
 return o

def catmull(points):
 out=[]
 for i in range(len(points)-1):
  p0=points[max(0,i-1)];p1=points[i];p2=points[i+1];p3=points[min(i+2,len(points)-1)]
  for j in range(100):
   t=j/100;out.append(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t))
 out.append(points[-1]);return out
def path_length(points):return sum((b-a).length for a,b in zip(points,points[1:]))
base_controls=[Vector(p) for p in P['suspension']['left_controls_mm']]
start=base_controls[0];initial_tangent=(base_controls[1]-start).normalized()
mount_data=oval_data(.88,.52,.18,'mount_template')
mounts=[]
for sign in [-1,1]:
 p=Vector((sign*4,0,4.3));t=Vector((sign*abs(initial_tangent.x),0,initial_tangent.z))
 mounts.append(instance_link(f'PENDING_SideMount_{sign}',mount_data,p,t,-pi/4,'pendant'))

def controls_at(scale):
 controls=[p.copy() for p in base_controls]
 for i in range(1,len(controls)):
  controls[i].x*=scale;controls[i].y*=scale;controls[i].z=4.3+(controls[i].z-4.3)*scale
 controls[-1].x=-Q['clasp_assembly_span_mm']/2
 controls[0]=start+initial_tangent*1.48
 return controls
target=(P['chain_length_mm']-Q['clasp_assembly_span_mm'])/2
lo=.5;hi=2
for _ in range(55):
 mid=(lo+hi)/2
 if path_length(catmull(controls_at(mid)))<target:lo=mid
 else:hi=mid
scale=(lo+hi)/2;controls=controls_at(scale);left=catmull(controls);right=[Vector((-p.x,p.y,p.z)) for p in left]
hardware_y=left[-1].y;hardware_z=left[-1].z
chain_records=[];chain_links=[]
for side,points in [('L',left),('R',right)]:
 length=path_length(points);n=round(length/Q['link_pitch_target_mm'])+1
 special=n-13 if side=='R' else -1;extra=1.6 if special>=0 else 0
 pitch=(length-extra)/(n-1);a=(pitch+.4)/2;b=Q['link_semiminor_mm'];r=Q['link_wire_radius_mm']
 data=oval_data(a,b,r,'PENDING_LinkTemplate_'+side)
 specialdata=oval_data(a+.8,1.8,r,'PENDING_AdjustmentRingTemplate') if special>=0 else None
 distances=[0]
 for i in range(n-1):distances.append(distances[-1]+pitch+(.8 if i==special or i+1==special else 0))
 cumulative=[0]
 for pa,pb in zip(points,points[1:]):cumulative.append(cumulative[-1]+(pb-pa).length)
 j=0
 for i,d in enumerate(distances):
  while j<len(cumulative)-2 and cumulative[j+1]<d:j+=1
  f=(d-cumulative[j])/max(cumulative[j+1]-cumulative[j],1e-12);p=points[j].lerp(points[j+1],f);t=(points[min(j+3,len(points)-1)]-points[max(j-2,0)]).normalized()
  special_here=i==special
  o=instance_link(f'PENDING_{"AdjustmentRing" if special_here else "ChainLink"}_{side}_{i:03}',specialdata if special_here else data,p,t,pi/4+(i%2)*pi/2)
  o['sequence_side']=side;o['sequence_index']=i;o['centerline_distance_mm']=d;chain_links.append(o)
 chain_records.append({'side':side,'centerline_length_mm':length,'link_count_including_adjustment_ring':n,'regular_link_outer_length_mm':2*(a+r),'regular_link_outer_width_mm':2*(b+r),'wire_diameter_mm':2*r,'regular_center_pitch_mm':pitch,'adjustment_ring_index':special})
 cu=bpy.data.curves.new('EditableSuspension_'+side,'CURVE');cu.dimensions='3D';sp=cu.splines.new('POLY');sample=resample(points,140,False);sp.points.add(len(sample)-1)
 for q,p in zip(sp.points,sample):q.co=(*tuple(p*MM),1)
 co=bpy.data.objects.new('SOURCE_PATH_'+side,cu);guides.objects.link(co);co.hide_render=True;co.hide_set(True);co['controls_mm']=json.dumps([list(p) for p in (controls if side=='L' else [Vector((-p.x,p.y,p.z)) for p in controls])]);co['regenerate']='Edit suspension controls in JSON and rerun script; mesh links are generated along this path.'

def clasp_point(x,z=0,y=0):return Vector((x,hardware_y+y,hardware_z+z))
def hardware_ring(name,x,a,b,twist=0):return instance_link(name,oval_data(a,b,.28,name+'_template'),clasp_point(x),Vector((1,0,0)),twist,'hardware')
hardware_ring('PENDING_ClaspEndRing_L',-12.3,1.9,1.15,0)
hardware_ring('PENDING_ClaspTagJoinRing',1.0,2.6,.9,pi/2)
hardware_ring('PENDING_ClaspEndRing_R',12.8,1.6,1.05,pi/2)
# Lobster outline, closed spring gate and thumb lever are separate editable meshes.
bodypts=[]
for i in range(42):
 t=.20+(2*pi-.70)*i/41;bodypts.append(clasp_point(-5+4.6*cos(t),2.1*sin(t),.05))
tube('PENDING_LobsterClasp_Body',bodypts,.65,'hardware')
tube('PENDING_LobsterClasp_ClosedGate',[bodypts[-1],clasp_point(-.4,-.10,.05),bodypts[0]],.43,'hardware')
tube('PENDING_LobsterClasp_Lever',[clasp_point(-3,-1.5),clasp_point(-3.1,-2.8),clasp_point(-4,-2.9)],.35,'hardware')
hardware_ring('PENDING_LobsterLeftEye',-10.0,1.4,.75,pi/2)

# Thin connector tag with two real holes. Lettering omitted in this structural draft.
bpy.ops.mesh.primitive_cube_add(size=1,location=clasp_point(7.4)*MM);tag=bpy.context.object;tag.name='PENDING_ConnectorTag_WithHoles'
for c in list(tag.users_collection):c.objects.unlink(tag)
product.objects.link(tag);tag.parent=root;tag.dimensions=(.0098,.00065,.0023);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);tag.data.materials.append(silver);tag['part']='hardware';tag['evidence']='连接牌与两个孔有图依据；具体尺寸暂定，草模未刻字'
bev=tag.modifiers.new('rounded_tag','BEVEL');bev.width=.0006;bev.segments=4 if DETAIL else 2;bpy.context.view_layer.objects.active=tag;bpy.ops.object.modifier_apply(modifier=bev.name)
for x in [3.6,11.2]:
 bpy.ops.mesh.primitive_cylinder_add(vertices=24 if DETAIL else 16,radius=.00058,depth=.004,location=clasp_point(x)*MM,rotation=(pi/2,0,0));cut=bpy.context.object
 mod=tag.modifiers.new('Actual_hole','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cut;bpy.context.view_layer.objects.active=tag;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)

# Small faceted charm next to clasp: visible in supplied detail image; material remains pending.
charmc=clasp_point(-12.3,4.6)
instance_link('PENDING_ClaspCharmJumpRing',oval_data(1.5,.9,.16,'charm_jump_template'),clasp_point(-12.3,2.2),Vector((0,0,1)),pi/2,'hardware')
tube('PENDING_ClaspCharmSeat',[charmc+Vector((1.2*cos(2*pi*i/32),.45,1.2*sin(2*pi*i/32))) for i in range(32)],.20,'hardware',closed=True)
n=12;v=[];f=[]
for rr,yy in [(.7,-.9),(1.3,-.1),(.45,.7)]:
 for i in range(n):v.append(charmc+Vector((rr*cos(2*pi*i/n),yy,rr*sin(2*pi*i/n))))
f.append(tuple(range(n)))
for layer in range(2):
 for i in range(n):a=layer*n+i;b=layer*n+(i+1)%n;f.extend([(a,b,b+n),(a,b+n,a+n)])
tip=len(v);v.append(charmc+Vector((0,1,0)))
for i in range(n):f.append((2*n+i,2*n+(i+1)%n,tip))
mesh('PENDING_ClaspCharm_LightStone',v,f,clear,'hardware','扣旁小颗浅色宝石可见，材质尺寸待确认')
for i in range(4):
 a=pi/4+i*pi/2;tube(f'PENDING_ClaspCharmProng_{i}',[charmc+Vector((1.3*cos(a),.5,1.3*sin(a))),charmc+Vector((1.1*cos(a),-.5,1.1*sin(a)))],.16,'hardware')

# Recenter complete product at its full bounds. Pendant remains at known focus coordinates.
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
verts=[]
for o in product.objects:
 if o.type=='MESH':verts.extend(o.matrix_world@Vector(c) for c in o.evaluated_get(dg).bound_box)
lower=Vector([min(v[k] for v in verts) for k in range(3)]);upper=Vector([max(v[k] for v in verts) for k in range(3)]);center=(lower+upper)/2
for o in list(product.objects)+list(guides.objects):
 if o!=root:o.location-=center
pendant_focus=-center;root['pendant_focus_blender_m']=list(pendant_focus);root['centerline_length_mm']=2*path_length(left)+Q['clasp_assembly_span_mm']

scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=48;scene.cycles.use_denoising=True;scene.cycles.max_bounces=8;scene.cycles.transmission_bounces=6
scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.world.use_nodes=True
scene.world.node_tree.nodes.get('Background').inputs[0].default_value=(.58,.58,.58,1);scene.world.node_tree.nodes.get('Background').inputs[1].default_value=.60
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
def area(name,pos,energy,size):
 d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);review.objects.link(o);o.location=Vector(pos);o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
area('Studio_Key',(-.17,-.24,.24),6,.18);area('Studio_Rim',(.19,.02,.13),5,.13);area('Studio_Front',(0,-.3,-.1),3,.14)
def camera(name,dir,target,scale):
 d=bpy.data.cameras.new(name);d.type='ORTHO';d.ortho_scale=scale;d.clip_start=.0001;d.clip_end=4;o=bpy.data.objects.new(name,d);review.objects.link(o)
 o.location=Vector(target)+Vector(dir).normalized()*.5;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
cams={name:camera('CAM_PENDANT_'+name,dr,pendant_focus,.0185) for name,dr in [('front',(0,-1,0)),('side',(1,0,0)),('back',(0,1,0)),('45deg',(1,-1.6,.6))]}
fullheight=(upper-lower).z;cams['full']=camera('CAM_FULL_RATIO',(0,-1,.035),(0,0,0),fullheight*1.22);cams['preview']=camera('CAM_FULL_DEFAULT',(.13,-1,.08),(0,0,0),fullheight*1.24)
scene.camera=cams['preview'];scene.render.resolution_x=1000;scene.render.resolution_y=1300
for filename in ['build_J001.py','J001-parameters-v01.json']:
 tx=bpy.data.texts.new(filename);tx.write((BASE/filename).read_text())
for screen in bpy.data.screens:
 for ar in screen.areas:
  if ar.type=='VIEW_3D':ar.spaces.active.clip_start=.0001;ar.spaces.active.clip_end=5;ar.spaces.active.region_3d.view_distance=.35
if DETAIL:bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'J001-source-v01.blend'))

# Export product-only evaluated meshes, batched by material; editable source remains unjoined.
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();batches=[]
for mat,label in [(silver,'Silver'),(pink,'PinkHeart'),(clear,'ClaspCharm')]:
 members=[o for o in product.objects if o.type=='MESH' and o.data.materials[0]==mat];bpy.ops.object.select_all(action='DESELECT');copies=[]
 for o in members:
  me=bpy.data.meshes.new_from_object(o.evaluated_get(dg),depsgraph=dg);copy=bpy.data.objects.new('export_'+o.name,me);scene.collection.objects.link(copy);copy.matrix_world=o.matrix_world;copy.select_set(True);copies.append(copy)
 bpy.context.view_layer.objects.active=copies[0];bpy.ops.object.join();ob=bpy.context.object;ob.name='J001_'+label;ob.parent=root;ob['editable_source_parts']=[o.name for o in members];batches.append(ob)
bpy.ops.object.select_all(action='DESELECT');root.select_set(True)
for o in batches:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(BASE/f'J001-{MODE}-v01.glb'),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_materials='EXPORT',export_extras=True,export_cameras=False,export_lights=False)
for o in batches:bpy.data.objects.remove(o,do_unlink=True)

bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();tri=0;partcounts={};allv=[]
for o in product.objects:
 if o.type!='MESH':continue
 ev=o.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles();tri+=len(me.loop_triangles);partcounts[o.get('part','other')]=partcounts.get(o.get('part','other'),0)+1;allv.extend(ev.matrix_world@v.co for v in me.vertices);ev.to_mesh_clear()
stats={'stage':P['stage'],'triangles':tri,'export_meshes':3,'materials':3,'source_mesh_objects_by_part':partcounts,'bounds_mm':[[min(v[k] for v in allv)*1000 for k in range(3)],[max(v[k] for v in allv)*1000 for k in range(3)]],'chain_centerline_length_mm':root['centerline_length_mm'],'chain_length_convention':P['length_convention_pending'],'chain_design':chain_records,'source_path_scale':scale,'pendant_focus_gltf_m':[pendant_focus.x,pendant_focus.z,-pendant_focus.y],'files':{f.name:f.stat().st_size for f in BASE.glob('*.glb')}}
(BASE/f'J001-{MODE}-stats.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2));print('BUILD_COMPLETE',json.dumps(stats),flush=True)
if '--render' in sys.argv:
 for name in ['front','side','back','45deg','full','preview']:
  close=name in ['front','side','back','45deg']
  for o in product.objects:
   if o.type=='MESH':o.hide_render=close and o.get('part')!='pendant'
  scene.camera=cams[name];scene.render.resolution_x=850 if close else 1100;scene.render.resolution_y=850 if close else 1400
  scene.render.filepath=str(BASE/f'J001-{name}-v01.png');bpy.ops.render.render(write_still=True);print('RENDER_COMPLETE',name,flush=True)
 print('J001_DONE',flush=True)
