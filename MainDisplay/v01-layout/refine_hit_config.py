import bpy,json,numpy as np,math
from pathlib import Path
from mathutils import Vector
B=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(B/'main-display-source.blend'));bpy.context.view_layer.update();p=B/'product-placement.json';d=json.loads(p.read_text())
def to_glb(v):return [float(v[0]),float(v[2]),float(-v[1])]
root=bpy.data.objects['necklace_product'];inv=root.matrix_world.inverted();vv=np.array([tuple(inv@o.matrix_world@v.co) for o in root.children_recursive if o.type=='MESH' and 'Silver' in o.name for v in o.data.vertices]);segments=[]
for sign in [-1,1]:
 points=[]
 for z in np.linspace(-.069,.074,36):
  a=vv[(np.abs(vv[:,2]-z)<.0025)&(vv[:,0]*sign>.001)]
  if len(a):points.append(to_glb(np.median(a,axis=0)))
 for a,b in zip(points,points[1:]):segments.append({'a':a,'b':b,'radius':.0025})
d['products']['necklace']['preferred_hit_region']={'type':'compound','capsules':segments,'boxes':[{'center':[0,-.073,.020],'size':[.013,.014,.013]}],'note':'Use chain-following capsules and pendant box, rather than the full bust-sized fallback box.'}
r=bpy.data.objects['earrings_product'];inv=r.matrix_world.inverted();boxes=[]
for ear in r.children:
 pts=[inv@o.matrix_world@v.co for o in ear.children_recursive if o.type=='MESH' for v in o.data.vertices];lo=np.min(pts,axis=0);hi=np.max(pts,axis=0);size=hi-lo+.004
 boxes.append({'name':ear.name,'center':to_glb((lo+hi)*.5),'size':[float(size[0]),float(size[2]),float(size[1])]})
d['products']['earrings']['preferred_hit_region']={'type':'compound','boxes':boxes}
points=[[.02866423734*math.cos(a),.001,-.02204941334*math.sin(a)] for a in np.linspace(0,2*math.pi,49)]
d['products']['bracelet']['preferred_hit_region']={'type':'compound','capsules':[{'a':a,'b':b,'radius':.003} for a,b in zip(points,points[1:])],'boxes':[{'center':[.010,.001,-.029],'size':[.023,.010,.020]}],'note':'Conservative ellipse plus clasp/tail pick box; no visible mesh.'}
d['products']['ring']['preferred_hit_region']={'type':'box',**d['products']['ring']['bounds_local_glb']}
d['click_helpers_visible']=False;d['click_region_coordinates']='All preferred regions are in each product local glTF coordinate system; parent to its product root so they follow animations.'
p.write_text(json.dumps(d,indent=2));print('HIT_CONFIG_DONE')
