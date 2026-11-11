"""Browser integration of the three labs and six graded activities, independent of render readiness."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'.pydeps'))
from playwright.sync_api import sync_playwright
report={};errors=[]
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
 page=browser.new_page(viewport={'width':1440,'height':1050});page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8770/content/script.json')
 page.set_content('<html><head><link rel="stylesheet" href="/site.css"><link rel="stylesheet" href="/lab.css"><link rel="stylesheet" href="/exercises.css"></head><body><main><section><h2>Studio experiments</h2><div id="lab"></div></section><section id="practice"></section></main></body></html>')
 page.evaluate('''async()=>{const {mountLab}=await import('/lab.js'),{mountExercises}=await import('/exercises.js');window.replayed=null;window.lab=mountLab(document.querySelector('#lab'),{onReplay:id=>window.replayed=id});window.exercises=mountExercises(document.querySelector('#practice'),{onReplay:id=>window.replayed=id,onTry:s=>window.lab.takeState(s),getLabState:()=>window.lab.getState()})}''')
 assert page.evaluate('lab.getState().metrics.hpwl')==48.5
 page.locator('[data-preset="distributed"]').click();assert page.evaluate('lab.getState().metrics.overflow')==0
 page.locator('[data-preset="crowded"]').first.click();page.locator('.lab-hint').click()
 assert page.locator('#lab').evaluate('(el)=>el.mentorState.suggestedCell')=='B'
 point=page.evaluate('''()=>{const m=document.querySelector('.lab-board-host svg').getScreenCTM(),a=new DOMPoint(160,640).matrixTransform(m),b=new DOMPoint(560,560).matrixTransform(m);return {a:{x:a.x,y:a.y},b:{x:b.x,y:b.y}}}''')
 page.mouse.move(**point['a']);page.mouse.down();page.mouse.move(**point['b'],steps=8);page.mouse.up()
 s=page.evaluate('lab.getState()');assert abs(s['positions']['B']['x']-6)<.02 and abs(s['positions']['B']['y']-2)<.02
 assert s['metrics']['overflow']==2 and abs(s['metrics']['hpwl']-48.5)<.001
 assert 'better' in page.locator('.companion-bubble h3').inner_text()
 page.locator('[data-cell="B"]').focus();page.keyboard.press('ArrowRight');page.keyboard.press('Tab');page.wait_for_timeout(350)
 assert page.evaluate('document.activeElement?.dataset.cell')=='C'
 page.locator('.nudge-cell').select_option('F');old_f=page.evaluate('lab.getState().positions.F.x');page.locator('[data-nudge="right"]').click();assert abs(page.evaluate('lab.getState().positions.F.x')-old_f-.25)<1e-10
 assert page.evaluate('lab.getState().positions.A.x')==0 and page.evaluate('lab.getState().positions.D.y')==8
 report['sandbox']='Presets, metrics, hint, real drag, keyboard and no focus theft pass'
 page.locator('[data-mode="hpwl"]').click();page.locator('.net-select').select_option('3');assert '14.00' in page.locator('.lab-measurement').inner_text()
 page.locator('.net-select').select_option('4');before=page.evaluate('lab.getState().metrics.perNet[4]')
 page.locator('[data-cell="B"]').focus();page.keyboard.press('ArrowRight');page.wait_for_timeout(350)
 assert page.evaluate('lab.getState().metrics.perNet[4]')==before==16
 assert 'did not change' in page.locator('.companion-bubble h3').inner_text()
 report['hpwl']='B-D14, multi-net16 and interior-point invariance pass'
 page.locator('[data-mode="reference"]').click();assert page.evaluate('lab.getState().capacity')==1
 assert page.evaluate('lab.getState().metrics.hpwl')==52
 for i in range(33):page.locator('.ref-step').click()
 assert abs(page.evaluate('lab.getState().metrics.hpwl')-48.12117617637419)<1e-10
 assert page.evaluate('lab.getState().metrics.overflow')==2
 assert page.locator('.ref-step').is_disabled()
 page.locator('.density-weight').evaluate('(el)=>{el.value=2;el.dispatchEvent(new Event("input",{bubbles:true}))}')
 assert page.evaluate('lab.getState().traceIndex')==0 and page.evaluate('lab.getState().weight')==2
 page.locator('.ref-run').click();page.wait_for_timeout(1400);page.locator('.ref-run').click()
 assert 1<=page.evaluate('lab.getState().traceIndex')<=3
 page.locator('.ref-reset').click();assert page.evaluate('lab.getState().metrics.hpwl')==52
 report['reference']='All33updates, exact default golden, capacity1, weight reset, run/pause pass'
 # Test exact intermediate transfer, preserving the capacity instead of coercing reference into sandbox.
 page.evaluate('''async()=>{const d=await import('/domain.js'),p=d.interpolatePositions(d.referenceTrace()[9].positions,d.referenceTrace()[10].positions,.37);window.expected=p;lab.takeState({positions:p,mode:'reference',capacity:1,traceIndex:9,cueId:'density_push',t:200})}''')
 assert page.evaluate('lab.getState().positions')==page.evaluate('expected')
 assert page.evaluate('lab.getState().capacity')==1
 page.locator('.lab-replay').click();assert page.evaluate('replayed')=='density_push'
 for id,answer in [('measure','14'),('overflow','3'),('bound','2')]:
  form=page.locator(f'[data-question="{id}"]');form.locator('input').fill(answer);form.locator('[type="submit"]').click();assert form.get_attribute('data-result')=='correct'
 for id,answer in [('choice','room'),('evidence','both')]:
  form=page.locator(f'[data-question="{id}"]');form.locator(f'[value="{answer}"]').check();form.locator('[type="submit"]').click();assert form.get_attribute('data-result')=='correct'
 page.locator('.grade-challenge').click();assert 'capacity 1' in page.locator('.experiment-challenge .exercise-feedback').inner_text()
 page.locator('.start-challenge').click();assert page.evaluate('lab.getState().mode')=='sandbox'
 page.evaluate('''async()=>{const d=await import('/domain.js');let p=d.clone(d.distributed);p.B={x:7,y:1};lab.takeState({positions:p,capacity:2,mode:'sandbox',cueId:'overflow'})}''')
 page.locator('.grade-challenge').click();assert page.evaluate('exercises.getProgress().completed')==6
 page.locator('[data-question="measure"] input').fill('9.9');page.locator('[data-question="measure"] [type="submit"]').click();assert page.evaluate('exercises.getProgress().completed')==5
 report['exercises']='Five answers, wrong-answer correction, reference-mode rejection and alternative feasible layout pass'
 page.locator('#lab').screenshot(path=str(ROOT/'review-course/lab-desktop.png'))
 page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
 page.locator('#lab').screenshot(path=str(ROOT/'review-course/lab-mobile.png'));report['mobile']='390px no horizontal overflow'
 report['pageErrors']=errors;assert not errors
 browser.close()
(ROOT/'review-course/lab-browser-checks.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report,indent=2))
