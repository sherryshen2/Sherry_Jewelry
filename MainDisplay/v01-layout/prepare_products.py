import bpy,json,math
from pathlib import Path
from mathutils import Vector,Matrix
B=Path(__file__).resolve().parent;W=B.parent.parent
sources={'necklace':('J001/v02-refined/J001-source-v02.blend','J001_ROOT'),'earrings':('J002/v02-refined/J002-source-v02.blend','J002_ROOT'),'ring':('J003/v06-prong-gold/J003-source-v06.blend','J003_ROOT'),'bracelet':('J004/v02-close-set/J004-source-v02.blend','J004_ROOT')}
report={}
for key,(rel,rn) in sources.items():
 bpy.ops.wm.open_mainfile(filepath=str(W/rel));root=bpy.data.objects[rn];bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();inv=root.matrix_world.inverted();batches={};pts=[];tri=0
 for o in list(root.children_recursive):
  if o.type!='MESH' or o.hide_render or any('cutter' in c.name.lower() for c in o.users_collection):continue
  ev=o.evaluated_get(dg);me=ev.to_mesh();mat=o.data.materials[0];part='body'
  if key=='earrings':
   cur=o
   while cur.parent and cur.parent!=root:cur=cur.parent
   part='left_earring' if 'A_MASTER' in cur.name else 'right_earring'
  bucket=batches.setdefault((part,mat.name),{'verts':[],'faces':[],'smooth':[],'normals':[],'material':mat});offset=len(bucket['verts']);M=inv@o.matrix_world;N=M.to_3x3().inverted().transposed()
  vv=[M@v.co for v in me.vertices];pts+=vv;bucket['verts']+=list(map(tuple,vv))
  for p in me.polygons:
   bucket['faces'].append(tuple(offset+i for i in p.vertices));bucket['smooth'].append(p.use_smooth)
  bucket['normals'] += [tuple((N@n.vector).normalized()) for n in me.corner_normals]
  me.calc_loop_triangles();tri+=len(me.loop_triangles);ev.to_mesh_clear()
 lo=[min(p[i] for p in pts) for i in range(3)];hi=[max(p[i] for p in pts) for i in range(3)]
 for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
 newroot=bpy.data.objects.new(key+'_product',None);bpy.context.scene.collection.objects.link(newroot);parts={}
 for (part,mn),data in batches.items():
  parent=newroot
  if key=='earrings':
   if part not in parts:
    e=bpy.data.objects.new(part,None);bpy.context.scene.collection.objects.link(e);e.parent=newroot;parts[part]=e
   parent=parts[part]
  me=bpy.data.meshes.new(key+'_'+part+'_'+mn);me.from_pydata(data['verts'],[],data['faces']);me.update();me.materials.append(data['material'])
  for p,sm in zip(me.polygons,data['smooth']):p.use_smooth=sm
  me.normals_split_custom_set(data['normals']);o=bpy.data.objects.new(me.name,me);bpy.context.scene.collection.objects.link(o);o.parent=parent
 bpy.ops.object.select_all(action='SELECT');bpy.context.view_layer.objects.active=newroot
 bpy.ops.export_scene.gltf(filepath=str(B/(key+'.glb')),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_extras=True,export_cameras=False,export_lights=False)
 report[key]={'source':rel,'original_root':rn,'product_root':newroot.name,'origin_relation':'Product local coordinates equal original Blender root local coordinates; unit scale 1. No geometry or material redesign. Evaluated source modifiers retained as mesh.','bounds_blender_m':[lo,hi],'dimensions_mm':[(hi[i]-lo[i])*1000 for i in range(3)],'triangles':tri,'material_count':len(set(k[1] for k in batches)),'mesh_batches':len(batches),'bytes':(B/(key+'.glb')).stat().st_size}
 print('PRODUCT_READY',key,report[key],flush=True)
(B/'product-audit.json').write_text(json.dumps(report,indent=2))
