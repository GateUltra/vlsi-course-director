"""Inspect actual below-picture captions as soon as the British master is available."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'.pydeps'))
from playwright.sync_api import sync_playwright
assert (ROOT/'course/media/lesson-en_gb.mp4').is_file()
clock=json.loads((ROOT/'course/media/timings/en_gb.json').read_text(encoding='utf8'))
cue=next(s for s in clock['segments'] if s['id']=='results');time=cue['start']+.55*(cue['end']-cue['start'])
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
 p=b.new_page(viewport={'width':1440,'height':1050});p.goto('http://127.0.0.1:8770/');p.wait_for_function('window.courseReady&&document.querySelector("#film").readyState>=2')
 for width,height,name in [(1440,1050,'desktop'),(390,844,'mobile')]:
  p.set_viewport_size({'width':width,'height':height});p.locator('#film').evaluate('(v,t)=>{v.pause();v.currentTime=t}',time);p.wait_for_function('!document.querySelector("#film").seeking&&document.querySelector("#film").readyState>=3')
  p.locator('#film').evaluate('(v)=>v.play()');p.wait_for_timeout(150);p.locator('#film').evaluate('(v)=>v.pause()')
  for lang in ['en','ja','ko']:
   p.locator('#captions').select_option(lang);p.wait_for_function('(lang)=>{const t=[...document.querySelector("#film").textTracks].find(t=>t.language===lang);return t.mode==="hidden"&&t.cues?.length>0}',arg=lang)
   p.locator('#film').hover();p.wait_for_timeout(600);p.locator('#film-view').screenshot(path=str(ROOT/f'review-course/caption-{lang}-{name}.png'))
 b.close()
print('Saved 6 real-video caption screenshots.')

