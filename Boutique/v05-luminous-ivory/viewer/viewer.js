import * as THREE from 'three';
import { GLTFLoader } from './vendor/loaders/GLTFLoader.js';
const host=document.querySelector('#viewport'),status=document.querySelector('#status');
const renderer=new THREE.WebGLRenderer({antialias:true,alpha:false,preserveDrawingBuffer:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,1.75));renderer.outputColorSpace=THREE.SRGBColorSpace;
renderer.toneMapping=THREE.NeutralToneMapping;renderer.toneMappingExposure=1.05;
renderer.shadowMap.enabled=false;
host.prepend(renderer.domElement);const canvas=renderer.domElement;canvas.tabIndex=0;
canvas.setAttribute('role','img');canvas.setAttribute('aria-label','可左右轻转的法式微缩珠宝店，方向键也可切换角度');
const scene=new THREE.Scene();renderer.setClearColor('#e9e5df');
const camera=new THREE.OrthographicCamera(-3.525,3.525,3.525,-3.525,.1,100);
const target=new THREE.Vector3(0,2.85,-1.1);let azimuth=0,elevation=8.002663,loaded=false,dirty=true;
let model;
// Neutral reflected light and broad softboxes, generated locally without an HDR download.
const env=new THREE.Scene();env.background=new THREE.Color(.18,.19,.21);
function panel(pos,w,h,color,power){const mat=new THREE.MeshBasicMaterial({color,side:THREE.DoubleSide});mat.color.multiplyScalar(power);const m=new THREE.Mesh(new THREE.PlaneGeometry(w,h),mat);m.position.fromArray(pos);m.lookAt(0,0,0);env.add(m);}
panel([-4,5,6],6,5,0xfff4e6,2.3);panel([5,2,3],4,5,0xe6efff,1.5);panel([0,6,-3],5,3,0xffffff,1.7);
const pmrem=new THREE.PMREMGenerator(renderer),envRT=pmrem.fromScene(env,.08,.1,30);scene.environment=envRT.texture;scene.environmentIntensity=.8;
// Six dynamic lights: soft exterior/facade fill plus the retained warm practicals. Contact shading is baked, avoiding aliasing on small reliefs.
const key=new THREE.DirectionalLight(0xfff5e8,2.5);key.position.set(-8,6.5,4);key.target.position.copy(target);scene.add(key,key.target);
scene.add(new THREE.HemisphereLight(0xeff3ff,0x9e826a,.90));
const facadeFill=new THREE.DirectionalLight(0xfff8ef,2.1);facadeFill.position.set(8,6.5,4);facadeFill.target.position.copy(target);scene.add(facadeFill,facadeFill.target);
const lamp=new THREE.PointLight(0xffd5a0,13.0,4.8,2);lamp.position.set(0,3.83,-1.0);scene.add(lamp);
for(const x of [-1.91,1.91]){const light=new THREE.PointLight(0xffd5a0,3.8,2.0,2);light.position.set(x,3.70,-2.0);scene.add(light);}
// Small candle halos make the warm practicals legible without full-scene bloom.
const haloCanvas=document.createElement('canvas');haloCanvas.width=haloCanvas.height=64;
const hc=haloCanvas.getContext('2d'),hg=hc.createRadialGradient(32,32,0,32,32,32);
hg.addColorStop(0,'rgba(255,229,177,.65)');hg.addColorStop(.18,'rgba(255,187,91,.32)');hg.addColorStop(.5,'rgba(255,156,61,.08)');hg.addColorStop(1,'rgba(255,150,50,0)');hc.fillStyle=hg;hc.fillRect(0,0,64,64);
const haloMaterial=new THREE.SpriteMaterial({map:new THREE.CanvasTexture(haloCanvas),transparent:true,depthWrite:false,blending:THREE.AdditiveBlending,toneMapped:false,opacity:.65});
for(let k=0;k<6;k++){const a=2*Math.PI*k/6+Math.PI/6,glow=new THREE.Sprite(haloMaterial);glow.position.set(.64*Math.cos(a),3.96,-1-.64*Math.sin(a));glow.scale.set(.24,.30,1);scene.add(glow);}

const ground=new THREE.Mesh(new THREE.PlaneGeometry(200,200),new THREE.MeshBasicMaterial({color:0xe9e5df,toneMapped:false}));ground.rotation.x=-Math.PI/2;ground.position.y=-.015;scene.add(ground);
const shadowCanvas=document.createElement('canvas');shadowCanvas.width=256;shadowCanvas.height=160;const sc=shadowCanvas.getContext('2d');
sc.shadowColor='rgba(43,34,25,.45)';sc.shadowBlur=22;sc.fillStyle='rgba(43,34,25,.34)';sc.shadowOffsetY=4;sc.fillRect(35,33,186,94);
const groundShadow=new THREE.Mesh(new THREE.PlaneGeometry(8,5),new THREE.MeshBasicMaterial({map:new THREE.CanvasTexture(shadowCanvas),transparent:true,depthWrite:false,toneMapped:false,opacity:.42}));groundShadow.rotation.x=-Math.PI/2;groundShadow.position.set(0,-.008,-1.08);scene.add(groundShadow);
function pose(){const a=THREE.MathUtils.degToRad(azimuth),e=THREE.MathUtils.degToRad(elevation);camera.position.set(target.x+17*Math.sin(a),target.y+17*Math.tan(e),target.z+17*Math.cos(a));camera.lookAt(target);camera.updateMatrixWorld();dirty=true;}
function resize(){const w=host.clientWidth,h=host.clientHeight,aspect=w/h,half=3.525/Math.min(1,aspect);renderer.setSize(w,h,false);camera.left=-half*aspect;camera.right=half*aspect;camera.top=half;camera.bottom=-half;camera.updateProjectionMatrix();dirty=true;}
new ResizeObserver(resize).observe(host);resize();pose();
function setView(a){azimuth=Math.max(-15,Math.min(15,a));elevation=8.002663;pose();document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.view)===a)));status.textContent='拖动轻转 · 左右各 15°';}
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>setView(Number(b.dataset.view)));
let pointer=null;
canvas.addEventListener('pointerdown',e=>{canvas.setPointerCapture(e.pointerId);pointer={id:e.pointerId,x:e.clientX,y:e.clientY};});
canvas.addEventListener('pointermove',e=>{if(!pointer||pointer.id!==e.pointerId)return;azimuth=THREE.MathUtils.clamp(azimuth+(e.clientX-pointer.x)*.065,-15,15);elevation=THREE.MathUtils.clamp(elevation+(e.clientY-pointer.y)*.025,5,11);pointer.x=e.clientX;pointer.y=e.clientY;pose();document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed','false'));});
for(const event of ['pointerup','pointercancel','lostpointercapture'])canvas.addEventListener(event,()=>pointer=null);
canvas.addEventListener('keydown',e=>{if(e.key==='ArrowLeft'||e.key==='ArrowRight'){e.preventDefault();setView(azimuth+(e.key==='ArrowLeft'?-2:2));}if(e.key==='Home')setView(0);});
try{
 const gltf=await new GLTFLoader().loadAsync('../Boutique-web.glb?v=5');model=gltf.scene;scene.add(model);
 model.traverse(o=>{if(o.isMesh){const m=o.material;m.envMapIntensity=1.0;
  if(m.name.includes('champagne')){m.envMap=envRT.texture;m.envMapIntensity=1.45;}
  if(m.name.includes('chandelier crystal')){m.depthWrite=false;m.side=THREE.FrontSide;m.envMap=envRT.texture;m.envMapIntensity=1.1;o.castShadow=false;o.renderOrder=1;}
  if(m.name.includes('display glass')){m.depthWrite=false;o.castShadow=false;o.renderOrder=2;}
  if(m.name.includes('floral ecru lace')){m.alphaTest=.45;m.transparent=false;m.side=THREE.DoubleSide;m.shadowSide=THREE.DoubleSide;}
  if(m.name.includes('softened silver mirror')){o.castShadow=false;m.envMap=envRT.texture;m.envMapIntensity=.4;}
 }});loaded=true;dirty=true;status.textContent='拖动轻转 · 左右各 15°';
}catch(e){document.querySelector('#error').textContent='模型载入失败。请通过本地服务器或网站打开此页面。';status.textContent='载入失败';console.error(e);}
function frame(){if(dirty){renderer.render(scene,camera);dirty=false;}requestAnimationFrame(frame);}frame();
function crystalDiagnostics(){let out=null;model?.traverse(o=>{if(o.isMesh&&o.material.name.includes('chandelier crystal')){const m=o.material;out={color:m.color.toArray(),opacity:m.opacity,metallic:m.metalness,roughness:m.roughness,transparent:m.transparent,depthWrite:m.depthWrite,frontSide:m.side===THREE.FrontSide};}});return out;}
// Read-only diagnostics for acceptance tests; no product interaction is attached to jewelry.
window.boutiqueDiagnostics=()=>({loaded,version:'v05-luminous-ivory',dynamicLights:6,crystal:crystalDiagnostics(),azimuth,elevation,webgl2:renderer.capabilities.isWebGL2,drawCalls:renderer.info.render.calls,triangles:renderer.info.render.triangles,meshes:renderer.info.memory.geometries,textures:renderer.info.memory.textures,canvas:[canvas.width,canvas.height],modelBounds:model?new THREE.Box3().setFromObject(model).toArray?.()??(()=>{const b=new THREE.Box3().setFromObject(model);return[b.min.toArray(),b.max.toArray()]})():null});
