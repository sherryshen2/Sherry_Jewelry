const $=id=>document.getElementById(id),reduced=matchMedia('(prefers-reduced-motion: reduce)'),mobile=()=>matchMedia('(pointer:coarse)').matches||innerWidth<768;
const products=await fetch('data/products.json').then(r=>r.json()),byId=Object.fromEntries(products.map(p=>[p.id,p]));
let engines,hero,stage,detail,heroPromise,stagePromise,detailPromise,view='home',selected=null,preview=null,photoMode=false,userPhoto=false,token=0,origin=null,returnFocus=null,hoverTimer,leaveTimer,prefetchTimer,entry=null,closing=false,transitionToken=0,preloading=false,needsEnter=true,detailContextLost=false;
const events=[];function event(type,data={}){events.push({type,...data,time:Date.now()});if(events.length>100)events.shift();window.dispatchEvent(new CustomEvent('sherry:event',{detail:{type,...data}}));}event('hero_view');
const dialog=$('product-dialog'),list=$('jewelry-list'),visual=$('product-visual');
function setImage(img,src,alt){img.classList.remove('photo-error');img.alt=alt;img.src=src;}
function photoError(e){e.target.classList.add('photo-error');e.target.alt='Photo unavailable';if(e.target.id==='detail-photo'){$('detail-status').textContent='Photo unavailable';$('photo-retry').hidden=false;}event('asset_error',{assetId:e.target.src,stage:'photo'});}
document.querySelectorAll('img').forEach(img=>img.addEventListener('error',photoError));
function buttonPiece(p,cls){const b=document.createElement('button');b.className=cls;b.dataset.id=p.id;b.setAttribute('aria-label','View '+p.name);const img=document.createElement('img');img.loading='lazy';img.decoding='async';setImage(img,cls==='list-piece'?p.photoUrl:p.thumbnailUrl,p.photoAlt);img.addEventListener('error',photoError);b.append(img);return b;}
products.forEach((p,i)=>{const b=buttonPiece(p,'list-piece');const label=document.createElement('span');label.className='eyebrow';label.textContent=`0${i+1} / ${p.type.toUpperCase()}`;const name=document.createElement('strong');name.textContent=p.name;b.append(label,name);b.onclick=()=>{openProduct(p.id,b,'list');list.close()};$('list-grid').append(b);
const m=buttonPiece(p,'mobile-piece');m.append(document.createTextNode(p.type[0].toUpperCase()+p.type.slice(1)));m.setAttribute('aria-pressed','false');m.onclick=()=>selectPiece(p.id,m,true);$('mobile-pieces').append(m);
const h=document.createElement('button');h.className='hotspot';h.dataset.id=p.id;h.setAttribute('aria-label',p.name);h.textContent='◇';h.onfocus=()=>showPreview(p.id);h.onblur=()=>scheduleHide();h.onclick=()=>openProduct(p.id,h,'keyboard');$('hotspots').append(h);});
async function engineModule(){return engines??=await import('./engines.js');}
let sceneWarmup,detailWarmup;
function backgroundTurn(){
 return new Promise(resolve=>{
  const wait=()=>{
   if(document.hidden||dialog.open)return;
   document.removeEventListener('visibilitychange',wait);window.removeEventListener('sherry:resume-background',wait);
   const finish=()=>{if(document.hidden||dialog.open)listen();else resolve();};
   if('requestIdleCallback'in window)requestIdleCallback(finish,{timeout:1200});else setTimeout(finish,50);
  };
  const listen=()=>{document.addEventListener('visibilitychange',wait);window.addEventListener('sherry:resume-background',wait);wait();};listen();
 });
}
function warmCollection(){
 return sceneWarmup??=(async()=>{await new Promise(resolve=>setTimeout(resolve,600));await backgroundTurn();await initStage();})();
}
function warmDetails(){
 if(detailWarmup)return detailWarmup;
 detailWarmup=(async()=>{
  $('detail-host').dataset.preloadState='loading';
  const failures=[];
  for(const p of products){
   await backgroundTurn();
   try{
    const d=await initDetail();await d.preload(p);
    const photo=new Image();photo.decoding='async';photo.src=window.localAsset?window.localAsset(p.photoUrl):p.photoUrl;await photo.decode().catch(()=>{});
    event('detail_preloaded',{productId:p.id});
   }catch(e){failures.push(p.id);event('asset_error',{assetId:p.id,stage:'detail_preload',errorType:e.message});}
  }
  $('detail-host').dataset.preloadState=detail?.cacheSize===products.length&&!detailContextLost?'ready':failures.length?'partial':'unavailable';
  $('detail-host').dataset.preloadFailures=failures.join(',');
  event('details_preloaded',{failed:failures});
 })();
 return detailWarmup;
}
async function initHero(){if(heroPromise)return heroPromise;$('hero-status').textContent='Bringing the boutique to life…';$('hero-retry').hidden=true;$('boutique-host').dataset.loadStartedMs=String(Math.round(performance.now()));heroPromise=(async()=>{try{const mod=await engineModule();hero=await mod.createHero($('boutique-host'));hero.setActive(view==='home'&&!dialog.open);$('boutique-host').classList.add('is-ready');$('boutique-poster').classList.add('ready');$('hero-status').textContent='';$('boutique-host').dataset.readyMs=String(Math.round(performance.now()));event('hero_ready');warmCollection();return hero;}catch(e){cleanupHost($('boutique-host'));$('boutique-host').classList.remove('is-ready');$('boutique-poster').classList.remove('ready');$('hero-status').textContent='Explore the boutique in photos';$('hero-retry').hidden=false;event('asset_error',{assetId:'boutique',errorType:e.message});heroPromise=null;}})();return heroPromise;}
let heroTimer,heroIdle;
function cancelScheduledHero(){clearTimeout(heroTimer);if(heroIdle!==undefined)window.cancelIdleCallback?.(heroIdle);heroIdle=undefined;}
function scheduleHero(){cancelScheduledHero();if(hero||heroPromise||view!=='home')return;heroTimer=setTimeout(()=>{const start=()=>{heroIdle=undefined;if(view==='home'&&!document.hidden)initHero();};if('requestIdleCallback'in window)heroIdle=requestIdleCallback(start,{timeout:1500});else start();},600);}
async function showStaticFirst(){const poster=$('boutique-poster');try{await poster.decode();}catch{}await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));$('app-shell').dataset.staticReadyMs=String(Math.round(performance.now()));event('static_ready');if(window.parent!==window)window.parent.postMessage({type:'sherry:static-ready'},location.origin);scheduleHero();}
document.addEventListener('visibilitychange',()=>{if(document.hidden)cancelScheduledHero();else scheduleHero();});
let stageProgressHideTimer;
function stageProgress(value){const bar=$('display-progress');bar.value=Math.max(bar.value,Math.min(100,value));}
async function initStage(){
 if(stagePromise)return stagePromise;
 const started=performance.now();clearTimeout(stageProgressHideTimer);
 $('collection').classList.add('is-loading');$('collection').classList.remove('is-photos');
 $('display-host').classList.remove('is-ready');$('display-host').setAttribute('aria-busy','true');
 $('display-poster').classList.remove('ready');$('hotspots').inert=true;
 $('display-loading').hidden=false;$('display-progress').hidden=false;$('display-progress').value=0;
 $('display-status').textContent='Loading the collection…';$('display-retry').hidden=true;
 stagePromise=(async()=>{try{
  const mod=await engineModule();stage=await mod.createStage($('display-host'),products,updateProjection,stageProgress);
  stage.setActive(view==='collection'&&!dialog.open);stageProgress(100);
  $('display-host').classList.add('is-ready');$('display-host').setAttribute('aria-busy','false');
  $('display-poster').classList.add('ready');$('hotspots').inert=false;
  $('collection').classList.remove('is-loading','is-photos');
  stageProgressHideTimer=setTimeout(()=>{$('display-loading').hidden=true;$('display-status').textContent='';},350);
  updateProjection();$('display-host').dataset.readyMs=String(Math.round(performance.now()));
  event('display_ready',{duration:performance.now()-started});warmDetails();return stage;
 }catch(e){
  $('collection').classList.remove('is-loading');$('collection').classList.add('is-photos');
  $('display-host').setAttribute('aria-busy','false');$('display-progress').hidden=true;
  $('display-status').textContent='Photo mode · Explore the four pieces below';$('display-retry').hidden=false;
  event('asset_error',{assetId:'display',errorType:e.message});stagePromise=null;
 }})();return stagePromise;
}
async function initDetail(){if(detailContextLost){cleanupHost($('detail-host'));detail=null;detailPromise=null;detailContextLost=false;}if(detailPromise)return detailPromise;detailPromise=(async()=>{const mod=await engineModule();detail=mod.createDetail($('detail-host'));bindDetail();return detail;})().catch(e=>{detailPromise=null;throw e});return detailPromise;}
function cleanupHost(host){engines?.disposeHost(host);host.querySelectorAll('canvas').forEach(c=>c.remove());}
$('hero-retry').onclick=()=>{hero?.setActive(false);hero=null;heroPromise=null;cleanupHost($('boutique-host'));initHero()};$('display-retry').onclick=()=>{stage?.setActive(false);stage=null;stagePromise=null;cleanupHost($('display-host'));initStage()};
function updateProjection(){if(!stage)return;const wrap=$('hotspots').getBoundingClientRect();document.querySelectorAll('.hotspot').forEach(b=>{const p=stage.project(b.dataset.id);b.style.left=p.x-wrap.left+'px';b.style.top=p.y-wrap.top+'px';});if(preview)positionPreview(preview);}
function positionPreview(id){const card=$('preview-card'),p=stage?.project(id),w=card.offsetWidth||184,h=card.offsetHeight||240;let x,y;if(p&&view==='collection'){x=p.x-w/2;y=p.top-h-12;if(y<90){x=p.x+p.width/2+16;y=Math.max(90,p.y-h/2);}}else{const b=document.querySelector(`.mobile-piece[data-id="${id}"]`).getBoundingClientRect();x=b.left+b.width/2-w/2;y=b.top-h-12;}card.style.left=Math.max(16,Math.min(innerWidth-w-16,x))+'px';card.style.top=Math.max(80,Math.min(innerHeight-h-16,y))+'px';}
function showPreview(id){if(dialog.open||view!=='collection')return;clearTimeout(leaveTimer);clearTimeout(hoverTimer);if(preview!==id){preview=id;stage?.hover(id);const p=byId[id];setImage($('preview-photo'),p.photoUrl,p.photoAlt);$('preview-name').textContent=p.name;$('preview-card').hidden=false;event('product_preview',{productId:id,inputType:mobile()?'touch':'pointer'});document.querySelectorAll('.mobile-piece').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.id===id)));clearTimeout(prefetchTimer);prefetchTimer=setTimeout(async()=>{if(preloading||navigator.connection?.saveData)return;preloading=true;try{const d=await initDetail();await d.preload(p);}catch{}finally{preloading=false}},300);}positionPreview(id);}
function hidePreview(){clearTimeout(hoverTimer);clearTimeout(leaveTimer);clearTimeout(prefetchTimer);preview=null;stage?.hover(null);$('preview-card').hidden=true;document.querySelectorAll('.mobile-piece').forEach(b=>b.setAttribute('aria-pressed','false'));}
function scheduleHide(){clearTimeout(leaveTimer);leaveTimer=setTimeout(hidePreview,140)}
$('preview-card').onpointerenter=()=>clearTimeout(leaveTimer);$('preview-card').onpointerleave=scheduleHide;$('preview-card').onclick=()=>preview&&openProduct(preview,$('preview-card'),'preview');
function selectPiece(id,trigger,touch=false){if(touch&&preview!==id){showPreview(id);}else openProduct(id,trigger,'display');}
async function navigateCollection(source='button',push=true){if(view==='collection')return;const ticket=++transitionToken;cancelScheduledHero();view='collection';if(push)history.pushState({sherry:true,view:'collection'},'');event('explore_click',{source});$('home').classList.add('leaving');initStage();await new Promise(r=>setTimeout(r,reduced.matches?0:220));if(ticket!==transitionToken)return;$('home').hidden=true;$('home').classList.remove('leaving');$('collection').hidden=false;$('collection').classList.add('page-enter');document.body.classList.add('in-collection');hero?.setActive(false);stage?.setActive(true);$('back-home').focus({preventScroll:true});setTimeout(()=>{$('collection').classList.remove('page-enter');},reduced.matches?0:3000);}
function showHome(){transitionToken++;hidePreview();view='home';$('collection').hidden=true;$('home').hidden=false;$('home').classList.remove('leaving');document.body.classList.remove('in-collection');hero?.setActive(true);stage?.setActive(false);scheduleHero();$('explore').focus({preventScroll:true});}
$('explore').onclick=()=>navigateCollection();$('back-home').onclick=()=>history.state?.view==='collection'?history.back():showHome();$('brand-home').onclick=()=>{if(dialog.open)closeProduct();if(view!=='home'){history.pushState({sherry:true,view:'home'},'');showHome()}};
function openList(){hidePreview();list.showModal();list.querySelector('button').focus()};$('header-collection').onclick=async()=>{await navigateCollection();openList()};$('list-close').onclick=()=>list.close();list.addEventListener('click',e=>{if(e.target===list){const r=list.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)list.close();}});
function bindScene(host,kind){let pointer=null;host.addEventListener('pointerdown',e=>{if(dialog.open||e.button>0)return;pointer={id:e.pointerId,startX:e.clientX,startY:e.clientY,x:e.clientX,y:e.clientY,moved:0,touch:e.pointerType==='touch'};host.setPointerCapture(e.pointerId);if(kind==='hero')hero?.setDragging(true)});host.addEventListener('pointermove',e=>{const engine=kind==='hero'?hero:stage;if(pointer?.id===e.pointerId){pointer.moved=Math.max(pointer.moved,Math.hypot(e.clientX-pointer.startX,e.clientY-pointer.startY));const dx=e.clientX-pointer.x,dy=e.clientY-pointer.y;pointer.x=e.clientX;pointer.y=e.clientY;if(pointer.moved>(pointer.touch?10:6)){hidePreview();engine?.drag(dx,dy);host.style.cursor='grabbing';}}else if(kind==='hero'&&e.pointerType==='mouse'&&hero){hero.hover(e.clientX,e.clientY);host.style.cursor=hero.hit(e.clientX,e.clientY)?'grab':'default';}else if(kind==='display'&&e.pointerType!=='touch'&&stage){const id=stage.hit(e.clientX,e.clientY);host.style.cursor=id?'pointer':'grab';if(id){clearTimeout(leaveTimer);if(preview!==id){clearTimeout(hoverTimer);hoverTimer=setTimeout(()=>showPreview(id),100)}}else{clearTimeout(hoverTimer);scheduleHide();}}});host.addEventListener('pointerup',e=>{if(!pointer||pointer.id!==e.pointerId)return;const p=pointer;pointer=null;hero?.setDragging(false);host.style.cursor='grab';if(p.moved<(p.touch?10:6)){if(kind==='hero'){if(!hero||hero.hit(e.clientX,e.clientY))navigateCollection('boutique')}else{const id=stage?.hit(e.clientX,e.clientY);if(id)selectPiece(id,document.querySelector(`.hotspot[data-id="${id}"]`),p.touch);else hidePreview();}}});for(const type of ['pointercancel','lostpointercapture'])host.addEventListener(type,()=>{pointer=null;hero?.setDragging(false)});host.addEventListener('pointerleave',()=>{if(kind==='hero')hero?.clearHover();if(kind==='display'&&!pointer)scheduleHide()});}
bindScene($('boutique-host'),'hero');bindScene($('display-host'),'display');$('boutique-host').addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();navigateCollection('boutique')}if(e.key.startsWith('Arrow')){e.preventDefault();hero?.drag(e.key==='ArrowLeft'?-30:e.key==='ArrowRight'?30:0,e.key==='ArrowUp'?-30:30)}});
function validBuy(p){try{const u=new URL(p.buyUrl);return u.protocol==='https:'&&u.hostname==='shopee.sg'}catch{return false}}
function updateMode(){const ready=detail?.id===selected;photoMode=userPhoto||!ready;$('detail-host').hidden=photoMode;$('detail-photo').hidden=!photoMode;$('toggle-photo').textContent=photoMode?'View 3D':'View photo';for(const id of ['zoom-in','zoom-out','reset-detail'])$(id).disabled=photoMode;$('necklace-controls').hidden=selected!=='J001'||photoMode;detail?.setActive(dialog.open&&!photoMode);}
async function loadCurrent(p,ticket){$('detail-status').textContent='Loading 3D…';$('retry-detail').hidden=true;const slow=setTimeout(()=>{if(ticket===token&&selected){$('detail-status').textContent='Showing photo · 3D is still loading';}},3000);const timeout=setTimeout(()=>{if(ticket===token&&selected){$('detail-status').textContent='3D unavailable · View the original photo';$('retry-detail').hidden=false;userPhoto=true;updateMode();}},15000);try{const d=await initDetail();if(ticket!==token)return;await d.load(p);if(ticket!==token||!dialog.open)return;clearTimeout(timeout);$('detail-status').textContent='';updateMode();if(!userPhoto&&needsEnter){startEntry();needsEnter=false;}event('product_ready',{productId:p.id});}catch(e){if(ticket!==token)return;userPhoto=true;$('detail-status').textContent='3D unavailable · View the original photo';$('retry-detail').hidden=false;updateMode();event('asset_error',{assetId:p.id,stage:'detail',errorType:e.message});}finally{clearTimeout(slow);clearTimeout(timeout);}}
function openProduct(id,trigger,source='display',push=true){if(!byId[id]||closing||selected===id&&dialog.open)return;const p=byId[id];returnFocus=trigger||document.querySelector(`.hotspot[data-id="${id}"]`);origin=stage&&source!=='list'?stage.project(id):(()=>{const r=trigger?.getBoundingClientRect();return r?{x:r.left+r.width/2,y:r.top+r.height/2,width:r.width,height:r.height}:null})();hidePreview();if(selected)stage?.hide(selected,false);selected=id;token++;userPhoto=false;needsEnter=true;entry=null;$('detail-host').style.transform='';$('piece-number').textContent=id;$('product-type').textContent=p.type.toUpperCase();$('product-name').textContent=p.name;setImage($('detail-photo'),p.photoUrl,p.photoAlt);$('photo-retry').hidden=true;$('buy-now').textContent=validBuy(p)?'Buy Now ⟶':'Temporarily unavailable';if(validBuy(p))$('buy-now').href=p.buyUrl;else $('buy-now').removeAttribute('href');$('buy-now').target=mobile()?'_self':'_blank';$('full-necklace').setAttribute('aria-pressed','true');$('pendant-detail').setAttribute('aria-pressed','false');if(!dialog.open)dialog.showModal();document.body.style.overflow='hidden';$('app-shell').inert=true;hero?.setActive(false);stage?.setActive(false);$('close-product').focus();if(push)history.pushState({sherry:true,view:'collection',product:id},'');updateMode();loadCurrent(p,token);event('product_open',{productId:id,source});}
function finishClose(){if(!dialog.open)return;detail?.endTransition();const id=selected;entry=null;token++;selected=null;detail?.cancel();dialog.close();window.dispatchEvent(new Event('sherry:resume-background'));$('app-shell').inert=false;document.body.style.overflow='';stage?.hide(id,false);stage?.setActive(view==='collection');hero?.setActive(view==='home');clearParticles();visual.style.transform='';visual.style.opacity='';closing=false;const focus=returnFocus?.isConnected&&!returnFocus.hidden?returnFocus:document.querySelector(`.hotspot[data-id="${id}"]`);if(focus?.closest('#jewelry-list'))$('header-collection').focus();else focus?.focus({preventScroll:true});hidePreview();}
function closeProduct(useHistory=true){if(!dialog.open||closing)return;closing=true;token++;const closeTicket=token;entry=null;clearParticles();const duration=reduced.matches?150:330;const target=stage?.project(selected)||origin,r=visual.getBoundingClientRect(),dx=target?target.x-r.left-r.width/2:0,dy=target?target.y-r.top-r.height/2:0,scale=target?Math.max(.06,Math.min(.5,Math.max(target.width,target.height)/Math.min(r.width,r.height))):.9;visual.animate([{opacity:1,transform:'translate(0,0) scale(1)'},{opacity:0,transform:reduced.matches?'scale(1)':`translate(${dx}px,${dy}px) scale(${scale})`}],{duration,easing:'ease-in',fill:'none'}).finished.catch(()=>{}).then(()=>{if(token!==closeTicket)return;finishClose();if(useHistory&&history.state?.product)history.back();});}
$('close-product').onclick=()=>closeProduct();dialog.addEventListener('cancel',e=>{e.preventDefault();closeProduct()});let backdropDown=null;dialog.addEventListener('pointerdown',e=>{backdropDown=e.target===dialog?{x:e.clientX,y:e.clientY,id:e.pointerId}:null});dialog.addEventListener('pointerup',e=>{if(backdropDown&&e.target===dialog&&e.pointerId===backdropDown.id&&Math.hypot(e.clientX-backdropDown.x,e.clientY-backdropDown.y)<6)closeProduct();backdropDown=null});
function interrupt(){detail?.endTransition();if(entry){entry=null;clearParticles();$('detail-host').style.transform='';}event('product_interact',{productId:selected});}
let detailBound=false;function bindDetail(){if(detailBound)return;detailBound=true;const host=$('detail-host'),pointers=new Map();let previousSpan=0;host.addEventListener('pointerdown',e=>{interrupt();host.setPointerCapture(e.pointerId);pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});previousSpan=0});host.addEventListener('pointermove',e=>{if(!pointers.has(e.pointerId))return;const prev=pointers.get(e.pointerId),dx=e.clientX-prev.x,dy=e.clientY-prev.y;pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});if(pointers.size===1){const s=Math.PI*2/Math.min(host.clientWidth,host.clientHeight);detail.rotate(dx*s,dy*s)}else{const[a,b]=[...pointers.values()],span=Math.hypot(a.x-b.x,a.y-b.y);if(previousSpan>0&&span>0)detail.zoomBy(span/previousSpan);previousSpan=span;}});for(const type of ['pointerup','pointercancel','lostpointercapture'])host.addEventListener(type,e=>{pointers.delete(e.pointerId);previousSpan=0});host.addEventListener('wheel',e=>{e.preventDefault();interrupt();detail.zoomBy(Math.exp(-e.deltaY*.001))},{passive:false});host.addEventListener('keydown',e=>{const keys={ArrowLeft:[-.2,0],ArrowRight:[.2,0],ArrowUp:[0,-.2],ArrowDown:[0,.2]};if(keys[e.key]){e.preventDefault();interrupt();detail.rotate(...keys[e.key])}if(e.key==='+'||e.key==='='){e.preventDefault();interrupt();detail.zoomBy(1.15)}if(e.key==='-'){e.preventDefault();interrupt();detail.zoomBy(1/1.15)}});}
$('zoom-in').onclick=()=>{interrupt();detail?.zoomBy(1.15)};$('zoom-out').onclick=()=>{interrupt();detail?.zoomBy(1/1.15)};$('reset-detail').onclick=()=>{interrupt();detail?.reset()};$('toggle-photo').onclick=()=>{interrupt();userPhoto=!photoMode;if(!userPhoto&&detail?.id!==selected)loadCurrent(byId[selected],token);updateMode()};$('retry-detail').onclick=()=>{if(detailContextLost){detail?.cancel();cleanupHost($('detail-host'));detail=null;detailPromise=null;detailContextLost=false;}userPhoto=false;loadCurrent(byId[selected],token)};$('photo-retry').onclick=()=>{const p=byId[selected];setImage($('detail-photo'),p.photoUrl+'?retry='+Date.now(),p.photoAlt);$('photo-retry').hidden=true;$('detail-status').textContent='';};for(const[id,close]of[['full-necklace',false],['pendant-detail',true]])$(id).onclick=()=>{interrupt();detail?.focus(close);$('full-necklace').setAttribute('aria-pressed',String(!close));$('pendant-detail').setAttribute('aria-pressed',String(close));};
const particleCanvas=$('particles'),ctx=particleCanvas.getContext('2d');let particles=[];function clearParticles(){particles=[];ctx.clearRect(0,0,particleCanvas.width,particleCanvas.height)}
function startEntry(){
 clearParticles();
 if(stage&&origin&&returnFocus?.closest('#hotspots'))detail.prepareTransition(stage.productRoots[selected],stage.camera);
 if(reduced.matches){detail.endTransition();detail.spin(0);return}
 const r=visual.getBoundingClientRect();stage?.hide(selected,true);
 entry={elapsed:0,width:r.width,height:r.height,dx:origin?origin.x-r.left-r.width/2:0,dy:origin?origin.y-r.top-r.height/2:0,scale:origin?Math.max(.08,Math.min(.65,Math.max(origin.width,origin.height)/(Math.min(r.width,r.height)*.8))):.9};
 const dpr=Math.min(devicePixelRatio||1,2);particleCanvas.width=Math.round(r.width*dpr);particleCanvas.height=Math.round(r.height*dpr);ctx.setTransform(dpr,0,0,dpr,0,0);
 // A visible, short-lived cream halo accompanies arrival and the first full rotation.
 particles=Array.from({length:mobile()?48:88},(_,i)=>({a:Math.random()*Math.PI*2,birth:i<16?0:Math.random()*1000,life:1100+Math.random()*1400,size:1.4+Math.random()*1.7,opacity:.7+Math.random()*.3,spread:18+Math.random()*42,spark:i%5===0}));
}
function drawParticles(t,arrival){
 ctx.clearRect(0,0,particleCanvas.width,particleCanvas.height);
 const w=entry.width,h=entry.height;
 for(const p of particles){
  const age=t-p.birth;if(age<0||age>p.life)continue;
  const q=age/p.life,fade=Math.min(age/140,1)*Math.pow(1-q,1.15),alpha=p.opacity*fade;
  const rx=w*.22+q*p.spread,ry=h*.26+q*p.spread;
  const x=w/2+Math.cos(p.a)*rx+entry.dx*(1-arrival),y=h/2+Math.sin(p.a)*ry+entry.dy*(1-arrival)-q*18;
  const radius=p.size*(.8+.2*Math.sin(q*Math.PI)),glow=ctx.createRadialGradient(x,y,0,x,y,radius*4);
  glow.addColorStop(0,`rgba(243,229,196,${alpha*.65})`);glow.addColorStop(1,'rgba(243,229,196,0)');
  ctx.fillStyle=glow;ctx.beginPath();ctx.arc(x,y,radius*4,0,Math.PI*2);ctx.fill();
  ctx.fillStyle=`rgba(243,229,196,${alpha})`;ctx.beginPath();
  if(p.spark){ctx.moveTo(x,y-radius*2.5);ctx.lineTo(x+radius*.55,y-radius*.55);ctx.lineTo(x+radius*2.5,y);ctx.lineTo(x+radius*.55,y+radius*.55);ctx.lineTo(x,y+radius*2.5);ctx.lineTo(x-radius*.55,y+radius*.55);ctx.lineTo(x-radius*2.5,y);ctx.lineTo(x-radius*.55,y-radius*.55);ctx.closePath();}
  else ctx.arc(x,y,radius,0,Math.PI*2);
  ctx.fill();
 }
}
let last=performance.now();function animate(now){
 requestAnimationFrame(animate);const dt=Math.min(now-last,50);last=now;
 if(!entry||document.hidden||!dialog.open)return;
 entry.elapsed+=dt;const t=entry.elapsed;
 detail.blendTransition(Math.min(1,Math.max(0,(t-600)/150)));
 const arrival=1-Math.pow(1-Math.min(t/600,1),3);
 $('detail-host').style.transform=`translate(${entry.dx*(1-arrival)}px,${entry.dy*(1-arrival)}px) scale(${entry.scale+(1-entry.scale)*arrival})`;
 if(t>=750){const spin=Math.min((t-750)/1200,1);detail.spin(spin*spin*(3-2*spin));}
 drawParticles(t,arrival);
 if(t>=3500){entry=null;clearParticles();$('detail-host').style.transform='';}
}requestAnimationFrame(animate);
let lastBuy=0;$('buy-now').onclick=e=>{if(performance.now()-lastBuy<800){e.preventDefault();return}lastBuy=performance.now();event('buy_click',{productId:selected,platform:'Shopee'});if(mobile()){try{sessionStorage.setItem('sherry-return',JSON.stringify({id:selected,detail:detail?.getState(),stage:stage?.getState(),saved:Date.now()}))}catch{}}};
window.addEventListener('popstate',async e=>{if(dialog.open)finishClose();if(list.open)list.close();if(e.state?.view==='collection'){if(view!=='collection')await navigateCollection('history',false);if(e.state.product)openProduct(e.state.product,null,'history',false)}else showHome();});history.replaceState({sherry:true,view:'home'},'');
window.addEventListener('resize',()=>{updateProjection();if(preview)positionPreview(preview)});document.addEventListener('graphicslost',e=>{event('asset_error',{stage:'context_lost'});if(e.target.id==='detail-host'){detailContextLost=true;$('detail-host').dataset.preloadState='unavailable';if(!dialog.open)return;}if(dialog.open){detailContextLost=true;userPhoto=true;updateMode();$('detail-status').textContent='3D unavailable · View photo';$('retry-detail').hidden=false;}else if(view==='collection'){clearTimeout(stageProgressHideTimer);$('collection').classList.remove('is-loading');$('display-host').classList.remove('is-ready');$('display-loading').hidden=false;$('display-progress').hidden=true;$('collection').classList.add('is-photos');$('display-poster').classList.remove('ready');$('display-status').textContent='Photo mode';$('display-retry').hidden=false;}else{$('boutique-host').classList.remove('is-ready');$('boutique-poster').classList.remove('ready');$('hero-retry').hidden=false;}});
window.addEventListener('resize',()=>{if(selected){updateMode();$('buy-now').target=mobile()?'_self':'_blank';}});
showStaticFirst();
const nav=performance.getEntriesByType('navigation')[0];if(nav?.type==='back_forward'){try{const saved=JSON.parse(sessionStorage.getItem('sherry-return'));if(saved&&byId[saved.id]&&Date.now()-saved.saved<86400000){await navigateCollection('return');openProduct(saved.id,null,'return');const ticket=token;initDetail().then(async d=>{await d.load(byId[saved.id]);if(ticket===token){needsEnter=false;interrupt();d.setState(saved.detail);updateMode();}});initStage().then(s=>s?.setState(saved.stage));sessionStorage.removeItem('sherry-return');}}catch{}}
window.sherryDiagnostics=()=>({view,selected,preview,photoMode,heroLoaded:!!hero,stageLoaded:!!stage,detailLoaded:detail?.id,cacheSize:detail?.cacheSize||0,particles:particles.length,animating:!!entry,heroPose:hero?.getState(),stagePose:stage?.getState(),detailPose:detail?.getState(),events:events.slice(-10),products:products.map(p=>({id:p.id,photo:p.photoUrl,buyUrl:p.buyUrl}))});

// Keep keyboard traversal inside the active modal, including Shift+Tab at its first control.
document.addEventListener('keydown',e=>{const modal=dialog.open?dialog:list.open?list:null;if(!modal||e.key!=='Tab')return;const focusable=[...modal.querySelectorAll('button:not([disabled]),a[href],[tabindex="0"]')].filter(el=>!el.hidden&&el.getClientRects().length);if(!focusable.length){e.preventDefault();return;}const first=focusable[0],last=focusable[focusable.length-1],active=document.activeElement;if(e.shiftKey&&(active===first||!modal.contains(active))){e.preventDefault();last.focus();}else if(!e.shiftKey&&(active===last||!modal.contains(active))){e.preventDefault();first.focus();}},true);
