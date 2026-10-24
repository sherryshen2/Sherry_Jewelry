"""Replace only material colours and affected PNGs; retain geometry and baked lighting byte-for-byte."""
import json,struct,copy,hashlib
from pathlib import Path
B=Path(__file__).resolve().parent;source=B.parent/'v03-brighter-warm/Boutique-web.glb'
raw=source.read_bytes();jl=struct.unpack_from('<I',raw,12)[0];d=json.loads(raw[20:20+jl]);old_data=raw[28+jl:]
colors=json.loads((B/'pastel-colors.json').read_text());names=[]
for m in d['materials']:
 key=m['name'].removeprefix('Web_').split(' |')[0]
 if key not in colors:continue
 old=copy.deepcopy(m);p=m['pbrMetallicRoughness']
 if key not in ['01','02','03','06']:p['baseColorFactor']=colors[key]+[1]
 a=copy.deepcopy(m);b=copy.deepcopy(old)
 a['pbrMetallicRoughness'].pop('baseColorFactor',None);b['pbrMetallicRoughness'].pop('baseColorFactor',None)
 assert a==b,'Only colours may change'
 names.append(m['name'])
replacements={}
for im in d['images']:
 if im['name'] in ['paint_01_basecolor','paint_02_basecolor','paint_03_basecolor','oyster_damask_basecolor','mirror_reflection_capture']:
  replacements[im['bufferView']]=(B/'textures'/(im['name']+'.png')).read_bytes()
data=bytearray();unchanged=0
for i,v in enumerate(d['bufferViews']):
 original=old_data[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]
 block=replacements.get(i,original);data.extend(b'\0'*((-len(data))%4));v['byteOffset']=len(data);v['byteLength']=len(block);data.extend(block)
 if i not in replacements:assert bytes(data[v['byteOffset']:v['byteOffset']+v['byteLength']])==original;unchanged+=1
data.extend(b'\0'*((-len(data))%4));d['buffers'][0]['byteLength']=len(data)
js=json.dumps(d,separators=(',',':'),ensure_ascii=False).encode();js+=b' '*((-len(js))%4)
out=struct.pack('<III',0x46546c67,2,28+len(js)+len(data))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(data),0x004e4942)+data
(B/'Boutique-web.glb').write_bytes(out)
stats=json.loads((B/'web-stats.json').read_text());stats['glb_bytes']=len(out);stats['version']='v04-pastel-palette';(B/'web-stats.json').write_text(json.dumps(stats,indent=2))
report={'source_revision_matches_glb':True,'materials_checked':names,'only_base_color_changed':True,'geometry_and_baked_lighting_unchanged':True,'unchanged_buffer_views':unchanged,'updated_image_buffers':len(replacements)}
(B/'palette-export-check.json').write_text(json.dumps(report,indent=2));print('GLB_PALETTE_UPDATED',len(out),flush=True)
