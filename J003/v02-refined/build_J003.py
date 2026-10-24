"""J003 refinement v02. Run with Blender 4.5:
blender --background --factory-startup --python build_J003.py -- --render
All modeling values are mm; generated geometry is meters. No third-party packages.
This is a review draft: do not treat provisional counts/underside as verified product.
"""
import bpy, math, json, sys, os
from pathlib import Path
from mathutils import Vector
from math import sin, cos, pi

BASE = Path(__file__).resolve().parent
P = json.loads((BASE / 'J003-parameters-v02.json').read_text())
E, T = P['estimated_from_images_mm'], P['provisional']
MODE='display' if '--display' in sys.argv else 'detail'
DETAIL=MODE=='detail'
MM = .001
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
    if c.name != 'Collection' and c.users == 0: bpy.data.collections.remove(c)
scene = bpy.context.scene
scene.unit_settings.system='METRIC'
scene.unit_settings.scale_length=1.0
scene.unit_settings.length_unit='MILLIMETERS'
product = bpy.data.collections.new('J003_PRODUCT_ONLY')
scene.collection.children.link(product)
review = bpy.data.collections.new('REVIEW_ONLY_cameras_lights')
scene.collection.children.link(review)
root = bpy.data.objects.new('J003_ROOT',None)
product.objects.link(root)
root.empty_display_size=.003
root['stage']='v02精修；背面结构仍待确认'
root['inner_diameter_mm']=16.0
root['nominal_size']='EU 50; actual circumference 50.265 mm'
root['provisional_counts']='halo 21 with empty cleft; shoulder 11+11; NOT confirmed counts'

def material(name, color, metallic=0, roughness=.25, transmission=0, ior=1.45):
    m=bpy.data.materials.new(name);m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Metallic'].default_value=metallic
    bs.inputs['Roughness'].default_value=roughness
    bs.inputs['Transmission Weight'].default_value=transmission
    bs.inputs['IOR'].default_value=ior
    m.diffuse_color=(*color,1)
    return m
gold=material('M01_RoseGold_user_color',(.76,.40,.28),1,.16)
gem=material('M02_PinkStone_optics_PENDING',(.86,.36,.49),0,.018,.48,2.15)
small=material('M03_PinkAccent_optics_PENDING',(.93,.49,.60),0,.025,.42,2.15)
for gemstone in [gem,small]:
    bs=gemstone.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Coat Weight'].default_value=.25
    bs.inputs['Coat Roughness'].default_value=.025
clay=material('REVIEW_Clay',(.48,.56,.62),.08,.5)

def mesh_obj(name, verts, faces, mat=gold, evidence='比例估算', smooth=False):
    me=bpy.data.meshes.new(name+'_Mesh')
    me.from_pydata([tuple(v*MM for v in p) for p in verts],[],faces);me.update()
    ob=bpy.data.objects.new(name,me);product.objects.link(ob);ob.parent=root
    ob.data.materials.append(mat)
    for f in me.polygons:f.use_smooth=smooth
    ob['evidence']=evidence
    return ob

def bevel_rect(radial=.95,width=1.4,r=.19,steps=4):
    # Counterclockwise profile in (radial offset, axial offset).
    out=[]
    for a,b,start in [(radial/2-r,width/2-r,0),(-radial/2+r,width/2-r,90),
                      (-radial/2+r,-width/2+r,180),(radial/2-r,-width/2+r,270)]:
        for k in range(steps+1):
            t=math.radians(start+90*k/steps)
            out.append((a+r*cos(t),b+r*sin(t)))
    return out

profile=bevel_rect(E['band_radial_thickness'],E['band_axial_width'],E['band_edge_radius'],steps=6 if DETAIL else 3)
R=8+E['band_radial_thickness']/2
gap=math.radians(E['band_top_gap_half_angle_degrees'])
arc_segments=512 if DETAIL else 96
angles=[gap+(2*pi-2*gap)*k/arc_segments for k in range(arc_segments+1)]
# Include cardinal directions for exact measuring points on the 16 mm inner cylinder.
angles=sorted(set(angles+[pi/2,pi,3*pi/2]))
verts=[];faces=[];n=len(profile)
for t in angles:
    for rr,yy in profile:verts.append(((R+rr)*sin(t),yy,(R+rr)*cos(t)))
for j in range(len(angles)-1):
    for k in range(n):
        a=j*n+k;b=j*n+(k+1)%n
        faces.append((a,b,b+n,a+n))
faces += [tuple(reversed(range(n))),tuple((len(angles)-1)*n+k for k in range(n))]
band=mesh_obj('01_Shank_ID16mm_width_EST',verts,faces,smooth=True,
              evidence='内径16mm 用户指定；戒臂宽厚、顶部缺口与肩部过渡按图片比例估算')

segments=[
 ((0,1.85),(.4,2.5),(.9,2.65),(1.30,2.55)),
 ((1.30,2.55),(1.95,2.5),(2.55,2.1),(2.45,1.45)),
 ((2.45,1.45),(2.6,0),(.9,-1.9),(0,-2.55)),
 ((0,-2.55),(-.9,-1.9),(-2.6,0),(-2.45,1.45)),
 ((-2.45,1.45),(-2.55,2.1),(-1.95,2.5),(-1.30,2.55)),
 ((-1.30,2.55),(-.9,2.65),(-.4,2.5),(0,1.85))]
raw=[]
for seg in segments:
    for k in range(100):
        t=k/100;u=1-t
        raw.append(Vector(tuple(u**3*seg[0][d]+3*u*u*t*seg[1][d]+3*u*t*t*seg[2][d]+t**3*seg[3][d] for d in range(2))))
xmax=max(abs(p.x) for p in raw);ymin=min(p.y for p in raw);ymax=max(p.y for p in raw)
for p in raw:
    p.x*=E['center_stone_width']/(2*xmax)
    p.y=(p.y-(ymin+ymax)/2)*E['center_stone_height']/(ymax-ymin)

def resample(points,count):
    lengths=[0.0]
    for a,b in zip(points,points[1:]+points[:1]):lengths.append(lengths[-1]+(b-a).length)
    out=[];j=0
    for k in range(count):
        d=lengths[-1]*k/count
        while lengths[j+1]<d:j+=1
        f=(d-lengths[j])/(lengths[j+1]-lengths[j])
        out.append(points[j].lerp(points[(j+1)%len(points)],f))
    return out

def offset(points,d):
    # Outline is clockwise; left hand normal points outward.
    out=[]
    for i,p in enumerate(points):
        tangent=(points[(i+1)%len(points)]-points[(i-1)%len(points)]).normalized()
        out.append(p+Vector((-tangent.y,tangent.x))*d)
    return out

outline=resample(raw,48)
verts=[];faces=[];N=48;M=12;K=24
# Broad table/star/crown facets: no texture, no painted highlight, no emissive stone.
# The crown alternates triangular star facets and independently oriented fan facets.
for i in range(M):
    p=outline[4*i];verts.append((p.x*.43,p.y*.43,E['center_table_z']))
for i in range(M):
    p=outline[4*i+2];verts.append((p.x*.72,p.y*.72,E['center_table_z']-.34))
G=2*M
for z in [E['center_girdle_z']+.035,E['center_girdle_z']-.035]:
    for p in outline:verts.append((p.x,p.y,z))
PV=len(verts)
for i in range(K):
    p=outline[2*i];verts.append((p.x*.48,p.y*.48,E['center_culet_z']+.42))
faces.append(tuple(range(M)))
for i in range(M):
    a=i;b=(i+1)%M;star=M+i
    g=[G+(4*i+j)%N for j in range(5)]
    faces += [(a,b,star),(a,star,g[2]),(a,g[2],g[1]),(a,g[1],g[0]),
              (b,g[4],g[3]),(b,g[3],g[2]),(b,g[2],star)]
for i in range(N):faces.append((G+i,G+(i+1)%N,G+N+(i+1)%N,G+N+i))
for i in range(K):
    a=PV+i;b=PV+(i+1)%K;g0=G+N+2*i;g1=G+N+(2*i+1)%N;g2=G+N+(2*i+2)%N
    faces += [(a,g0,g1),(a,g1,b),(b,g1,g2)]
tip=len(verts);verts.append((0,-.25,E['center_culet_z']))
for i in range(K):faces.append((PV+i,PV+(i+1)%K,tip))
center=mesh_obj('02_Center_Heart_outline_EST_cut_PENDING',verts,faces,gem,
                'v02按用户反馈矮胖化；冠部/亭部独立切面精修，非已确认切割图')

def ring_wall(name,inner,outer,bottom,top):
    n=len(inner);vs=[];fs=[]
    for z in [bottom,top]:
        for loop in [inner,outer]:vs += [(p.x,p.y,z) for p in loop]
    for i in range(n):
        j=(i+1)%n
        fs += [(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),
               (i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)]
    ob=mesh_obj(name,vs,fs,gold,'待确认：背面未提供，临时心形开底镶座；外轮廓有图依据',True)
    bevel=ob.modifiers.new('Editable_edge_softening_0.06mm','BEVEL');bevel.width=.00006;bevel.segments=3 if DETAIL else 1
    return ob
hi=resample(raw,144)
gallery=ring_wall('PENDING_03_OpenBack_Gallery',[p*E['gallery_inner_scale'] for p in hi],[p*E['gallery_outer_scale'] for p in hi],
                  E['gallery_bottom_z'],E['gallery_top_z'])

def ball(name,pos,r,mat=gold,evidence='待确认：简化的镶嵌微爪',seg=12,rings=8):
    seg=16 if DETAIL else 8; rings=10 if DETAIL else 6
    vs=[(pos[0],pos[1],pos[2]+r)];fs=[]
    for j in range(1,rings):
        a=pi*j/rings
        for i in range(seg):
            t=2*pi*i/seg
            vs.append((pos[0]+r*sin(a)*cos(t),pos[1]+r*sin(a)*sin(t),pos[2]+r*cos(a)))
    bottom=len(vs);vs.append((pos[0],pos[1],pos[2]-r))
    for i in range(seg):fs.append((0,1+i,1+(i+1)%seg))
    for j in range(rings-2):
        for i in range(seg):
            a=1+j*seg+i;b=1+j*seg+(i+1)%seg;fs.append((a,a+seg,b+seg,b))
    for i in range(seg):fs.append((bottom,1+(rings-2)*seg+(i+1)%seg,1+(rings-2)*seg+i))
    return mesh_obj(name,vs,fs,mat,evidence,True)

def tube(name,path,radius,segments=12,evidence='比例估算'):
    vs=[];fs=[]
    for i,p in enumerate(path):
        tangent=Vector(path[min(i+1,len(path)-1)])-Vector(path[max(i-1,0)])
        tangent.normalize();axis=Vector((0,1,0))
        if abs(tangent.dot(axis))>.9:axis=Vector((1,0,0))
        u=tangent.cross(axis).normalized();v=tangent.cross(u).normalized()
        for k in range(segments):
            q=Vector(p)+radius*(u*cos(2*pi*k/segments)+v*sin(2*pi*k/segments));vs.append(q)
    for i in range(len(path)-1):
        for k in range(segments):
            a=i*segments+k;b=i*segments+(k+1)%segments;fs.append((a,b,b+segments,a+segments))
    fs += [tuple(reversed(range(segments))),tuple((len(path)-1)*segments+k for k in range(segments))]
    return mesh_obj(name,vs,fs,gold,evidence,True)

# Shoulder transitions are independent and editable; they touch the shank and carrier.
for sign in [-1,1]:
    vs=[];fs=[]
    stations=[(sign*R*sin(gap),R*cos(gap),.95), (sign*3.07,8.52,.88), (sign*3.05,8.98,.70)]
    for j,(x,z,thick) in enumerate(stations):
        for rr,yy in profile:
            # Start at the same profile as the shank cap, then loft vertically into the gallery.
            if j==0:vs.append((x+sign*rr*sin(gap),yy,z+rr*cos(gap)))
            else:vs.append((x+sign*rr*thick/.95,yy,z))
    for j in range(2):
        for k in range(n):a=j*n+k;b=j*n+(k+1)%n;fs.append((a,b,b+n,a+n))
    fs += [tuple(reversed(range(n))),tuple(2*n+k for k in range(n))]
    shoulder=mesh_obj('PENDING_04_ShoulderJoin_'+str(sign),vs,fs,gold,'连接关系有图依据；过渡曲面与内侧连接位置待确认',True)
    soften=shoulder.modifiers.new('Refined_transition_edges','BEVEL')
    soften.width=.000035;soften.segments=3 if DETAIL else 1

# Three clearly visible primary prongs, with approximate lengths and profiles.
prong_points=[(x*5.20/4.95,y*4.78/5.15) for x,y in [(-1.93,1.69),(1.93,1.69),(0,-2.47)]]
for i,(x,y) in enumerate(prong_points):
    direction=Vector((x,y)).normalized()
    path=[(x+direction.x*.20,y+direction.y*.20,9.04),
          (x+direction.x*.17,y+direction.y*.17,9.57),
          (x-direction.x*.11,y-direction.y*.11,10.02)]
    tube('05_MainProng_%02d_EST'%(i+1),path,.16,12,'三处主石镶爪位置由图片确认；爪形、粗细按比例估算')
    ball('05_MainProngTip_%02d_EST'%(i+1),path[-1],.175,evidence='主爪端部形状估算')

def brilliant_mesh(radius=.45):
    n=16;vs=[];fs=[]
    for r,z,phase in [(radius*.44,.28,0),(radius,.025,0),(radius,-.025,0),(radius*.46,-.29,pi/16)]:
        for i in range(n):
            a=2*pi*i/n+phase;vs.append((r*cos(a),r*sin(a),z))
    fs.append(tuple(range(n)))
    for row in range(3):
        for i in range(n):
            a=row*n+i;b=row*n+(i+1)%n;c=b+n;d=a+n
            if row==1:fs.append((a,d,c,b))
            else:fs.extend([(a,d,b),(b,d,c)])
    vs.append((0,0,-.40));tip=len(vs)-1
    for i in range(n):fs.append((3*n+i,tip,3*n+(i+1)%n))
    return vs,fs

def add_stone(name,center,normal,radius,group):
    vs,fs=brilliant_mesh(radius);normal=Vector(normal).normalized()
    q=Vector((0,0,1)).rotation_difference(normal)
    vs=[q@Vector(v)+Vector(center) for v in vs]
    ob=mesh_obj(name,vs,fs,small,'辅石存在已确认；该排列颗数/切面为待确认草稿')
    ob['group']=group
    return ob

halo_path=resample([p*E['halo_centerline_scale'] for p in hi],T['halo_stone_count']+1)[1:]
for i,p in enumerate(halo_path):
    add_stone('PENDING_Halo_%02d'%(i+1),(p.x,p.y,E['halo_girdle_z']),(0,0,1),E['halo_stone_diameter']/2,'halo')
    nextp=halo_path[(i+1)%len(halo_path)];mid=(p+nextp)/2
    t=(nextp-p).normalized();nn=Vector((-t.y,t.x))
    for k,sgn in enumerate([-1,1]):
        c=mid+nn*.27
        if sgn<0:c=mid-nn*.27
        ball('PENDING_HaloBead_%02d_%s'%(i+1,k),(c.x,c.y,9.58),.11)

for sign in [-1,1]:
    count=T['shoulder_stone_count_each_side']
    a,b=T['shoulder_pave_angle_degrees']
    for i in range(count):
        t=math.radians(a+(b-a)*i/(count-1))*sign
        nr=Vector((sin(t),0,cos(t)))
        c=nr*(8+E['band_radial_thickness']+.045)
        add_stone('PENDING_ShoulderStone_%s_%02d'%(sign,i+1),c,nr,E['shoulder_stone_diameter']/2,'shoulder')
        for s in [-1,1]:
            cp=c+Vector((0,s*.49,0))+nr*.01
            ball('PENDING_ShoulderBead_%s_%02d_%s'%(sign,i+1,s),cp,.12)

# Normalize all closed mesh normals; preserve intentional hard gemstone facets.
for ob in product.objects:
    if ob.type=='MESH':
        bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
        bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT')

# Render staging is separate from the product and is never exported.
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=72
scene.cycles.use_denoising=True
scene.cycles.max_bounces=10;scene.cycles.transmission_bounces=8
scene.render.resolution_x=900;scene.render.resolution_y=900;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=False
scene.world.use_nodes=True
scene.world.node_tree.nodes.get('Background').inputs[0].default_value=(.42,.44,.48,1)
scene.world.node_tree.nodes.get('Background').inputs[1].default_value=.4
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'

def area(name,xyz,power,size,color=(1,1,1),sy=None):
    d=bpy.data.lights.new(name,'AREA');d.energy=power*.02;d.color=color
    d.shape='RECTANGLE';d.size=size*MM;d.size_y=(sy or size)*MM
    o=bpy.data.objects.new(name,d);review.objects.link(o);o.location=Vector(xyz)*MM
    o.rotation_euler=(Vector((0,0,.002))-o.location).to_track_quat('-Z','Y').to_euler()
area('Key_softbox',(-25,-30,45),.75,30,(1,.96,.93),50)
area('Rim_softbox',(30,12,30),1.05,20,(.92,.96,1),40)
area('Front_strip',(0,-36,5),.25,9,(1,1,1),40)
area('Top_strip',(-8,24,38),.65,15,(1,1,1),45)
area('Bottom_fill',(0,0,-32),.18,25,(1,1,1),30)
area('Facet_pin_1',(-14,-18,32),.035,1.6,(1,1,1),2.2)
area('Facet_pin_2',(20,-7,25),.030,1.8,(1,1,1),1.8)
area('Facet_pin_3',(6,24,24),.025,1.5,(1,1,1),2.4)

def camera(name,direction,target=(0,0,.7),scale=24):
    data=bpy.data.cameras.new(name);data.type='ORTHO';data.ortho_scale=scale*MM
    data.clip_start=.001;data.clip_end=1
    o=bpy.data.objects.new(name,data);review.objects.link(o)
    tar=Vector(target)*MM;o.location=tar+Vector(direction).normalized()*.09
    o.rotation_euler=(tar-o.location).to_track_quat('-Z','Y').to_euler()
    return o
views={
 'front':camera('CAM_01_FRONT_heart_face',(0,0,1),(0,0,0),23),
 'side':camera('CAM_02_SIDE_profile',(1,0,0),(0,0,.8),23.5),
 'back':camera('CAM_03_BACK_ring_plane',(0,1,0),(0,0,.8),23.5),
 '45deg':camera('CAM_04_45DEG_default',P['coordinates']['default_camera_direction'],(0,0,.8),25.5),
 'underside':camera('CAM_05_UNDERSIDE_review',(0,-1,-.45),(0,0,1),25.5)
}
scene.camera=views['45deg']
# Store reproducible source and assumptions inside the .blend too.
for filename in ['build_J003.py','J003-parameters-v02.json']:
    tx=bpy.data.texts.new(filename);tx.write((BASE/filename).read_text())
for screen in bpy.data.screens:
    for ar in screen.areas:
        if ar.type=='VIEW_3D':
            ar.spaces.active.region_3d.view_distance=.038
            ar.spaces.active.region_3d.view_location=(0,0,.001)
            ar.spaces.active.clip_start=.0001;ar.spaces.active.clip_end=10
            ar.spaces.active.shading.type='MATERIAL'
bpy.ops.object.select_all(action='DESELECT');root.select_set(True);bpy.context.view_layer.objects.active=root
if DETAIL:bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'J003-source-v02.blend'))

# Keep editable source parts; batch export meshes by material to reduce browser draw calls.
export_collection=bpy.data.collections.new('TEMP_EXPORT_BATCHES')
scene.collection.children.link(export_collection)
export_batches=[]
dg=bpy.context.evaluated_depsgraph_get()
for mat,label in [(gold,'Metal'),(gem,'MainStone'),(small,'AccentStones')]:
    members=[o for o in product.objects if o.type=='MESH' and o.data.materials[0]==mat]
    bpy.ops.object.select_all(action='DESELECT')
    copies=[]
    for source in members:
        me=bpy.data.meshes.new_from_object(source.evaluated_get(dg),depsgraph=dg)
        copy=bpy.data.objects.new('export_'+source.name,me)
        export_collection.objects.link(copy);copy.matrix_world=source.matrix_world
        copy.select_set(True);copies.append(copy)
    bpy.context.view_layer.objects.active=copies[0];bpy.ops.object.join()
    joined=bpy.context.object;joined.name='J003_'+label;joined.parent=root
    joined['editable_source_parts']=[o.name for o in members]
    joined['unconfirmed_details']='stone counts and rear gallery remain provisional; see source and notes'
    export_batches.append(joined)
bpy.ops.object.select_all(action='DESELECT');root.select_set(True)
for ob in export_batches:ob.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(BASE/f'J003-{MODE}-v02.glb'),export_format='GLB',
    use_selection=True,export_apply=True,export_yup=True,export_cameras=False,export_lights=False,
    export_extras=True,export_materials='EXPORT')
for ob in export_batches:bpy.data.objects.remove(ob,do_unlink=True)
bpy.data.collections.remove(export_collection)

depsgraph=bpy.context.evaluated_depsgraph_get();triangle_count=0;bounds=[];objstats=[]
for ob in product.objects:
    if ob.type!='MESH':continue
    ev=ob.evaluated_get(depsgraph);me=ev.to_mesh();me.calc_loop_triangles()
    count=len(me.loop_triangles);triangle_count+=count
    bounds.extend([ev.matrix_world@v.co for v in me.vertices])
    objstats.append({'name':ob.name,'triangles':count,'evidence':ob.get('evidence','')})
    ev.to_mesh_clear()
lo=[min(v[k] for v in bounds)*1000 for k in range(3)];hi3=[max(v[k] for v in bounds)*1000 for k in range(3)]
stats={'stage':P['stage'],'mesh_objects':len(objstats),'export_mesh_objects':3,'triangles':triangle_count,
       'material_count_product':3,'bounds_min_mm':lo,'bounds_max_mm':hi3,
       'dimensions_mm':[hi3[k]-lo[k] for k in range(3)],'objects':objstats,
       'files':{f.name:f.stat().st_size for f in BASE.iterdir() if f.suffix in ['.blend','.glb']}}
(BASE/f'J003-{MODE}-stats.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2))
print('BUILD_COMPLETE',json.dumps({k:v for k,v in stats.items() if k!='objects'}))

if '--proof' in sys.argv:
    scene.camera=views['45deg'];scene.render.filepath=str(BASE/'J003-proof.png')
    scene.render.resolution_x=700;scene.render.resolution_y=700;scene.cycles.samples=32
    bpy.ops.render.render(write_still=True)
if '--render' in sys.argv:
    for name,cam in views.items():
        scene.camera=cam;scene.render.filepath=str(BASE/('J003-'+name+'-v02.png'))
        bpy.ops.render.render(write_still=True)
        print('RENDER_COMPLETE',name,flush=True)
    scene.camera=views['45deg']
    scene.render.filepath=str(BASE/'J003-preview-v02.png')
    scene.render.resolution_x=1200;scene.render.resolution_y=1200;scene.cycles.samples=128
    bpy.ops.render.render(write_still=True)
    print('RENDER_COMPLETE preview',flush=True)
print('J003_DONE')
