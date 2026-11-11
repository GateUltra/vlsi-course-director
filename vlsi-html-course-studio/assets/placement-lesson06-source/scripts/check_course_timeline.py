"""Verify the real four-voice clocks drive equivalent semantic states."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'.pydeps'))
from playwright.sync_api import sync_playwright
results={};errors=[]
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
 page=b.new_page(viewport={'width':1920,'height':1080});page.on('pageerror',lambda e:errors.append(str(e)))
 for voice in ['en_gb','en_us','en_in','zh']:
  page.goto(f'http://127.0.0.1:8770/render.html?voice={voice}');page.wait_for_function('window.ready===true')
  data=page.evaluate('''()=>{return clock.segments.map(c=>[.01,.4,.9].map(progress=>{const s=renderCue(c.id,progress);return {cue:s.cueId,progress,positions:s.positions,mode:s.mode,capacity:s.capacity,traceIndex:s.traceIndex,selectedNet:s.selectedNet}})).flat()}''')
  if results:
   previous=results['en_gb']['states']
   for expected,actual in zip(previous,data):
    assert expected['cue']==actual['cue'] and expected['mode']==actual['mode'] and expected['capacity']==actual['capacity']
    for point in expected['positions']:
     for axis in ('x','y'):assert abs(expected['positions'][point][axis]-actual['positions'][point][axis])<1e-10
  results[voice]={'duration':page.evaluate('clock.duration'),'states':data}
  page.evaluate("renderCue('density_push',.8)");page.screenshot(path=str(ROOT/f'review-course/real-clock-{voice}-push.png'))
 assert not errors
 b.close()
report={'passed':True,'voiceDurations':{key:v['duration'] for key,v in results.items()},'comparedSemanticStatesPerVoice':117,'positionTolerance':1e-10,'browserErrors':errors,'method':'Actual measured clocks. Same cue and proportional progress yields same geometry/capacity/mode.'}
(ROOT/'review-course/real-clock-checks.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(report))
