import {NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import {dedup,meshopt,textureCompress} from '@gltf-transform/functions';
import {MeshoptEncoder,MeshoptDecoder} from 'meshoptimizer';
import sharp from 'sharp';
import fs from 'node:fs/promises';
await MeshoptEncoder.ready;
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'meshopt.encoder':MeshoptEncoder,'meshopt.decoder':MeshoptDecoder});
const root=new URL('../dist/assets/',import.meta.url);const report=[];
for(const name of (await fs.readdir(root)).filter(n=>n.endsWith('.glb'))){const path=new URL(name,root);const before=(await fs.stat(path)).size;const doc=await io.read(decodeURIComponent(path.pathname));await doc.transform(dedup(),textureCompress({encoder:sharp,targetFormat:'webp',quality:88,resize:[1024,1024]}),meshopt({encoder:MeshoptEncoder,level:'medium',quantizePosition:16,quantizeNormal:12,quantizeTexcoord:14,quantizeColor:12}));await io.write(decodeURIComponent(path.pathname),doc);const after=(await fs.stat(path)).size;report.push({name,before,after});console.log(name,(before/1e6).toFixed(2)+' → '+(after/1e6).toFixed(2)+' MB');}
await fs.writeFile(new URL('../asset-sizes.json',import.meta.url),JSON.stringify(report,null,2));await fs.copyFile(new URL('./node_modules/meshoptimizer/meshopt_decoder.mjs',import.meta.url),new URL('../dist/vendor/meshopt_decoder.module.js',import.meta.url));await fs.copyFile(new URL('./node_modules/meshoptimizer/LICENSE.md',import.meta.url),new URL('../dist/vendor/MESHOPT-LICENSE.md',import.meta.url));
