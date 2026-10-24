"""Static material batches + baked vertex contact occlusion, portable uncompressed glTF."""
import bpy,bmesh,math,json,time,struct
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
B=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(B/'Boutique-final.blend'))
s=bpy.context.scene
source=[o for c in s.collection.children if c.name.startswith('0') for o in c.objects if o.type in ['MESH','CURVE']]
for o in source:
    if o.type=='CURVE':o.data.bevel_resolution=min(o.data.bevel_resolution,2)
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
exportcol=bpy.data.collections.new('WEB_EXPORT_BATCHES');s.collection.children.link(exportcol)
by_material={};fullvs=[];fullfs=[]
for o in source:
    me=bpy.data.meshes.new_from_object(o.evaluated_get(dg),preserve_all_data_layers=True,depsgraph=dg)
    me.transform(o.matrix_world);me.update()
    if not len(me.vertices):continue
    mat=me.materials[0]
    if not me.uv_layers:
        uv=me.uv_layers.new(name='UVMap')
        for f in me.polygons:
            dominant=max(range(3),key=lambda k:abs(f.normal[k]));a,b=[k for k in range(3) if k!=dominant]
            for li in f.loop_indices:
                co=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(co[a],co[b])
    # Standardise UV names before joining.
    me.uv_layers.active.name='UVMap'
    ob=bpy.data.objects.new('web '+o.name,me);exportcol.objects.link(ob)
    by_material.setdefault(mat,[]).append(ob)
    if not mat.name.startswith(('09 |','14 |')):
        base=len(fullvs);fullvs.extend(tuple(v.co) for v in me.vertices);fullfs.extend(tuple(base+i for i in f.vertices) for f in me.polygons)
for o in source:o.hide_render=True;o.hide_set(True)
bvh=BVHTree.FromPolygons(fullvs,fullfs,all_triangles=False,epsilon=.00001)
print('BVH_READY',len(fullvs),len(fullfs),flush=True)

def merge(obs,name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:o.select_set(True)
    bpy.context.view_layer.objects.active=obs[0]
    if len(obs)>1:bpy.ops.object.join()
    ob=bpy.context.object;ob.name=name;return ob
batches=[];tri=0;totalverts=0;ao_sample_count=10
for mat,obs in by_material.items():
    ob=merge(obs,'Boutique_'+mat.name.split(' | ')[0]);me=ob.data
    webmat=mat.copy();webmat.name='Web_'+mat.name;me.materials.clear();me.materials.append(webmat)
    for f in me.polygons:f.material_index=0
    p=webmat.node_tree.nodes.get('Principled BSDF')
    if mat.name.startswith('14 |'):
        p.inputs['Transmission Weight'].default_value=0;p.inputs['Alpha'].default_value=.18;p.inputs['Roughness'].default_value=.20;p.inputs['Base Color'].default_value=(.80,.90,.94,1)
        webmat.surface_render_method='DITHERED';webmat.use_backface_culling=False
        ob['web_role']='single_layer_glass'
    elif mat.name.startswith(('13 |','15 |')):
        p.inputs['Transmission Weight'].default_value=0;p.inputs['Metallic'].default_value=.18;p.inputs['Coat Weight'].default_value=.60;p.inputs['Coat Roughness'].default_value=.12
        p.inputs['Roughness'].default_value=.16 if mat.name.startswith('15') else .19
        ob['web_role']='opaque_faceted_crystal' if mat.name.startswith('15') else 'faceted_gem'
    elif mat.name.startswith('16 |'):
        im=bpy.data.images.load(str(B/'textures/mirror_reflection_capture.png'));nt=webmat.node_tree;t=nt.nodes.new('ShaderNodeTexImage');t.image=im
        nt.links.new(t.outputs['Color'],p.inputs['Base Color']);nt.links.new(t.outputs['Color'],p.inputs['Emission Color'])
        p.inputs['Emission Strength'].default_value=.22;p.inputs['Metallic'].default_value=.32;p.inputs['Roughness'].default_value=.28
        uv=me.uv_layers.active
        for f in me.polygons:
            for li in f.loop_indices:
                co=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(.5-co.x/1.58,(co.z-1.68)/2.30)
        ob['web_role']='static_soft_reflection_plus_environment'
    elif mat.name.startswith('09 |'):ob['web_role']='alpha_tested_lace'

    # Extra sampling points only on large panels, leaving small carvings intact.
    if not mat.name.startswith(('09 |','14 |','16 |','20 |')):
        bm=bmesh.new();bm.from_mesh(me)
        longs=[e for e in bm.edges if e.calc_length()>.52]
        if longs:bmesh.ops.subdivide_edges(bm,edges=longs,cuts=2,use_grid_fill=True)
        bm.to_mesh(me);bm.free();me.update()
        attr=me.color_attributes.new(name='ContactAO',type='BYTE_COLOR',domain='POINT')
        for i,vert in enumerate(me.vertices):
            norm=vert.normal.normalized();axis=Vector((0,0,1)) if abs(norm.z)<.9 else Vector((0,1,0));u=norm.cross(axis).normalized();v=norm.cross(u).normalized();origin=vert.co+norm*.003;occluded=0
            for k in range(ao_sample_count):
                r=math.sqrt((k+.5)/ao_sample_count);a=k*2.39996322973
                direction=u*(r*math.cos(a))+v*(r*math.sin(a))+norm*math.sqrt(1-r*r)
                hit=bvh.ray_cast(origin,direction,.48)
                if hit[0] is not None:occluded+=(1-min(1,hit[3]/.48))
            ao=max(.48,1-.55*occluded/ao_sample_count)
            # Soft visibility of the approved studio key/fill, baked into vertex colour.
            # Large sources avoid the harsh tiny-relief edges of realtime shadow maps.
            visibility=[]
            for lx,ly,lz,radius in [(-4.3,-6.5,8,2.5),(4,-4,5,2.0)]:
                lit=0
                for k in range(6):
                    a=k*2.39996322973;r=radius*math.sqrt((k+.5)/6);lp=Vector((lx+r*math.cos(a),ly,lz+r*math.sin(a)));ray=lp-origin;dist=ray.length;hit=bvh.ray_cast(origin,ray.normalized(),dist)
                    if hit[0] is None:lit+=1
                visibility.append(lit/6)
            shade=.62+.28*visibility[0]+.10*visibility[1]
            ao=max(.32,ao*shade);attr.data[i].color=(ao,ao,ao,1)
        me.color_attributes.active_color_index=len(me.color_attributes)-1;me.color_attributes.render_color_index=len(me.color_attributes)-1
    me.calc_loop_triangles();tri+=len(me.loop_triangles);totalverts+=len(me.vertices);batches.append(ob)
    print('BATCH',mat.name,len(me.vertices),'vertices',flush=True)

root=bpy.data.objects.new('BOUTIQUE_ROOT',None);exportcol.objects.link(root);root['purpose']='Static boutique scene; decorative jewelry, no product interactions';root['orbit_limit_degrees']=15
for o in batches:o.parent=root
bpy.ops.object.select_all(action='DESELECT');root.select_set(True)
for o in batches:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(B/'Boutique-web.glb'),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_extras=True,export_cameras=False,export_lights=False,export_vertex_color='NAME',export_vertex_color_name='ContactAO',export_all_vertex_colors=False)
# Alpha mask is explicit in glTF; Blender 4.5's Dithered UI also covers blend materials.
raw=(B/'Boutique-web.glb').read_bytes();jl,jt=struct.unpack_from('<II',raw,12);doc=json.loads(raw[20:20+jl]);tail=raw[20+jl:]
for m in doc['materials']:
    if 'floral ecru lace' in m['name']:m['alphaMode']='MASK';m['alphaCutoff']=.45;m['doubleSided']=True
    if 'display glass' in m['name']:m['alphaMode']='BLEND';m['doubleSided']=True
js=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();js+=b' '*((-len(js))%4)
out=struct.pack('<III',0x46546c67,2,20+len(js)+len(tail))+struct.pack('<II',len(js),0x4e4f534a)+js+tail;(B/'Boutique-web.glb').write_bytes(out)
stats={'triangles':tri,'mesh_vertices_before_gltf_uv_splits':totalverts,'mesh_batches':len(batches),'materials':len(doc['materials']),'images':len(doc.get('images',[])),'embedded_images':all('bufferView' in im for im in doc.get('images',[])),'glb_bytes':len(out),'extensions_used':doc.get('extensionsUsed',[]),'occlusion':'10 cosine-weighted local AO rays plus 6 key and 6 fill visibility rays per vertex; COLOR_0, final minimum 0.32','mirror':'Softened 512x704 static reflection capture plus environment highlights','alpha_mask_materials':sum(m.get('alphaMode')=='MASK' for m in doc['materials']),'alpha_blend_materials':sum(m.get('alphaMode')=='BLEND' for m in doc['materials']),'default_coordinate_system':'Y up; facade faces +Z','source_objects':len(source),'web_dynamic_lights':3}
(B/'web-stats.json').write_text(json.dumps(stats,indent=2,ensure_ascii=False));print('WEB_EXPORT_DONE',json.dumps(stats),flush=True)
