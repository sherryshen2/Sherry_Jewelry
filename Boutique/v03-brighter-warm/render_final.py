import bpy,sys
from pathlib import Path
from mathutils import Vector
B=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(B/'Boutique-final.blend'))
s=bpy.context.scene
if '--reflection' in sys.argv:
    for o in bpy.data.collections['04_Mirror'].objects:o.hide_render=True
    d=bpy.data.cameras.new('Reflection_capture');d.type='ORTHO';d.ortho_scale=2.30;d.clip_start=.01
    c=bpy.data.objects.new('Reflection_capture',d);s.collection.objects.link(c);c.location=(0,2.36,2.83);c.rotation_euler=(Vector((0,-1,-.14))).to_track_quat('-Z','Y').to_euler();s.camera=c
    s.render.resolution_x=512;s.render.resolution_y=704;s.cycles.samples=32;s.render.filepath=str(B/'textures'/'mirror_reflection_capture.png')
    s.use_nodes=True;nt=s.node_tree;nt.nodes.clear();rl=nt.nodes.new('CompositorNodeRLayers');blur=nt.nodes.new('CompositorNodeBlur');blur.filter_type='GAUSS';blur.size_x=28;blur.size_y=28;out=nt.nodes.new('CompositorNodeComposite');nt.links.new(rl.outputs['Image'],blur.inputs['Image']);nt.links.new(blur.outputs['Image'],out.inputs['Image'])
    bpy.ops.render.render(write_still=True);print('REFLECTION_DONE',flush=True)
else:
    proof='--proof' in sys.argv
    names=['01_Front'] if proof else ['01_Front','02_Left','03_Right']
    for name in names:
        s.camera=bpy.data.objects[name];s.cycles.samples=16 if proof else 48
        s.render.resolution_x=850 if proof else (1400 if name=='01_Front' else 1200);s.render.resolution_y=s.render.resolution_x
        filename='proof-refined.png' if proof else ('Boutique-hero.png' if name=='01_Front' else name+'.png')
        s.render.filepath=str(B/filename);bpy.ops.render.render(write_still=True);print('RENDER_DONE',filename,flush=True)
