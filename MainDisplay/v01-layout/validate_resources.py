from pathlib import Path
import json,struct,math,hashlib
B=Path(__file__).resolve().parent;report={'stage':'stage1','files':{},'pass':True}
for name in ['main-display-scene','necklace','earrings','ring','bracelet']:
 p=B/(name+'.glb');raw=p.read_bytes();magic,version,length=struct.unpack_from('<III',raw);assert magic==0x46546c67 and version==2 and length==len(raw)
 jl=struct.unpack_from('<I',raw,12)[0];d=json.loads(raw[20:20+jl]);bl=struct.unpack_from('<I',raw,20+jl)[0];binary=raw[28+jl:];assert len(binary)==bl
 for v in d.get('bufferViews',[]):assert v.get('byteOffset',0)+v['byteLength']<=len(binary)
 tri=0
 for m in d.get('meshes',[]):
  for pr in m['primitives']:
   assert pr.get('mode',4)==4;acc=d['accessors'][pr['attributes']['POSITION']];assert all(math.isfinite(x) for x in acc['min']+acc['max']);tri+=(d['accessors'][pr['indices']]['count'] if 'indices' in pr else acc['count'])//3
   assert pr.get('material',0)<len(d.get('materials',[]))
 for im in d.get('images',[]):assert 'bufferView' in im and 'uri' not in im
 names=[n.get('name','') for n in d['nodes']]
 if name=='main-display-scene':assert sum(n.endswith('_anchor') for n in names)==4 and not any(n.endswith('_product') for n in names)
 if name=='earrings':assert 'left_earring' in names and 'right_earring' in names
 report['files'][p.name]={'bytes':len(raw),'megabytes':round(len(raw)/1e6,3),'triangles':tri,'materials':len(d.get('materials',[])),'meshes':len(d.get('meshes',[])),'images':len(d.get('images',[])),'extensions':d.get('extensionsUsed',[]),'sha256':hashlib.sha256(raw).hexdigest()}
report['total_triangles']=sum(x['triangles'] for x in report['files'].values());report['total_glb_bytes']=sum(x['bytes'] for x in report['files'].values());(B/'resource-check.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
