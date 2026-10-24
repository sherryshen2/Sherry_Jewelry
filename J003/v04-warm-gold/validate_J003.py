"""Read-only geometry and GLB round-trip checks; writes measured results to JSON."""
import bpy,bmesh,json,math,struct
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
BASE=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(BASE/'J003-source-v04.blend'))
objects=[o for o in bpy.data.collections['J003_PRODUCT_ONLY'].objects if o.type=='MESH']
dg=bpy.context.evaluated_depsgraph_get()
issues=[];bvh={};metal_bvh={};vertsall=[]
for o in objects:
    ev=o.evaluated_get(dg);me=ev.to_mesh();bm=bmesh.new();bm.from_mesh(me)
    boundary=sum(not e.is_manifold for e in bm.edges)
    area0=sum(f.calc_area()<1e-16 for f in bm.faces)
    vol=bm.calc_volume(signed=True)
    if boundary or area0 or vol<=0:
        issues.append({'object':o.name,'nonmanifold_edges':boundary,'zero_area_faces':area0,'signed_volume_m3':vol})
    vertsall += [o.matrix_world@v.co for v in me.vertices]
    if 'Stone_' in o.name or 'Halo_' in o.name or o.name.startswith('02_Center'):
        bvh[o.name]=BVHTree.FromBMesh(bm)
    elif o.data.materials and o.data.materials[0].name.startswith('M01_'):
        metal_bvh[o.name]=BVHTree.FromBMesh(bm)
    bm.free();ev.to_mesh_clear()
overlaps=[]
for i,(an,a) in enumerate(bvh.items()):
    for bn,b in list(bvh.items())[i+1:]:
        hit=a.overlap(b)
        if hit:overlaps.append({'a':an,'b':bn,'surface_triangle_pairs':len(hit)})
support_contacts={}
for name,stone in bvh.items():
    support_contacts[name]=[m for m,metal in metal_bvh.items() if stone.overlap(metal)]
framing={}
for cam in [o for o in bpy.data.objects if o.type=='CAMERA']:
    p=[world_to_camera_view(bpy.context.scene,cam,v) for v in vertsall]
    framing[cam.name]={'min_xy':[min(v[k] for v in p) for k in [0,1]],
                       'max_xy':[max(v[k] for v in p) for k in [0,1]],
                       'all_inside_frame':all(0<=v.x<=1 and 0<=v.y<=1 and v.z>0 for v in p)}
band=bpy.data.objects['01_Shank_ID16mm_width_EST']
radii=[math.hypot(v.co.x,v.co.z)*1000 for v in band.data.vertices]
source_bounds=[[min(v[k] for v in vertsall)*1000 for k in range(3)],
               [max(v[k] for v in vertsall)*1000 for k in range(3)]]
glb=(BASE/'J003-detail-v04.glb').read_bytes()
length,kind=struct.unpack_from('<II',glb,12);doc=json.loads(glb[20:20+length])
result={'source_closed_mesh_issues':issues,'gem_surface_intersections':overlaps,
        'stone_metal_contacts':support_contacts,
        'stones_without_detected_metal_contact':[name for name,c in support_contacts.items() if not c],
        'source_inner_vertex_diameter_mm':2*min(radii),
        'source_bounds_mm':source_bounds,'camera_framing':framing,
        'gltf_version':doc['asset']['version'],'gltf_extensions':doc.get('extensionsUsed',[]),
        'glb_file_size_bytes':len(glb),'glb_nodes':len(doc['nodes']),
        'glb_materials':[m['name'] for m in doc['materials']],
        'glb_images':len(doc.get('images',[])),
        'glb_has_camera_or_lights':bool(doc.get('cameras') or 'KHR_lights_punctual' in doc.get('extensions',{})),
        'limitations':['no full rear reference; open gallery is provisional',
                      'overlap checks exclude intentional metal-to-setting contacts',
                      'stone counts and cutting diagram are not verified by source photographs']}
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(BASE/'J003-detail-v04.glb'))
rv=[];tris=0
for o in bpy.context.scene.objects:
    if o.type=='MESH':
        rv.extend(o.matrix_world@v.co for v in o.data.vertices)
        o.data.calc_loop_triangles();tris+=len(o.data.loop_triangles)
rb=[[min(v[k] for v in rv)*1000 for k in range(3)],[max(v[k] for v in rv)*1000 for k in range(3)]]
result['roundtrip_bounds_mm']=rb
result['roundtrip_max_bound_error_mm']=max(abs(rb[j][k]-source_bounds[j][k]) for j in range(2) for k in range(3))
result['roundtrip_triangles']=tris
result['roundtrip_root_found']='J003_ROOT' in bpy.data.objects
result['lods']={}
for mode in ['detail','display']:
    path=BASE/f'J003-{mode}-v04.glb'
    raw=path.read_bytes();chunk_length,_=struct.unpack_from('<II',raw,12)
    gltf=json.loads(raw[20:20+chunk_length])
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(path))
    points=[];triangle_count=0;material_names=set();normal_issues=[]
    for o in bpy.context.scene.objects:
        if o.type!='MESH':continue
        points.extend(o.matrix_world@v.co for v in o.data.vertices)
        o.data.calc_loop_triangles();triangle_count+=len(o.data.loop_triangles)
        material_names.update(m.name for m in o.data.materials if m)
        if any(v.normal.length<.9 for v in o.data.vertices):normal_issues.append(o.name)
    bounds=[[min(v[k] for v in points)*1000 for k in range(3)],
            [max(v[k] for v in points)*1000 for k in range(3)]]
    materials=[]
    for m in gltf['materials']:
        ext=m.get('extensions',{})
        materials.append({'name':m['name'],'roughness':m['pbrMetallicRoughness'].get('roughnessFactor',1),
             'transmission':ext.get('KHR_materials_transmission',{}).get('transmissionFactor',0),
             'emissive':m.get('emissiveFactor',[0,0,0])})
    root_ob=bpy.data.objects.get('J003_ROOT')
    result['lods'][mode]={'bytes':len(raw),'triangles':triangle_count,'bounds_mm':bounds,
        'max_bound_error_vs_source_mm':max(abs(bounds[j][k]-source_bounds[j][k]) for j in range(2) for k in range(3)),
        'meshes':len(gltf['meshes']),'materials':materials,'root':root_ob.name if root_ob else None,
        'root_location':list(root_ob.location) if root_ob else None,
        'root_scale':list(root_ob.scale) if root_ob else None,
        'invalid_vertex_normals':normal_issues,'images':len(gltf.get('images',[])),
        'cameras':len(gltf.get('cameras',[])),'extensions':gltf.get('extensionsUsed',[])}
(BASE/'J003-validation-v04.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps(result,ensure_ascii=False,indent=2))
