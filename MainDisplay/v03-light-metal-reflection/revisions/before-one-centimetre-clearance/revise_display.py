import bpy, math, json, struct
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

B = Path(__file__).resolve().parent
W = B.parent.parent
bpy.ops.wm.open_mainfile(filepath=str(B.parent/'v01-layout/main-display-source.blend'))
s = bpy.context.scene
nx = -.052
anchor = bpy.data.objects['necklace_anchor']
root = bpy.data.objects['necklace_product']
original_other = {o.name: [list(row) for row in o.matrix_world] for key in ['earrings','ring','bracelet'] for o in [bpy.data.objects[key+'_anchor']]}

# Continuous, flattened sections: narrow foot, broad shoulders, soft neck.
# z, half width, half depth, centre y. All dimensions are metres.
profile = np.array([
 [.131,.023,.009,.034], [.140,.026,.010,.032],
 [.165,.036,.014,.027], [.195,.047,.017,.024],
 [.225,.056,.017,.025], [.249,.063,.015,.030],
 [.260,.064,.014,.034], [.267,.059,.013,.036],
 [.278,.040,.013,.040], [.287,.027,.0125,.044],
 [.296,.022,.012,.046], [.307,.022,.012,.046]
])
def section(z):
 # Cubic Hermite interpolation with monotonic slopes prevents shoulder ripples.
 x=profile[:,0]; i=max(0,min(len(x)-2,int(np.searchsorted(x,z)-1)))
 h=x[i+1]-x[i]; t=max(0,min(1,(z-x[i])/h)); out=[]
 for k in [1,2,3]:
  v=profile[:,k]; d=np.diff(v)/np.diff(x); slopes=np.zeros(len(x))
  slopes[0]=d[0];slopes[-1]=d[-1]
  for j in range(1,len(x)-1):
   if d[j-1]*d[j]>0:
    h0=x[j]-x[j-1];h1=x[j+1]-x[j];w1=2*h1+h0;w2=h1+2*h0
    slopes[j]=(w1+w2)/(w1/d[j-1]+w2/d[j])
  out.append((2*t**3-3*t*t+1)*v[i]+(t**3-2*t*t+t)*h*slopes[i]+(-2*t**3+3*t*t)*v[i+1]+(t**3-t*t)*h*slopes[i+1])
 return out
def surface(x,z,back=False):
 rx,ry,cy=section(z)
 return cy+(1 if back else -1)*ry*math.sqrt(max(.001,1-(x/rx)**2))

old=bpy.data.objects['fitted soft shoulder necklace bust'];mat=old.data.materials[0]
verts=[];faces=[];N=128;zs=np.linspace(.131,.307,150)
for z in zs:
 rx,ry,cy=section(z)
 for i in range(N):
  a=2*math.pi*i/N;verts.append((nx+rx*math.cos(a),cy+ry*math.sin(a),z))
for j in range(len(zs)-1):
 for i in range(N):
  a=j*N+i;b=j*N+(i+1)%N;faces.append((a,b,b+N,a+N))
faces += [tuple(reversed(range(N))),tuple((len(zs)-1)*N+i for i in range(N))]
me=bpy.data.meshes.new('continuous flattened bust surface');me.from_pydata(verts,[],faces);me.update();me.materials.append(mat)
old.modifiers.clear();old.data=me
for p in me.polygons:p.use_smooth=len(p.vertices)==4
old['revision']='Reference silhouette: continuous neck/shoulder, broad upper body tapering to foot, shallow curved side profile.'
# Flatten the existing ivory and gold plinth in depth to follow the new bust.
for name in ['necklace oval plinth','necklace gold plinth bead']:
 o=bpy.data.objects[name]
 M=Matrix.Translation((nx,.034,.120))@Matrix.Diagonal((1,.64,1.5,1))@Matrix.Translation((-nx,-.032,-.120))
 o.matrix_world=M@o.matrix_world
# Discreet fabric-coloured rear keeper supports the folded surplus at the clasp.
cu=bpy.data.curves.new('rear chain keeper','CURVE');cu.dimensions='3D';cu.bevel_depth=.0007;cu.bevel_resolution=3;cu.resolution_u=16
sp=cu.splines.new('BEZIER');sp.bezier_points.add(3)
for p,co in zip(sp.bezier_points,[(nx+.006,surface(.006,.277,True)-.0003,.277),(nx+.006,.060,.277),(nx+.006,.0645,.278),(nx+.006,.0645,.2805)]):
 p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
keeper=bpy.data.objects.new('necklace hidden rear retaining hook',cu);bpy.data.collections['02_Fixed_Supports'].objects.link(keeper);cu.materials.append(mat)

# Enlarge mirror and surrounding architectural decoration around their bottom.
pivot=Vector((.01,.140,.130));background_changes=[]
for o in bpy.data.collections['03_Fixed_Background'].objects:
 factor=1.95
 if o.name.startswith(('background cabinet','quiet background')):factor=1.60
 M=Matrix.Translation(pivot)@Matrix.Diagonal((factor,1.15,factor,1))@Matrix.Translation(-pivot)
 o.matrix_world=M@o.matrix_world
 lift=0 if o.name in {'soft oyster backdrop','rear dado'} else .030
 o.location.z+=lift
 background_changes.append({'name':o.name,'width_height_factor':factor,'vertical_lift_m':lift})

# Centre the whole mirror assembly between the two existing drapes.
bpy.context.view_layer.update()
def center_x(o):
 points=[o.matrix_world@Vector(v) for v in o.bound_box]
 return (min(v.x for v in points)+max(v.x for v in points))/2
background_center=(center_x(bpy.data.objects['left backdrop drape'])+center_x(bpy.data.objects['right backdrop drape']))/2
mirror_center_before=center_x(bpy.data.objects['oval mirror glass'])
mirror_shift_x=background_center-mirror_center_before
for o in bpy.data.collections['03_Fixed_Background'].objects:
 if o.name.startswith(('mirror ','oval mirror')):o.location.x+=mirror_shift_x
mirror_alignment={'background_center_x_m':background_center,'previous_mirror_center_x_m':mirror_center_before,'mirror_shift_x_m':mirror_shift_x,'new_mirror_center_x_m':background_center}
print('MIRROR_ALIGNMENT',json.dumps(mirror_alignment),flush=True)

# Load the original editable necklace so each link is moved rigidly, not stretched.
for o in list(root.children_recursive):bpy.data.objects.remove(o,do_unlink=True)
with bpy.data.libraries.load(str(W/'J001/v02-refined/J001-source-v02.blend'),link=False) as (src,dst):
 dst.collections=['J001_PRODUCT_ONLY']
loaded=dst.collections[0];s.collection.children.link(loaded);bpy.context.view_layer.update()
srcroot=next(o for o in loaded.objects if o.name.startswith('J001_ROOT'))
focus=Vector(srcroot['pendant_focus_blender_m'])
items=[o for o in loaded.objects if o.type=='MESH']
pc=Vector((nx,surface(0,.219)-.0049,.219))
anchor_inv=anchor.matrix_world.inverted()

def catmull(points,n=36):
 points=[Vector(p) for p in points];out=[]
 for i in range(len(points)-1):
  a=points[max(0,i-1)];b=points[i];c=points[i+1];d=points[min(len(points)-1,i+2)]
  for j in range(n):
   t=j/n;out.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
 out.append(points[-1]);return out
def length(points):return sum((b-a).length for a,b in zip(points,points[1:]))
# User-approved spacing: 25 mm on each side of the neck, 50 mm total.
neck_clearance=.025
neck_edge_z=.296
chain_wire_allowance=.0005
spread_rx=section(neck_edge_z)[0]+neck_clearance+chain_wire_allowance
spread_ry=.0165
spread_cy=section(neck_edge_z)[2]
def path_for(sign,sag):
 # Widen across the shoulders rather than suspend the chain beside the neck.
 # Front shoulder entry is 25 mm beyond each straight neck edge horizontally.
 controls=[]
 for x,z in [(.0045,.2232),(.016,.233),(.030,.247),(.041,.260),(spread_rx,.268)]:
  controls.append(Vector((nx+sign*x,surface(x,z)-.0015,z)))
 controls[0]=Vector((nx+sign*.0045,pc.y,.2232))
 for a,z in [(-.45,.271),(0,.273),(.40,.272),(.80,.268),(1.1,.264)]:
  rx,ry,cy=section(z)
  controls.append(Vector((nx+sign*(rx+.0015)*math.cos(a),cy+(ry+.0015)*math.sin(a),z)))
 controls += [Vector((nx+sign*.018,.064,.267)),Vector((nx+sign*.020,.065,sag+.006)),Vector((nx+sign*.017,.066,sag)),Vector((nx+sign*.010,.064,sag+.006)),Vector((nx+sign*.013,.064,.278))]
 return catmull(controls,64)

paths={};reports={}
for side,sign in [('L',-1),('R',1)]:
 links=sorted([o for o in items if o.get('part')=='chain' and o.get('sequence_side')==side],key=lambda o:o['sequence_index'])
 target=max(o['centerline_distance_mm'] for o in links)*.001
 lo=.205;hi=.280
 for _ in range(45):
  mid=(lo+hi)/2
  if length(path_for(sign,mid))>target:lo=mid
  else:hi=mid
 points=path_for(sign,(lo+hi)/2);cum=np.array([0]+list(np.cumsum([(b-a).length for a,b in zip(points,points[1:])])))
 paths[side]=points
 for o in links:
  dist=o['centerline_distance_mm']*.001;j=max(0,min(len(points)-2,int(np.searchsorted(cum,dist)-1)))
  t=(dist-cum[j])/(cum[j+1]-cum[j]);p=points[j].lerp(points[j+1],t)
  tangent=(points[min(j+2,len(points)-1)]-points[max(0,j-1)]).normalized()
  normal=Vector((0,1,0))
  if abs(tangent.dot(normal))>.95:normal=Vector((1,0,0))
  u=normal.cross(tangent).normalized();v=tangent.cross(u).normalized();twist=math.pi/4+(o['sequence_index']%2)*math.pi/2
  ux=u*math.cos(twist)+v*math.sin(twist);vy=-u*math.sin(twist)+v*math.cos(twist)
  o.parent=None;o.matrix_world=Matrix.Translation(p)@Matrix((ux,vy,tangent)).transposed().to_4x4()
 reports[side]={'links':len(links),'centerline_mm':length(points)*1000,'original_centerline_mm':target*1000,'back_fold_low_z_mm':(lo+hi)*500}

# Original hardware remains rigid, parked at the back between both chain ends.
old_end=next(o for o in items if o.get('sequence_side')=='L' and o.get('sequence_index')==max(q['sequence_index'] for q in items if q.get('sequence_side')=='L'))
# Original source end coordinates can be read from its path data in the source parameters.
hardware=[o for o in items if o.get('part')=='hardware']
# A clasp end ring has local position equal to the hardware reference plus x offset.
ref=next(o for o in hardware if o.name.startswith('PENDING_ClaspEndRing_L'))
hardware_origin=ref.matrix_world.translation-Vector((-.0123,0,0))
hardware_target=Vector((nx,.064,.278))
for o in items:
 if o.get('part')=='pendant':o.matrix_world=Matrix.Translation(pc-focus)@o.matrix_world
 elif o.get('part')=='hardware':o.matrix_world=Matrix.Translation(hardware_target-hardware_origin)@o.matrix_world
 world=o.matrix_world.copy();o.parent=root;o.matrix_parent_inverse=Matrix.Identity(4);o.matrix_basis=anchor_inv@world
 for c in list(o.users_collection):c.objects.unlink(o)
 bpy.data.collections['06_Products'].objects.link(o)
 # Reuse the original scene material rather than importing another colour variant.
 if o.data.materials:
  name=o.data.materials[0].name
  canonical=name.rsplit('.',1)[0] if name.rsplit('.',1)[-1].isdigit() else name
  if canonical in bpy.data.materials:o.data.materials[0]=bpy.data.materials[canonical]
bpy.data.objects.remove(srcroot,do_unlink=True);bpy.data.collections.remove(loaded)
bpy.context.view_layer.update()

# Retain champagne colour while increasing metallic reflections.
for ma in bpy.data.materials:
 if not ma.use_nodes:continue
 bs=next((n for n in ma.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
 if not bs:continue
 if 'champagne' in ma.name:
  bs.inputs['Metallic'].default_value=1.0
  bs.inputs['Roughness'].default_value=.19 if 'satin' in ma.name else .14
 if 'softened silver mirror' in ma.name:
  bs.inputs['Metallic'].default_value=1.0
  bs.inputs['Roughness'].default_value=.13
  bs.inputs['Base Color'].default_value=(.96,.96,.96,1)
# Give only the mirror's metalwork its own lighter champagne gold.
mirror_metals={}
for o in bpy.data.collections['03_Fixed_Background'].objects:
 if not o.name.startswith('mirror ') or o.type not in {'MESH','CURVE'}:continue
 for i,ma in enumerate(o.data.materials):
  if not ma or 'champagne' not in ma.name:continue
  if ma.name not in mirror_metals:
   light_gold=ma.copy();light_gold.name='Mirror | pale champagne mirror '+('satin gold' if 'satin' in ma.name else 'polished gold')
   bs=next(n for n in light_gold.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
   bs.inputs['Base Color'].default_value=(1.0,.76,.38,1)
   bs.inputs['Metallic'].default_value=1.0
   bs.inputs['Roughness'].default_value=.22 if 'satin' in ma.name else .17
   bs.inputs['Coat Weight'].default_value=.22;bs.inputs['Coat Roughness'].default_value=.16
   mirror_metals[ma.name]=light_gold
  # Data may be shared with another gold ornament; isolate the mirror's assignment.
  if o.data.users>1:o.data=o.data.copy()
  o.data.materials[i]=mirror_metals[ma.name]

light=bpy.data.objects.get('top soft reflection')
if light:
 light.location=(0,-.025,.58);light.data.color=(1,.69,.36);light.data.energy=4.8;light.data.size=.24
 light.rotation_euler=(Vector((-.025,.015,.18))-light.location).to_track_quat('-Z','Y').to_euler()
# A softer neutral key lets the overhead warmth read without recolouring the products.
bpy.data.objects['neutral jewelry softbox'].data.energy=1.8
# Warm light on the rear wall and reflected sides of the display.
wall_light=bpy.data.objects['warm backdrop wash']
wall_light.location=(0,-.12,.58);wall_light.data.energy=2.8;wall_light.data.color=(1,.61,.28);wall_light.data.size=.38
wall_light.rotation_euler=(Vector((0,.15,.30))-wall_light.location).to_track_quat('-Z','Y').to_euler()
dat=bpy.data.lights.new('warm reflected objects bounce','AREA');dat.energy=1.5;dat.color=(1,.72,.43);dat.shape='DISK';dat.size=.30
ob=bpy.data.objects.new('warm reflected objects bounce',dat);s.collection.objects.link(ob);ob.location=(0,.115,.43)
ob.rotation_euler=(Vector((-.025,.015,.20))-ob.location).to_track_quat('-Z','Y').to_euler()


# Export the revised necklace in the same local anchor coordinates, batched by material.
dg=bpy.context.evaluated_depsgraph_get();batches={};allpts=[]
for o in items:
 ev=o.evaluated_get(dg);mesh=ev.to_mesh();M=anchor_inv@o.matrix_world;ma=o.data.materials[0]
 rec=batches.setdefault(ma.name,{'v':[],'f':[],'smooth':[],'mat':ma});offset=len(rec['v'])
 vv=[M@v.co for v in mesh.vertices];allpts+=vv;rec['v']+=list(map(tuple,vv))
 for face in mesh.polygons:rec['f'].append(tuple(offset+i for i in face.vertices));rec['smooth'].append(face.use_smooth)
 ev.to_mesh_clear()
temp=bpy.data.objects.new('necklace_export_root',None);s.collection.objects.link(temp);temp.name='necklace_product_v02'
exportobs=[]
for name,rec in batches.items():
 me=bpy.data.meshes.new(name+'_display_mesh');me.from_pydata(rec['v'],[],rec['f']);me.update();me.materials.append(rec['mat'])
 for p,sm in zip(me.polygons,rec['smooth']):p.use_smooth=sm
 o=bpy.data.objects.new(name+'_display',me);s.collection.objects.link(o);o.parent=temp;exportobs.append(o)
bpy.ops.object.select_all(action='DESELECT');temp.select_set(True)
for o in exportobs:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(B/'necklace.glb'),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_extras=True,export_cameras=False,export_lights=False)
for o in exportobs+[temp]:bpy.data.objects.remove(o,do_unlink=True)
glb=B/'necklace.glb';raw=glb.read_bytes();jl=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+jl]);tail=raw[20+jl:]
for node in doc['nodes']:
 if node.get('name')=='necklace_product_v02':node['name']='necklace_product'
js=json.dumps(doc,separators=(',',':')).encode();js+=b' '*((-len(js))%4)
glb.write_bytes(struct.pack('<III',0x46546c67,2,20+len(js)+len(tail))+struct.pack('<II',len(js),0x4e4f534a)+js+tail)

config=json.loads((B/'product-placement.json').read_text());p=config['products']['necklace']
lo=Vector([min(v[k] for v in allpts) for k in range(3)]);hi=Vector([max(v[k] for v in allpts) for k in range(3)]);c=(lo+hi)/2;size=hi-lo
p['bounds_local_glb']={'center':[c.x,c.z,-c.y],'size':[size.x+.006,size.z+.006,size.y+.006]}
p['dimensions_mm']=list(size*1000);p['original_origin_relation']='v03 reposed individual chain links; pendant unchanged in size; same display anchor'
p.pop('preferred_hit_region',None);p['pose_note']='Pendant centred; widened shoulder drape with 25 mm lateral clearance at each neck side; full chain length retained behind.'
config['stage']='v03 smooth neck, warm overhead light and metal mirror';(B/'product-placement.json').write_text(json.dumps(config,indent=2))
audit=json.loads((B/'product-audit.json').read_text());audit['necklace'].update({'bounds_blender_m':[list(lo),list(hi)],'dimensions_mm':list(size*1000),'bytes':glb.stat().st_size,'origin_relation':p['original_origin_relation'],'pose_revision':p['pose_note']});(B/'product-audit.json').write_text(json.dumps(audit,indent=2))
root['pose_revision']='v03 smooth centred pendant; surplus chain folded behind bust';root['chain_path_report']=json.dumps(reports)
for o in bpy.data.collections['99_Hit_Areas_NOT_EXPORTED'].objects:
 if o.name.startswith('necklace'):o.hide_viewport=True
for im in bpy.data.images:
 if im.users and im.packed_file:pass
s.camera=bpy.data.objects['01_Front'];s.cycles.device='CPU';s.cycles.samples=24
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(B/'main-display-source.blend'),compress=True)
report={'version':'v03','mirror_alignment':mirror_alignment,'pendant_center_world_m':list(pc),'bust_height_range_m':[.131,.307],'bust_max_width_m':.128,'bust_max_depth_m':.034,'necklace_paths':reports,'necklace_neck_clearance_per_side_m':neck_clearance,'necklace_neck_clearance_total_m':neck_clearance*2,'necklace_neck_edge_reference_z_m':neck_edge_z,'necklace_shoulder_entry_z_m':.268,'necklace_clearance_measurement':'Horizontal gap from neck side to front shoulder entry, excluding wire radius','necklace_upper_span_m':spread_rx*2,'background_changes':background_changes,'other_product_anchors_preserved':all(original_other[n]==[list(row) for row in bpy.data.objects[n].matrix_world] for n in original_other)}
(B/'revision-details.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('REVISION_SAVED',json.dumps(report),flush=True)
