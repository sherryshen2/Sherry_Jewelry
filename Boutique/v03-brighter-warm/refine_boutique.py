"""Stage two: refine the approved Blender scene without changing its layout."""
import bpy,math,json,random,ast,struct,zlib,binascii
from math import sin,cos,pi
from mathutils import Vector
from pathlib import Path
import numpy as np
OUT=Path(__file__).resolve().parent
SRC=OUT.parent/'v01-preview'
bpy.ops.wm.open_mainfile(filepath=str(SRC/'Boutique-stage1.blend'))
scene=bpy.context.scene;groups={c.name:c for c in scene.collection.children};active='01_Architecture';ball_cache={}
random.seed(24)
def getmat(prefix):return next(m for m in bpy.data.materials if m.name.startswith(prefix+' |'))
ivory=getmat('01');edge=getmat('02');recess=getmat('03');gold=getmat('04');goldlight=getmat('05');wall=getmat('06');rose=getmat('07');silk=getmat('08');lace=getmat('09');velvet=getmat('10');linen=getmat('11');pearl=getmat('12');gem=getmat('13');glass=getmat('14');crystal=getmat('15');mirror=getmat('16');leaves=getmat('17');petalpink=getmat('18');petalcream=getmat('19');bulb=getmat('20')
# Reuse the source's editable modelling helpers, not its build routine.
tree=ast.parse((SRC/'build_boutique.py').read_text())
keep=['move','material','mesh','cube','uvball','tube','lathe','oval','rectframe','leaf','flourish','drop']
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in keep],type_ignores=[]),'<source_helpers>','exec'))

def png(name,data,noncolor=False):
    a=np.uint8(np.clip(data,0,1)*255+.5);h,w=a.shape[:2]
    if a.shape[2]==3:a=np.concatenate([a,np.full((h,w,1),255,np.uint8)],axis=2)
    def chunk(t,d):return struct.pack('>I',len(d))+t+d+struct.pack('>I',binascii.crc32(t+d)&0xffffffff)
    p=OUT/'textures'/(name+'.png')
    raw=b''.join(b'\0'+a[y].tobytes() for y in range(h))
    p.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw,8))+chunk(b'IEND',b''))
    im=bpy.data.images.load(str(p),check_existing=False);im.name=name
    im.colorspace_settings.name='Non-Color' if noncolor else 'sRGB';return im
def srgb(a):return np.where(a<=.0031308,a*12.92,1.055*np.maximum(a,0)**(1/2.4)-.055)
def texlink(m,im,socket,normal=False,strength=.2):
    nt=m.node_tree;p=nt.nodes.get('Principled BSDF');t=nt.nodes.new('ShaderNodeTexImage');t.image=im;t.interpolation='Linear'
    if normal:
        n=nt.nodes.new('ShaderNodeNormalMap');n.inputs['Strength'].default_value=strength;nt.links.new(t.outputs['Color'],n.inputs['Color']);nt.links.new(n.outputs['Normal'],p.inputs['Normal'])
    else:nt.links.new(t.outputs['Color'],p.inputs[socket])
    return t
def normal_from_height(h,scale):
    dy,dx=np.gradient(h);v=np.stack([-dx*scale,-dy*scale,np.ones_like(h)],axis=-1);v/=np.linalg.norm(v,axis=-1,keepdims=True);return v*.5+.5
n=512;yy,xx=np.mgrid[0:n,0:n];u=xx/n;v=yy/n;rng=np.random.default_rng(17)
grain=.3*sin(0) + .025*np.sin(xx*.36+np.sin(yy*.024))+.009*rng.normal(size=(n,n))
fine=png('lacquer_normal',normal_from_height(grain,1.8),True)
rough=png('lacquer_roughness',np.repeat(np.clip(.39+grain*.8,0,1)[:,:,None],3,axis=2),True)
for m in [ivory,edge,recess]:
    nt=m.node_tree;p=nt.nodes.get('Principled BSDF')
    for node in list(nt.nodes):
        if node.type in ['TEX_IMAGE','BUMP','NORMAL_MAP']:nt.nodes.remove(node)
    base=np.array(p.inputs['Base Color'].default_value[:3]);d=np.minimum.reduce([u,v,1-u,1-v]);border=np.exp(-d*95)
    # Low contrast wear: maintained painted joinery, not distressed furniture.
    variation=(grain*.10-.022*border+.015*(border>.8)*rng.random((n,n)))[:,:,None]
    im=png('paint_'+m.name[:2]+'_basecolor',srgb(np.clip(base+variation,0,1)))
    texlink(m,im,'Base Color');texlink(m,fine,'Normal',True,.18);texlink(m,rough,'Roughness')

weave=.010*np.sin(xx*pi/2)*np.sin(yy*pi/2)+.006*np.cos(xx*pi/4)
woven=png('woven_fabric_normal',normal_from_height(weave,3.5),True)
for m in [silk,linen,velvet,rose]:texlink(m,woven,'Normal',True,.22 if m==silk else .32)
def uv_grid(o,nu,nv,sx=1,sy=1):
    uv=o.data.uv_layers.get('UVMap') or o.data.uv_layers.new(name='UVMap')
    for f in o.data.polygons:
        for li in f.loop_indices:
            k=o.data.loops[li].vertex_index;uv.data[li].uv=((k%(nu+1))/nu*sx,(k//(nu+1))/nv*sy)
for o in groups['05_Textiles'].objects:
    if o.name in ['left backdrop drape','right backdrop drape']:uv_grid(o,32,56,6,24)
    if o.name in ['front left swag','front right swag']:uv_grid(o,70,16,16,3)
for o in groups['07_Jewelry'].objects:
    if o.type=='MESH' and len(o.data.materials) and o.data.materials[0]==linen:
        uv=o.data.uv_layers.new(name='UVMap')
        for f in o.data.polygons:
            for li in f.loop_indices:
                co=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=(co.x*14,co.z*14)

# Floral lace, one alpha-tested sheet per edge. No dense 3D lace lattice.
w,h=1024,256;Y,X=np.mgrid[0:h,0:w];U=X/w;V=Y/h;A=np.zeros((h,w))
def stroke(xs,ys,width):
    global A
    dist=np.full((h,w),9.)
    for x,y in zip(xs,ys):dist=np.minimum(dist,((U-x)*3.0)**2+(V-y)**2)
    A=np.maximum(A,np.clip((width-np.sqrt(dist))*240+.5,0,1))
t=np.linspace(0,2*pi,420)
for center in [.25,.75]:
    rr=.18+.060*np.cos(t*6);stroke(center+rr*np.cos(t)/3,.48+rr*np.sin(t),.011)
    stroke(center+.075*np.cos(t)/3,.48+.075*np.sin(t),.009)
    for k in range(6):
        a=k*pi/3;stroke(center+(.13+.065*np.cos(t))*cos(a)/3+.022*np.sin(t)*sin(a)/3,.48+(.13+.065*np.cos(t))*sin(a)-.022*np.sin(t)*cos(a),.007)
stroke(np.linspace(0,1,800),.20+.075*np.sin(np.linspace(0,4*pi,800)),.009)
stroke(np.linspace(0,1,800),.78+.12*np.cos(np.linspace(0,4*pi,800)),.011)
net1=np.abs(np.sin((U*12+V*2.3)*pi));net2=np.abs(np.sin((U*12-V*2.3)*pi))
net=(np.minimum(net1,net2)<.045)*.58
A=np.maximum(A,net);A=np.maximum(A,(V<.055)*1.);A=np.maximum(A,(np.abs(V-(.93-.045*np.cos(U*8*pi)))<.011)*1.)
rgba=np.ones((h,w,4));rgba[:,:,3]=A
laceimage=png('floral_lace_rgba',rgba)
lace.name='09 | floral ecru lace cutout';lace.use_backface_culling=False
p=lace.node_tree.nodes.get('Principled BSDF');tx=lace.node_tree.nodes.new('ShaderNodeTexImage');tx.image=laceimage
lace.node_tree.links.new(tx.outputs['Alpha'],p.inputs['Alpha']);p.inputs['Sheen Weight'].default_value=.24
lace.surface_render_method='DITHERED';lace['web_alpha_mode']='MASK';lace['web_alpha_cutoff']=.45
for o in list(groups['05_Textiles'].objects):
    if 'scalloped lace preview' in o.name:
        o.name=o.name.replace(' preview',' openwork')
        for i in range(141):
            top=o.data.vertices[i*2].co.z;bt=o.data.vertices[i*2+1];bt.co.z=top+(bt.co.z-top)*1.85
        uv=o.data.uv_layers.new(name='UVMap')
        for f in o.data.polygons:
            for li in f.loop_indices:
                k=o.data.loops[li].vertex_index;uv.data[li].uv=((k//2)/140*8,1-(k%2))
active='05_Textiles'
for name,edgecol in [('left backdrop drape',32),('right backdrop drape',0)]:
    old=bpy.data.objects[name];vs=[];fs=[]
    for j in range(57):
        a=old.data.vertices[j*33+edgecol].co.copy()
        vs.extend([tuple(a+Vector((0,-.018,0))),tuple(a+Vector((-.072 if edgecol==32 else .072,-.022,0)))])
    for j in range(56):q=j*2;fs.append((q,q+1,q+3,q+2))
    o=mesh(name+' lace selvedge',vs,fs,lace,True);uv=o.data.uv_layers.new(name='UVMap')
    for f in o.data.polygons:
        for li in f.loop_indices:
            k=o.data.loops[li].vertex_index;uv.data[li].uv=((k//2)/56*10,k%2)

# Quiet damask wallpaper: replace small repeated meshes with a shared bitmap.
for o in list(groups['01_Architecture'].objects):
    if o.name.startswith('wall damask sprig'):bpy.data.objects.remove(o,do_unlink=True)
n=512;Y,X=np.mgrid[0:n,0:n];U=X/n-.5;V=Y/n-.5
rad=np.sqrt((U*1.25)**2+(V*.85)**2);theta=np.arctan2(V,U)
pattern=np.exp(-((rad-(.19+.065*np.cos(theta*4)))/.008)**2)
pattern+=.6*np.exp(-((rad-.075)/.006)**2)
pattern=np.clip(pattern,0,1)
base=np.array((.69,.61,.53));walltex=png('oyster_damask_basecolor',srgb(np.clip(base[None,None,:]-.025*pattern[:,:,None],0,1)))
texlink(wall,walltex,'Base Color')
for o in groups['01_Architecture'].objects:
    if o.type=='MESH' and o.data.materials and o.data.materials[0]==wall:
        uv=o.data.uv_layers.get('UVMap') or o.data.uv_layers.new(name='UVMap')
        for f in o.data.polygons:
            a,b=(0,2) if abs(f.normal.y)>.5 else (1,2)
            for li in f.loop_indices:
                co=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=(co[a]/.42,co[b]/.42)

# Raised acanthus detail concentrates in the crest, counter apron and frame edges.
def acanthus(name,x,y,z,L,angle,width=.05,mat=edge):
    vs=[];fs=[]
    for i in range(11):
        t=i/10;wid=width*sin(pi*t)**.7*(1+.16*sin(t*pi*9));bend=.12*L*sin(t*pi)
        for j in range(5):
            s=(j-2)/2;dx=s*wid+bend;dz=L*t;depth=.024*sin(pi*t)*(1-s*s)
            vs.append((x+dx*cos(angle)-dz*sin(angle),y-depth,z+dx*sin(angle)+dz*cos(angle)))
    for i in range(10):
        for j in range(4):q=i*5+j;fs.append((q,q+1,q+6,q+5))
    o=mesh(name,vs,fs,mat,True);mod=o.modifiers.new('carved leaf thickness','SOLIDIFY');mod.thickness=.007
    pts=[]
    for t in np.linspace(0,1,20):dx=.12*L*sin(t*pi);dz=L*t;pts.append((x+dx*cos(angle)-dz*sin(angle),y-.025*sin(pi*t)-.002,z+dx*sin(angle)+dz*cos(angle)))
    tube(name+' fine vein',pts,.004,ivory,res=1)
def enrich(name,x,y,z,s):
    for side in [-1,1]:
        for k in range(5):
            a=-.55+k*.37;cx=x+side*(.20+.13*k)*s;cz=z+(.06+.065*sin(k))*s
            acanthus(name+' acanthus',cx,y,cz,(.24-.015*k)*s,-side*(.28+k*.28),.045*s)
        pts=[(x+side*(.15+.67*t)*s,y+.002,z-.03*s+.11*s*sin(pi*t)) for t in np.linspace(0,1,48)]
        tube(name+' inner tendril',pts,.009*s,gold,res=2)
        for k in range(4):
            q=.31+.14*k;acanthus(name+' lower fan',x+side*q*s,y,z-.06*s,.13*s,side*(2.1+k*.12),.030*s)
active='01_Architecture';enrich('pediment',0,-.59,5.04,1.65)
for k in range(9):
    a=(k-4)*.22;t=np.linspace(0,1,24)
    tube('cartouche shell rib',[(sin(a)*(.04+.105*f),-.685-.018*sin(pi*f),5.1+f*.23) for f in t],.007,edge,res=1)
for side in [-1,1]:
    for k in [-1,0,1]:acanthus('column cap detail',side*2.75+k*.075,-.535,4.22,.16,-k*.35,.035)
# Concealed structural hanger connects the chandelier to the front header.
cube('chandelier concealed hanger',(0,.27,4.75),(.12,1.52,.095),ivory,.012)
active='02_Counter';enrich('counter apron',0,-.10,.97,.85)
for x in [-1.43,1.43]:
    for zz in [.70,1.22]:
        acanthus('counter corner foliate',x,-.080,zz,.13,-.65 if x<0 else .65,.032)
for x in np.linspace(-1.38,1.38,39):uvball('counter top pearl moulding',(x,-.076,1.77),(.012,.008,.012),edge,8,6)
active='03_Display_cabinets'
for x in [-1.91,1.91]:enrich('cabinet crest',x,1.735,4.06,.36)
active='04_Mirror';enrich('mirror crown detail',0,2.33,4.0,.52)

# Fine settings and a single pendant focal detail, without adding display clutter.
active='07_Jewelry'
p=pearl.node_tree.nodes.get('Principled BSDF');p.inputs['Metallic'].default_value=.03;p.inputs['Coat Weight'].default_value=.24;p.inputs['Coat Roughness'].default_value=.20
for o in list(groups['07_Jewelry'].objects):
    if o.type=='MESH' and o.data.materials and o.data.materials[0]==gem:
        for f in o.data.polygons:f.use_smooth=False
        if 'pendant' in o.name:
            x,y,z=o.location;rx,ry,rz=o.scale
            oval('pendant gold bezel',x,y-.006,z,rx*1.12,rz*1.10,.005,goldlight)
            for t in np.linspace(0,2*pi,12,endpoint=False):uvball('pendant halo seed pearl',(x+rx*1.38*cos(t),y-.015,z+rz*1.32*sin(t)),(.007,.007,.007),pearl,8,6)
        if 'ring stone' in o.name:
            x,y,z=o.location
            for a in [pi/4,3*pi/4,5*pi/4,7*pi/4]:uvball('ring prong',(x+.018*cos(a),y+.018*sin(a),z+.011),(.006,.006,.009),goldlight,8,6)

# Restore self-contained relative bitmap paths and save the fully editable master.
for im in list(bpy.data.images):
    if im.name in ['Render Result','Viewer Node']:continue
    if im.users==0:bpy.data.images.remove(im);continue
    if im.source=='FILE':
        if not im.packed_file:im.pack()
        im.filepath='//textures/'+Path(im.filepath).name
scene['stage']='FINAL — approved layout 2026-10-23; refined materials and decoration'
scene['web_notes']='Use delivered GLB for browser: baked vertex contact occlusion, alpha-tested lace, one-layer glass, reflection capture and opaque crystal approximation.'
if 'future_refinement' in scene:del scene['future_refinement']
if bpy.data.texts.get('ABOUT_STAGE_1'):bpy.data.texts.remove(bpy.data.texts['ABOUT_STAGE_1'])
t=bpy.data.texts.new('READ_ME');t.write('可编辑精品店完成版。布局于2026-10-23获确认。\n分组保留建模结构与曲线。源文件采用Cycles摄影灯光；网页请使用随附GLB与viewer。\n镜面、水晶、玻璃的网页近似与灯光参数见交付说明。\n')
scene.camera=bpy.data.objects['01_Front'];scene.cycles.samples=48;scene.render.resolution_x=1400;scene.render.resolution_y=1400
scene.render.filepath='//Boutique-hero.png';bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Boutique-final.blend'))
print('REFINEMENT_SAVED',len(bpy.data.objects),flush=True)
