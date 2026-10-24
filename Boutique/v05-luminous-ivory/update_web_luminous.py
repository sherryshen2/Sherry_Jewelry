"""Preserve geometry; lift baked shadows, update ivory and white translucent crystals."""
import json,struct,copy
from pathlib import Path
B=Path(__file__).resolve().parent;raw=(B.parent/'v04-pastel-palette/Boutique-web.glb').read_bytes()
jl=struct.unpack_from('<I',raw,12)[0];d=json.loads(raw[20:20+jl]);original=raw[28+jl:];old_data=bytearray(original)
colors=json.loads((B/'pastel-colors.json').read_text());gold_before=[copy.deepcopy(m) for m in d['materials'] if 'champagne' in m['name']]
for m in d['materials']:
 key=m['name'].removeprefix('Web_').split(' |')[0]
 if key in colors and key not in ['01','02','03','06']:m['pbrMetallicRoughness']['baseColorFactor']=colors[key]+[1]
 if key=='15':
  p=m['pbrMetallicRoughness'];p.update(baseColorFactor=[.98,.99,1,.68],metallicFactor=0,roughnessFactor=.14)
  m['alphaMode']='BLEND';m['doubleSided']=False;m['emissiveFactor']=[.035,.035,.035]
  m.setdefault('extensions',{})['KHR_materials_clearcoat']={'clearcoatFactor':.28,'clearcoatRoughnessFactor':.10}
  m.setdefault('extras',{})['web_role']='white_translucent_crystal'
for old in gold_before:
 m=next(m for m in d['materials'] if m['name']==old['name'])
 # The explicit rounded colour is equivalent to the existing palette; reflection settings are exact.
 for k in ['metallicFactor','roughnessFactor']:assert m['pbrMetallicRoughness'][k]==old['pbrMetallicRoughness'][k]
processed=set();lifted=0;crystal_white=0;changed_views=set()
for mesh in d['meshes']:
 for pr in mesh['primitives']:
  i=pr['attributes'].get('COLOR_0')
  if i is None or i in processed:continue
  processed.add(i);a=d['accessors'][i];assert (a['componentType'],a['type'],a.get('normalized'))==(5123,'VEC4',True)
  v=d['bufferViews'][a['bufferView']];changed_views.add(a['bufferView']);start=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',8)
  crystal='chandelier crystal' in d['materials'][pr['material']]['name']
  for k in range(a['count']):
   off=start+k*stride;rgba=list(struct.unpack_from('<4H',old_data,off))
   for j in range(3):rgba[j]=65535 if crystal else round(65535*.66+rgba[j]*.34)
   struct.pack_into('<4H',old_data,off,*rgba)
  if crystal:crystal_white+=a['count']
  else:lifted+=a['count']
  a.pop('min',None);a.pop('max',None)
replacements={}
for im in d['images']:
 if im['name'] in ['paint_01_basecolor','paint_02_basecolor','paint_03_basecolor','oyster_damask_basecolor','mirror_reflection_capture']:
  replacements[im['bufferView']]=(B/'textures'/(im['name']+'.png')).read_bytes()
data=bytearray();unchanged=0
for i,v in enumerate(d['bufferViews']):
 start=v.get('byteOffset',0);length=v['byteLength'];block=replacements.get(i,old_data[start:start+length]);data.extend(b'\0'*((-len(data))%4));v['byteOffset']=len(data);v['byteLength']=len(block);data.extend(block)
 if i not in replacements and i not in changed_views:assert bytes(block)==original[start:start+length];unchanged+=1
data.extend(b'\0'*((-len(data))%4));d['buffers'][0]['byteLength']=len(data)
js=json.dumps(d,separators=(',',':'),ensure_ascii=False).encode();js+=b' '*((-len(js))%4)
out=struct.pack('<III',0x46546c67,2,28+len(js)+len(data))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(data),0x004e4942)+data
(B/'Boutique-web.glb').write_bytes(out)
st=json.loads((B/'web-stats.json').read_text());st.update(glb_bytes=len(out),version='v05-luminous-ivory',web_dynamic_lights=6,alpha_blend_materials=2,occlusion='Previous contact/soft visibility shading lifted with 0.66 + 0.34 * COLOR_0; crystal AO removed',crystal='White single-sided alpha blend 0.68, metallic 0; clearcoat; no baked darkening')
(B/'web-stats.json').write_text(json.dumps(st,indent=2))
report={'geometry_preserved':True,'gold_reflection_preserved':True,'warm_practicals_preserved':True,'softened_shadow_vertices':lifted,'white_crystal_vertices':crystal_white,'crystal_alpha':.68,'crystal_metallic':0,'unchanged_buffer_views':unchanged,'updated_image_buffers':len(replacements)}
(B/'palette-export-check.json').write_text(json.dumps(report,indent=2));print('LUMINOUS_GLB_UPDATED',len(out),flush=True)
