const {chromium}=require('/Users/sherry.shen/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs');const path=require('path');
let browser;
(async()=>{
 browser=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader','--no-first-run']});
 const page=await browser.newPage({viewport:{width:900,height:900},deviceScaleFactor:1});const errors=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
 await page.goto('http://127.0.0.1:8769/viewer/',{waitUntil:'networkidle'});
 await page.waitForFunction(()=>window.boutiqueDiagnostics?.().loaded,null,{timeout:90000});
 await page.waitForTimeout(1200);const views={};
 for(const [name,a] of [['front',0],['left',-13],['right',13]]){
  await page.locator(`[data-view="${a}"]`).click();await page.waitForTimeout(500);
  views[name]=await page.evaluate(()=>window.boutiqueDiagnostics());console.log('VIEW',name,JSON.stringify(views[name]));
  const png=await page.evaluate(()=>document.querySelector('canvas').toDataURL('image/png'));fs.writeFileSync(path.join(__dirname,`web-${name}.png`),Buffer.from(png.split(',')[1],'base64'));
 }
 await page.locator('[data-view="0"]').click();const canvas=page.locator('canvas');const box=await canvas.boundingBox();
 await page.mouse.move(box.x+box.width/2,box.y+box.height/2);await page.mouse.down();await page.mouse.move(box.x+box.width-20,box.y+box.height/2,{steps:1});await page.mouse.up();await page.waitForTimeout(300);
 const drag=await page.evaluate(()=>window.boutiqueDiagnostics());
 await page.mouse.move(box.x+box.width-20,box.y+box.height/2);await page.mouse.down();await page.mouse.move(box.x+20,box.y+box.height/2,{steps:1});await page.mouse.up();await page.waitForTimeout(300);const dragNegative=await page.evaluate(()=>window.boutiqueDiagnostics());
 await page.setViewportSize({width:390,height:844});await page.locator('[data-view="0"]').click();await page.waitForTimeout(800);const mobilepng=await page.evaluate(()=>document.querySelector('canvas').toDataURL('image/png'));fs.writeFileSync(path.join(__dirname,'web-mobile.png'),Buffer.from(mobilepng.split(',')[1],'base64'));
 const mobile=await page.evaluate(()=>({diagnostics:window.boutiqueDiagnostics(),horizontalOverflow:document.documentElement.scrollWidth>innerWidth}));
 const report={engine:'Chrome headless / software WebGL2; visual and functional check, not device FPS benchmark',views,drag,dragNegative,mobile,errors,pass:errors.length===0&&drag.azimuth===15&&dragNegative.azimuth===-15&&!mobile.horizontalOverflow};
 fs.writeFileSync(path.join(__dirname,'browser-check.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));await browser.close();
 if(!report.pass)process.exit(1);
})().catch(async e=>{console.error(e);if(browser)await browser.close();process.exit(1)});
