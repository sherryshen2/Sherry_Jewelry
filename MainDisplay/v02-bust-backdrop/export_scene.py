import bpy,json,struct
from pathlib import Path
B=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(B/'main-display-source.blend'));s=bpy.context.scene
source=[o for c in s.collection.children if c.name.startswith(('01_','02_','03_','04_')) for o in c.objects if o.type in ['MESH','CURVE']]
for o in source:
 if o.type=='CURVE':o.data.bevel_resolution=min(2,o.data.bevel_resolution)
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();by={};col=bpy.data.collections.new('TEMP_EXPORT');s.collection.children.link(col)
for o in source:
 me=bpy.data.meshes.new_from_object(o.evaluated_get(dg),preserve_all_data_layers=True,depsgraph=dg);me.transform(o.matrix_world);me.update();mat=o.data.materials[0]
 if not me.uv_layers:
  uv=me.uv_layers.new(name='UVMap')
  for f in me.polygons:
   axis=max(range(3),key=lambda k:abs(f.normal[k]));a,b=[k for k in range(3) if k!=axis]
   for li in f.loop_indices:
    p=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(p[a]*8,p[b]*8)
 me.uv_layers.active.name='UVMap';ob=bpy.data.objects.new('export_'+o.name,me);col.objects.link(ob);by.setdefault(('Background_' if o in list(bpy.data.collections['03_Fixed_Background'].objects) else '')+mat.name,[]).append(ob)
bpy.context.view_layer.update();batches=[];tri=0
for name,obs in by.items():
 bpy.ops.object.select_all(action='DESELECT')
 for o in obs:o.select_set(True)
 bpy.context.view_layer.objects.active=obs[0]
 if len(obs)>1:bpy.ops.object.join()
 o=bpy.context.object;o.name='Fixed_'+name;o.data.calc_loop_triangles();tri+=len(o.data.loop_triangles);batches.append(o)
bpy.ops.object.select_all(action='DESELECT')
for o in batches:o.select_set(True)
for o in bpy.data.collections['05_Product_Anchors'].objects:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(B/'main-display-scene.glb'),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_extras=True,export_cameras=False,export_lights=False)
p=B/'main-display-scene.glb';raw=p.read_bytes();jl=struct.unpack_from('<I',raw,12)[0];d=json.loads(raw[20:20+jl]);tail=raw[20+jl:]
for m in d.get('materials',[]):
 if 'lace' in m.get('name',''):m['alphaMode']='MASK';m['alphaCutoff']=.45;m['doubleSided']=True
js=json.dumps(d,separators=(',',':')).encode();js+=b' '*((-len(js))%4);p.write_bytes(struct.pack('<III',0x46546c67,2,20+len(js)+len(tail))+struct.pack('<II',len(js),0x4e4f534a)+js+tail)
assert not any('product' in n.get('name','') for n in d['nodes']);assert len([n for n in d['nodes'] if n.get('name','').endswith('_anchor')])==4
(B/'scene-stats.json').write_text(json.dumps({'triangles':tri,'mesh_batches':len(batches),'materials':len(d.get('materials',[])),'textures':len(d.get('images',[])),'bytes':p.stat().st_size,'anchors':4,'contains_product_geometry':False},indent=2));print('SCENE_EXPORTED',tri,flush=True)
