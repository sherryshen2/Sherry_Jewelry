const {chromium}=require('/Users/sherry.shen/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs');const path=require('path');
let browser;
(async()=>{
 browser=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader','--no-first-run']});
 const page=await browser.newPage({viewport:{width:900,height:900},deviceScaleFactor:1});const errors=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
 await page.goto('http://127.0.0.1:8770/viewer/',{waitUntil:'networkidle'});
 await page.waitForFunction(()=>window.boutiqueDiagnostics?.().loaded,null,{timeout:90000});
 await page.waitForTimeout(1200);const views={};
 for(const [name,a] of [['front',0]]){
  await page.locator(`[data-view="${a}"]`).click();await page.waitForTimeout(500);
  views[name]=await page.evaluate(()=>window.boutiqueDiagnostics());console.log('VIEW',name,JSON.stringify(views[name]));
  const png=await page.evaluate(()=>document.querySelector('canvas').toDataURL('image/png'));fs.writeFileSync(path.join(__dirname,`web-${name}.png`),Buffer.from(png.split(',')[1],'base64'));
 }
 await browser.close();
})().catch(async e=>{console.error(e);if(browser)await browser.close();process.exit(1)});
