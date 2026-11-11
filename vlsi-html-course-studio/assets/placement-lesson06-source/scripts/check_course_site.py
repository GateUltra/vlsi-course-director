"""Full real-media website validation. Refuses missing MP4s or caption files."""
import json,sys,math,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'course';QA=ROOT/'review-course';sys.path.insert(0,str(ROOT/'.pydeps'))
from playwright.sync_api import sync_playwright
manifest=json.loads((SITE/'media/manifest.json').read_text(encoding='utf-8-sig'))
script=json.loads((SITE/'content/script.json').read_text(encoding='utf-8-sig'))
clocks={t['id']:json.loads((SITE/t['timing']).read_text(encoding='utf-8-sig')) for t in manifest['tracks']}
for track in manifest['tracks']:
 for filename in [track['video'],*track['captions'].values()]:assert (SITE/filename).is_file(),f'Final media missing: {filename}'
report={'realMedia':True,'voices':{},'transfers':[]};errors=[];failed=[]
def seek(page,time):
 page.locator('#film').evaluate('(v,t)=>{v.pause();v.currentTime=t}',time)
 page.wait_for_function('(t)=>{const v=document.querySelector("#film");return !v.seeking&&v.readyState>=3&&Math.abs(v.currentTime-t)<.06}',arg=time)
def current(page):return page.evaluate('window.course.player.getState()')
def caption_check(page,lang,duration):
 page.locator('#captions').select_option(lang)
 page.wait_for_function('(lang)=>{const t=[...document.querySelector("#film").textTracks].find(t=>t.language===lang);return t&&t.mode==="hidden"&&t.cues&&t.cues.length>0}',arg=lang)
 cues=page.evaluate('(lang)=>[...[...document.querySelector("#film").textTracks].find(t=>t.language===lang).cues].map(c=>({id:c.id,start:c.startTime,end:c.endTime,text:c.text}))',lang)
 previous=0
 for cue in cues:
  assert previous<=cue['start']+.003<cue['end']<=duration+.06 and cue['text'].strip(),cue
  previous=cue['end']
 for left,right in zip(cues,cues[1:]):
  same_semantic_cue=left['id'].rsplit('-',1)[0]==right['id'].rsplit('-',1)[0]
  if same_semantic_cue:
   assert not(re.search(r'\d\.$',re.sub(r'\s','',left['text'])) and re.match(r'\d',right['text'].strip())),f'Decimal split between cues: {left} / {right}'
 assert page.locator('#download-caption').is_visible()
 assert page.locator('#caption-strip').is_visible()
 active=page.evaluate('(lang)=>[...([...document.querySelector("#film").textTracks].find(t=>t.language===lang).activeCues||[])].map(c=>c.text).join("\\n")',lang)
 if active:
  page.wait_for_function('(text)=>document.querySelector("#caption-text").textContent.replace(/\\s/g,"")===text.replace(/\\s/g,"")',arg=active)
 return len(cues)
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
 page=browser.new_page(viewport={'width':1440,'height':1050});page.set_default_timeout(18000)
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.on('response',lambda r:failed.append({'url':r.url,'status':r.status}) if r.status>=400 else None)
 page.goto('http://127.0.0.1:8770/');page.wait_for_function('window.courseReady')
 page.wait_for_function('document.querySelector("#film").readyState>=2&&!document.querySelector("#film").seeking')
 page.emulate_media(reduced_motion='reduce')
 for track in manifest['tracks']:
  voice=track['id'];clock=clocks[voice]
  page.evaluate('async(id)=>{await course.player.switchVoice(id,{position:{cueId:"welcome",progress:0},resume:false})}',voice)
  page.wait_for_function('document.querySelector("#film").readyState>=2&&!document.querySelector("#film").seeking')
  duration=page.locator('#film').evaluate('(v)=>v.duration');assert abs(duration-clock['duration'])<.12
  assert page.locator('#film').evaluate('(v)=>v.paused')
  assert page.locator('#voice').input_value()==voice
  before=page.locator('#film').evaluate('(v)=>{v.muted=false;return v.currentTime}')
  page.locator('#film').evaluate('(v)=>v.play()');page.wait_for_timeout(700);page.locator('#film').evaluate('(v)=>v.pause()')
  assert page.locator('#film').evaluate('(v)=>v.currentTime')>before+.25
  chapter_checks=[]
  for chapter in script['chapters']:
   start=next(s['start'] for s in clock['segments'] if s['chapter']==chapter['id'])
   page.locator(f'#chapters [data-chapter="{chapter["id"]}"]').click()
   page.locator('#film').evaluate('(v)=>v.pause()');page.wait_for_function('!document.querySelector("#film").seeking')
   assert abs(page.locator('#film').evaluate('(v)=>v.currentTime')-start)<.5
   assert page.locator(f'#chapters [data-chapter="{chapter["id"]}"]').get_attribute('aria-current')=='true'
   chapter_checks.append(chapter['id'])
  counts={lang:caption_check(page,lang,duration) for lang in manifest['captionLanguages']}
  page.locator('#captions').select_option('off');assert page.locator('#film').evaluate('(v)=>[...v.textTracks].every(t=>t.mode==="disabled")');assert not page.locator('#caption-strip').is_visible()
  for cue_id,mode,capacity in [('hpwl_inside','hpwl',2),('capacity','sandbox',2),('density_push','reference',1)]:
   cue=next(s for s in clock['segments'] if s['id']==cue_id);t=cue['start']+.43*(cue['sceneEnd']-cue['start']);seek(page,t);expected=current(page)
   page.locator('#take-state').click();actual=page.evaluate('course.lab.getState()')
   assert actual['mode']==mode and actual['capacity']==capacity and actual['positions']==expected['positions']
   assert page.locator('#film').evaluate('(v)=>v.paused')
   report['transfers'].append({'voice':voice,'cue':cue_id,'mode':mode,'capacity':capacity,'exactPositions':True})
  report['voices'][voice]={'duration':duration,'playbackClock':'advances with muted=false','chapters':chapter_checks,'captions':counts}
  if voice=='en_gb':
   cue=next(s for s in clock['segments'] if s['id']=='results');caption_time=cue['start']+.55*(cue['end']-cue['start'])
   for width,height,name in [(1440,1050,'desktop'),(390,844,'mobile')]:
    page.set_viewport_size({'width':width,'height':height});seek(page,caption_time)
    page.locator('#film').evaluate('(v)=>v.play()');page.wait_for_timeout(150);page.locator('#film').evaluate('(v)=>v.pause()')
    for lang in ['en','ja','ko']:
     caption_check(page,lang,duration);page.locator('#film').hover();page.wait_for_timeout(600)
     page.locator('#film-view').screenshot(path=str(QA/f'caption-{lang}-{name}.png'))
   page.set_viewport_size({'width':1440,'height':1050})
   report['captionScreenshots']='English, Japanese and Korean below the picture at results cue, desktop and mobile with paused controls visible'
 # Semantic position, independent captions, speed and pause survive normal voice switches.
 for i,next_voice in enumerate(['en_gb','en_us','en_in','zh']):
  old_clock=page.evaluate('course.player.getClock()');cue=next(s for s in old_clock['segments'] if s['id']=='predict');seek(page,cue['start']+.61*(cue['sceneEnd']-cue['start']))
  page.locator('#captions').select_option('ja');page.locator('#speed').select_option('1.5')
  page.locator('#voice').select_option(next_voice)
  page.wait_for_function('(id)=>course.player.getVoice()===id&&document.querySelector("#video-status").textContent===""&&!document.querySelector("#film").seeking',arg=next_voice)
  mapped=current(page);assert mapped['cueId']=='predict' and abs(mapped['progress']-.61)<.005
  assert page.locator('#film').evaluate('(v)=>v.paused&&v.playbackRate===1.5')
  assert page.locator('#captions').input_value()=='ja';caption_check(page,'ja',clocks[next_voice]['duration'])
 # Resume state after a playing switch, while mapping the same semantic cue.
 page.locator('#film').evaluate('(v)=>v.play()');page.wait_for_timeout(150)
 page.evaluate('()=>course.player.switchVoice("en_gb")');page.wait_for_timeout(400)
 assert not page.locator('#film').evaluate('(v)=>v.paused');assert current(page)['cueId']=='predict';page.locator('#film').evaluate('(v)=>v.pause()')
 stable=current(page)
 page.evaluate('''async()=>{const a=course.player.switchVoice('en_us'),b=course.player.switchVoice('en_in');await Promise.allSettled([a,b])}''')
 page.wait_for_function('!document.querySelector("#film").seeking&&document.querySelector("#video-status").textContent===""')
 rapid=current(page);assert rapid['cueId']==stable['cueId'] and abs(rapid['progress']-stable['progress'])<.005
 assert page.locator('#voice').input_value()=='en_in' and page.locator('#film').evaluate('(v)=>v.paused')
 report['voiceSwitch']='same cue/fraction, Japanese captions,1.5x speed and pause/play state preserved, including two switches before metadata arrives'
 page.locator('#film').evaluate('(v)=>v.requestFullscreen()')
 page.wait_for_function('document.fullscreenElement===document.querySelector("#film")')
 page.wait_for_function('[...document.querySelector("#film").textTracks].some(t=>t.language==="ja"&&t.mode==="showing")')
 page.evaluate('document.exitFullscreen()');page.wait_for_function('!document.fullscreenElement')
 page.wait_for_function('[...document.querySelector("#film").textTracks].some(t=>t.language==="ja"&&t.mode==="hidden")')
 assert page.locator('#caption-strip').is_visible();report['fullscreenCaptions']='Native showing in fullscreen; hidden track plus separate caption strip after exit'
 # Public transfer state from the webpage leads into the shared lab and practice.
 page.locator('[data-mode="reference"]').click();page.locator('.ref-step').click();assert page.evaluate('course.lab.getState().traceIndex')==1
 page.locator('.start-challenge').click();assert page.evaluate('course.lab.getState().mode')=='sandbox'
 page.locator('.grade-challenge').click();assert 'Not yet' in page.locator('.experiment-challenge .exercise-feedback').inner_text()
 page.locator('[data-preset="distributed"]').click();page.locator('.grade-challenge').click();assert 'one valid solution' in page.locator('.experiment-challenge .exercise-feedback').inner_text()
 page.locator('[data-question="measure"] [data-replay]').click();page.locator('#film').evaluate('(v)=>v.pause()');assert current(page)['cueId']=='hpwl_measure'
 page.screenshot(path=str(QA/'site-desktop.png'),full_page=True)
 page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(150)
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
 page.screenshot(path=str(QA/'site-mobile.png'),full_page=True)
 assert page.locator('#voice').is_visible() and page.locator('#captions').is_visible()
 report['mobile']='390×844 full page has no horizontal overflow; controls, lab and activities present'
 report['pageErrors']=errors;report['httpErrors']=failed;assert not errors and not failed
 # Local-file notice is tested separately; ES modules may be blocked before app.js runs.
 filepage=browser.new_page();filepage.goto((SITE/'index.html').as_uri());filepage.wait_for_timeout(800)
 notice=filepage.locator('#video-status').inner_text();report['fileProtocolNotice']=notice
 assert 'START_PREVIEW' in notice or 'START_COURSE' in notice or 'local server' in notice.lower(),notice
 browser.close()
(QA/'site-browser-checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False,indent=2))

