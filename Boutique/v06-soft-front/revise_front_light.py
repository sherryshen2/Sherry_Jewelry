import bpy,json
from pathlib import Path
B=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(B/'Boutique-final.blend'))
bpy.data.objects['facade broad soft fill'].data.energy=80
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(B/'Boutique-final.blend'))
p=B/'palette-and-light-revision.json';d=json.loads(p.read_text());d['version']='v06 soft front light; v05 palette and materials preserved'
for light in d['lights']:
 if light['name']=='facade broad soft fill':light['energy']=80
p.write_text(json.dumps(d,indent=2,ensure_ascii=False))
exec(compile((B/'validate_source.py').read_text(),str(B/'validate_source.py'),'exec'))
exec(compile((B/'render_final.py').read_text(),str(B/'render_final.py'),'exec'))
