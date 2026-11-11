"""Rebuild the four authorised narration tracks and seven independent captions.

Exact text/voice/rate caches; measured per-cue clocks, never global time stretching.
Translated caption chunks use proportional reading time inside a spoken cue;
this is semantic alignment, not an assertion of word-level translated alignment.
"""
import argparse, asyncio, hashlib, json, math, re, subprocess, textwrap, wave
from pathlib import Path
import edge_tts
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'course'; PROD=ROOT/'production'; SR=48000
VOICES={
 'en_gb':('en','en-GB-ThomasNeural','British English · Thomas'),
 'en_us':('en','en-US-GuyNeural','American English · Guy'),
 'en_in':('en','en-IN-PrabhatNeural','Indian English · Prabhat'),
 'zh':('zh','zh-CN-YunxiNeural','普通话 · 云希'),
}
LANGUAGES={'en':'English','zh':'中文','fr':'Français','es':'Español','de':'Deutsch','ja':'日本語','ko':'한국어'}

def atomic_json(path,data):
 path.parent.mkdir(parents=True,exist_ok=True)
 tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8');tmp.replace(path)

def duration(path):
 return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(path)],text=True).strip())

def read_script():
 data=json.loads((SITE/'content/script.json').read_text(encoding='utf-8-sig'))
 return data['cues'] if isinstance(data,dict) else data

async def synth(voice_id,script,semaphore):
 language,voice,label=VOICES[voice_id];folder=PROD/voice_id/'clips';folder.mkdir(parents=True,exist_ok=True)
 for n,cue in enumerate(script):
  text=cue[language];path=folder/f'{cue["id"]}.mp3';key=path.with_suffix('.sha256')
  fingerprint=hashlib.sha256(json.dumps([text,voice,'+0%','+0Hz'],ensure_ascii=False).encode()).hexdigest()
  if path.exists() and key.exists() and key.read_text()==fingerprint and path.stat().st_size>512:continue
  for attempt in range(5):
   try:
    async with semaphore:
     boundaries=[];temporary=path.with_suffix('.tmp.mp3')
     with temporary.open('wb') as f:
      async for chunk in edge_tts.Communicate(text,voice=voice,rate='+0%',boundary='WordBoundary').stream():
       if chunk['type']=='audio':f.write(chunk['data'])
       elif chunk['type']=='WordBoundary':boundaries.append(chunk)
     if temporary.stat().st_size<512:raise RuntimeError('Empty speech response')
     temporary.replace(path);key.write_text(fingerprint)
     atomic_json(path.with_suffix('.boundaries.json'),boundaries)
    break
   except Exception as exc:
    print(f'{voice_id}/{cue["id"]} retry {attempt+1}: {type(exc).__name__}',flush=True)
    if attempt==4:raise
    await asyncio.sleep(2*(attempt+1))
  print(f'{voice_id}: {n+1}/{len(script)} {cue["id"]}',flush=True)

def write_wav(path,data):
 with wave.open(str(path),'wb') as w:
  w.setparams((1,2,SR,0,'NONE','not compressed'));w.writeframes((np.clip(data,-1,1)*32767).astype('<i2').tobytes())

def read_wav(path):
 with wave.open(str(path),'rb') as w:
  assert w.getnchannels()==1 and w.getframerate()==SR and w.getsampwidth()==2
  return np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(np.float32)/32768

def original_bed(total):
 """Same sparse original pluck motif as the accepted studio-v3, efficiently tiled."""
 length=math.ceil(total*SR);bed=np.zeros(length,dtype=np.float32)
 notes=[261.6256,329.6276,391.9954,440,391.9954,329.6276,293.6648,391.9954]
 x=np.arange(SR*3,dtype=np.float32)/SR
 env=np.minimum(x/.014,1)*np.exp(-x*3.8)
 for i,hit in enumerate(np.arange(.15,total,1.35)):
  frequency=notes[i%len(notes)];n=min(len(x),length-round(hit*SR));start=round(hit*SR)
  tone=np.sin(2*np.pi*frequency*x)+.22*np.sin(2*np.pi*2*frequency*x)+.07*np.sin(2*np.pi*3*frequency*x)
  bed[start:start+n]+=.0065*(tone*env)[:n]
 # Small chunks avoid full-course temporary arrays for every oscillator.
 for begin in range(0,length,SR*10):
  stop=min(begin+SR*10,length);t=np.arange(begin,stop,dtype=np.float32)/SR
  for n,f in enumerate([130.8128,195.9977,220]):bed[begin:stop]+=.0008*np.sin(2*np.pi*f*t+.1*np.sin(.5*t+n))
  bed[begin:stop]*=np.minimum(t/1.8,1)*np.clip((total-t)/2,0,1)
 return bed

def assemble(voice_id,script):
 language,voice,label=VOICES[voice_id];folder=PROD/voice_id;segments=[];cursor=.8
 for cue in script:
  path=folder/'clips'/f'{cue["id"]}.mp3';length=duration(path);end=cursor+length;scene_end=end+.3+float(cue.get('pauseAfter',0))
  segments.append({**{k:cue[k] for k in ('id','chapter','title','layout') if k in cue},'start':round(cursor,6),'end':round(end,6),'sceneEnd':round(scene_end,6),'text':cue[language],'zh':cue['zh'],'en':cue['en'],'clip':f'production/{voice_id}/clips/{cue["id"]}.mp3'})
  cursor=scene_end
 total=round(cursor+.8,6)
 master=np.zeros(math.ceil(total*SR),dtype=np.float32)
 for s in segments:
  pcm=subprocess.check_output(['ffmpeg','-v','error','-i',str(folder/'clips'/f'{s["id"]}.mp3'),'-f','s16le','-ac','1','-ar',str(SR),'-'])
  sample=np.frombuffer(pcm,dtype='<i2').astype(np.float32)/32768;start=round(s['start']*SR)
  master[start:start+len(sample)]+=sample
 write_wav(folder/'narration-raw.wav',master);del master
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(folder/'narration-raw.wav'),'-af','loudnorm=I=-17:TP=-2:LRA=7','-ar',str(SR),'-ac','1',str(folder/'narration.wav')],check=True)
 voice_samples=read_wav(folder/'narration.wav')
 bed=original_bed(len(voice_samples)/SR);mixed=voice_samples+bed[:len(voice_samples)]
 assert np.max(np.abs(mixed))<.95,'Unexpected clipping headroom'
 write_wav(folder/'mix.wav',mixed)
 write_wav(folder/'original-bed.wav',bed)
 fps=25;block=SR//fps;padded=np.pad(voice_samples,(0,(-len(voice_samples))%block));rms=np.sqrt(np.mean(padded.reshape(-1,block)**2,axis=1))
 voiced=rms[rms>.008];reference=float(np.percentile(voiced,85));values=np.clip((rms-.008)/max(.001,reference-.008),0,1)**.7
 envelope={'fps':fps,'duration':total,'method':'40 ms voice-only RMS; moustache motion, not lip synchronisation','values':[round(float(v),4) for v in values]}
 atomic_json(SITE/'media/timings'/f'{voice_id}-envelope.json',envelope)
 timeline={'id':voice_id,'voice':voice,'language':language,'label':label,'rate':'+0%','pitch':'default','duration':total,'segments':segments,'envelope':f'media/timings/{voice_id}-envelope.json'}
 atomic_json(SITE/'media/timings'/f'{voice_id}.json',timeline)
 loudness=subprocess.run(['ffmpeg','-hide_banner','-i',str(folder/'mix.wav'),'-af','volumedetect','-f','null','NUL'],capture_output=True,text=True,check=True)
 (folder/'levels.txt').write_text(loudness.stderr,encoding='utf8')
 print(f'ASSEMBLED {voice_id}: {total:.3f} seconds',flush=True)
 return timeline

def split_caption(text,lang):
 # Maximum two lines per screen. Recursively balance long sentences so a final
 # word never becomes its own flashing caption after two completely full lines.
 cjk=lang in ('zh','ja');limit=24 if cjk else (28 if lang=='ko' else 43)
 # A dot inside 48.1 is not sentence punctuation. Preserve numeric tokens at
 # sentence, caption and line boundaries, including decimal-comma languages.
 number_pattern=re.compile(r'\d+(?:[.,]\d+)*')
 def safe_cut(clause,cut):
  for match in number_pattern.finditer(clause):
   if match.start()<cut<match.end():return match.start() if match.start()>0 else match.end()
  return cut
 def allowed_cut(clause,cut):return safe_cut(clause,cut)==cut
 clauses=[];begin=0
 for match in re.finditer(r'[。！？.!?;；]\s*',text):
  at=match.start()
  if text[at]=='.' and at>0 and at+1<len(text) and text[at-1].isdigit() and text[at+1].isdigit():continue
  clauses.append(text[begin:match.end()]);begin=match.end()
 if begin<len(text):clauses.append(text[begin:])
 def wrap(clause):
  if cjk:
   lines=[]
   while len(clause)>limit:
    cut=max([clause.rfind(c,0,limit+1)+1 for c in '，、,：:']+[0])
    if cut<limit//2:cut=limit
    cut=safe_cut(clause,cut)
    lines.append(clause[:cut]);clause=clause[cut:]
   if clause:lines.append(clause)
  else:lines=textwrap.wrap(clause,width=limit,break_long_words=False,break_on_hyphens=False)
  return lines
 def balanced(clause):
  clause=clause.strip();lines=wrap(clause)
  if len(lines)<=2:return ['\n'.join(lines)] if lines else []
  cuts=[m.end() for m in re.finditer(r'[，、,:：]|\s+',clause)]
  cuts=[c for c in cuts if len(clause)*.25<=c<=len(clause)*.75 and allowed_cut(clause,c)]
  if not cuts:cuts=[c for c in range(1,len(clause)) if allowed_cut(clause,c)]
  cut=min(cuts,key=lambda x:abs(x-len(clause)/2))
  return balanced(clause[:cut])+balanced(clause[cut:])
 chunks=[]
 for clause in clauses:chunks+=balanced(clause)
 return chunks

def vtt_time(value):
 ms=round(value*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02}.{ms%1000:03}'

def captions(voice_id,script):
 timeline=json.loads((SITE/'media/timings'/f'{voice_id}.json').read_text(encoding='utf8'))
 translated=json.loads((SITE/'content/translations.json').read_text(encoding='utf-8-sig'))
 translated=translated.get('cues',translated)
 if isinstance(translated,list):translated={c['id']:c for c in translated}
 for language in LANGUAGES:
  cues=[]
  for source,segment in zip(script,timeline['segments']):
   assert source['id']==segment['id']
   text=source[language] if language in ('en','zh') else translated[source['id']][language]
   chunks=split_caption(text,language);weights=[max(1,len(t.replace('\n',''))) for t in chunks];cursor=segment['start'];end=segment['end']
   span=end-segment['start'];minimum=min(1.15,span/len(chunks));available=span-minimum*len(chunks)
   for index,(chunk,weight) in enumerate(zip(chunks,weights)):
    next_time=end if index==len(chunks)-1 else cursor+minimum+available*weight/sum(weights)
    assert cursor<next_time
    cues.append(f'{source["id"]}-{index+1}\n{vtt_time(cursor)} --> {vtt_time(next_time)}\n{chunk}');cursor=next_time
  path=SITE/'media/captions'/f'{voice_id}-{language}.vtt';path.write_text('WEBVTT\n\n'+'\n\n'.join(cues)+'\n',encoding='utf8')
 print(f'CAPTIONS {voice_id}: seven languages',flush=True)

async def main():
 parser=argparse.ArgumentParser();parser.add_argument('--voice',choices=VOICES);parser.add_argument('--audio-only',action='store_true');parser.add_argument('--captions-only',action='store_true');args=parser.parse_args()
 script=read_script();voice_ids=[args.voice] if args.voice else list(VOICES)
 if not args.captions_only:
  voices=await edge_tts.list_voices();selected=[v for v in voices if v['ShortName'] in {v[1] for v in VOICES.values()}]
  atomic_json(SITE/'content/voice-provenance.json',{'service':'edge_tts','requested':VOICES,'available':selected,'synthetic':True,'note':'Named service voices; no public-person impersonation or age claim.'})
  available={v['ShortName'] for v in selected}
  assert all(VOICES[v][1] in available for v in voice_ids),'Requested voice unavailable; no silent fallback'
  await asyncio.gather(*(synth(v,script,asyncio.Semaphore(1)) for v in voice_ids))
  for voice_id in voice_ids:assemble(voice_id,script)
 if not args.audio_only:
  for voice_id in voice_ids:captions(voice_id,script)

if __name__=='__main__':asyncio.run(main())
