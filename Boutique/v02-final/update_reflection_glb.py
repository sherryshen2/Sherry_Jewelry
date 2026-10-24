import json,struct
from pathlib import Path
B=Path(__file__).resolve().parent;p=B/'Boutique-web.glb';raw=p.read_bytes();jl=struct.unpack_from('<I',raw,12)[0];d=json.loads(raw[20:20+jl]);data=raw[28+jl:]
im=next(i for i in d['images'] if i.get('name')=='mirror_reflection_capture');vi=im['bufferView'];bv=d['bufferViews'][vi];start=bv.get('byteOffset',0);oldlen=bv['byteLength'];oldpadded=(oldlen+3)//4*4
new=(B/'textures/mirror_reflection_capture.png').read_bytes();newpadded=new+b'\0'*((-len(new))%4);delta=len(newpadded)-oldpadded
data=data[:start]+newpadded+data[start+oldpadded:]
for i,v in enumerate(d['bufferViews']):
 if i!=vi and v.get('byteOffset',0)>=start+oldpadded:v['byteOffset']=v.get('byteOffset',0)+delta
bv['byteLength']=len(new);d['buffers'][0]['byteLength']=len(data)
js=json.dumps(d,separators=(',',':'),ensure_ascii=False).encode();js+=b' '*((-len(js))%4)
out=struct.pack('<III',0x46546c67,2,28+len(js)+len(data))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(data),0x004e4942)+data;p.write_bytes(out)
st=json.loads((B/'web-stats.json').read_text());st['glb_bytes']=len(out);st['mirror']='Softened 512×704 reflection capture, fixed image plus environment highlights; not a realtime planar mirror';(B/'web-stats.json').write_text(json.dumps(st,indent=2,ensure_ascii=False));print('REFLECTION_UPDATED',len(out))
