import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
const canvas=document.querySelector('canvas'),renderer=new THREE.WebGLRenderer({canvas,antialias:true,preserveDrawingBuffer:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,1.8));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.0;renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.VSMShadowMap;
const scene=new THREE.Scene();scene.background=new THREE.Color('#eae5df');
const target=new THREE.Vector3(0,.177,-.015),camera=new THREE.OrthographicCamera(-.2,.2,.2,-.2,.001,10);let yaw=0,loaded=false;const productRoots={};let pendingFrame=false,mirror=null;
function draw(){if(pendingFrame)return;pendingFrame=true;requestAnimationFrame(()=>{if(mirror)mirror.update();renderer.render(scene,camera);pendingFrame=false;});}
const pmrem=new THREE.PMREMGenerator(renderer),env=new THREE.Scene();env.background=new THREE.Color().setRGB(.18,.19,.21);
function panel(pos,w,h,power,color=0xffffff){const o=new THREE.Mesh(new THREE.PlaneGeometry(w,h),new THREE.MeshBasicMaterial({color:new THREE.Color(color).multiplyScalar(power),side:THREE.DoubleSide}));o.position.set(...pos);o.lookAt(0,0,0);env.add(o)}
panel([-4,5,6],4,5,3);panel([5,3,3],2,5,2.3);panel([0,6,0],4,3,3.1,0xffe5b4);scene.environment=pmrem.fromScene(env,.035).texture;scene.environmentIntensity=.85;
const key=new THREE.DirectionalLight(0xfffaf4,1.55);key.position.set(-.28,.47,.38);key.target.position.copy(target);key.castShadow=true;key.shadow.mapSize.set(2048,2048);Object.assign(key.shadow.camera,{left:-.4,right:.4,top:.5,bottom:-.25,near:.01,far:1.5});key.shadow.bias=-.00001;key.shadow.normalBias=.00016;key.shadow.radius=5;key.shadow.blurSamples=8;scene.add(key,key.target);
const fill=new THREE.DirectionalLight(0xf0f4ff,.65);fill.position.set(.3,.32,.18);fill.target.position.copy(target);scene.add(fill,fill.target);
const warm=new THREE.DirectionalLight(0xffcf82,2.5);warm.position.set(0,.65,.025);warm.target.position.set(-.025,.18,-.015);warm.castShadow=true;warm.shadow.mapSize.set(2048,2048);Object.assign(warm.shadow.camera,{left:-.38,right:.38,top:.38,bottom:-.38,near:.01,far:1.2});warm.shadow.bias=-.000015;warm.shadow.normalBias=.00012;warm.shadow.radius=7;warm.shadow.blurSamples=8;scene.add(warm,warm.target);scene.add(new THREE.HemisphereLight(0xf1eee7,0xb6a28c,.6));
const overheadPool=new THREE.SpotLight(0xffc46b,.40,1,.56,.85,2);overheadPool.position.set(-.035,.52,.12);overheadPool.target.position.set(-.025,.17,-.005);scene.add(overheadPool,overheadPool.target);
const bounce=new THREE.DirectionalLight(0xffffff,1.8);bounce.position.set(0,.38,-.4);bounce.target.position.copy(target);scene.add(bounce,bounce.target);
const ground=new THREE.Mesh(new THREE.PlaneGeometry(5,5),new THREE.MeshStandardMaterial({color:0xeae5df,roughness:.95}));ground.rotation.x=-Math.PI/2;ground.position.y=.002;ground.receiveShadow=true;scene.add(ground);
function pose(){const a=THREE.MathUtils.degToRad(yaw),e=THREE.MathUtils.degToRad(19);camera.position.copy(target).add(new THREE.Vector3(Math.sin(a)*Math.cos(e),Math.sin(e),Math.cos(a)*Math.cos(e)).multiplyScalar(.9));camera.lookAt(target);camera.updateMatrixWorld();for(const b of document.querySelectorAll('[data-view]'))b.setAttribute('aria-pressed',Number(b.dataset.view)===yaw?'true':'false');document.querySelector('#rotation').value=yaw;document.querySelector('#angle').textContent=Math.round(yaw)+'°';draw();}
function resize(){const {width,height}=canvas.getBoundingClientRect(),aspect=width/height,vertical=.3804167/Math.min(1,aspect/.95);camera.left=-vertical*aspect/2;camera.right=vertical*aspect/2;camera.top=vertical/2;camera.bottom=-vertical/2;camera.updateProjectionMatrix();renderer.setSize(width,height,false);pose();}window.addEventListener('resize',resize);resize();
for(const b of document.querySelectorAll('[data-view]'))b.addEventListener('click',()=>{yaw=Number(b.dataset.view);pose()});
document.querySelector('#rotation').addEventListener('input',e=>{yaw=Number(e.target.value);pose()});
let drag=null;canvas.addEventListener('pointerdown',e=>{drag=[e.clientX,yaw];canvas.setPointerCapture(e.pointerId);canvas.classList.add('dragging')});canvas.addEventListener('pointermove',e=>{if(drag){yaw=THREE.MathUtils.clamp(drag[1]+(e.clientX-drag[0])*180/canvas.clientWidth,-90,90);pose()}});for(const name of ['pointerup','pointercancel','lostpointercapture'])canvas.addEventListener(name,()=>{drag=null;canvas.classList.remove('dragging')});
const loader=new GLTFLoader();let config,fixed;
function configure(root,isProduct=false){root.traverse(o=>{if(!o.isMesh)return;o.castShadow=!o.name.includes('Background_');o.receiveShadow=!o.name.includes('Background_');for(const m of Array.isArray(o.material)?o.material:[o.material]){if(m.name.includes('lace')){m.alphaTest=.45;m.transparent=false;m.side=THREE.DoubleSide;}if(!isProduct&&m.name.includes('champagne')){m.metalness=1;m.roughness=m.name.includes('satin')?.19:.14;m.envMapIntensity=1.15;}m.needsUpdate=true;}});}
function makeSoftMirror(source){
 scene.updateMatrixWorld(true);const box=new THREE.Box3().setFromObject(source),center=box.getCenter(new THREE.Vector3()),size=box.getSize(new THREE.Vector3()),planeZ=box.max.z+.0001;
 source.visible=false;
 const buffer=new THREE.WebGLRenderTarget(1024,1024,{type:THREE.HalfFloatType,minFilter:THREE.LinearFilter,magFilter:THREE.LinearFilter,depthBuffer:true});
 const reflectedCamera=new THREE.OrthographicCamera(),projection=new THREE.Matrix4(),bias=new THREE.Matrix4().set(.5,0,0,.5,0,.5,0,.5,0,0,.5,.5,0,0,0,1);
 const material=new THREE.ShaderMaterial({uniforms:{reflection:{value:buffer.texture},projection:{value:projection},softness:{value:.006}},vertexShader:`uniform mat4 projection; varying vec4 mirrorCoord; void main(){vec4 world=modelMatrix*vec4(position,1.0);mirrorCoord=projection*world;gl_Position=projectionMatrix*viewMatrix*world;}`,fragmentShader:`uniform sampler2D reflection; uniform float softness; varying vec4 mirrorCoord; void main(){vec2 uv=mirrorCoord.xy/mirrorCoord.w;vec3 c=vec3(0.0);float weight=0.0;for(int x=-2;x<=2;x++){for(int y=-2;y<=2;y++){float w=exp(-float(x*x+y*y)*.45);c+=texture2D(reflection,uv+vec2(float(x),float(y))*softness).rgb*w;weight+=w;}}c/=weight;gl_FragColor=vec4(c*1.22+vec3(.22),1.0);\n #include <tonemapping_fragment>\n #include <colorspace_fragment>\n}`});
 const disc=new THREE.Mesh(new THREE.CircleGeometry(1,128),material);disc.name='Soft live mirror reflection';disc.position.set(center.x,center.y,planeZ);disc.scale.set(size.x/2,size.y/2,1);scene.add(disc);
 const background=[];fixed.traverse(o=>{if(o.isMesh&&o.name.includes('Background_'))background.push(o)});
 return {update(){
  if(camera.position.z<=planeZ+.001)return;
  reflectedCamera.copy(camera);reflectedCamera.position.z=2*planeZ-camera.position.z;
  const reflectedTarget=target.clone();reflectedTarget.z=2*planeZ-target.z;reflectedCamera.lookAt(reflectedTarget);reflectedCamera.updateMatrixWorld();reflectedCamera.updateProjectionMatrix();
  projection.copy(bias).multiply(reflectedCamera.projectionMatrix).multiply(reflectedCamera.matrixWorldInverse);
  const visibility=background.map(o=>o.visible);background.forEach(o=>o.visible=false);disc.visible=false;
  const previous=renderer.getRenderTarget(),shadowUpdate=renderer.shadowMap.autoUpdate;renderer.shadowMap.autoUpdate=false;
  renderer.setRenderTarget(buffer);renderer.render(scene,reflectedCamera);renderer.setRenderTarget(previous);renderer.shadowMap.autoUpdate=shadowUpdate;
  background.forEach((o,i)=>o.visible=visibility[i]);disc.visible=true;
 }};
}
try{config=await(await fetch('../product-placement.json')).json();fixed=(await loader.loadAsync('../main-display-scene.glb')).scene;configure(fixed);scene.add(fixed);
for(const [key,p] of Object.entries(config.products)){const root=(await loader.loadAsync('../'+p.file)).scene,anchor=fixed.getObjectByName(p.anchor);if(!anchor)throw Error('Missing anchor '+p.anchor);configure(root,true);anchor.add(root);productRoots[key]=root;}
let mirrorSource;fixed.traverse(o=>{if(o.isMesh&&(Array.isArray(o.material)?o.material:[o.material]).some(m=>m.name.includes('softened silver mirror')))mirrorSource=o});
// Populate soft shadows once before reflecting the completed scene.
renderer.render(scene,camera);if(mirrorSource)mirror=makeSoftMirror(mirrorSource);
loaded=true;draw();document.querySelector('#status').hidden=true;
}catch(e){document.querySelector('#status').textContent='预览加载失败，请刷新重试';console.error(e);}
draw();
