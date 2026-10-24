import bpy
from pathlib import Path
B=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(B/'main-display-source.blend'))
for ma in bpy.data.materials:
 if 'pale champagne mirror' in ma.name:
  bs=next(n for n in ma.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
  bs.inputs['Base Color'].default_value=(.99,.87,.46,1)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(B/'main-display-source.blend'),compress=True)
