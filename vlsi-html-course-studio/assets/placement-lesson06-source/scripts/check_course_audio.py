"""Mechanical media/caption checks; does not claim human listening or native review."""
import hashlib,json,re,subprocess,sys,wave
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'course';PROD=ROOT/'production'
sys.path.insert(0,str(ROOT/'scripts'))
from make_course_audio import VOICES,LANGUAGES,read_script,duration,split_caption
script=read_script();output={'voices':{},'captionPairs':0,'nativeTranslationReview':False,'subjectiveListeningReview':False}
translated=json.loads((SITE/'content/translations.json').read_text(encoding='utf-8-sig'))['cues']
number_pattern=re.compile(r'\d+(?:[.,]\d+)*')
# Every numeric token must survive intact on one caption line, in its original order.
# Synthetic boundary positions exercise both sides of the 24-character CJK wrap.
for language in LANGUAGES:
 for n in range(18,28):
  sample=('配' * n if language in ('ja','zh') else 'prefix ' * n)+'48.1 '+('長' * n if language in ('ja','zh') else ' words ' * n)+'48.5 and 48,1.'
  chunks=split_caption(sample,language)
  assert [number for chunk in chunks for line in chunk.splitlines() for number in number_pattern.findall(line)]==number_pattern.findall(sample),(language,n,chunks)
for source in script:
 for language in LANGUAGES:
  original=source[language] if language in ('en','zh') else translated[source['id']][language]
  chunks=split_caption(original,language)
  assert [number for chunk in chunks for line in chunk.splitlines() for number in number_pattern.findall(line)]==number_pattern.findall(original),(source['id'],language,chunks)
output['numericTokenRegression']='48.1 / 48.5 / 48,1 remain intact across sentence, caption and line boundaries; all 39 cues × seven languages checked'
def seconds(s):
 h,m,t=s.split(':');return 3600*int(h)+60*int(m)+float(t)
for id,(lang,name,label) in VOICES.items():
 clock=json.loads((SITE/'media/timings'/f'{id}.json').read_text(encoding='utf8'))
 assert len(clock['segments'])==len(script) and clock['voice']==name
 previous=0
 for source,s in zip(script,clock['segments']):
  assert source['id']==s['id'] and source[lang]==s['text']
  assert previous<=s['start']<s['end']<s['sceneEnd']<=clock['duration']
  assert abs(s['end']-s['start']-duration(PROD/id/'clips'/f'{s["id"]}.mp3'))<.002
  previous=s['sceneEnd']
  cache=PROD/id/'clips'/f'{s["id"]}.sha256'
  assert cache.read_text()==hashlib.sha256(json.dumps([source[lang],name,'+0%','+0Hz'],ensure_ascii=False).encode()).hexdigest()
 audio=PROD/id/'mix.wav';assert abs(duration(audio)-clock['duration'])<.002
 with wave.open(str(audio)) as w:
  assert w.getnchannels()==1 and w.getframerate()==48000
  samples=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(float)/32768
  peak=float(abs(samples).max());rms=float(np.sqrt(np.mean(samples*samples)))
  assert .01<rms<.3 and peak<.95
 correlations=[]
 for index in (0,len(script)//2,len(script)-1):
  s=clock['segments'][index]
  pcm=subprocess.check_output(['ffmpeg','-v','error','-i',str(PROD/id/'clips'/f'{s["id"]}.mp3'),'-f','s16le','-ac','1','-ar','48000','-'])
  original=np.frombuffer(pcm,dtype='<i2').astype(float)/32768
  begin=round(s['start']*48000);length=min(48000*3,len(original))
  correlation=float(np.corrcoef(original[:length],samples[begin:begin+length])[0,1])
  assert correlation>.95,(id,s['id'],correlation)
  correlations.append({'cue':s['id'],'atSeconds':s['start'],'correlation':round(correlation,5)})
 envelope=json.loads((SITE/'media/timings'/f'{id}-envelope.json').read_text())
 assert len(envelope['values'])==int(np.ceil(clock['duration']*25))
 assert max(envelope['values'][:15])==0 and all(0<=v<=1 for v in envelope['values'])
 pairs={}
 for language in LANGUAGES:
  text=(SITE/'media/captions'/f'{id}-{language}.vtt').read_text(encoding='utf8')
  assert text.startswith('WEBVTT\n\n')
  previous=0;ids=set();count=0;shortest=999;longest=0;numbers={}
  for block in text.strip().split('\n\n')[1:]:
   lines=block.splitlines();assert len(lines) in (3,4)
   cue_id,number=lines[0].rsplit('-',1);ids.add(cue_id)
   start,end=map(seconds,lines[1].split(' --> '));assert previous<=start<end<=clock['duration']+.001
   assert all(line.strip() for line in lines[2:])
   numbers.setdefault(cue_id,[]).extend(number for line in lines[2:] for number in number_pattern.findall(line))
   previous=end;count+=1;shortest=min(shortest,end-start);longest=max(longest,max(map(len,lines[2:])))
  assert ids=={s['id'] for s in script}
  for source in script:
   original=source[language] if language in ('en','zh') else translated[source['id']][language]
   assert numbers[source['id']]==number_pattern.findall(original),(id,language,source['id'],numbers[source['id']])
  pairs[language]={'cues':count,'minimumSeconds':round(shortest,3),'maximumLineCharacters':longest}
  output['captionPairs']+=1
 subprocess.run(['ffmpeg','-v','error','-i',str(audio),'-f','null','NUL'],check=True)
 output['voices'][id]={'voice':name,'duration':clock['duration'],'peak':round(peak,5),'rms':round(rms,5),'captionChecks':pairs,'measuredClipTiming':'pass','exactScriptCache':'pass','fullDecode':'pass','beginningMiddleEndMasterAlignment':correlations}
(ROOT/'review-course/audio-checks.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(output,ensure_ascii=False,indent=2))
