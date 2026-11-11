"""Validate final voiced MP4s, their semantic picture cuts and soundtrack timing.

Run after render_course.py --assemble completes. No new audio is synthesised.
The alignment test compares exported AAC to its exact pre-encode WAV master;
it proves mux timing/consistency, not human listening or pronunciation quality.
"""
import argparse,json,math,re,subprocess
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'course';PROD=ROOT/'production';QA=ROOT/'review-course'
VOICES=['en_gb','en_us','en_in','zh'];FPS=30;SR=48000

def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def clock(voice):return load(SITE/'media/timings'/f'{voice}.json')
def probe(path):
 assert path.is_file(),f'Missing artifact: {path}'
 return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration,size,start_time:stream=index,codec_type,codec_name,width,height,avg_frame_rate,duration,nb_frames,start_time,time_base','-of','json',str(path)],text=True))
def stream(data,kind):return next(s for s in data['streams'] if s['codec_type']==kind)
def fps(value):
 a,b=map(float,value.split('/'));return a/b

def pcm(path,start=None,length=None):
 args=['ffmpeg','-v','error']
 if start is not None:args+=['-ss',str(start)]
 args+=['-i',str(path)]
 if length is not None:args+=['-t',str(length)]
 args+=['-vn','-ac','1','-ar',str(SR),'-f','f32le','-']
 return np.frombuffer(subprocess.check_output(args),dtype='<f4').astype(np.float64)

def correlation_with_offset(master,encoded):
 # Search ±80ms at 0.25ms resolution; enough to detect AAC priming or accumulated drift.
 a=master[::12];b=encoded[::12];n=min(len(a),len(b));a=a[:n]-a[:n].mean();b=b[:n]-b[:n].mean()
 best=(-2,None);zero=None
 for lag in range(-320,321):
  if lag>0:x=a[:-lag];y=b[lag:]
  elif lag<0:x=a[-lag:];y=b[:lag]
  else:x=a;y=b
  value=float(np.sum(x*y)/max(1e-15,np.sqrt(np.sum(x*x)*np.sum(y*y))))
  if lag==0:zero=value
  if value>best[0]:best=(value,lag/4000)
 return {'zeroOffsetCorrelation':round(zero,6),'bestCorrelation':round(best[0],6),'exportedDelaySeconds':best[1]}

def check_picture_boundaries(voice,primary,target):
 expected=math.ceil(target['duration']*FPS)
 if voice=='en_gb':
  record=load(QA/'render-primary.json');assert record['fps']==FPS and record['frames']==expected
  assert record['pageErrors']==[]
  return {'method':'Primary frame-by-frame Chromium render','frames':expected,'renderErrors':[]}
 record=load(QA/f'retime-{voice}.json');assert record['fps']==FPS
 regions=[('intro',0,primary['segments'][0]['start'],0,target['segments'][0]['start'])]
 for a,b in zip(primary['segments'],target['segments']):
  assert a['id']==b['id']
  regions.append((a['id'],a['start'],a['sceneEnd'],b['start'],b['sceneEnd']))
 regions.append(('tail',primary['segments'][-1]['sceneEnd'],primary['duration'],target['segments'][-1]['sceneEnd'],target['duration']))
 assert len(record['cuts'])==len(regions)
 previous=0;previous_source=0;maximum_error=0;rows=[]
 for i,(cut,region) in enumerate(zip(record['cuts'],regions)):
  id,a,b,x,y=region
  assert cut['id']==id
  assert cut['sourceStartFrame']==round(a*FPS) and cut['sourceEndFrame']==round(b*FPS)
  assert cut['startFrame']==round(x*FPS)
  assert cut['endFrame']==(math.ceil(y*FPS) if i==len(regions)-1 else round(y*FPS))
  assert cut['startFrame']==previous and cut['sourceStartFrame']==previous_source
  n=cut['endFrame']-cut['startFrame'];assert n>0
  error=max(abs(cut['startFrame']/FPS-x),abs(cut['endFrame']/FPS-y));assert error<1/FPS+.000001
  maximum_error=max(maximum_error,error)
  path=PROD/voice/'picture-clips'/f'{i:02d}-{id}.mp4';data=probe(path);v=stream(data,'video')
  assert int(v['nb_frames'])==n,(voice,id,n,v['nb_frames'])
  assert abs(float(v['duration'])-n/FPS)<.00001
  assert abs(fps(v['avg_frame_rate'])-FPS)<.00001 and float(v['start_time'])==0
  rows.append({'cue':id,'frames':n,'cumulativeEndFrame':cut['endFrame'],'boundaryErrorSeconds':round(error,6)})
  previous=cut['endFrame'];previous_source=cut['sourceEndFrame']
 assert previous==expected and record['frames']==expected
 assembled=stream(probe(PROD/f'picture-{voice}.mp4'),'video')
 assert int(assembled['nb_frames'])==expected and abs(float(assembled['duration'])-expected/FPS)<.00001
 return {'method':record['method'],'actualClipsChecked':len(rows),'frames':expected,'maximumBoundaryErrorSeconds':round(maximum_error,6),'accumulatedFrameError':0,'cuts':rows}

def check_voice(voice,primary):
 target=clock(voice);path=SITE/'media'/f'lesson-{voice}.mp4';data=probe(path)
 v=stream(data,'video');a=stream(data,'audio');expected=math.ceil(target['duration']*FPS)
 assert v['codec_name']=='h264' and a['codec_name']=='aac'
 assert (v['width'],v['height'])==(1920,1080) and abs(fps(v['avg_frame_rate'])-FPS)<.00001
 assert int(v['nb_frames'])==expected,(voice,'frame count',v['nb_frames'],expected)
 assert abs(float(data['format']['duration'])-target['duration'])<=1/FPS+.001
 assert abs(float(v['duration'])-target['duration'])<=1/FPS+.001
 assert abs(float(a['duration'])-target['duration'])<.002
 assert abs(float(v['start_time']))<.001 and abs(float(a['start_time']))<.001
 cuts=check_picture_boundaries(voice,primary,target)
 # Decode both entire streams, and verify decoded frame count rather than just metadata.
 decode=subprocess.run(['ffmpeg','-v','error','-nostats','-progress','pipe:1','-i',str(path),'-map','0:v:0','-map','0:a:0','-fps_mode','passthrough','-f','null','NUL'],text=True,capture_output=True,check=True)
 assert not decode.stderr.strip(),decode.stderr
 decoded_frames=int(re.findall(r'^frame=(\d+)$',decode.stdout,re.M)[-1]);assert decoded_frames==expected
 samples=pcm(path);peak=float(np.abs(samples).max());rms=float(np.sqrt(np.mean(samples*samples)))
 assert .01<rms<.3 and peak<.99,(voice,'exported levels',peak,rms)
 assert abs(len(samples)/SR-target['duration'])<.05 # AAC packet padding at the end may remain in raw decode.
 windows=[]
 for index in (0,len(target['segments'])//2,len(target['segments'])-1):
  cue=target['segments'][index];begin=cue['start']+.3;length=min(3,cue['end']-begin)
  assert length>1
  source_audio=pcm(PROD/voice/'mix.wav',begin,length);exported_audio=pcm(path,begin,length)
  match=correlation_with_offset(source_audio,exported_audio)
  assert match['bestCorrelation']>.95,(voice,cue['id'],match)
  assert match['zeroOffsetCorrelation']>.94,(voice,cue['id'],match)
  assert abs(match['exportedDelaySeconds'])<=.002,(voice,cue['id'],match)
  windows.append({'cue':cue['id'],'start':round(begin,6),'length':length,**match})
 print(f'PASS {voice}: {expected} decoded frames, {target["duration"]:.3f}s, peak={peak:.4f}, aligned beginning/middle/end',flush=True)
 return {'file':f'media/lesson-{voice}.mp4','sizeBytes':int(data['format']['size']),'video':v,'audio':a,'clockDuration':target['duration'],'formatDuration':float(data['format']['duration']),'fullDecode':{'frames':decoded_frames,'errors':[]},'pictureBoundaries':cuts,'exportedAudio':{'peak':round(peak,6),'rms':round(rms,6),'alignmentWindows':windows}}

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--voice',choices=VOICES);args=parser.parse_args()
 result={'fps':FPS,'validation':'Actual final MP4s, actual retimed clips, complete decoding and master-to-export audio comparison. Does not claim human audition.','voices':{}}
 primary=clock('en_gb')
 for voice in ([args.voice] if args.voice else VOICES):result['voices'][voice]=check_voice(voice,primary)
 output=QA/('media-checks.json' if not args.voice else f'media-checks-{args.voice}.json');output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
 print(f'Wrote {output}',flush=True)
