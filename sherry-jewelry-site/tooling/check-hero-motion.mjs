import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import * as THREE from '../dist/vendor/three.module.js';
const source=fs.readFileSync(new URL('../dist/engines.js',import.meta.url),'utf8');
const settings=JSON.parse(fs.readFileSync(new URL('../dist/data/settings.json',import.meta.url),'utf8'));
const begin=source.indexOf('function frame(t){');
const end=source.indexOf('\n}\n\nexport async function createStage',begin);
const pose=source.slice(source.indexOf('function pose(){'),source.indexOf('\nwatchSize(host'));
const camera=new THREE.OrthographicCamera(-5,5,3.8,-3.8,.1,100);camera.zoom=1.1;
const box={left:0,top:0,width:800,height:630};
const context={THREE:{...THREE,Raycaster:class{setFromCamera(){}intersectObject(){return [{}]}}},
 camera,host:{clientHeight:630},canvas:{width:800,height:630,getBoundingClientRect:()=>box},
 model:{position:new THREE.Vector3()},target:new THREE.Vector3(0,2.85,-1.1),rad:THREE.MathUtils.degToRad,
 motion:settings.scenes.hero.motion,renderer:{render(){}},scene:{},document:{hidden:false},
 reduced:{matches:false},reflection:{},context:{drawImage(){}},requestAnimationFrame(fn){context.tick=fn},onPose:undefined};
vm.createContext(context);
context.engine=vm.runInContext(`(()=>{let azimuth=0,elevation=8.002663,dirty=true,active=true,dragging=false,hoverTarget=0,hoverOffset=0,lastFrame=0,floatPhase=0,lastReflection=0;
function unitsPerPixel(){return (camera.top-camera.bottom)/camera.zoom/Math.max(1,host.clientHeight);}
${pose}\n${source.slice(begin,end)}})()`,context);
const samples=[];for(let t=1;t<=11001;t+=10){context.tick(t);samples.push({t,...context.engine.getState()});}
const min=Math.min(...samples.map(s=>s.floatOffsetPx)),max=Math.max(...samples.map(s=>s.floatOffsetPx));
assert.ok(Math.abs(max-min-12)<.01);
assert.ok(Math.abs(samples[550].floatOffsetPx-samples[0].floatOffsetPx)<.01);
context.engine.hover(650,300);for(let t=11011;t<=11201;t+=10)context.tick(t);
assert.ok(context.engine.getState().hoverOffset>.88, 'Hover responds within 200 ms');
for(let t=11211;t<=12011;t+=10)context.tick(t);
assert.ok(context.engine.getState().hoverOffset>.8);assert.ok(context.model.position.x>0);
const yaw=()=>THREE.MathUtils.radToDeg(Math.atan2(camera.position.x-context.target.x,camera.position.z-context.target.z));
assert.ok(Math.abs(yaw()-15)<.01, 'Hover reaches the right drag limit');
context.engine.hover(150,300);for(let t=12021;t<=13521;t+=10)context.tick(t);
assert.ok(context.engine.getState().hoverOffset<-.8);assert.ok(context.model.position.x<0);
assert.ok(Math.abs(yaw()+15)<.01, 'Hover reaches the left drag limit');
context.engine.setDragging(true);context.engine.drag(10000,10000);
assert.equal(context.engine.getState().azimuth,15);assert.equal(context.engine.getState().elevation,11);
const held=context.model.position.y;context.tick(13531);assert.equal(context.model.position.y,held);
context.engine.setDragging(false);context.engine.clearHover();for(let t=13541;t<=15541;t+=10)context.tick(t);
assert.ok(Math.abs(context.engine.getState().hoverOffset)<.001);
context.reduced.matches=true;context.tick(15551);assert.equal(context.model.position.length(),0);
console.log(JSON.stringify({floatTravelPx:max-min,periodMs:5500,hoverBothDirections:true,hoverYawLimitDegrees:15,hoverResponseMs:90,dragLimits:true,dragPausesFloat:true,reducedMotion:true}));
