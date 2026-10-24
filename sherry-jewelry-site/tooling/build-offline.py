from pathlib import Path
import json,base64,re
root=Path(__file__).resolve().parents[1];dist=root/'dist'
files={}
for p in dist.rglob('*'):
 if p.is_file() and p.suffix in ['.glb','.webp','.ttf','.json','.js']:
  files[str(p.relative_to(dist))]=base64.b64encode(p.read_bytes()).decode()
bootstrap=r'''
requestAnimationFrame(()=>requestAnimationFrame(()=>{
 const encoded=__FILES__,urls={};
 const types={glb:'model/gltf-binary',webp:'image/webp',ttf:'font/ttf',json:'application/json',js:'text/javascript'};
 const decode=name=>Uint8Array.from(atob(encoded[name]),c=>c.charCodeAt(0));
 function assetUrl(name){return urls[name]??=URL.createObjectURL(new Blob([decode(name)],{type:types[name.split('.').pop()]||'application/octet-stream'}));}
 function resolve(value){const raw=typeof value==='string'?value:value.url;for(const k of Object.keys(encoded))if(raw===k||raw.endsWith('/'+k))return assetUrl(k);return raw;}
 const originalFetch=window.fetch.bind(window);window.fetch=(input,init)=>{const mapped=resolve(input);return originalFetch(mapped,init);};window.localAsset=resolve;
 document.querySelectorAll('img[src]').forEach(i=>i.src=resolve(i.getAttribute('src')));
 const style=document.createElement('style');style.textContent=__CSS__.replace(/url\(['"]?([^)'"\s]+)['"]?\)/g,(_,p)=>`url('${resolve(p)}')`);document.head.append(style);
 const modules={
  'sherry-core':['vendor/three.core.js',{}],
  'three':['vendor/three.module.js',{'./three.core.js':'sherry-core'}],
  'sherry-utils':['vendor/utils/BufferGeometryUtils.js',{}],
  'sherry-loader':['vendor/loaders/GLTFLoader.js',{'../utils/BufferGeometryUtils.js':'sherry-utils'}],
  'sherry-meshopt':['vendor/meshopt_decoder.module.js',{}],
  'sherry-engine':['engines.js',{'./vendor/loaders/GLTFLoader.js':'sherry-loader','./vendor/meshopt_decoder.module.js':'sherry-meshopt'}],
  'sherry-app':['app.js',{'./engines.js':'sherry-engine'}]
 };const imports={};
 for(const [name,[file,replacements]]of Object.entries(modules)){let code=new TextDecoder().decode(decode(file));for(const[from,to]of Object.entries(replacements))code=code.split(from).join(to);if(file==='app.js')code=code.replace('img.src=src;','img.src=window.localAsset(src.split("?")[0]);').replace('img.src=p.thumbnailUrl;','img.src=window.localAsset(p.thumbnailUrl);');imports[name]=URL.createObjectURL(new Blob([code],{type:'text/javascript'}));}
 const map=document.createElement('script');map.type='importmap';map.textContent=JSON.stringify({imports});document.head.append(map);const app=document.createElement('script');app.type='module';app.textContent="import 'sherry-app';";document.body.append(app);
}));
'''
bootstrap=bootstrap.replace('__FILES__',json.dumps(files)).replace('__CSS__',json.dumps((dist/'style.css').read_text())).replace('</script','<\\/script')
html=(dist/'index.html').read_text()
# Paint the same lightweight home before preparing any model blobs. Offline
# exports cannot preload sibling assets, because they must work as one file.
initial_css=re.sub(r'@font-face\{[^}]*\}', '', (dist/'style.css').read_text())
html=html.replace('<link rel="stylesheet" href="style.css">','<style>'+initial_css+'</style>')
html=re.sub(r'<link rel="preload"[^>]*>','',html)
html=html.replace('src="assets/boutique-poster.webp"','src="data:image/webp;base64,'+files['assets/boutique-poster.webp']+'"')
html=re.sub(r'<script type="importmap">.*?</script>','',html)
html=html.replace('<script type="module" src="app.js"></script>','<script>'+bootstrap+'</script>')
output=root.parent/'index.html';output.write_text(html);print(output,output.stat().st_size)
