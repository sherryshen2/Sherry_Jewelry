import * as THREE from 'three';
import { GLTFLoader } from './vendor/loaders/GLTFLoader.js';

// Product files stay at real meter scale and retain J002_ROOT. Only this viewer pivot rotates.
const host=document.querySelector('#viewport'), status=document.querySelector('#status');
const scene=new THREE.Scene(),pivot=new THREE.Group();scene.add(pivot);
const renderer=new THREE.WebGLRenderer({antialias:true,alpha:true,preserveDrawingBuffer:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.outputColorSpace=THREE.SRGBColorSpace;
renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.0;
host.prepend(renderer.domElement);
const canvas=renderer.domElement;canvas.tabIndex=0;canvas.role='img';
canvas.setAttribute('aria-label','J002耳环，可连续360度旋转。拖动或使用方向键旋转，滚轮缩放。');
const camera=new THREE.PerspectiveCamera(30,1,.0001,2);camera.position.set(0,0,.07);
const cameraDistance={min:.025,max:.16};
let fullDistance=.07;
const UP=new THREE.Vector3(0,1,0),RIGHT=new THREE.Vector3(1,0,0);
let dirty=true,loaded=false,auto=false,lastTime=0,spin=null,currentMode='detail';
let dragX=0,dragY=0,loadGeneration=0;
const cache=new Map(),loader=new GLTFLoader();
const checks={horizontal:null,vertical:null,dragHorizontalDegrees:0,dragVerticalDegrees:0};

// A neutral jewelry studio: large softboxes plus small bright panels create view-dependent flashes.
// Environment meshes and lights are viewer-only. No product textures or emissive gemstone tricks.
const environment=new THREE.Scene();environment.background=new THREE.Color(.35,.35,.35);
function panel(position,width,height,brightness,color=0xffffff){
  const mat=new THREE.MeshBasicMaterial({color,side:THREE.DoubleSide});mat.color.multiplyScalar(brightness);
  const p=new THREE.Mesh(new THREE.PlaneGeometry(width,height),mat);p.position.fromArray(position);p.lookAt(0,0,0);environment.add(p);
}
panel([-3,3,4],2.2,4.0,4.2);panel([3,1,2],.40,4.0,6.0);
panel([0,4,-2],3,1.3,3.0);panel([-3,-2,-2],1.4,3,1.3);
panel([2,-3,2],2.5,.55,2.8);panel([-1,1,4],.18,.30,12);
panel([2,3,3],.22,.18,10);panel([-3,0,2],.16,.24,9);
for(let i=0;i<12;i++){
 const a=i*Math.PI/6;
 panel([4*Math.cos(a),4*Math.sin(a),2.0],.38,.52,20);
}
const pmrem=new THREE.PMREMGenerator(renderer);
const envTarget=pmrem.fromScene(environment,.015,.1,20);scene.environment=envTarget.texture;
const key=new THREE.DirectionalLight(0xffffff,2.2);key.position.set(-2,3,4);scene.add(key);
const rim=new THREE.DirectionalLight(0xffffff,1.5);rim.position.set(3,1,-2);scene.add(rim);
const pin=new THREE.DirectionalLight(0xffffff,1.0);pin.position.set(2,-2,3);scene.add(pin);
scene.add(new THREE.HemisphereLight(0xffffff,0x4b3932,.18));

function initialQuaternion(){
 const c=new THREE.PerspectiveCamera();c.position.set(0,.25,1);c.lookAt(0,0,0);
 return c.quaternion.clone().invert();
}
const orientations={default:initialQuaternion(),front:new THREE.Quaternion(),
 side:new THREE.Quaternion().setFromAxisAngle(UP,-Math.PI/2),back:new THREE.Quaternion().setFromAxisAngle(UP,Math.PI),
 underside:new THREE.Quaternion().setFromAxisAngle(RIGHT,-Math.PI/5)};
pivot.quaternion.copy(orientations.default);

function resize(){const w=host.clientWidth,h=host.clientHeight;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();dirty=true;}
new ResizeObserver(resize).observe(host);resize();
function setStatus(s){status.textContent=s;}
function stopMotion(){auto=false;spin=null;document.querySelector('#auto').setAttribute('aria-pressed','false');}
function rotate(axis,angle){pivot.quaternion.premultiply(new THREE.Quaternion().setFromAxisAngle(axis,angle)).normalize();dirty=true;}
function selectView(name){stopMotion();pivot.quaternion.copy(orientations[name]);camera.position.z=fullDistance;dirty=true;
 document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===name)));
 setStatus(`${document.querySelector(`[data-view="${name}"]`).textContent}视角 · 可连续拖动翻转`);
}
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>selectView(b.dataset.view));
document.querySelector('#reset').onclick=()=>selectView('default');

async function loadModel(mode){
 const ticket=++loadGeneration;currentMode=mode;setStatus('正在加载'+(mode==='detail'?'详情版':'展厅版')+'…');
 try{
  if(!cache.has(mode)){const gltf=await loader.loadAsync(`../J002-${mode}-v01.glb`);cache.set(mode,gltf.scene);}
  if(ticket!==loadGeneration)return;
  pivot.clear();const product=cache.get(mode);pivot.add(product);
  product.traverse(o=>{if(o.isMesh){o.frustumCulled=false;o.material.envMapIntensity=o.material.name.includes('Stone')||o.material.name.includes('CZ')?1.30:1.0;}});
  loaded=true;dirty=true;setStatus('已加载 · 拖动可连续360°旋转与翻转');
  document.querySelector('#detail').setAttribute('aria-pressed',String(mode==='detail'));
  document.querySelector('#display').setAttribute('aria-pressed',String(mode==='display'));
  const s=await fetch(`../J002-${mode}-stats.json`).then(r=>r.json());
  const lo=new THREE.Vector3(...s.bounds_mm[0]),hi=new THREE.Vector3(...s.bounds_mm[1]);const radius=hi.sub(lo).length()*.0005;fullDistance=radius/Math.sin(Math.atan(Math.tan(Math.PI/12)*Math.min(1,camera.aspect)))*1.06;camera.position.z=fullDistance;dirty=true;
  if(ticket===loadGeneration)document.querySelector('#model-stats').innerHTML=`${mode==='detail'?'详情版':'展厅版'} · ${(s.files[`J002-${mode}-v01.glb`]/1e6).toFixed(2)} MB · ${s.triangles.toLocaleString()} 三角面<div class="small">2个材质 · 真实尺度 · 相同旋转中心</div>`;
 }catch(error){setStatus('模型加载失败，请查看本地文件。');console.error(error);}
}
document.querySelector('#detail').onclick=()=>loadModel('detail');
document.querySelector('#display').onclick=()=>loadModel('display');

function zoom(mult){camera.position.z=THREE.MathUtils.clamp(camera.position.z*mult,cameraDistance.min,cameraDistance.max);dirty=true;setStatus('观察距离 '+(camera.position.z*1000).toFixed(1)+' mm');}
document.querySelector('#zoom-in').onclick=()=>zoom(.87);document.querySelector('#zoom-out').onclick=()=>zoom(1.15);
canvas.addEventListener('wheel',e=>{e.preventDefault();zoom(Math.exp(e.deltaY*.001));},{passive:false});
const pointers=new Map();let previousSpan=0;
canvas.addEventListener('pointerdown',e=>{stopMotion();canvas.setPointerCapture(e.pointerId);pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});previousSpan=0;});
canvas.addEventListener('pointermove',e=>{
 if(!pointers.has(e.pointerId))return;
 const prev=pointers.get(e.pointerId),dx=e.clientX-prev.x,dy=e.clientY-prev.y;
 pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});
 if(pointers.size===1){
  // No Euler latitude clamp: incremental world-space quaternions cross either pole indefinitely.
  const sensitivity=2*Math.PI/Math.min(host.clientWidth,host.clientHeight);
  rotate(UP,dx*sensitivity);rotate(RIGHT,dy*sensitivity);
  dragX+=dx*sensitivity;dragY+=dy*sensitivity;
  checks.dragHorizontalDegrees=THREE.MathUtils.radToDeg(dragX);checks.dragVerticalDegrees=THREE.MathUtils.radToDeg(dragY);
  setStatus('自由旋转 · 水平与纵向无180°限制');
  document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed','false'));
 }else if(pointers.size===2){
  const [a,b]=[...pointers.values()],span=Math.hypot(a.x-b.x,a.y-b.y);if(previousSpan>0&&span>0)zoom(previousSpan/span);previousSpan=span;
 }
});
for(const type of ['pointerup','pointercancel','lostpointercapture'])canvas.addEventListener(type,e=>{pointers.delete(e.pointerId);previousSpan=0;updateDiagnostics();});
canvas.addEventListener('keydown',e=>{
 const keys={ArrowLeft:[UP,-1],ArrowRight:[UP,1],ArrowUp:[RIGHT,-1],ArrowDown:[RIGHT,1]};
 if(keys[e.key]){e.preventDefault();stopMotion();rotate(keys[e.key][0],keys[e.key][1]*Math.PI/12);setStatus('自由旋转 · 方向键每次15°');}
});
function updateDiagnostics(){
 const format=c=>c?`已连续转过 ${c.angleDegrees}°；回到起点误差 ${c.returnErrorDegrees.toFixed(6)}°`:'未执行';
 const text=`水平一圈：${format(checks.horizontal)}\n纵向一圈：${format(checks.vertical)}\n拖动累计：水平 ${checks.dragHorizontalDegrees.toFixed(1)}° / 纵向 ${checks.dragVerticalDegrees.toFixed(1)}°`;
 document.querySelector('#diagnostics').textContent=text;
 document.querySelector('#diagnostics').dataset.results=JSON.stringify(checks);
}
function startTurn(axis,key){if(!loaded)return;stopMotion();spin={axis,key,start:pivot.quaternion.clone(),began:performance.now(),duration:4200};}
document.querySelector('#turn-y').onclick=()=>startTurn(UP,'horizontal');
document.querySelector('#turn-x').onclick=()=>startTurn(RIGHT,'vertical');
document.querySelector('#auto').onclick=()=>{spin=null;auto=!auto;document.querySelector('#auto').setAttribute('aria-pressed',String(auto));setStatus(auto?'自动欣赏 · 拖动即可停止':'已停止自动欣赏');};
function frame(now){
 const dt=Math.min((now-lastTime)/1000,.05);lastTime=now;
 if(spin){
  const t=Math.min(1,(now-spin.began)/spin.duration),angle=t*Math.PI*2;
  pivot.quaternion.copy(spin.start).premultiply(new THREE.Quaternion().setFromAxisAngle(spin.axis,angle)).normalize();dirty=true;
  setStatus(`${spin.key==='vertical'?'纵向翻转':'水平旋转'} ${Math.round(t*360)}° / 360°`);
  if(t===1){checks[spin.key]={angleDegrees:360,returnErrorDegrees:THREE.MathUtils.radToDeg(pivot.quaternion.angleTo(spin.start))};setStatus((spin.key==='vertical'?'纵向':'水平')+'360°完成 · 可继续拖动');spin=null;updateDiagnostics();}
 }
 if(auto){rotate(UP,dt*.26);}
 if(dirty){renderer.render(scene,camera);dirty=false;}
 requestAnimationFrame(frame);
}
updateDiagnostics();loadModel('detail');requestAnimationFrame(frame);
