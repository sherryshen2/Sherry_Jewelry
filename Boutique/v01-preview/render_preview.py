import bpy,json,sys
from pathlib import Path
from mathutils import Vector
B=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(B/'Boutique-stage1.blend'))
s=bpy.context.scene
proof='--proof' in sys.argv
s.render.resolution_x=760 if proof else 1200
s.render.resolution_y=s.render.resolution_x
s.cycles.samples=16 if proof else 32
for name in (['01_Front'] if proof else ['01_Front','02_Left','03_Right']):
    s.camera=bpy.data.objects[name]
    s.render.filepath=str(B/(('proof-' if proof else '')+name+'.png'))
    bpy.ops.render.render(write_still=True)
    print('RENDER_DONE',name,flush=True)
s.camera=bpy.data.objects['01_Front']
if not proof:
    dg=bpy.context.evaluated_depsgraph_get();triangles=0;pts=[];objects=0
    for c in s.collection.children:
        if not c.name.startswith(('0','90','91')):continue
        if c.name.startswith(('90','91')):continue
        for o in c.objects:
            if o.type not in ['MESH','CURVE']:continue
            ev=o.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles();triangles+=len(me.loop_triangles);objects+=1
            pts.extend(o.matrix_world@v.co for v in me.vertices);ev.to_mesh_clear()
    stats={'stage':'01 spatial palette lighting review','source_geometry_objects':objects,'evaluated_triangles_before_web_optimization':triangles,'material_count':len(bpy.data.materials),'bounds_blender_metres':[[min(v[i] for v in pts) for i in range(3)],[max(v[i] for v in pts) for i in range(3)]],'external_images':[{'name':im.name,'path':im.filepath,'size':list(im.size)} for im in bpy.data.images if im.source=='FILE'],'files':{p.name:p.stat().st_size for p in B.glob('*') if p.suffix in ['.blend','.png','.json']}}
    (B/'preview-audit.json').write_text(json.dumps(stats,indent=2,ensure_ascii=False))
    s.render.filepath=str(B/'01_Front.png')
    bpy.ops.wm.save_as_mainfile(filepath=str(B/'Boutique-stage1.blend'))
    print('PREVIEW_AUDIT',json.dumps(stats),flush=True)
