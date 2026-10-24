import * as THREE from 'three';
import { GLTFLoader } from './vendor/loaders/GLTFLoader.js';
import { MeshoptDecoder } from './vendor/meshopt_decoder.module.js';
export {THREE};
const settings=await fetch('data/settings.json').then(r=>r.json());
const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
const renderers=new WeakMap();
export function disposeHost(host){const r=renderers.get(host);if(r){r.disposed=true;r.dispose();r.forceContextLoss();renderers.delete(host);}host.querySelectorAll('canvas').forEach(c=>c.remove());}
const reduced=matchMedia('(prefers-reduced-motion: reduce)');
const rad=THREE.MathUtils.degToRad;
function makeRenderer(host){const r=new THREE.WebGLRenderer({alpha:true,antialias:true,preserveDrawingBuffer:true});r.setPixelRatio(Math.min(devicePixelRatio,innerWidth<768?1.25:1.75));r.outputColorSpace=THREE.SRGBColorSpace;r.setClearColor(0,0);host.prepend(r.domElement);renderers.set(host,r);r.domElement.addEventListener('webglcontextlost',e=>{e.preventDefault();if(r.disposed)return;host.dispatchEvent(new CustomEvent('graphicslost',{bubbles:true}));});return r;}
function watchSize(host,renderer,camera,fit){const resize=()=>{const w=host.clientWidth,h=host.clientHeight;if(!w||!h)return;renderer.setSize(w,h,false);fit(w/h);camera.updateProjectionMatrix();};resize();new ResizeObserver(resize).observe(host);}

export async function createHero(host,onPose){
const renderer=makeRenderer(host),canvas=renderer.domElement,scene=new THREE.Scene();renderer.toneMapping=THREE.NeutralToneMapping;renderer.toneMappingExposure=1.05;
const camera=new THREE.OrthographicCamera(-4,4,4,-4,.1,100),target=new THREE.Vector3(...settings.scenes.hero.camera.target);
let azimuth=0,elevation=8.002663,dirty=true,active=true,dragging=false,model;
const motion=settings.scenes.hero.motion;
let hoverTarget=0,hoverOffset=0,lastFrame=0,floatPhase=0;
function unitsPerPixel(){return (camera.top-camera.bottom)/camera.zoom/Math.max(1,host.clientHeight);}
const env=new THREE.Scene();env.background=new THREE.Color(.18,.19,.21);
function panel(pos,w,h,color,power){const mat=new THREE.MeshBasicMaterial({color,side:THREE.DoubleSide});mat.color.multiplyScalar(power);const m=new THREE.Mesh(new THREE.PlaneGeometry(w,h),mat);m.position.fromArray(pos);m.lookAt(0,0,0);env.add(m);}
panel([-4,5,6],6,5,0xfff4e6,2.3);panel([5,2,3],4,5,0xe6efff,1.5);panel([0,6,-3],5,3,0xffffff,1.7);
const pmrem=new THREE.PMREMGenerator(renderer),envRT=pmrem.fromScene(env,.04,.1,30);scene.environment=envRT.texture;scene.environmentIntensity=.8;
// Six dynamic lights: soft exterior/facade fill plus the retained warm practicals. Contact shading is baked, avoiding aliasing on small reliefs.
const key=new THREE.DirectionalLight(0xfff5e8,2.384040);key.position.set(-8,6.5,2.98);key.target.position.copy(target);scene.add(key,key.target);
scene.add(new THREE.HemisphereLight(0xeff3ff,0x9e826a,.90));
const facadeFill=new THREE.DirectionalLight(0xfff8ef,2.002594);facadeFill.position.set(8,6.5,2.98);facadeFill.target.position.copy(target);scene.add(facadeFill,facadeFill.target);
const lamp=new THREE.PointLight(0xffd5a0,13.0,4.8,2);lamp.position.set(0,3.83,-1.0);scene.add(lamp);
for(const x of [-1.91,1.91]){const light=new THREE.PointLight(0xffd5a0,3.8,2.0,2);light.position.set(x,3.70,-2.0);scene.add(light);}
// Small candle halos make the warm practicals legible without full-scene bloom.
const haloCanvas=document.createElement('canvas');haloCanvas.width=haloCanvas.height=64;
const hc=haloCanvas.getContext('2d'),hg=hc.createRadialGradient(32,32,0,32,32,32);
hg.addColorStop(0,'rgba(255,229,177,.65)');hg.addColorStop(.18,'rgba(255,187,91,.32)');hg.addColorStop(.5,'rgba(255,156,61,.08)');hg.addColorStop(1,'rgba(255,150,50,0)');hc.fillStyle=hg;hc.fillRect(0,0,64,64);
const haloMaterial=new THREE.SpriteMaterial({map:new THREE.CanvasTexture(haloCanvas),transparent:true,depthWrite:false,blending:THREE.AdditiveBlending,toneMapped:false,opacity:.65});
for(let k=0;k<6;k++){const a=2*Math.PI*k/6+Math.PI/6,glow=new THREE.Sprite(haloMaterial);glow.position.set(.64*Math.cos(a),3.96,-1-.64*Math.sin(a));glow.scale.set(.24,.30,1);scene.add(glow);}


function pose(){const a=rad(THREE.MathUtils.clamp(azimuth+hoverOffset*motion.hoverYawDegrees,-15,15)),e=rad(elevation);camera.position.set(target.x+17*Math.sin(a),target.y+17*Math.tan(e),target.z+17*Math.cos(a));camera.lookAt(target);camera.updateMatrixWorld();dirty=true;}
watchSize(host,renderer,camera,aspect=>{const half=settings.scenes.hero.camera.verticalSize/2/Math.min(1,aspect);camera.left=-half*aspect;camera.right=half*aspect;camera.top=half;camera.bottom=-half;camera.zoom=innerWidth>=768?settings.scenes.hero.camera.desktopZoom:1;dirty=true;});pose();
model=(await loader.loadAsync(settings.scenes.hero.modelUrl)).scene;scene.add(model);
 model.traverse(o=>{if(o.isMesh){const m=o.material;m.envMapIntensity=1.0;
  if(m.name.includes('champagne')){m.envMap=envRT.texture;m.envMapIntensity=1.45;}
  if(m.name.includes('chandelier crystal')){m.depthWrite=false;m.side=THREE.FrontSide;m.envMap=envRT.texture;m.envMapIntensity=1.1;o.castShadow=false;o.renderOrder=1;}
  if(m.name.includes('display glass')){m.depthWrite=false;o.castShadow=false;o.renderOrder=2;}
  if(m.name.includes('floral ecru lace')){m.alphaTest=.45;m.transparent=false;m.side=THREE.DoubleSide;m.shadowSide=THREE.DoubleSide;}
  if(m.name.includes('softened silver mirror')){o.castShadow=false;m.envMap=envRT.texture;m.envMapIntensity=.4;}
 }});
const reflection=document.createElement('canvas');reflection.className='boutique-reflection';reflection.setAttribute('aria-hidden','true');host.append(reflection);const context=reflection.getContext('2d');let lastReflection=0;
function frame(t){
 if(renderer.disposed)return;requestAnimationFrame(frame);
 const dt=lastFrame?Math.min(t-lastFrame,64):0;lastFrame=t;
 if(!active||document.hidden)return;
 if(reduced.matches){if(hoverOffset||model.position.x||model.position.y){hoverOffset=0;model.position.set(0,0,0);pose();}}
 else if(!dragging){
  floatPhase=(floatPhase+dt/motion.floatPeriodMs*Math.PI*2)%(Math.PI*2);
  // Convert CSS pixels to world units so the peak-to-peak travel stays 12 px on every screen.
  model.position.y=Math.sin(floatPhase)*(motion.floatTravelPx/2)*unitsPerPixel()/Math.cos(rad(elevation));
  hoverOffset=THREE.MathUtils.lerp(hoverOffset,hoverTarget,1-Math.exp(-dt/motion.hoverResponseMs));
  model.position.x=hoverOffset*(motion.hoverTravelPx/2)*unitsPerPixel();pose();
 }
 if(dirty){renderer.render(scene,camera);dirty=false;if(t-lastReflection>70){reflection.width=canvas.width/2;reflection.height=canvas.height/2;context.drawImage(canvas,0,0,reflection.width,reflection.height);lastReflection=t;}onPose?.();}
}requestAnimationFrame(frame);
const ray=new THREE.Raycaster();
function hit(x,y){const r=canvas.getBoundingClientRect();ray.setFromCamera(new THREE.Vector2((x-r.left)/r.width*2-1,1-(y-r.top)/r.height*2),camera);return ray.intersectObject(model,true).length>0;}
// Draw the complete scene before allowing the poster to fade.
renderer.render(scene,camera);
return {renderer,camera,scene,canvas,
 setActive(v){active=v;if(!v)hoverTarget=0;dirty=true},
 drag(dx,dy){azimuth=THREE.MathUtils.clamp(azimuth+dx*.065,-15,15);elevation=THREE.MathUtils.clamp(elevation+dy*.025,5,11);pose();},
 setDragging(v){dragging=v;if(v){azimuth=THREE.MathUtils.clamp(azimuth+hoverOffset*motion.hoverYawDegrees,-15,15);hoverOffset=hoverTarget=0;pose();}},
 hover(x,y){if(reduced.matches||dragging)return;const r=canvas.getBoundingClientRect();hoverTarget=hit(x,y)?THREE.MathUtils.clamp((x-r.left-r.width/2)/(r.width*.25),-1,1):0;},
 clearHover(){hoverTarget=0},hit,
 reset(){azimuth=0;elevation=8;hoverOffset=hoverTarget=0;pose()},
 getState(){return {azimuth,elevation,hoverOffset,floatOffsetPx:model.position.y*Math.cos(rad(elevation))/unitsPerPixel(),floatTravelPx:motion.floatTravelPx,floatPeriodMs:motion.floatPeriodMs}},
 capture(){renderer.render(scene,camera);return canvas.toDataURL('image/png')}
};
}

export async function createStage(host,products,onPose){
const renderer=makeRenderer(host),canvas=renderer.domElement,scene=new THREE.Scene();renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1;renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.VSMShadowMap;
const target=new THREE.Vector3(...settings.scenes.display.camera.target),camera=new THREE.OrthographicCamera(-.2,.2,.2,-.2,.001,10);
let yaw=0,active=true,dirty=true,mirror=null,fixed;const productRoots={},originals={};function draw(){dirty=true;}
const pmrem=new THREE.PMREMGenerator(renderer),env=new THREE.Scene();env.background=new THREE.Color().setRGB(.18,.19,.21);
function panel(pos,w,h,power,color=0xffffff){const o=new THREE.Mesh(new THREE.PlaneGeometry(w,h),new THREE.MeshBasicMaterial({color:new THREE.Color(color).multiplyScalar(power),side:THREE.DoubleSide}));o.position.set(...pos);o.lookAt(0,0,0);env.add(o)}
panel([-4,5,6],4,5,3);panel([5,3,3],2,5,2.3);panel([0,6,0],4,3,4.6,0xffdb9f);panel([1,4,5],2,4,3.8,0xffdfac);scene.environment=pmrem.fromScene(env,.035).texture;scene.environmentIntensity=.85;
const key=new THREE.DirectionalLight(0xfffaf4,1.55);key.position.set(-.28,.47,.38);key.target.position.copy(target);key.castShadow=true;key.shadow.mapSize.set(1024,1024);Object.assign(key.shadow.camera,{left:-.4,right:.4,top:.5,bottom:-.25,near:.01,far:1.5});key.shadow.bias=-.00001;key.shadow.normalBias=.00016;key.shadow.radius=5;key.shadow.blurSamples=8;scene.add(key,key.target);
const fill=new THREE.DirectionalLight(0xf0f4ff,.65);fill.position.set(.3,.32,.18);fill.target.position.copy(target);scene.add(fill,fill.target);
const warm=new THREE.DirectionalLight(0xffcf82,3.2);warm.position.set(0,.65,.025);warm.target.position.set(-.025,.18,-.015);warm.castShadow=true;warm.shadow.mapSize.set(1024,1024);Object.assign(warm.shadow.camera,{left:-.38,right:.38,top:.38,bottom:-.38,near:.01,far:1.2});warm.shadow.bias=-.000015;warm.shadow.normalBias=.00012;warm.shadow.radius=7;warm.shadow.blurSamples=8;scene.add(warm,warm.target);scene.add(new THREE.HemisphereLight(0xf1eee7,0xb6a28c,.6));
const overheadPool=new THREE.SpotLight(0xffc46b,.65,1,.56,.85,2);overheadPool.position.set(-.035,.52,.12);overheadPool.target.position.set(-.025,.17,-.005);scene.add(overheadPool,overheadPool.target);
const wallWash=new THREE.DirectionalLight(0xffb86b,2.2);wallWash.position.set(0,.68,.32);wallWash.target.position.set(0,.32,-.16);scene.add(wallWash,wallWash.target);
const bounce=new THREE.DirectionalLight(0xffd4a3,3.0);bounce.position.set(0,.38,-.4);bounce.target.position.copy(target);scene.add(bounce,bounce.target);
const ground=new THREE.Mesh(new THREE.PlaneGeometry(5,5),new THREE.MeshStandardMaterial({color:0xf4ede3,roughness:.95}));ground.rotation.x=-Math.PI/2;ground.position.y=.002;ground.receiveShadow=true;scene.add(ground);

function pose(){const a=rad(yaw),e=rad(19);camera.position.copy(target).add(new THREE.Vector3(Math.sin(a)*Math.cos(e),Math.sin(e),Math.cos(a)*Math.cos(e)).multiplyScalar(.9));camera.lookAt(target);camera.updateMatrixWorld();draw();}
watchSize(host,renderer,camera,aspect=>{const vertical=settings.scenes.display.camera.verticalSize/Math.min(1,aspect/.95);camera.left=-vertical*aspect/2;camera.right=vertical*aspect/2;camera.top=vertical/2;camera.bottom=-vertical/2;pose();});pose();
function warmHeightShader(material,kind){
 material.onBeforeCompile=shader=>{
  shader.vertexShader=shader.vertexShader.replace('#include <common>','#include <common>\nvarying float warmWorldHeight;').replace('#include <worldpos_vertex>','#include <worldpos_vertex>\nwarmWorldHeight=(modelMatrix*vec4(transformed,1.0)).y;');
  const grade=kind==='table'
   ? 'float warmth=smoothstep(.015,.135,warmWorldHeight);outgoingLight*=mix(vec3(1.025,.985,.88),vec3(1.10,.95,.73),warmth)*(1.0+.10*warmth);'
   : kind==='mirror-metal'
    ? 'float warmth=smoothstep(.14,.43,warmWorldHeight);outgoingLight*=mix(vec3(1.16,1.07,1.02),vec3(1.23,1.08,.99),warmth)*(1.0+.06*warmth);'
   : kind==='metal'
    ? 'float warmth=smoothstep(.14,.43,warmWorldHeight);outgoingLight*=mix(vec3(1.01,1.0,.96),vec3(1.22,.94,.64),warmth)*(1.0+.20*warmth);'
    : kind==='bust'
     ? 'float warmth=smoothstep(.14,.31,warmWorldHeight);outgoingLight*=mix(vec3(1.0),vec3(1.10,.98,.87),warmth)*(1.0+.17*warmth);'
     : 'float warmth=smoothstep(.14,.43,warmWorldHeight);outgoingLight*=mix(vec3(1.02,.98,.91),vec3(1.18,.84,.55),warmth)*(1.0+.23*warmth);';
  shader.fragmentShader=shader.fragmentShader.replace('#include <common>','#include <common>\nvarying float warmWorldHeight;').replace('#include <opaque_fragment>',grade+'\n#include <opaque_fragment>');
 };material.customProgramCacheKey=()=>`world-toplight-${kind}-v3-orange`;
}
function configure(root,isProduct=false){root.traverse(o=>{
 if(!o.isMesh)return;
 const background=o.name.includes('Background_');o.castShadow=!background;o.receiveShadow=!background;
 if(!isProduct)o.material=Array.isArray(o.material)?o.material.map(m=>m.clone()):o.material.clone();
 for(const m of Array.isArray(o.material)?o.material:[o.material]){
  if(m.name.includes('lace')){m.alphaTest=.45;m.transparent=false;m.side=THREE.DoubleSide;}
  if(!isProduct&&m.name.includes('champagne')){m.metalness=1;m.roughness=m.name.includes('satin')?.17:.12;m.envMapIntensity=1.5;}
  const mirrorGold=m.name.includes('pale champagne mirror');
  if(mirrorGold){m.metalness=1;m.roughness=m.name.includes('satin')?.22:.17;m.envMapIntensity=2.0;}
  const pink=/blush|pink|silk|suede|petal/i.test(m.name);
  if(!isProduct&&!pink){
   if(mirrorGold)warmHeightShader(m,'mirror-metal');
   else if(background&&!m.name.includes('mirror'))warmHeightShader(m,m.metalness>.5?'metal':'wall');
   else if(!background&&m.name.includes('warm ivory velvet'))warmHeightShader(m,'bust');
   else if(!background&&/warm ivory lacquer|ivory carved edges|inset warm putty/i.test(m.name))warmHeightShader(m,'table');
  }
  m.needsUpdate=true;
 }
});}
function makeSoftMirror(source){
 scene.updateMatrixWorld(true);const box=new THREE.Box3().setFromObject(source),center=box.getCenter(new THREE.Vector3()),size=box.getSize(new THREE.Vector3()),planeZ=box.max.z+.0001;
 source.visible=false;
 const buffer=new THREE.WebGLRenderTarget((innerWidth<768?256:512),(innerWidth<768?256:512),{type:THREE.HalfFloatType,minFilter:THREE.LinearFilter,magFilter:THREE.LinearFilter,depthBuffer:true});
 const reflectedCamera=new THREE.OrthographicCamera(),projection=new THREE.Matrix4(),bias=new THREE.Matrix4().set(.5,0,0,.5,0,.5,0,.5,0,0,.5,.5,0,0,0,1);
 // Alpha separates reflected objects from the neutral mirror background.
 const material=new THREE.ShaderMaterial({uniforms:{reflection:{value:buffer.texture},projection:{value:projection},softness:{value:.0034}},vertexShader:`uniform mat4 projection; varying vec4 mirrorCoord; varying vec2 mirrorUv; varying float mirrorWorldHeight; void main(){mirrorUv=uv;mirrorWorldHeight=(modelMatrix*vec4(position,1.0)).y;vec4 world=modelMatrix*vec4(position,1.0);mirrorCoord=projection*world;gl_Position=projectionMatrix*viewMatrix*world;}`,fragmentShader:`uniform sampler2D reflection; uniform float softness; varying vec4 mirrorCoord; varying vec2 mirrorUv; varying float mirrorWorldHeight;
 void main(){vec2 uv=mirrorCoord.xy/mirrorCoord.w;vec4 reflected=vec4(0.0);float weight=0.0;
 for(int x=-4;x<=4;x++){for(int y=-4;y<=4;y++){float w=exp(-float(x*x+y*y)*.12);reflected+=texture2D(reflection,uv+vec2(float(x),float(y))*softness)*w;weight+=w;}}
 reflected/=weight;float mask=clamp(reflected.a,0.0,1.0);vec3 objectColor=reflected.rgb/max(mask,.001);
 // Preserve source RGB differences; warm the lit objects, not the entire mirror.
 float topGlow=smoothstep(.14,.43,mirrorWorldHeight);
 objectColor=objectColor*mix(vec3(1.08,1.04,.96),vec3(1.34,1.02,.66),topGlow)+mix(vec3(.20,.19,.16),vec3(.39,.23,.09),topGlow);
 vec3 greyBackground=mix(vec3(.43,.44,.45),vec3(.57,.43,.27),topGlow);
 vec3 color=mix(greyBackground,objectColor,mask);
 gl_FragColor=vec4(color,1.0);
 #include <tonemapping_fragment>
 #include <colorspace_fragment>
 }`});
 const disc=new THREE.Mesh(new THREE.CircleGeometry(1,128),material);disc.name='Soft live mirror reflection';disc.position.set(center.x,center.y,planeZ);disc.scale.set(size.x/2,size.y/2,1);scene.add(disc);
 const background=[];fixed.traverse(o=>{if(o.isMesh&&o.name.includes('Background_'))background.push(o)});
 return {update(){
  if(camera.position.z<=planeZ+.001)return;
  reflectedCamera.copy(camera);reflectedCamera.position.z=2*planeZ-camera.position.z;
  const reflectedTarget=target.clone();reflectedTarget.z=2*planeZ-target.z;reflectedCamera.lookAt(reflectedTarget);reflectedCamera.updateMatrixWorld();reflectedCamera.updateProjectionMatrix();
  projection.copy(bias).multiply(reflectedCamera.projectionMatrix).multiply(reflectedCamera.matrixWorldInverse);
  const visibility=background.map(o=>o.visible);background.forEach(o=>o.visible=false);disc.visible=false;
  const previous=renderer.getRenderTarget(),shadowUpdate=renderer.shadowMap.autoUpdate;renderer.shadowMap.autoUpdate=false;
  const previousBackground=scene.background,previousGround=ground.visible,previousClear=renderer.getClearColor(new THREE.Color()),previousAlpha=renderer.getClearAlpha();scene.background=null;ground.visible=false;renderer.setClearColor(0x000000,0);
  renderer.setRenderTarget(buffer);renderer.render(scene,reflectedCamera);renderer.setRenderTarget(previous);renderer.shadowMap.autoUpdate=shadowUpdate;scene.background=previousBackground;ground.visible=previousGround;renderer.setClearColor(previousClear,previousAlpha);
  background.forEach((o,i)=>o.visible=visibility[i]);disc.visible=true;
 }};
}

const config=await fetch('data/placement.json').then(r=>r.json());fixed=(await loader.loadAsync(settings.scenes.display.modelUrl)).scene;configure(fixed);scene.add(fixed);
for(const p of products){const root=(await loader.loadAsync(p.displayModelUrl)).scene,anchor=fixed.getObjectByName(p.anchorName);if(!anchor)throw Error('Missing anchor '+p.anchorName);configure(root,true);anchor.add(root);productRoots[p.id]=root;root.updateMatrixWorld(true);originals[p.id]={position:root.position.clone(),scale:root.scale.clone()};root.traverse(o=>o.userData.productId=p.id);}
let mirrorSource;fixed.traverse(o=>{if(o.isMesh&&(Array.isArray(o.material)?o.material:[o.material]).some(m=>m.name.includes('softened silver mirror')))mirrorSource=o;});
renderer.render(scene,camera);if(mirrorSource)mirror=makeSoftMirror(mirrorSource);draw();
let hover=null,lastTime=0;function frame(t){if(renderer.disposed)return;requestAnimationFrame(frame);if(!active||document.hidden)return;const dt=Math.min((t-lastTime)/180,1);lastTime=t;
for(const p of products){const root=productRoots[p.id],goal=hover===p.id?p.hoverScale:1,next=THREE.MathUtils.lerp(root.scale.x,goal,dt);if(Math.abs(next-root.scale.x)>.00005){root.scale.setScalar(next);const pivot=new THREE.Vector3(...(p.id==='J001'?[0,0,0]:config.products[p.type].bounds_local_glb.center));root.position.copy(originals[p.id].position).addScaledVector(pivot,1-next);dirty=true;}}
if(dirty){scene.updateMatrixWorld(true);mirror?.update();renderer.render(scene,camera);onPose?.();dirty=false;}}requestAnimationFrame(frame);
const ray=new THREE.Raycaster();function screen(v){v.project(camera);const r=canvas.getBoundingClientRect();return{x:r.left+(v.x+1)*r.width/2,y:r.top+(1-v.y)*r.height/2};}
function project(id){const root=productRoots[id],box=new THREE.Box3().setFromObject(root),corners=[];for(const x of [box.min.x,box.max.x])for(const y of [box.min.y,box.max.y])for(const z of [box.min.z,box.max.z])corners.push(screen(new THREE.Vector3(x,y,z)));const xs=corners.map(p=>p.x),ys=corners.map(p=>p.y);return {x:(Math.min(...xs)+Math.max(...xs))/2,y:(Math.min(...ys)+Math.max(...ys))/2,width:Math.max(...xs)-Math.min(...xs),height:Math.max(...ys)-Math.min(...ys),top:Math.min(...ys)};}
function hit(x,y){const r=canvas.getBoundingClientRect();ray.setFromCamera(new THREE.Vector2((x-r.left)/r.width*2-1,1-(y-r.top)/r.height*2),camera);const actual=ray.intersectObjects(Object.values(productRoots),true).find(v=>v.object.userData.productId);if(actual)return actual.object.userData.productId;
let best=null,distance=Infinity;
for(const p of products){const root=productRoots[p.id],cfg=config.products[p.type],region=cfg.preferred_hit_region;let points=[];
if(region?.capsules)points=region.capsules.flatMap(c=>[c.a,c.b]);else if(region?.boxes)points=region.boxes.map(b=>b.center);else if(p.id==='J001')points=[[0,0,0],[-.024,.045,.018],[.024,.045,.018]];else points=[cfg.bounds_local_glb.center];
for(const a of points){const q=screen(root.localToWorld(new THREE.Vector3(...a))),d=Math.hypot(q.x-x,q.y-y),radius=p.id==='J004'?Math.max(7,Math.min(14,project(p.id).width*.10)):22;if(d<radius&&d<distance){best=p.id;distance=d;}}}return best;}
return{renderer,canvas,scene,camera,productRoots,project,hit,setActive(v){active=v;dirty=true},hover(id){hover=id;draw()},hide(id,hidden){productRoots[id].visible=!hidden;draw();mirror?.update();renderer.render(scene,camera)},drag(dx){yaw=THREE.MathUtils.clamp(yaw+dx*.065,-15,15);pose()},reset(){yaw=0;pose()},getState(){return {yaw}},setState(s){yaw=THREE.MathUtils.clamp(s?.yaw||0,-15,15);pose()},capture(){mirror?.update();renderer.render(scene,camera);return canvas.toDataURL('image/png')}};
}

export function createDetail(host){
 const renderer=makeRenderer(host),canvas=renderer.domElement,scene=new THREE.Scene(),pivot=new THREE.Group();scene.add(pivot);renderer.toneMapping=THREE.ACESFilmicToneMapping;
 const camera=new THREE.OrthographicCamera(-1,1,1,-1,.00001,20);camera.position.z=2;let active=false,dirty=true,current=null,defaultQ=new THREE.Quaternion(),radius=.1,baseRadius=.1,zoom=1,aspect=1,center=new THREE.Vector3(),pendant=false,generation=0;
 let transition=null;
const cache=new Map(),pending=new Map(),environment=new THREE.Scene();environment.background=new THREE.Color(.30,.30,.30);
 function panel(position,width,height,brightness){const m=new THREE.MeshBasicMaterial({color:0xffffff,side:THREE.DoubleSide});m.color.multiplyScalar(brightness);const p=new THREE.Mesh(new THREE.PlaneGeometry(width,height),m);p.position.fromArray(position);p.lookAt(0,0,0);environment.add(p);}
 panel([-3,3,4],2.2,4,4.2);panel([3,1,2],.4,4,6);panel([0,4,-2],3,1.3,3);panel([-3,-2,-2],1.4,3,1.3);panel([2,-3,2],2.5,.55,2.8);for(let i=0;i<12;i++){const a=i*Math.PI/6;panel([4*Math.cos(a),4*Math.sin(a),2],.38,.52,20);}
 const pmrem=new THREE.PMREMGenerator(renderer);scene.environment=pmrem.fromScene(environment,.015,.1,20).texture;
 for(const [pos,power] of [[[-2,3,4],2.2],[[3,1,-2],1.5],[[2,-2,3],1]]){const l=new THREE.DirectionalLight(0xffffff,power);l.position.fromArray(pos);scene.add(l);}scene.add(new THREE.HemisphereLight(0xffffff,0x4b3932,.18));
 function fit(){const half=radius*(current?.config.fitPadding||1.15)/Math.min(aspect,1);camera.left=-half*aspect;camera.right=half*aspect;camera.top=half;camera.bottom=-half;host.dataset.zoom=String(zoom);host.dataset.model=current?.id||'';host.dataset.cacheSize=String(cache.size);camera.zoom=zoom;camera.updateProjectionMatrix();dirty=true;}
 watchSize(host,renderer,camera,a=>{aspect=a;fit()});
 function orient(id){if(id==='J001')return new THREE.Quaternion();const c=new THREE.PerspectiveCamera();c.position.fromArray(id==='J003'?[.85,1.1,1.25]:id==='J004'?[.25,1.3,1.4]:[.4,.35,1.6]);c.lookAt(0,0,0);return c.quaternion.clone().invert();}
 // All four details share one renderer and one download queue. Warm resources
 // in a separate scene without replacing the product the visitor is viewing.
 const preloadQueue=[];let processingPreloads=false;
 async function prepareScene(root){
  const warming=new THREE.Scene();warming.environment=scene.environment;
  for(const child of scene.children)if(child.isLight)warming.add(child.clone());
  const position=root.position.clone();warming.add(root);warming.updateMatrixWorld(true);
  const bounds=new THREE.Box3().setFromObject(root),center=bounds.getCenter(new THREE.Vector3()),size=bounds.getSize(new THREE.Vector3()).length()/2;
  root.position.sub(center);
  const half=Math.max(size*1.2,.001),warmCamera=new THREE.OrthographicCamera(-half,half,half,-half,.00001,20);warmCamera.position.z=2;
  const target=new THREE.WebGLRenderTarget(32,32);
  try{
   await renderer.compileAsync(warming,warmCamera);
   if(renderer.disposed||renderer.getContext().isContextLost())throw Error('3D context unavailable');
   const previous=renderer.getRenderTarget();
   try{renderer.setRenderTarget(target);renderer.render(warming,warmCamera);}finally{renderer.setRenderTarget(previous);}
  }finally{target.dispose();warming.remove(root);root.position.copy(position);}
 }
 async function processPreloads(){
  if(processingPreloads)return;processingPreloads=true;
  while(preloadQueue.length){
   const job=preloadQueue.shift();
   try{
    if(renderer.disposed)throw Error('3D viewer was replaced');
    const root=(await loader.loadAsync(job.product.detailModelUrl)).scene;
    root.traverse(o=>{if(o.isMesh){o.frustumCulled=false;for(const m of Array.isArray(o.material)?o.material:[o.material])m.envMapIntensity=/Stone|Accent/.test(m.name)?1.3:1;}});
    await prepareScene(root);cache.set(job.product.id,root);
    host.dataset.cacheSize=String(cache.size);host.dataset.preloadedModels=[...cache.keys()].join(',');
    if(host.dataset.preloadFailures){host.dataset.preloadFailures=host.dataset.preloadFailures.split(',').filter(id=>!cache.has(id)).join(',');if(!host.dataset.preloadFailures&&host.dataset.preloadState==='partial')host.dataset.preloadState='ready';}
    job.resolve(root);
   }catch(error){job.reject(error);}finally{pending.delete(job.product.id);}
  }
  processingPreloads=false;
 }
 function preload(p,priority=false){
  if(cache.has(p.id))return Promise.resolve(cache.get(p.id));
  if(pending.has(p.id)){
   const index=preloadQueue.findIndex(job=>job.product.id===p.id);
   if(priority&&index>0)preloadQueue.unshift(...preloadQueue.splice(index,1));
   return pending.get(p.id);
  }
  let resolve,reject;const promise=new Promise((yes,no)=>{resolve=yes;reject=no;});
  pending.set(p.id,promise);const job={product:p,resolve,reject};
  if(priority)preloadQueue.unshift(job);else preloadQueue.push(job);
  processPreloads();return promise;
 }
 function endTransition(){if(!transition)return;scene.remove(transition.group);transition.materials.forEach(m=>m.dispose());transition=null;pivot.visible=true;restoreMaterials();dirty=true;}
function prepareTransition(source,sourceCamera){endTransition();if(!current)return;source.updateWorldMatrix(true,true);const clone=source.clone(true),materials=[];clone.visible=true;clone.position.set(0,0,0);clone.quaternion.copy(source.getWorldQuaternion(new THREE.Quaternion())).premultiply(sourceCamera.quaternion.clone().invert());clone.scale.setScalar(1);clone.traverse(o=>{if(o.isMesh){o.material=Array.isArray(o.material)?o.material.map(m=>m.clone()):o.material.clone();for(const m of Array.isArray(o.material)?o.material:[o.material]){m.userData.savedOpacity=m.opacity;m.transparent=true;materials.push(m);}}});const group=new THREE.Group();group.add(clone);group.updateMatrixWorld(true);const box=new THREE.Box3().setFromObject(clone),c=box.getCenter(new THREE.Vector3()),sr=box.getSize(new THREE.Vector3()).length()/2;clone.position.sub(c);group.scale.setScalar(baseRadius/sr);scene.add(group);transition={group,materials};pivot.visible=false;dirty=true;}
function blendTransition(t){if(!transition)return;if(t>=1){endTransition();return;}transition.materials.forEach(m=>m.opacity=m.userData.savedOpacity*(1-t));pivot.visible=t>0;current.root.traverse(o=>{if(o.isMesh){for(const m of Array.isArray(o.material)?o.material:[o.material]){if(m.userData.savedOpacity===undefined){m.userData.savedOpacity=m.opacity;m.userData.savedTransparent=m.transparent;}m.opacity=m.userData.savedOpacity*t;m.transparent=true;}}});dirty=true;}
function restoreMaterials(){current?.root.traverse(o=>{if(o.isMesh)for(const m of Array.isArray(o.material)?o.material:[o.material])if(m.userData.savedOpacity!==undefined){m.opacity=m.userData.savedOpacity;m.transparent=m.userData.savedTransparent;}});}
function reset(){if(!current)return;zoom=1;pivot.quaternion.copy(defaultQ);fit();}
 function rotate(dx,dy){pivot.quaternion.premultiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,1,0),dx)).premultiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(1,0,0),dy)).normalize();dirty=true;}
 function frame(){if(renderer.disposed)return;requestAnimationFrame(frame);if(active&&!document.hidden&&dirty){renderer.render(scene,camera);dirty=false;}}requestAnimationFrame(frame);
 return {renderer,canvas,preload,prepareTransition,blendTransition,endTransition,get loaded(){return !!current},get id(){return current?.id},async load(p){endTransition();const ticket=++generation;const root=await preload(p,true);if(ticket!==generation)return false;pivot.clear();root.position.set(0,0,0);root.updateMatrixWorld(true);const box=new THREE.Box3().setFromObject(root);center=box.getCenter(new THREE.Vector3());baseRadius=box.getSize(new THREE.Vector3()).length()/2;radius=baseRadius;root.position.copy(center).negate();pivot.add(root);current={id:p.id,root,config:p};defaultQ=p.defaultRotation?new THREE.Quaternion().fromArray(p.defaultRotation):orient(p.id);pendant=false;reset();return true;},cancel(){generation++;active=false},setActive(v){active=v;dirty=true},rotate,zoomBy(f){zoom=THREE.MathUtils.clamp(zoom*f,current?.config.minZoom||.75,current?.config.maxZoom||2.5);fit()},reset,spin(t){pivot.quaternion.copy(defaultQ).premultiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,1,0),t*Math.PI*2));dirty=true},focus(close){if(current?.id!=='J001')return;pendant=close;current.root.position.copy(close?new THREE.Vector3(-.000001339,-.073023155,.020015823):center).negate();radius=close?.009:baseRadius;defaultQ=close?new THREE.Quaternion().setFromEuler(new THREE.Euler(.06,-.22,0)):new THREE.Quaternion().fromArray(current.config.defaultRotation);reset()},getState(){return{quaternion:pivot.quaternion.toArray(),zoom,pendant}},setState(s){if(!s)return;if(s.pendant)this.focus(true);pivot.quaternion.fromArray(s.quaternion);zoom=THREE.MathUtils.clamp(s.zoom,.75,2.5);fit()},get cacheSize(){return cache.size}};
}
