"""Inspect all authored scenes with an explicitly internal QA clock, never write a media clock."""
import base64,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'.pydeps'))
from playwright.sync_api import sync_playwright
OUT=ROOT/'review-course';OUT.mkdir(exist_ok=True)
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
 page=browser.new_page(viewport={'width':1920,'height':1080},device_scale_factor=1)
 page.goto('http://127.0.0.1:8770/film-art.js')
 page.set_content('<html><head><style>html,body{margin:0;width:100%;height:100%;overflow:hidden}svg.teaching-scene{width:100vw;height:100vh;display:block}</style></head><body><div id="frame"></div></body></html>')
 page.evaluate('''async()=>{const a=await import('/scene.js'),b=await import('/timeline.js'),s=await fetch('/content/script.json').then(r=>r.json());window.script=s;window.Scene=a.Scene;window.stateAt=b.stateAt;window.qaClock={duration:s.cues.length*10,segments:s.cues.map((c,i)=>({...c,start:i*10,end:i*10+9.7,sceneEnd:(i+1)*10}))};window.show=(id,p)=>{const q=qaClock.segments.find(c=>c.id===id),state=stateAt(q.start+10*p,qaClock,script);document.querySelector('#frame').innerHTML=Scene(state);return state};}''')
 cues=page.evaluate('script.cues.map(c=>c.id)');records=[];images=[]
 for cue in cues:
  state=page.evaluate('([id,p])=>show(id,p)',[cue,.68])
  svg=page.locator('#frame').inner_html();assert 'NaN' not in svg
  # Ignore the sourced character's hidden original body geometry: its nested viewBox deliberately clips it.
  bounds=page.evaluate('''()=>[...document.querySelector('.teaching-scene').children].filter(n=>n.tagName==='text').map(n=>{const b=n.getBBox();return {text:n.textContent,x:b.x,y:b.y,right:b.x+b.width,bottom:b.y+b.height}})''')
  outside=[b for b in bounds if b['x']<0 or b['right']>1919 or b['y']<0 or b['bottom']>1079]
  # Footer/progress are intentional near the lower edge.
  assert not outside,(cue,outside)
  text_bottom=page.evaluate('''()=>Math.max(...[...document.querySelectorAll('.caption-safe-content text')].filter(n=>!n.closest('.scientist-rig')).map(n=>n.getBoundingClientRect().bottom))''')
  assert text_bottom<=930,(cue,text_bottom)
  name=f'film-{cue}.png';page.screenshot(path=str(OUT/name));images.append((cue,name))
  records.append({'cue':cue,'mode':state['mode'],'capacity':state['capacity'],'traceIndex':state['traceIndex'],'topLevelTextWithinCanvas':True,'teachingTextBottom':text_bottom,'captionSafeArea':'975–1080 px'})
 # Check deterministic random access and core lesson claims through the actual scene state.
 page.evaluate("show('density_push',.68)");first=page.screenshot();page.evaluate("show('ending',.9)");page.evaluate("show('density_push',.68)");assert first==page.screenshot()
 checks=page.evaluate('''async()=>{const d=await import('/domain.js');let a=show('hpwl_measure',.7),b=show('hpwl_inside',.7),c=show('spread_demo',.9),e=show('results',.6);return {oneNet:d.netBounds(3,a.positions).hpwl,interiorNet:d.netBounds(4,b.positions).hpwl,designed:d.metrics(c.positions,c.capacity),reference:d.metrics(e.positions,e.capacity)}}''')
 assert checks['oneNet']==14 and checks['interiorNet']==16
 assert checks['designed']['hpwl']==52 and checks['designed']['overflow']==0
 assert abs(checks['reference']['hpwl']-48.12117617637419)<1e-8 and checks['reference']['overflow']==2
 # Browser lays out the contact sheet; no raster drawing library is used.
 html='<style>body{margin:0;background:#ded8c4;display:grid;grid-template-columns:repeat(3,640px);gap:10px;font:20px Segoe UI}.item{background:#fff9ec}h3{margin:0;padding:10px}img{display:block;width:640px;height:360px}</style>'
 for cue,name in images:
  src=base64.b64encode((OUT/name).read_bytes()).decode();html+=f'<div class="item"><h3>{cue}</h3><img src="data:image/png;base64,{src}"></div>'
 page.set_viewport_size({'width':1940,'height':1100});page.set_content(html);page.screenshot(path=str(OUT/'film-contact-sheet.png'),full_page=True)
 browser.close()
 report={'clock':'Internal10secondcueQAclock; no delivery timeline generated','cues':records,'metrics':checks,'deterministicRandomAccess':True}
 (OUT/'film-scene-checks.json').write_text(json.dumps(report,indent=2),encoding='utf8')
 print(json.dumps({'passed':True,'cues':len(cues),'metrics':checks}))
