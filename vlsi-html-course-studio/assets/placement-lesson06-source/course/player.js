import {stateAt} from './timeline.js';

const labels={en:'English',zh:'中文',fr:'Français',es:'Español',de:'Deutsch',ja:'日本語',ko:'한국어'};
export const formatTime=t=>`${Math.floor(t/60)}:${String(Math.floor(t%60)).padStart(2,'0')}`;
export function semanticPosition(t,clock){
 const cue=clock.segments.find(s=>t>=s.start&&t<(s.sceneEnd??s.end))||[...clock.segments].reverse().find(s=>t>=s.start)||clock.segments[0];
 return {cueId:cue.id,progress:Math.max(0,Math.min(1,(t-cue.start)/Math.max(.01,(cue.sceneEnd??cue.end)-cue.start)))};
}
export function semanticTime(position,clock){const cue=clock.segments.find(s=>s.id===position.cueId)||clock.segments[0];return cue.start+position.progress*((cue.sceneEnd??cue.end)-cue.start)}

export function createPlayer({script,manifest,clocks,onTransfer}){
 const video=document.querySelector('#film'),voiceSelect=document.querySelector('#voice'),captionSelect=document.querySelector('#captions'),speed=document.querySelector('#speed'),status=document.querySelector('#video-status');
 let voice=manifest.tracks[0].id,loadedVoice=null,token=0,pendingPosition=null,pendingResume=null;
 const currentClock=()=>clocks[voice];
 const fullscreen=()=>!!((document.fullscreenElement&&(document.fullscreenElement===video||document.fullscreenElement.contains(video)))||video.webkitDisplayingFullscreen);
 function renderCaption(){
  const lang=captionSelect.value,strip=document.querySelector('#caption-strip'),track=[...video.textTracks].find(t=>t.language===lang);
  strip.hidden=lang==='off'||fullscreen();
  document.querySelector('#caption-language').textContent=lang==='off'?'':`CAPTIONS · ${labels[lang]}`;
  document.querySelector('#caption-text').textContent=track?.activeCues?[...track.activeCues].map(cue=>cue.text.replace(/\n/g,['zh','ja'].includes(lang)?'':' ')).join(' '):'';
 }
 function captions(){
  const lang=captionSelect.value;
  for(const track of video.textTracks)track.mode=track.language===lang?(fullscreen()?'showing':'hidden'):'disabled';
  const link=document.querySelector('#download-caption');link.hidden=lang==='off';
  if(lang!=='off'){link.href=manifest.tracks.find(t=>t.id===voice).captions[lang];link.download=`placement-${voice}-${lang}.vtt`}
  renderCaption();
 }
 function update(){
  const position=semanticPosition(video.currentTime,currentClock()),cue=script.cues.find(c=>c.id===position.cueId);
  document.querySelector('#now-playing').textContent=`${cue.chapter} / ${cue.title}`;
  document.querySelectorAll('[data-chapter]').forEach(b=>{const active=b.dataset.chapter===cue.chapter;b.classList.toggle('active',active);if(active)b.setAttribute('aria-current','true');else b.removeAttribute('aria-current')});
  document.querySelectorAll('[data-transcript]').forEach(b=>b.classList.toggle('active',b.dataset.transcript===cue.id));
  window.playerState={voice,cueId:cue.id,time:video.currentTime,duration:currentClock().duration};
 }
 function chapters(){
  const parent=document.querySelector('#chapters');parent.replaceChildren();
  for(const chapter of script.chapters){const segment=currentClock().segments.find(s=>s.chapter===chapter.id);const button=document.createElement('button');button.dataset.chapter=chapter.id;const stamp=document.createElement('span');stamp.textContent=formatTime(segment.start);const text=document.createElement('span');text.className='chapter-copy';text.textContent=`${chapter.id} / ${chapter.title}`;button.append(stamp,text);button.onclick=()=>goToCue(segment.id);parent.append(button)}
  document.querySelector('#film-length').textContent=`${formatTime(currentClock().duration)} · 8 CHAPTERS`;
 }
 async function switchVoice(next,{position=null,resume=null}={}){
  const request=++token,previousClock=clocks[loadedVoice||voice];
  const target=position||pendingPosition||semanticPosition(video.currentTime,previousClock),shouldPlay=resume??pendingResume??(!video.paused&&!video.ended),rate=+speed.value,firstLoad=loadedVoice===null;
  pendingPosition=target;pendingResume=shouldPlay;document.querySelector('#take-state').disabled=true;
  voice=next;voiceSelect.value=next;video.pause();status.textContent='Loading the selected narration…';
  const track=manifest.tracks.find(t=>t.id===next);chapters();
  video.querySelectorAll('track').forEach(t=>t.remove());
  for(const [lang,src] of Object.entries(track.captions)){const element=document.createElement('track');element.kind='subtitles';element.srclang=lang;element.label=labels[lang];element.src=src;video.append(element);element.track.addEventListener('cuechange',renderCaption);element.addEventListener('load',renderCaption)}
  const ready=new Promise((resolve,reject)=>{const done=()=>{cleanup();resolve()},fail=()=>{cleanup();reject(new Error('Video media could not be loaded.'))};const cleanup=()=>{video.removeEventListener('loadedmetadata',done);video.removeEventListener('error',fail)};video.addEventListener('loadedmetadata',done,{once:true});video.addEventListener('error',fail,{once:true})});
  video.src=track.video;video.load();captions();
  document.querySelector('#download-film').href=track.video;document.querySelector('#download-film').download=`placement-${next}.mp4`;
  try{await ready;if(request!==token)return;loadedVoice=next;pendingPosition=null;pendingResume=null;video.currentTime=firstLoad&&target.cueId===script.cues[0].id&&target.progress===0?0:Math.min(video.duration-.05,semanticTime(target,currentClock()));video.playbackRate=rate;captions();document.querySelector('#take-state').disabled=false;status.textContent='';update();if(shouldPlay)await video.play().catch(()=>{status.textContent='Press play to continue with the selected voice.'})}
  catch(error){if(request===token)status.textContent=location.protocol==='file:'?'Start START_COURSE.cmd and open the localhost address to use the lesson.':'The video could not load. Keep the media folder with the website and use the included local server.'}
 }
 function goToCue(cueId,{play=true}={}){const segment=currentClock().segments.find(s=>s.id===cueId);if(!segment)return;document.querySelector('#watch').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});if(pendingPosition){switchVoice(voice,{position:{cueId,progress:0},resume:play});return}video.currentTime=segment.start;update();if(play)video.play().catch(()=>{})}
 voiceSelect.onchange=()=>switchVoice(voiceSelect.value);captionSelect.onchange=captions;speed.onchange=()=>video.playbackRate=+speed.value;
 video.addEventListener('timeupdate',update);
 video.addEventListener('timeupdate',renderCaption);video.addEventListener('seeked',renderCaption);
 document.addEventListener('fullscreenchange',captions);video.addEventListener('webkitbeginfullscreen',captions);video.addEventListener('webkitendfullscreen',captions);
 video.textTracks.addEventListener('change',()=>{const showing=[...video.textTracks].find(t=>t.mode==='showing');if(showing&&!fullscreen()){captionSelect.value=showing.language;captions()}else renderCaption()});
 document.querySelector('#take-state').onclick=()=>{video.pause();const state=stateAt(video.currentTime,currentClock(),script);onTransfer(state);document.querySelector('#lab').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'})};
 const transcript=document.querySelector('#transcript');
 for(const chapter of script.chapters){const heading=document.createElement('h3');heading.textContent=`${chapter.id} / ${chapter.title}`;transcript.append(heading);for(const cue of script.cues.filter(c=>c.chapter===chapter.id)){const b=document.createElement('button');b.dataset.transcript=cue.id;b.textContent=cue.en;b.onclick=()=>goToCue(cue.id);transcript.append(b)}}
 switchVoice(voice,{position:{cueId:script.cues[0].id,progress:0},resume:false});
 return {goToCue,switchVoice,getVoice:()=>voice,getClock:currentClock,getState:()=>stateAt(video.currentTime,currentClock(),script)};
}
