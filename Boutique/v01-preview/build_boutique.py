"""Editable Blender spatial / palette / lighting study. Stage 1, approval pending.
All dimensions are authored in scene metres as a presentation model.
Front is -Y, up is Z. The web export changes to glTF +Y up.
"""
import bpy, math, json, random, sys
from math import sin, cos, pi
from mathutils import Vector
from pathlib import Path
import numpy as np

OUT=Path(__file__).resolve().parent
random.seed(24)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
    if c.name!='Collection': bpy.data.collections.remove(c)
scene=bpy.context.scene
scene.unit_settings.system='METRIC'
groups={}
for name in ['01_Architecture','02_Counter','03_Display_cabinets','04_Mirror','05_Textiles','06_Chandelier','07_Jewelry','08_Flowers_and_gifts','90_Studio','91_Cameras']:
    c=bpy.data.collections.new(name); scene.collection.children.link(c); groups[name]=c
active='01_Architecture'
def move(o):
    for c in list(o.users_collection): c.objects.unlink(o)
    groups[active].objects.link(o)
    return o
def material(name,col,metal=0,rough=.45,trans=0):
    m=bpy.data.materials.new(name); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*col,1); p.inputs['Metallic'].default_value=metal
    p.inputs['Roughness'].default_value=rough; p.inputs['Transmission Weight'].default_value=trans
    p.inputs['IOR'].default_value=1.46
    m.diffuse_color=(*col,1)
    return m
ivory=material('01 | warm ivory lacquer',(.66,.57,.46),.04,.37)
edge=material('02 | ivory carved edges',(.80,.70,.56),.05,.34)
recess=material('03 | inset warm putty',(.49,.40,.31),0,.52)
gold=material('04 | satin champagne brass',(.62,.41,.19),.77,.28)
goldlight=material('05 | champagne polished accents',(.80,.60,.31),.84,.23)
wall=material('06 | warm oyster wall',(.69,.61,.53),0,.75)
rose=material('07 | dusty blush silk',(.58,.33,.32),0,.60)
silk=material('08 | pale warm drapery',(.84,.74,.63),0,.63)
lace=material('09 | ecru lace preview',(.88,.81,.71),0,.80)
velvet=material('10 | rose velvet lining',(.39,.22,.22),0,.86)
linen=material('11 | oatmeal velvet display forms',(.78,.70,.59),0,.77)
pearl=material('12 | soft ivory pearls',(.92,.88,.76),.14,.23)
gem=material('13 | rose quartz faceted accents',(.64,.37,.38),.18,.15,.15)
glass=material('14 | display glass',(.93,.98,1.0),0,.12,.98)
crystal=material('15 | chandelier crystal',(.91,.96,1.0),.08,.10,.68)
mirror=material('16 | softened silver mirror',(.80,.85,.84),.94,.17)
leaves=material('17 | muted eucalyptus',(.23,.32,.20),0,.65)
petalpink=material('18 | pale blush petals',(.68,.42,.39),0,.72)
petalcream=material('19 | buttercream petals',(.85,.74,.55),0,.74)
bulb=material('20 | warm candle light',(.98,.80,.49),0,.30)
p=bulb.node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(1,.68,.34,1);p.inputs['Emission Strength'].default_value=3
studio=material('21 | warm grey backdrop',(.70,.67,.63),0,.86)
p=studio.node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(.70,.67,.63,1);p.inputs['Emission Strength'].default_value=.30

# Small reusable bitmap textures keep the preview portable in glTF.
def texture(name,arr):
    h,w=arr.shape[:2]; im=bpy.data.images.new(name,width=w,height=h,alpha=True)
    im.pixels.foreach_set(arr.astype(np.float32).ravel()); im.filepath_raw=str(OUT/'textures'/f'{name}.png');im.file_format='PNG';im.save();im.filepath='//textures/'+name+'.png'
    return im
n=512; yy,xx=np.mgrid[0:n,0:n];rng=np.random.default_rng(42)
noise=rng.normal(0,.007,(n,n));grain=.012*np.sin(xx*.52+np.sin(yy*.014)*1.8)+noise
arr=np.ones((n,n,4));arr[:,:,:3]=np.clip(.80+grain[:,:,None],0,1)
im=texture('fine_painted_wood',arr)
for m in [ivory,edge,recess]:
    nt=m.node_tree;p=nt.nodes.get('Principled BSDF');t=nt.nodes.new('ShaderNodeTexImage');t.image=im;t.label='Subtle lacquer grain';b=nt.nodes.new('ShaderNodeBump');b.inputs['Strength'].default_value=.12;b.inputs['Distance'].default_value=.013;nt.links.new(t.outputs['Color'],b.inputs['Height']);nt.links.new(b.outputs['Normal'],p.inputs['Normal'])
for m in [silk,linen,velvet,rose]:
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Sheen Weight'].default_value=.28;p.inputs['Sheen Roughness'].default_value=.6

def mesh(name,verts,faces,mat,smooth=False):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
    o=bpy.data.objects.new(name,me);groups[active].objects.link(o)
    if mat: me.materials.append(mat)
    for f in me.polygons: f.use_smooth=smooth
    return o
def cube(name,pos,size,mat,bevel=.015):
    vs=[(a*size[0]/2,b*size[1]/2,c*size[2]/2) for a,b,c in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
    fs=[(2,6,4,0),(5,7,3,1),(4,5,1,0),(3,7,6,2),(1,3,2,0),(6,7,5,4)]
    o=mesh(name,vs,fs,mat);o.location=pos
    uv=o.data.uv_layers.new(name='UVMap')
    for f in o.data.polygons:
        for idx,co in zip(f.loop_indices,[(0,0),(1,0),(1,1),(0,1)]):uv.data[idx].uv=co
    if bevel:
        b=o.modifiers.new('soft joinery edges','BEVEL');b.width=bevel;b.segments=3
        b=o.modifiers.new('weighted cabinet normals','WEIGHTED_NORMAL')
    return o
ball_cache={}
def uvball(name,pos,scale,mat,seg=16,rings=10):
    key=(seg,rings,mat.name)
    if key not in ball_cache:
        vs=[(0,0,1)];fs=[]
        for j in range(1,rings):
            t=pi*j/rings
            for k in range(seg):a=2*pi*k/seg;vs.append((sin(t)*cos(a),sin(t)*sin(a),cos(t)))
        end=len(vs);vs.append((0,0,-1))
        for k in range(seg):fs.append((0,1+k,1+(k+1)%seg))
        for j in range(rings-2):
            for k in range(seg):a=1+j*seg+k;b=1+j*seg+(k+1)%seg;fs.append((a,a+seg,b+seg,b))
        for k in range(seg):fs.append((end,1+(rings-2)*seg+(k+1)%seg,1+(rings-2)*seg+k))
        me=bpy.data.meshes.new('shared '+mat.name+str((seg,rings)));me.from_pydata(vs,[],fs);me.materials.append(mat);me.update()
        for f in me.polygons:f.use_smooth=True
        ball_cache[key]=me
    o=bpy.data.objects.new(name,ball_cache[key]);groups[active].objects.link(o);o.location=pos;o.scale=scale;return o
def tube(name,pts,r,mat,closed=False,res=3):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=1;cu.bevel_depth=r;cu.bevel_resolution=res
    sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
    for p,co in zip(sp.points,pts):p.co=(*co,1)
    sp.use_cyclic_u=closed;o=bpy.data.objects.new(name,cu);groups[active].objects.link(o);cu.materials.append(mat);return o
def lathe(name,pos,profile,mat,segments=32):
    verts=[];faces=[]
    for z,r in profile:
        for j in range(segments):a=2*pi*j/segments;verts.append((pos[0]+r*cos(a),pos[1]+r*sin(a),pos[2]+z))
    for k in range(len(profile)-1):
        for j in range(segments):q=k*segments+j;qn=k*segments+(j+1)%segments;faces.append((q,qn,qn+segments,q+segments))
    faces.extend([tuple(reversed(range(segments))),tuple((len(profile)-1)*segments+j for j in range(segments))]);return mesh(name,verts,faces,mat,True)
def oval(name,x,y,z,rx,rz,r,mat):
    return tube(name,[(x+rx*cos(2*pi*i/96),y,z+rz*sin(2*pi*i/96)) for i in range(96)],r,mat,True)
def rectframe(name,x,y,z,w,h,r,mat):
    # Rounded rectangular moulding in the XZ plane.
    pts=[];rr=min(.055,w/6,h/6)
    for cx,cz,a0 in [(x+w/2-rr,z+h/2-rr,0),(x-w/2+rr,z+h/2-rr,90),(x-w/2+rr,z-h/2+rr,180),(x+w/2-rr,z-h/2+rr,270)]:
        for i in range(7):a=math.radians(a0+90*i/6);pts.append((cx+rr*cos(a),y,cz+rr*sin(a)))
    return tube(name,pts,r,mat,True)
def leaf(name,x,y,z,length,ang,mat=edge,width=.055):
    # Curved acanthus-like relief leaf, with its ridge standing toward the viewer.
    verts=[]
    for i in range(9):
        t=i/8;ww=width*sin(pi*t)**.8
        for side in [-1,0,1]:
            dx=side*ww+.08*length*sin(pi*t);dz=length*t
            verts.append((x+dx*cos(ang)-dz*sin(ang),y-.035*sin(pi*t)*(1-abs(side)*.65),z+dx*sin(ang)+dz*cos(ang)))
    faces=[]
    for i in range(8):
        for j in range(2):q=i*3+j;faces.append((q,q+1,q+4,q+3))
    ob=mesh(name,verts,faces,mat,True);m=ob.modifiers.new('leaf thickness','SOLIDIFY');m.thickness=.007
    return ob
def flourish(name,x,y,z,s=1,mat=edge):
    for side in [-1,1]:
        pts=[]
        for i in range(54):
            t=i/53;theta=-pi*.65+t*pi*2.0;r=.28*s*(1-.82*t)
            pts.append((x+side*(.29*s+r*cos(theta)),y-.016*sin(t*pi),z+.03*s+r*sin(theta)))
        tube(name+' volute',pts,.020*s,mat,res=2)
        tube(name+' stem',[(x+side*t*.68*s,y,z-.08*s+.11*s*sin(t*pi)) for t in np.linspace(0,1,26)],.014*s,mat,res=2)
        for k in range(3):
            leaf(name+' foliage',x+side*(.24+.17*k)*s,y-.009,z+(.04-.03*k)*s,(.22-.045*k)*s,-side*(.55+k*.32),mat,.055*s)
    uvball(name+' heart',(x,y-.02,z+.04*s),(.10*s,.045*s,.15*s),mat)
    for side in [-1,1]:leaf(name+' crest',x+side*.035*s,y-.035,z+.10*s,.22*s,-side*.36,mat,.065*s)
def boxpoly(name,outline,depth,y,mat):
    n=len(outline);vs=[(x,y-d*depth,z) for d in [0,1] for x,z in outline];fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    for i in range(n):j=(i+1)%n;fs.append((i,j,j+n,i+n))
    return mesh(name,vs,fs,mat)

# Foundation and the genuinely deep, open-front room.
cube('layered plinth lower',(0,1.12,.105),(6.12,3.48,.21),ivory,.055)
cube('plinth gold hairline',(0,1.12,.23),(6.16,3.51,.032),gold,.012)
cube('plinth upper bullnose',(0,1.12,.285),(6.10,3.46,.09),edge,.04)
cube('floor substrate',(0,1.14,.342),(5.72,3.21,.045),recess,.008)
floors=[material('oak parquet '+str(i),(.49+i*.013,.38+i*.012,.27+i*.010),0,.55) for i in range(7)]
# Diagonally cut chevron parquet, modelled as strips clipped at the room border.
def clip(poly,axis,val,keep):
    out=[]
    for i,a in enumerate(poly):
        b=poly[(i+1)%len(poly)];ia=(a[axis]-val)*keep>=0;ib=(b[axis]-val)*keep>=0
        if ia:out.append(a)
        if ia!=ib:
            t=(val-a[axis])/(b[axis]-a[axis]);out.append(tuple(a[k]+t*(b[k]-a[k]) for k in range(2)))
    return out
for row in range(-5,12):
    for col in range(-5,6):
        x0=col*.66;y0=row*.27
        sg=1 if col%2==0 else -1
        poly=[(x0,y0),(x0+.655,y0+sg*.42),(x0+.655,y0+sg*.42+.259),(x0,y0+.259)]
        for ax,val,keep in [(0,-2.83,1),(0,2.83,-1),(1,-.43,1),(1,2.73,-1)]:
            if poly:poly=clip(poly,ax,val,keep)
        if len(poly)>2:mesh('chevron parquet',[(x,y,.37) for x,y in poly],[tuple(range(len(poly)))],random.choice(floors))
cube('back wall',(0,2.73,2.37),(5.80,.18,4.07),wall,.025)
for side in [-1,1]:
    cube('side wall', (side*2.83,1.19,2.37),(.18,3.05,4.07),wall,.024)
    cube('side wall skirting',(side*2.70,1.19,.54),(.12,3.0,.31),ivory,.018)
    cube('side wall upper crown',(side*2.72,1.19,4.32),(.18,3.05,.16),edge,.02)
cube('rear wainscot',(0,2.60,.89),(5.50,.10,1.0),ivory)
for x in [-2.14,-1.07,0,1.07,2.14]:rectframe('rear panelling',x,2.525,.91,.93,.66,.022,edge)
cube('rear dado rail',(0,2.51,1.43),(5.49,.16,.09),edge,.018)
cube('rear cornice',(0,2.55,4.32),(5.25,.23,.16),ivory,.02)
cube('rear cornice gilt',(0,2.41,4.25),(5.54,.035,.026),gold,.008)
# Tone-on-tone wall sprigs suggest wallpaper without crowding the scene.
for x in np.arange(-2.4,2.5,.38):
    for z in np.arange(1.65,4.20,.40):
        for side in [-1,1]:leaf('wall damask sprig',x,2.626,z,.095,side*.55,recess,.020)

# Complete front portal with fluted columns, caps and pediment.
for side in [-1,1]:
    x=side*2.75;y=-.25
    cube('pilaster backing',(x,y,2.58),(.36,.35,4.47),ivory,.018)
    cube('column square foot',(x,y-.025,.54),(.48,.50,.35),ivory,.025)
    cube('column foot step',(x,y-.05,.39),(.51,.53,.08),edge,.018)
    lathe('turned column',(x,y-.15,0),[(.68,.19),(.73,.21),(.78,.17),(.84,.15),(1.0,.135),(3.99,.115),(4.06,.15),(4.12,.17),(4.17,.17)],edge,40)
    for a in np.linspace(pi,2*pi,10):
        tube('flute highlight',[(x+.139*cos(a),y-.15+.139*sin(a),.89),(x+.119*cos(a),y-.15+.119*sin(a),3.99)],.010,ivory,res=2)
    for zz,ww,dd,hh in [(4.20,.43,.48,.12),(4.37,.49,.51,.12),(4.46,.53,.55,.07),(4.79,.50,.52,.12)]:cube('capital moulding',(x,y-.04,zz),(ww,dd,hh),edge,.015)
    cube('capital carved block',(x,y,4.61),(.38,.39,.28),ivory,.008)
    for dx in [-.10,0,.10]:leaf('capital acanthus',x+dx,y-.27,4.20,.24,-dx*2.5,edge,.058)
    rectframe('capital inset',x,y-.20,4.61,.23,.21,.014,gold)
    lathe('finial foot',(x,y,4.86),[(0,.16),(.06,.19),(.12,.12),(.19,.09)],edge)
    uvball('acorn finial',(x,y,5.12),(.115,.115,.17),edge,20,12)
    for a in np.linspace(0,2*pi,9)[:-1]:tube('acorn rib',[(x+.114*sin(t)*cos(a),y+.114*sin(t)*sin(a),5.12+.17*cos(t)) for t in np.linspace(.18,pi-.18,18)],.008,ivory,res=1)
def arch(x):return 4.90+.72*max(0,cos(min(abs(x)/2.36,1)*pi/2))**1.45
xs=np.linspace(-2.72,2.72,120)
outline=[(-2.72,4.56),(2.72,4.56)]+[(x,arch(x)) for x in reversed(xs)]
boxpoly('arched pediment panel',outline,.29,-.22,ivory)
for offset,r,mat in [(0,.057,edge),(-.080,.026,recess),(-.115,.023,edge)]:tube('arched crown moulding',[(x,-.55,arch(x)+offset) for x in xs],r,mat,res=3)
for zz,h,depth,mat in [(4.56,.11,.39,edge),(4.67,.035,.44,gold),(4.72,.07,.38,ivory)]:cube('horizontal entablature',(0,-.35,zz),(5.55,depth,h),mat,.012)
flourish('pediment carved relief',0,-.555,5.03,1.65,edge)
oval('crest cartouche',0,-.63,5.20,.15,.23,.035,edge)
for k in range(7):
    a=-.9+k*.3;leaf('crest crown leaves',sin(a)*.13,-.63,5.28,.21,-a,edge,.048)

# Central furniture: curved legs, panelled apron, glazed upper case.
active='02_Counter'
for x in [-1.38,1.38]:
    for y in [.14,.93]:
        tube('cabriole counter foot',[(x,y,.39),(x*1.02,y-.02,.49),(x*.98,y,.66)],.070,ivory)
        uvball('gilt foot shoe',(x,y-.01,.405),(.085,.083,.028),gold)
cube('counter main carcass',(0,.55,.98),(3.08,1.0,.75),ivory,.06)
cube('counter bottom ogee',(0,.53,.615),(3.16,1.06,.12),edge,.04)
cube('counter central recessed panel',(0,.025,.98),(1.81,.035,.54),recess,.035)
cube('counter central ivory field',(0,-.002,.98),(1.71,.024,.44),ivory,.025)
rectframe('central applied moulding',0,-.029,.98,1.77,.50,.025,edge)
for x in [-1.19,1.19]:
    cube('counter side panel',(x,.018,.98),(.48,.040,.55),ivory,.025);rectframe('side field trim',x,-.023,.98,.38,.45,.022,edge)
for x in [-1.51,-.95,.95,1.51]:
    cube('front carved stile',(x,-.012,.98),(.065,.09,.66),edge,.018)
flourish('counter relief',0,-.072,.97,.85,edge)
cube('showcase sill',(0,.53,1.37),(3.19,1.08,.10),edge,.023)
cube('velvet display shelf',(0,.55,1.433),(2.95,.86,.035),velvet,.012)
for x in [-1.49,-.52,.52,1.49]:cube('slender brass glazing bar',(x,.025,1.60),(.025,.035,.35),gold,.008)
for x in [-1.48,1.48]:cube('counter corner uprights',(x,.56,1.60),(.07,1.04,.38),ivory,.012)
cube('front glass single layer',(0,.043,1.60),(2.92,.009,.34),glass,.003)
cube('counter top',(0,.53,1.82),(3.29,1.16,.11),ivory,.045)
cube('counter top gilt edge',(0,-.065,1.81),(3.22,.021,.027),gold,.007)
for x in [-1.40,1.40]:flourish('counter shoulder carving',x,-.074,1.30,.18,gold)

# Matched narrow vitrines, with open-front preview glazing strategy.
active='03_Display_cabinets'
for x in [-1.91,1.91]:
    y=2.12
    for dx in [-.38,.38]:lathe('display feet',(x+dx,y-.22,.37),[(0,.055),(.12,.047),(.20,.07)],ivory,20)
    cube('display cabinet backing',(x,y+.30,2.25),(.96,.09,3.45),ivory,.025)
    cube('display cabinet lining',(x,y+.24,2.63),(.78,.018,2.45),recess,.01)
    cube('cabinet base',(x,y,.87),(1.02,.72,.66),ivory,.035)
    cube('base top moulding',(x,y,1.22),(1.08,.76,.09),edge,.02)
    for zz in [.73,1.00]:
        rectframe('cabinet drawer',x,y-.372,zz,.80,.19,.017,edge)
        uvball('drawer drop pull',(x,y-.409,zz),(.038,.019,.023),goldlight)
    for dx in [-.46,.46]:
        cube('vitrine side stile',(x+dx,y-.01,2.60),(.085,.67,2.73),ivory,.016)
        tube('vitrine gilt vertical',[(x+dx,y-.36,1.28),(x+dx,y-.36,3.86)],.012,gold)
    for zz in [1.35,2.13,2.92]:
        cube('glass cabinet shelf',(x,y,zz),(.85,.57,.035),edge,.009)
        tube('shelf brass lip',[(x-.43,y-.30,zz),(x+.43,y-.30,zz)],.011,gold)
        cube('undershelf warm line',(x,y-.20,zz-.038),(.67,.020,.014),bulb,.004)
    cube('cabinet upper crown',(x,y,3.93),(1.08,.77,.15),edge,.028)
    tube('cabinet arched top',[(x+.49*cos(t),y-.35,3.98+.22*sin(t)) for t in np.linspace(0,pi,50)],.045,ivory)
    flourish('cabinet crown ornament',x,y-.36,4.07,.35,edge)
    # A shallow brass arch frames the opening.
    tube('cabinet inside arch',[(x+.40*cos(t),y-.363,3.62+.23*sin(t)) for t in np.linspace(0,pi,42)],.021,gold)

active='04_Mirror'
# Oval mirrored glass and layered gilded frame.
uvball('oval mirror glass',(0,2.495,2.83),(.79,.020,1.08),mirror,64,32)
for rx,rz,r,mat in [(.81,1.1,.055,gold),(.88,1.17,.035,edge),(.86,1.15,.023,goldlight),(.75,1.04,.016,goldlight)]:oval('mirror layered frame',0,2.44,2.83,rx,rz,r,mat)
for t in np.linspace(0,2*pi,48,endpoint=False):uvball('mirror beaded edge',(.815*cos(t),2.38,2.83+1.105*sin(t)),(.018,.013,.018),goldlight,10,6)
flourish('mirror crown',0,2.36,4.0,.55,gold)
for side in [-1,1]:
    for k in range(3):leaf('mirror foliage',side*.83,2.375,2.43+k*.36,.19,side*.75,gold,.05)
cube('mirror console ledge',(0,2.29,1.62),(1.72,.55,.10),ivory,.025)

# Draped fabrics: coherent continuous surfaces with folded silhouettes.
active='05_Textiles'
def swag(name,x0,x1,y,ztop,drop):
    verts=[];faces=[];nu=70;nv=16
    for j in range(nv+1):
        v=j/nv
        for i in range(nu+1):
            u=i/nu;archsin=sin(pi*u)**.6
            z=ztop-.05*v-drop*archsin*v+.015*sin(u*pi*16)*v
            yy=y-.10*sin(pi*u)-.042*sin(pi*v*7)*archsin
            verts.append((x0+(x1-x0)*u,yy,z))
    for j in range(nv):
        for i in range(nu):a=j*(nu+1)+i;faces.append((a,a+1,a+nu+2,a+nu+1))
    ob=mesh(name,verts,faces,silk,True);mod=ob.modifiers.new('fabric edge','SOLIDIFY');mod.thickness=.006
    pts=[(x0+(x1-x0)*u,y-.10*sin(pi*u)-.018,ztop-.05-drop*sin(pi*u)**.6+.015*sin(u*pi*16)) for u in np.linspace(0,1,100)]
    tube(name+' lace seam',pts,.018,lace,res=2)
    # Broad scalloped lace band is a stage-1 shape proxy, not final openwork.
    vv=[];ff=[]
    for i in range(141):
        u=i/140;x=x0+(x1-x0)*u;zz=ztop-.05-drop*sin(pi*u)**.6+.015*sin(u*pi*16);yy=y-.10*sin(pi*u)-.02
        vv.extend([(x,yy,zz),(x,yy-.008,zz-.07-.045*(.5-.5*cos(u*20*pi)))])
    for i in range(140):ff.append((2*i,2*i+1,2*i+3,2*i+2))
    mesh(name+' scalloped lace preview',vv,ff,lace,True)
swag('front left swag',-2.54,0,-.10,4.56,.30)
swag('front right swag',0,2.54,-.10,4.56,.30)
def curtain(name,side):
    verts=[];faces=[];nu=32;nv=56
    for j in range(nv+1):
        v=j/nv;z=4.35-2.76*v
        center=side*(.82+.49*sin(pi*v*.85)**1.5);width=.68-.25*sin(pi*v*.88)
        for i in range(nu+1):
            u=i/nu;xx=center+(u-.5)*width;yy=2.24+.060*cos(u*10*pi)+.06*sin(pi*v)
            verts.append((xx,yy,z+.035*cos(u*10*pi)*v))
    for j in range(nv):
        for i in range(nu):a=j*(nu+1)+i;faces.append((a,a+1,a+nu+2,a+nu+1))
    ob=mesh(name,verts,faces,silk,True);mod=ob.modifiers.new('fabric body','SOLIDIFY');mod.thickness=.009
    v=.70;z=4.35-2.76*v;c=side*(.82+.49*sin(pi*v*.85)**1.5);w=.68-.25*sin(pi*v*.88)
    tube('curtain gold tieback',[(c-w/2+w*t,2.19-.045*sin(pi*t),z-.05*sin(pi*t)) for t in np.linspace(0,1,32)],.020,gold)
    tube('curtain tassel cord',[(c-side*.14,2.19,z),(c-side*.17,2.16,z-.20)],.011,gold)
    lathe('curtain tassel',(c-side*.17,2.16,z-.34),[(0,.035),(.10,.025),(.14,.04),(.17,.016)],gold,20)
curtain('left backdrop drape',-1);curtain('right backdrop drape',1)

# One six-arm chandelier; crystal geometry is deliberately low polygon.
active='06_Chandelier'
cx=0;cy=1.0
lathe('ceiling rose',(0,cy,4.67),[(0,.16),(.06,.20),(.10,.12)],gold)
for i in range(5):
    a=i%2*pi/2
    tube('chain link',[(.042*cos(t)*cos(a),cy+.042*cos(t)*sin(a),4.64-i*.075+.065*sin(t)) for t in np.linspace(0,2*pi,28)],.010,gold,True,2)
lathe('chandelier central spindle',(0,cy,3.28),[(0,.055),(.10,.12),(.16,.09),(.25,.11),(.34,.14),(.40,.10),(.63,.06),(.77,.12),(.83,.07),(.98,.045)],gold,40)
def drop(name,pos,length=.17):
    x,y,z=pos;verts=[(x,y,z)];n=8
    for dz,r in [(-.035,.028),(-length*.52,.045),(-length*.82,.026)]:
        for k in range(n):a=2*pi*k/n;verts.append((x+r*cos(a),y+r*sin(a),z+dz))
    verts.append((x,y,z-length));fs=[]
    for k in range(n):fs.append((0,1+k,1+(k+1)%n))
    for j in range(2):
        for k in range(n):a=1+j*n+k;b=1+j*n+(k+1)%n;fs.append((a,b,b+n,a+n))
    for k in range(n):fs.append((len(verts)-1,17+(k+1)%n,17+k))
    mesh(name,verts,fs,crystal)
for k in range(6):
    a=2*pi*k/6+pi/6
    pts=[]
    for t in np.linspace(0,1,42):r=.11+.53*t;z=3.63-.21*sin(pi*t)+.06*t;pts.append((r*cos(a),cy+r*sin(a),z))
    tube('chandelier swan arm',pts,.023,gold)
    x=.64*cos(a);y=cy+.64*sin(a)
    lathe('candle bobeche',(x,y,3.66),[(0,.045),(.035,.105),(.060,.11),(.08,.052)],gold,24)
    lathe('ivory candle',(x,y,3.73),[(0,.027),(.20,.027)],ivory,16)
    uvball('warm candle flame',(x,y,3.96),(.028,.028,.067),bulb,12,8)
    drop('arm crystal pendant',(x,y,3.61),.19)
    # Graceful bead garlands from hub to each arm.
    for j in range(10):
        t=j/9;r=.12+.47*t;zz=3.76-.27*sin(pi*t)
        uvball('crystal garland bead',(r*cos(a),cy+r*sin(a),zz),(.022,.022,.027),crystal,8,6)
    drop('inner hanging crystal',(.30*cos(a),cy+.30*sin(a),3.39),.17)
drop('chandelier terminal crystal',(0,cy,3.26),.23)

# Limited, readable jewelry groupings, permanently part of the scene.
active='07_Jewelry'
def bust(name,x,y,z,s=1,pearls=True):
    # Body contours taper from a broad shoulder to the waist, then a slender neck.
    profile=[(0,.15,.095),(.05,.17,.105),(.18,.22,.11),(.37,.29,.12),(.48,.31,.11),(.53,.22,.10),(.57,.11,.085),(.73,.095,.078)]
    verts=[];faces=[];nn=32
    for zz,rx,ry in profile:
        for k in range(nn):t=2*pi*k/nn;verts.append((x+s*rx*cos(t),y+s*ry*sin(t),z+s*zz))
    for j in range(len(profile)-1):
        for k in range(nn):a=j*nn+k;b=j*nn+(k+1)%nn;faces.append((a,b,b+nn,a+nn))
    faces.extend([tuple(reversed(range(nn))),tuple((len(profile)-1)*nn+k for k in range(nn))])
    mesh(name,verts,faces,linen,True)
    lathe(name+' pedestal',(x,y,z-.04*s),[(0,.19*s),(.035*s,.19*s),(.05*s,.16*s)],gold,24)
    pts=[]
    for k in range(29):
        t=k/28;xx=(-.225+.45*t)*s;zz=(.48-.22*sin(pi*t))*s;yy=y-.12*s-.035*sin(pi*t)*s;pts.append((x+xx,yy,z+zz))
    tube(name+' necklace chain',pts,.008*s,gold,res=1)
    for k,p in enumerate(pts):uvball(name+' pearl',p,(.019*s,.019*s,.019*s),pearl,12,8)
    uvball(name+' necklace pendant',(x,y-.16*s,z+.235*s),(.039*s,.024*s,.051*s),gem,8,4)
def tray(name,x,y,z,w=.47,d=.28):
    cube(name+' gilt border',(x,y,z),(w,d,.038),gold,.018)
    cube(name+' velvet pad',(x,y,z+.021),(w-.026,d-.026,.018),velvet,.014)
    for dx in [-.12,0,.12]:
        if abs(dx)<w*.4:
            o=tube(name+' ring',[(x+dx+.038*cos(t),y+.038*sin(t),z+.05) for t in np.linspace(0,2*pi,24)],.009,goldlight,True,2)
            uvball(name+' ring stone',(x+dx,y-.033,z+.062),(.019,.020,.018),gem,8,4)
def jewelbox(name,x,y,z,w=.34,mat=rose):
    cube(name+' base',(x,y,z+.07),(w,w*.73,.14),mat,.025)
    cube(name+' gilt seam',(x,y,z+.14),(w+.008,w*.73+.008,.014),gold,.005)
    lid=cube(name+' lid',(x,y+.085,z+.23),(w+.014,.045,w*.63),mat,.018);lid.rotation_euler.x=math.radians(-14)
    cube(name+' velvet insert',(x,y,z+.15),(w*.87,w*.60,.015),velvet,.01)
    uvball(name+' clasp',(x,y-w*.37,z+.135),(.022,.012,.018),goldlight)
def earrings(name,x,y,z,s=1):
    lathe(name+' foot',(x,y,z),[(0,.12*s),(.025*s,.13*s),(.05*s,.07*s)],gold,24)
    tube(name+' stem',[(x,y,z+.03*s),(x,y,z+.48*s)],.014*s,gold)
    tube(name+' crossbar',[(x-.16*s,y,z+.41*s),(x,y,z+.48*s),(x+.16*s,y,z+.41*s)],.013*s,gold)
    for side in [-1,1]:
        tube(name+' drop chain',[(x+side*.13*s,y,z+.42*s),(x+side*.13*s,y,z+.27*s)],.006*s,goldlight)
        uvball(name+' pearl drop',(x+side*.13*s,y,z+.24*s),(.027*s,.024*s,.040*s),pearl)
bust('hero pearl necklace bust',0,.63,1.92,1.05)
tray('counter ring tray',.72,.30,1.89,.48,.30)
jewelbox('counter jewelry box',-.69,.38,1.89,.32)
earrings('counter earring stand',1.08,.72,1.89,.68)
for x,lev in [(-1.91,2.15),(1.91,2.94)]:bust('cabinet necklace form',x,2.08,lev,.78)
earrings('left cabinet earrings',-1.91,2.04,2.96,.83)
tray('right cabinet ring selection',1.91,2.02,2.16,.57,.31)
jewelbox('left cabinet presentation case',-1.91,2.04,1.39,.43,ivory)
jewelbox('right cabinet presentation case',1.91,2.04,1.39,.43,rose)
for x in [-.96,.05,.95]:tray('counter lower display',x,.46,1.46,.53,.30)

# Two small floral accents and two ribbon parcels.
active='08_Flowers_and_gifts'
def flower(name,pos,s,mat):
    x,y,z=pos
    for ring,(count,r,sz) in enumerate([(7,.065,.067),(6,.039,.052),(4,.019,.038)]):
        for k in range(count):
            a=2*pi*k/count+ring*.6
            ob=uvball(name+' rose petal',(x+s*r*cos(a),y+s*r*sin(a),z+s*(.022+ring*.026)),(s*sz,s*sz*.65,s*.040),mat,12,8)
            ob.rotation_euler=(.35*cos(a),.35*sin(a),a)
    uvball(name+' rose heart',(x,y,z+.09*s),(.026*s,.026*s,.033*s),mat,12,8)
def bouquet(name,x,y,z,s):
    lathe(name+' urn',(x,y,z),[(0,.12*s),(.04*s,.15*s),(.09*s,.095*s),(.16*s,.09*s),(.30*s,.17*s),(.38*s,.19*s),(.41*s,.18*s)],ivory,32)
    lathe(name+' urn lip',(x,y,z+.40*s),[(0,.18*s),(.035*s,.20*s),(.055*s,.18*s)],gold,32)
    for k in range(7):
        a=k*2.4;r=.16*math.sqrt(k/6)*s;xx=x+r*cos(a);yy=y+r*sin(a);zz=z+s*(.58+.11*cos(k*1.2))
        tube(name+' stem',[(x,y,z+.36*s),(xx,yy,zz)],.008*s,leaves,res=1)
        flower(name,(xx,yy,zz),.9*s,petalpink if k%3 else petalcream)
        ob=uvball(name+' eucalyptus',(xx+.07*s*cos(a),yy+.07*s*sin(a),zz-.11*s),(.09*s,.034*s,.018*s),leaves);ob.rotation_euler.z=a
bouquet('counter small roses',-1.12,.76,1.89,.62)
lathe('side flower pedestal',(-2.10,.37,.37),[(0,.26),(.07,.28),(.12,.20),(.57,.13),(.68,.29),(.73,.30)],ivory,32)
bouquet('floor accent roses',-2.10,.37,1.10,.90)
def parcel(x,y,z,w,h,mat):
    cube('ribbon gift box',(x,y,z+h/2),(w,w*.76,h),mat,.018)
    cube('gift lid',(x,y,z+h),(w+.02,w*.76+.02,.045),edge,.010)
    cube('gift ribbon crossing x',(x,y,z+h+.027),(w+.025,.052,.008),rose,.003)
    cube('gift ribbon crossing y',(x,y,z+h+.029),(.055,w*.76+.023,.008),rose,.003)
    for side in [-1,1]:tube('ribbon bow',[(x+side*.11*sin(t),y+.035*sin(2*t),z+h+.05+.045*sin(t)) for t in np.linspace(0,pi,32)],.012,rose,res=2)
parcel(2.05,.30,.38,.49,.28,rose);parcel(2.16,.42,.71,.34,.20,ivory)

# Neutral studio and restrained warm practicals.
active='90_Studio'
cube('studio ground',(0,0,-.075),(200,200,.10),studio,.0)
scene.world.use_nodes=True;bg=scene.world.node_tree.nodes.get('Background');bg.inputs[0].default_value=(.73,.76,.80,1);bg.inputs[1].default_value=.22
def area(name,pos,target,energy,size,color=(1,.91,.80),shape='DISK',size_y=None):
    d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.shape=shape;d.size=size;d.color=color
    if size_y is not None:d.size_y=size_y
    o=bpy.data.objects.new(name,d);groups[active].objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
area('large soft key',(-4.3,-6.5,8),(0,1,2.3),580,5.0,(1,.94,.86))
area('cool front fill',(4,-4,5),(0,1,2.7),240,4.0,(.86,.91,1))
area('overhead silk light',(0,1,7),(0,1,1),240,3.5,(1,.91,.81))
area('front jewelry highlight',(-1,-3,3.5),(0,.6,1.7),40,2,(1,.95,.87))
area('chandelier practical',(0,1,3.93),(0,.5,1),34,.60,(1,.74,.43))
for x in [-1.91,1.91]:area('cabinet warm practical',(x,1.94,3.77),(x,2.1,2),12,.44,(1,.80,.56))

active='91_Cameras'
target=Vector((0,1.1,2.85))
def camera(name,az):
    a=math.radians(az);d=bpy.data.cameras.new(name);d.type='ORTHO';d.ortho_scale=7.05;d.lens=55;d.clip_start=.1;d.clip_end=100
    o=bpy.data.objects.new(name,d);groups[active].objects.link(o);o.location=target+Vector((17*sin(a),-17*cos(a),2.39));o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler();return o
cams=[camera('01_Front',0),camera('02_Left',-13),camera('03_Right',13)]
scene.camera=cams[0]
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=48;scene.cycles.use_denoising=True;scene.cycles.max_bounces=7;scene.cycles.transmission_bounces=6
scene.render.resolution_x=1200;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=.0
scene['stage']='01 spatial palette lighting preview — awaiting style approval'
scene['reference']='店铺装修.jpg, supplied by user'
scene['future_refinement']='Texture-based lace openwork, refined acanthus relief, jewelry settings, subtle edge wear, baked web lighting and mirror treatment after approval.'
scene['web_orbit_yaw_limit_degrees']=15
for screen in bpy.data.screens:
    for ar in screen.areas:
        if ar.type=='VIEW_3D':
            ar.spaces.active.region_3d.view_perspective='CAMERA';ar.spaces.active.clip_end=200
txt=bpy.data.texts.new('ABOUT_STAGE_1');txt.write('第一阶段：空间、家具、配色与灯光预览。\n雕花为主要轮廓；蕾丝为形态占位，尚未制作镂空纹理。\n确认风格后完善细节，并制作最终网页材质、灯光烘焙与验证。\n三个相机均使用同一完整模型。\n')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Boutique-stage1.blend'))
params={'stage':'preview_awaiting_approval','coordinate_system_blender':'Z up; front -Y','coordinate_system_glb':'Y up; front +Z','camera_type':'orthographic','orthographic_vertical_size':7.05,'target_blender':list(target),'target_glb':[target.x,target.z,-target.y],'default_camera_blender':list(cams[0].location),'default_camera_glb':[cams[0].location.x,cams[0].location.z,-cams[0].location.y],'elevation_degrees':math.degrees(math.atan2(2.39,17)),'orbit_azimuth_limit_degrees':[-15,15],'preview_azimuths_degrees':[0,-13,13],'resolution':[1200,1200],'color_management':{'view':'AgX','look':'Medium High Contrast','exposure':.0}}
(OUT/'camera-preview.json').write_text(json.dumps(params,indent=2))
print('BUILD_SAVED',len(bpy.data.objects),'objects',flush=True)
if '--render' in sys.argv:
    for cam in cams:
        scene.camera=cam;scene.render.filepath=str(OUT/(cam.name+'.png'));bpy.ops.render.render(write_still=True);print('VIEW_DONE',cam.name,flush=True)
    scene.camera=cams[0];bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Boutique-stage1.blend'))
