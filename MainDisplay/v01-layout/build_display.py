import bpy,math,json,random,ast,shutil
import numpy as np
from math import sin,cos,pi
from mathutils import Vector,Matrix,Euler
from pathlib import Path
B=Path(__file__).resolve().parent; W=B.parent.parent;random.seed(24)
bpy.ops.wm.open_mainfile(filepath=str(W/'Boutique/v06-soft-front/Boutique-final.blend'))
s=bpy.context.scene
# Reuse the approved furniture language, without the shop's decorative jewelry.
keep={}
for cn in ['02_Counter','04_Mirror','05_Textiles','08_Flowers_and_gifts']:
 for o in bpy.data.collections[cn].objects:
  if cn=='02_Counter' and any(t in o.name for t in ['glass','glazing','velvet display']):continue
  if cn=='05_Textiles' and not any(t in o.name for t in ['backdrop','tieback','tassel']):continue
  if cn=='08_Flowers_and_gifts' and not o.name.startswith('counter small roses'):continue
  keep[o.name]=cn
for o in list(bpy.data.objects):
 if o.name not in keep:bpy.data.objects.remove(o,do_unlink=True)
groups={}
for name in ['01_Fixed_Counter','02_Fixed_Supports','03_Fixed_Background','04_Fixed_Decor','05_Product_Anchors','06_Products','90_Lighting','91_Cameras','99_Hit_Areas_NOT_EXPORTED']:
 c=bpy.data.collections.new(name);s.collection.children.link(c);groups[name]=c
for o in list(bpy.data.objects):
 cn=keep[o.name]
 if cn=='02_Counter':M=Matrix.Translation((0,-.0901,-.001875))@Matrix.Diagonal((.105,.17,.065,1));dest='01_Fixed_Counter'
 elif cn=='04_Mirror':M=Matrix.Translation((.01,-.05,.011))@Matrix.Diagonal((.075,.075,.075,1));dest='03_Fixed_Background'
 elif cn=='05_Textiles':M=Matrix.Translation((0,-.006,.018))@Matrix.Diagonal((.07,.07,.072,1));dest='03_Fixed_Background'
 else:M=Matrix.Translation((-.062,-.021,.007))@Matrix.Diagonal((.06,.06,.06,1));dest='04_Fixed_Decor'
 o.matrix_world=M@o.matrix_world
 for c in list(o.users_collection):c.objects.unlink(o)
 groups[dest].objects.link(o)
for c in list(bpy.data.collections):
 if c not in groups.values():bpy.data.collections.remove(c)
# Available pure geometry helpers from the existing project.
mat=lambda prefix:next(m for m in bpy.data.materials if m.name.startswith(prefix))
ivory=mat('01 |');edge=mat('02 |');recess=mat('03 |');gold=mat('04 |');goldlight=mat('05 |');wall=mat('06 |');rose=mat('07 |');silk=mat('08 |');lace=mat('09 |');velvet=mat('10 |');linen=mat('11 |');studio=mat('21 |')
active='02_Fixed_Supports';ball_cache={}
tree=ast.parse((W/'Boutique/v01-preview/build_boutique.py').read_text());names={'move','mesh','cube','uvball','tube','lathe','oval','rectframe','leaf','flourish','material'}
for node in tree.body:
 if isinstance(node,ast.FunctionDef) and node.name in names:exec(compile(ast.Module(body=[node],type_ignores=[]),'geometry_helpers','exec'))
# Fine texture scale follows actual millimetre-sized furniture.
for m in [ivory,edge,recess,rose,velvet,linen,silk]:
 if m.use_nodes:
  for n in m.node_tree.nodes:
   if n.type=='BUMP':n.inputs['Distance'].default_value=.00006
# Matt fabric keeps product metals distinct.
insert=material('Display | pale blush suede',(.67,.42,.46),0,.82);insert.node_tree.nodes['Principled BSDF'].inputs['Sheen Weight'].default_value=.35
cream=material('Display | warm ivory velvet',(.61,.56,.49),0,.86);cream.node_tree.nodes['Principled BSDF'].inputs['Sheen Weight'].default_value=.32
mirror=mat('16 |');mp=mirror.node_tree.nodes['Principled BSDF'];mp.inputs['Metallic'].default_value=.30;mp.inputs['Roughness'].default_value=.36
# The upper counter is a quiet drawer band, avoiding extra jewelry inside glass.
active='01_Fixed_Counter';cube('ivory upper drawer band',(0,0,.100),(.318,.175,.023),ivory,.003)
for x in [-.106,0,.106]:
 cube('blush drawer inset',(x,-.0885,.100),(.098,.0018,.015),rose,.002)
 tube('drawer gold hairline',[(x-.045,-.090,.093),(x+.045,-.090,.093)],.00035,gold,res=1)
 uvball('drawer pull',(x,-.092,.100),(.004,.0018,.0013),goldlight)
active='03_Fixed_Background'
cube('soft oyster backdrop',(0,.185,.205),(.395,.008,.31),wall,.004)
cube('rear dado',(0,.173,.135),(.39,.012,.036),ivory,.002)
for x in [-.145,.145]:
 cube('background cabinet silhouette',(x,.155,.21),(.06,.025,.15),ivory,.003)
 rectframe('quiet background panel',x,.140,.215,.048,.12,.0008,edge)
# Import actual products with unit scale and their existing poses.
active='06_Products';products={};anchors={};audit=json.loads((B/'product-audit.json').read_text())
poses={'necklace':((-.052,.022,.220),(0,0,0)),'earrings':((.069,.024,.255),(0,0,0)),'ring':((-.080,-.064,.145),(math.radians(60),0,math.radians(-10))),'bracelet':((.073,-.043,.152),(math.radians(38),0,math.radians(-8)))}
for key,(pos,rot) in poses.items():
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(B/(key+'.glb')));new=set(bpy.data.objects)-before;root=next(o for o in new if o.parent is None)
 for o in new:
  for c in list(o.users_collection):c.objects.unlink(o)
  groups['06_Products'].objects.link(o)
 anchor=bpy.data.objects.new(key+'_anchor',None);groups['05_Product_Anchors'].objects.link(anchor);anchor.empty_display_type='PLAIN_AXES';anchor.empty_display_size=.012;anchor.location=pos;anchor.rotation_euler=rot
 root.parent=anchor;root.matrix_parent_inverse=Matrix.Identity(4);root.location=(0,0,0);root.rotation_euler=(0,0,0);root.scale=(1,1,1);products[key]=root;anchors[key]=anchor
# Necklace bust shaped around the existing 154 mm hanging silhouette.
active='02_Fixed_Supports';nx,ny,nz=poses['necklace'][0]
lathe('necklace oval plinth',(nx,ny+.010,.120),[(0,.025),(.003,.027),(.005,.026),(.008,.021)],ivory,48)
lathe('necklace gold plinth bead',(nx,ny+.010,.123),[(0,.0273),(.001,.0273)],gold,48)
prof=[(-.089,.022,.018,.012),(-.080,.027,.023,.012),(-.073,.030,.028,.012),(-.060,.039,.043,.018),(-.030,.049,.043,.018),(0,.055,.047,.020),(.030,.054,.052,.020),(.050,.049,.045,.024),(.063,.038,.027,.014),(.071,.025,.012,.010),(.082,.022,.012,.010)]
# Fit the bust cross-sections to the unchanged jewelry envelope.
bpy.context.view_layer.update();jewelry=[]
for o in products['necklace'].children_recursive:
 if o.type=='MESH':jewelry += [anchors['necklace'].matrix_world.inverted()@o.matrix_world@v.co for v in o.data.vertices]
arr=np.array([tuple(p) for p in jewelry]);baseprof=np.array(prof);refined=[]
zs=np.linspace(-.089,.082,98)
for z in zs:
 rx,ry,cy=[float(np.interp(z,baseprof[:,0],baseprof[:,k])) for k in [1,2,3]]
 pts=arr[np.abs(arr[:,2]-z)<.0018]
 if len(pts):
  ratios=np.sqrt((pts[:,0]/rx)**2+((pts[:,1]-cy)/ry)**2)
  f=min(1,float(np.min(ratios))*.978);rx*=f;ry*=f
 refined.append([z,rx,ry,cy])
# Smooth inward only, so the fabric cannot grow back into the chain.
a=np.array(refined)
for k in [1,2]:
 vals=a[:,k].copy()
 for i in range(len(vals)):
  window=vals[max(0,i-3):min(len(vals),i+4)]
  a[i,k]=min(vals[i],float(np.mean(window)))
refined=a.tolist()
prof=refined;vs=[];fs=[];N=128
for z,rx,ry,cy in prof:
 for i in range(N):
  a=2*pi*i/N;vs.append((nx+rx*cos(a),ny+cy+ry*sin(a),nz+z))
for j in range(len(prof)-1):
 for i in range(N):a=j*N+i;b=j*N+(i+1)%N;fs.append((a,b,b+N,a+N))
fs.extend([tuple(reversed(range(N))),tuple((len(prof)-1)*N+i for i in range(N))]);bust=mesh('fitted soft shoulder necklace bust',vs,fs,cream,True)
sub=bust.modifiers.new('soft fabric shoulders','SUBSURF');sub.levels=1;sub.render_levels=1
# Earring support: separate tiny saddles respect the original pair placement.
ex,ey,ez=poses['earrings'][0]
cube('earrings tiered ivory base',(ex,ey+.010,.127),(.041,.028,.014),ivory,.004)
cube('earrings blush inset',(ex,ey+.010,.135),(.034,.022,.003),insert,.003)
tube('earring stand stem',[(ex,ey+.010,.136),(ex,ey+.010,.264)],.0011,goldlight,res=2)
tube('earring stand crossbar',[(ex-.014,ey+.010,.264),(ex+.014,ey+.010,.264)],.0008,goldlight,res=2)
for dx,dz in [(-.0065,.00035),(.0065,-.00035)]:
 tube('earring hook',[(ex+dx,ey+.010,.264),(ex+dx,ey+.005,.264),(ex+dx,ey+.001,.260+dz),(ex+dx,ey-.0003,.2586+dz)],.00040,goldlight,res=2)
# Ring tray, raised pad and an insert inside the lower shank, below the gem head.
cube('ring ivory tray',(-.080,-.064,.123),(.056,.047,.006),ivory,.006)
cube('ring blush tray lining',(-.080,-.064,.127),(.049,.040,.003),insert,.005)
for side in [-1,1]:tube('ring tray gold edge',[(-.080+side*.025,-.084,.128),(-.080+side*.025,-.044,.128)],.00055,gold,res=1)
cube('ring raised cushion',(-.080,-.064,.133),(.030,.025,.012),insert,.006)
R=Euler(poses['ring'][1]).to_matrix();ob=uvball('ring fitted inner velvet support',Vector(poses['ring'][0])+R@Vector((0,0,-.002)),(.0065,.0015,.0058),insert,32,16);ob.rotation_euler=poses['ring'][1]
# Bracelet shallow tilted tray in its original planar shape; no bending of the chain.
anchor=anchors['bracelet'];R=Euler(poses['bracelet'][1]).to_matrix();p=Vector(poses['bracelet'][0])
for name,local,size,ma,bev in [('bracelet ivory tray',(0,.005,-.0038),(.073,.077,.004),ivory,.006),('bracelet velvet surface',(0,.005,-.0016),(.068,.072,.0018),insert,.004)]:
 o=cube(name,p+R@Vector(local),size,ma,bev);o.rotation_euler=poses['bracelet'][1]
for side in [-1,1]:
 pts=[p+R@Vector((side*.035,y,-.001)) for y in [-.03,.04]];tube('bracelet gilt tray lip',pts,.00055,gold,res=1)
cube('bracelet tray rear riser',(.073,-.021,.141),(.040,.012,.040),ivory,.003)
# Soft runner passes through the open area, draping at the front edge.
active='04_Fixed_Decor';verts=[];faces=[];rows=42;cols=12
for j in range(rows):
 t=j/(rows-1);y=.085-.20*t;z=.1218 if y>=-.095 else .1218-(abs(y)-.095)*1.35
 for i in range(cols):
  u=i/(cols-1);x=-.005+(u-.5)*.035;verts.append((x,y,z+.0006*sin(u*pi*5+t*3)*sin(pi*t)))
for j in range(rows-1):
 for i in range(cols-1):a=j*cols+i;faces.append((a,a+1,a+1+cols,a+cols))
o=mesh('folded lace table runner',verts,faces,lace);uv=o.data.uv_layers.new(name='UVMap')
for poly in o.data.polygons:
 for li in poly.loop_indices:
  vi=o.data.loops[li].vertex_index;uv.data[li].uv=(vi%cols/(cols-1),(vi//cols)/(rows-1)*3)
# Small closed ribbon boxes stay at the edge, below product contrast.
for x,y,z,sz in [(.135,.040,.133,.027),(-.130,-.042,.131,.022)]:
 cube('small closed blush jewelry box',(x,y,z),(sz,sz*.8,sz*.75),rose,.002)
 cube('ivory box lid',(x,y,z+sz*.39),(sz*1.04,sz*.84,.003),edge,.0012)
 cube('silk ribbon band',(x,y,z+sz*.46),(.004,sz*.85,.0006),silk,.0002)
 for sg in [-1,1]:tube('ribbon bow',[(x,y,z+sz*.48),(x+sg*.006,y+.003,z+sz*.48+.003),(x+sg*.007,y-.002,z+sz*.48+.002),(x,y,z+sz*.48)],.0006,silk,res=2)
# Slightly raised neutral stage and studio floor.
active='01_Fixed_Counter';cube('display grounding plinth',(0,.003,.015),(.36,.216,.011),ivory,.004)
active='90_Lighting';cube('studio floor',(0,0,-.002),(200,200,.002),studio,0)
def area(name,pos,target,energy,size,color):
 d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.shape='DISK';d.size=size;d.color=color;o=bpy.data.objects.new(name,d);groups['90_Lighting'].objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
area('neutral jewelry softbox',(-.28,-.38,.47),(0,0,.19),2.3,.34,(1,.97,.94))
area('neutral reflection strip',(.27,-.18,.34),(0,0,.20),1.1,.26,(.93,.96,1))
area('warm backdrop wash',(0,.10,.39),(0,.16,.20),.7,.18,(1,.77,.55))
area('soft front fill',(0,-.42,.24),(0,0,.17),.30,.30,(1,.98,.95))
area('top soft reflection',(0,.02,.55),(0,0,.15),.8,.30,(1,.96,.91))
s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.40,.42,.46,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.25
s.unit_settings.system='METRIC';s.unit_settings.scale_length=1;s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.use_denoising=True;s.render.resolution_x=1200;s.render.resolution_y=1100;s.render.resolution_percentage=100;s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=0;s.render.image_settings.file_format='PNG'
for name,yaw in [('01_Front',0),('02_Left',-12),('03_Right',12)]:
 d=bpy.data.cameras.new(name);d.type='ORTHO';d.ortho_scale=.415;d.clip_start=.001;d.clip_end=100;d.dof.use_dof=False;o=bpy.data.objects.new(name,d);groups['91_Cameras'].objects.link(o);target=Vector((0,.015,.177));a=math.radians(yaw);e=math.radians(19);o.location=target+Vector((sin(a)*cos(e),-cos(a)*cos(e),sin(e)))*.9;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
s.camera=bpy.data.objects['01_Front'];bpy.context.view_layer.update()
# Invisible bounds stored separately; not included in any visible export.
config={'stage':'stage 1 layout for approval','units':'metres; multiply by 1000 for millimetres','blender_axes':'X right, Z up, front -Y','glb_axes':'X right, Y up, front +Z','assembly':'Load scene; attach each product GLB scene under matching anchor with identity transform. Do not apply anchor transform twice. Product local coordinates retain original source root origin.','products':{}}
C=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)))
for key,root in products.items():
 a=anchors[key];lo,hi=audit[key]['bounds_blender_m'];center=(Vector(lo)+Vector(hi))*.5;size=Vector(hi)-Vector(lo);margin=.0025 if key in ['ring','earrings'] else .003
 hit=bpy.data.objects.new(key+'_hit_area',None);groups['99_Hit_Areas_NOT_EXPORTED'].objects.link(hit);hit.empty_display_type='CUBE';hit.empty_display_size=1;hit.matrix_world=a.matrix_world@Matrix.Translation(center)@Matrix.Diagonal(tuple((size+Vector((margin*2,)*3))*.5)+(1,));hit.hide_render=True
 M=C@a.matrix_world@C.inverted();loc,quat,sc=M.decompose();hc=C.to_3x3()@center;hs=size+Vector((margin*2,)*3)
 config['products'][key]={'file':key+'.glb','anchor':a.name,'root':root.name,'position':list(loc),'quaternion_xyzw':[quat.x,quat.y,quat.z,quat.w],'scale':list(sc),'pivot_local':[0,0,0],'original_origin_relation':'identity; same root local coordinate system as supplied Blender source','bounds_local_glb':{'center':list(hc),'size':[hs.x,hs.z,hs.y]},'blender_position':list(a.location),'blender_euler_xyz':list(a.rotation_euler),'dimensions_mm':audit[key]['dimensions_mm'],'animation':'Rigid whole-product translation and rotation; necklace/bracelet pose fixed. Earrings left/right remain child groups.'}
(B/'product-placement.json').write_text(json.dumps(config,indent=2))
(B/'camera-and-lighting.json').write_text(json.dumps({'units':'metres','target_glb':[0,.177,-.015],'orthographic_vertical_size':.415*1100/1200,'yaw_limits_degrees':[-15,15],'preview_yaws':[0,-12,12],'elevation_degrees':19,'depth_of_field':False,'blender_lights':[{'name':o.name,'position':list(o.location),'energy_watts':o.data.energy,'size':o.data.size,'color':list(o.data.color)} for o in groups['90_Lighting'].objects if o.type=='LIGHT'],'web_note':'Use neutral PMREM reflection, warm backdrop fill, soft directional shadows. Do not tint product materials. See viewer for executable settings.'},indent=2))
for im in bpy.data.images:
 if im.users and im.size[0]>0 and im.name not in ['Render Result','Viewer Node']:
  im.filepath_raw=str(B/'textures'/(im.name+'.png'));im.file_format='PNG';im.save();im.pack()
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(B/'main-display-source.blend'),compress=True)
print('BUILD_DONE',flush=True)
