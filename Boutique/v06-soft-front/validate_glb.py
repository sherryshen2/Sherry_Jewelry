import json,struct,math,sys
from pathlib import Path
B=Path(__file__).resolve().parent;p=B/'Boutique-web.glb';raw=p.read_bytes();magic,version,length=struct.unpack_from('<III',raw,0)
assert (magic,version,length)==(0x46546c67,2,len(raw))
jl,jtype=struct.unpack_from('<II',raw,12);assert jtype==0x4e4f534a
d=json.loads(raw[20:20+jl]);bl,bt=struct.unpack_from('<II',raw,20+jl);assert bt==0x004e4942;data=raw[28+jl:];assert bl==len(data)
assert len(d['buffers'])==1 and d['buffers'][0]['byteLength']<=len(data)
sizes={5120:1,5121:1,5122:2,5123:2,5125:4,5126:4};fmts={5120:'b',5121:'B',5122:'h',5123:'H',5125:'I',5126:'f'};components={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
for v in d['bufferViews']:assert v.get('byteOffset',0)+v['byteLength']<=len(data)
def values(i):
 a=d['accessors'][i];v=d['bufferViews'][a['bufferView']];n=components[a['type']];fmt='<'+fmts[a['componentType']]*n;step=v.get('byteStride',n*sizes[a['componentType']]);start=v.get('byteOffset',0)+a.get('byteOffset',0)
 assert a.get('byteOffset',0)+(a['count']-1)*step+struct.calcsize(fmt)<=v['byteLength']
 return [struct.unpack_from(fmt,data,start+k*step) for k in range(a['count'])]
triangles=0;vertices=0;primitives=0;allpoints=[];colored=0
for mesh in d['meshes']:
 for pr in mesh['primitives']:
  assert pr.get('mode',4)==4;attrs=pr['attributes'];pos=values(attrs['POSITION']);norms=values(attrs['NORMAL']);idx=values(pr['indices']);assert max(i[0] for i in idx)<len(pos);assert len(norms)==len(pos)
  assert all(math.isfinite(v) for p0 in pos for v in p0);assert all(math.isfinite(v) for n in norms for v in n)
  assert 0<=pr['material']<len(d['materials'])
  if 'COLOR_0' in attrs:assert len(values(attrs['COLOR_0']))==len(pos);colored+=1
  if 'TEXCOORD_0' in attrs:assert len(values(attrs['TEXCOORD_0']))==len(pos)
  triangles+=len(idx)//3;vertices+=len(pos);primitives+=1;allpoints+=pos
images=[]
for im in d['images']:
 assert 'uri' not in im and 'bufferView' in im
 v=d['bufferViews'][im['bufferView']];imagebytes=data[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]
 assert imagebytes.startswith(b'\x89PNG') or imagebytes.startswith(b'\xff\xd8')
 images.append({'name':im.get('name'),'bytes':len(imagebytes),'mime':im['mimeType']})
expected=json.loads((B/'web-stats.json').read_text());assert triangles==expected['triangles']
report={'valid_glb_header_and_buffers':True,'all_indices_in_range':True,'finite_positions_and_normals':True,'all_images_embedded':True,'external_dependencies':[],'triangle_count_matches_export':True,'triangles':triangles,'gltf_vertices_after_uv_normal_splits':vertices,'primitives':primitives,'primitives_with_baked_contact_color':colored,'materials':len(d['materials']),'images':images,'bounds_gltf':[[min(p[k] for p in allpoints) for k in range(3)],[max(p[k] for p in allpoints) for k in range(3)]],'bytes':len(raw)}
(B/'glb-check.json').write_text(json.dumps(report,indent=2,ensure_ascii=False));print(json.dumps(report,ensure_ascii=False))
