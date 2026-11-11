"""Render shared HTML/SVG once; retime semantic picture clips to each measured voice.

Speech is never sped up. Each cue keeps its independently measured audio clock.
The moustache is expressive animation, not phoneme-accurate lip synchronisation.
"""
import argparse, concurrent.futures, json, math, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'course'; PROD=ROOT/'production'; REVIEW=ROOT/'review-course'
sys.path.insert(0,str(ROOT/'.pydeps'))
from playwright.sync_api import sync_playwright
VOICES=['en_gb','en_us','en_in','zh']

def clock(voice): return json.loads((SITE/f'media/timings/{voice}.json').read_text(encoding='utf-8-sig'))
def ffmpeg(args): subprocess.run(['ffmpeg','-v','error','-y',*map(str,args)],check=True)
def write_json(path,data): path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')

def primary(fps,preview=False):
    REVIEW.mkdir(exist_ok=True); PROD.mkdir(exist_ok=True)
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True,args=['--disable-background-timer-throttling','--hide-scrollbars'])
        page=browser.new_page(viewport={'width':1920,'height':1080},device_scale_factor=1)
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto('http://127.0.0.1:8770/render.html?voice=en_gb');page.wait_for_function('window.ready===true')
        c=clock('en_gb');duration=c['duration']
        if preview:
            for cue in c['segments']:
                page.evaluate('(t)=>window.renderAt(t)',cue['start']+.65*(cue['sceneEnd']-cue['start']))
                page.screenshot(path=str(REVIEW/f'frame-{cue["id"]}.jpg'),type='jpeg',quality=92)
            s=next(s for s in c['segments'] if s['id']=='tradeoff')
            page.evaluate('(t)=>window.renderAt(t)',s['start']+.8*(s['sceneEnd']-s['start']))
            page.screenshot(path=str(SITE/'poster.jpg'),type='jpeg',quality=95)
            print(json.dumps({'previewFrames':len(c['segments']),'errors':errors}),flush=True);browser.close();return
        frames=math.ceil(duration*fps);start=time.monotonic()
        cmd=['ffmpeg','-v','error','-y','-f','image2pipe','-vcodec','mjpeg','-framerate',str(fps),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-g',str(fps),'-movflags','+faststart',str(PROD/'picture-en_gb.mp4')]
        process=subprocess.Popen(cmd,stdin=subprocess.PIPE)
        try:
            for frame in range(frames):
                page.evaluate('(t)=>window.renderAt(t)',frame/fps)
                process.stdin.write(page.screenshot(type='jpeg',quality=95))
                if frame%600==0:print(f'PRIMARY {frame}/{frames} frames; {time.monotonic()-start:.1f}s',flush=True)
            process.stdin.close();assert process.wait()==0
        except BaseException:
            process.kill();raise
        record={'fps':fps,'duration':duration,'frames':frames,'wallSeconds':time.monotonic()-start,'pageErrors':errors,'renderer':'Chromium shared SVG/HTML components, 1920x1080'}
        write_json(REVIEW/'render-primary.json',record);browser.close();assert not errors
        print(json.dumps(record),flush=True)

def mux(voice,picture):
    c=clock(voice)
    ffmpeg(['-i',picture,'-i',PROD/voice/'mix.wav','-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-t',c['duration'],'-movflags','+faststart',SITE/f'media/lesson-{voice}.mp4'])
    print(f'MUXED {voice}: {c["duration"]:.3f}s',flush=True)

def retime_voice(voice,fps,workers):
    base=clock('en_gb');target=clock(voice);folder=PROD/voice/'picture-clips';folder.mkdir(exist_ok=True)
    source=PROD/'picture-en_gb.mp4'
    # Integer frame boundaries prevent tiny independent cue rounding errors from accumulating.
    regions=[('intro',0,base['segments'][0]['start'],0,target['segments'][0]['start'])]
    for a,b in zip(base['segments'],target['segments']):
        assert a['id']==b['id'];regions.append((a['id'],a['start'],a['sceneEnd'],b['start'],b['sceneEnd']))
    regions.append(('tail',base['segments'][-1]['sceneEnd'],base['duration'],target['segments'][-1]['sceneEnd'],target['duration']))
    cuts=[]
    for i,(id,a,b,x,y) in enumerate(regions):
        src_start=round(a*fps);src_end=round(b*fps)
        dst_start=round(x*fps);dst_end=math.ceil(y*fps) if i==len(regions)-1 else round(y*fps)
        cuts.append({'id':id,'sourceStartFrame':src_start,'sourceEndFrame':src_end,'startFrame':dst_start,'endFrame':dst_end,'path':folder/f'{i:02d}-{id}.mp4'})
    def encode(cut):
        n=cut['endFrame']-cut['startFrame'];old=max(1,cut['sourceEndFrame']-cut['sourceStartFrame']);ratio=n/old
        filters=f'setpts=PTS-STARTPTS,setpts={ratio:.12f}*PTS,fps={fps},tpad=stop_mode=clone:stop_duration=2'
        ffmpeg(['-ss',cut['sourceStartFrame']/fps,'-t',old/fps,'-i',source,'-an','-vf',filters,'-frames:v',n,'-c:v','libx264','-threads','2','-preset','fast','-crf','18','-pix_fmt','yuv420p','-g',fps,'-video_track_timescale','15360',cut['path']])
        return cut
    started=time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        for done,_ in enumerate(executor.map(encode,cuts),1):
            if done%8==0:print(f'RETIME {voice}: {done}/{len(cuts)} cues; {time.monotonic()-started:.1f}s',flush=True)
    concat=folder/'concat.txt';concat.write_text(''.join("file '"+cut['path'].as_posix()+"'\n" for cut in cuts),encoding='utf8')
    picture=PROD/f'picture-{voice}.mp4'
    ffmpeg(['-f','concat','-safe','0','-i',concat,'-c','copy','-movflags','+faststart',picture])
    write_json(REVIEW/f'retime-{voice}.json',{'voice':voice,'fps':fps,'method':'Each semantic picture cue retimed to its measured narration window; speech unchanged. Frame-boundary error <1 frame.','frames':sum(c['endFrame']-c['startFrame'] for c in cuts),'cuts':[{k:v for k,v in c.items() if k!='path'} for c in cuts]})
    mux(voice,picture)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--preview',action='store_true');parser.add_argument('--primary',action='store_true');parser.add_argument('--assemble',action='store_true');parser.add_argument('--voice',choices=VOICES);parser.add_argument('--fps',type=int,default=30);parser.add_argument('--workers',type=int,default=4);args=parser.parse_args()
    if args.preview:primary(args.fps,True)
    if args.primary:primary(args.fps)
    if args.assemble:
        for voice in ([args.voice] if args.voice else VOICES):
            if voice=='en_gb':mux(voice,PROD/'picture-en_gb.mp4')
            else:retime_voice(voice,args.fps,args.workers)
