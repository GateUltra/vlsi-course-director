import {loadStudio,copy,escapeText as esc,snapshotAt,importSnapshot,semanticPosition,semanticTime,assertJson} from './core.mjs';
import {scientist} from './scene.mjs';

const $ = selector => document.querySelector(selector);
const video = $('#video');
const languageNames = {en:'English',zh:'中文',fr:'Français',es:'Español',de:'Deutsch',ja:'日本語',ko:'한국어'};
function showError(error) { $('#error').hidden=false; $('#error').textContent=error.message||String(error); }
try {
  const {course,manifest,adapter,clocks} = await loadStudio();
  document.title=course.title; $('#title').textContent=course.title; $('#description').textContent=course.description;
  $('#scope').textContent=course.scope||course.description;
  let currentVoice=manifest.defaultVoice, request=0, pending=null, cancelLoad=null;
  let labState=copy(adapter.initialState(course)), imported=null, resetState=copy(labState);
  let selectedCaption='off', rate=1, pointer=null;
  const getClock=()=>clocks.get(currentVoice);
  const updateCaptions=()=>{
    const fullscreen=document.fullscreenElement===video || Boolean(video.webkitDisplayingFullscreen);
    let active=[];
    for(let i=0;i<video.textTracks.length;i++) {
      const track=video.textTracks[i], selected=track.language===selectedCaption;
      track.mode=selected?(fullscreen?'showing':'hidden'):'disabled';
      if(selected && track.activeCues)active=[...track.activeCues].map(cue=>cue.text);
    }
    $('#captions').textContent=active.join('\n');
    $('#captions').hidden=fullscreen||selectedCaption==='off'||!active.length;
  };
  const refreshChapters=()=>{
    const position=pending?.position||semanticPosition(video.currentTime||0,getClock());
    const cue=course.cues.find(item=>item.id===position.cueId);
    for(const button of document.querySelectorAll('.chapter')) {
      const active=button.dataset.chapter===cue.chapter;
      button.classList.toggle('active',active); button.setAttribute('aria-current',active?'step':'false');
    }
  };
  async function selectVoice(id) {
    const track=manifest.tracks.find(item=>item.id===id);
    if(!track)throw new Error(`Unknown voice ${id}`);
    const source=(track.sources||[{src:track.video,type:'video/mp4; codecs="avc1.640028, mp4a.40.2"'}]).find(item=>video.canPlayType(item.type));
    if(!source)throw new Error(`This browser cannot play the available formats for ${track.label||id}. Try a browser with VP8/Opus or H.264/AAC support.`);
    const previous=pending?{...pending,position:copy(pending.position)}:{position:semanticPosition(video.currentTime||0,getClock()),playing:!video.paused};
    const token=++request;
    cancelLoad?.();
    pending={position:previous.position,playing:previous.playing};
    $('#error').hidden=true;$('#error').textContent='';
    $('#take').disabled=true; $('#voice').value=id;
    video.pause();
    video.querySelectorAll('track').forEach(element=>element.remove());
    for(const [language,path] of Object.entries(track.captions)) {
      const element=document.createElement('track'); element.kind='subtitles';element.srclang=language;element.label=languageNames[language]||language;element.src=path;
      element.addEventListener('load',updateCaptions); element.addEventListener('error',()=>showError(new Error(`Subtitle could not load: ${language}`)));
      video.append(element);
      element.track.addEventListener('cuechange',updateCaptions);
    }
    video.src=source.src;
    const loaded=await new Promise((resolve,reject)=>{
      const clean=()=>{clearTimeout(timer);video.removeEventListener('loadedmetadata',done);video.removeEventListener('error',bad);};
      const done=()=>{clean();resolve(true);};
      const bad=()=>{clean();reject(new Error(`Video unavailable: ${track.label||id}`));};
      const timer=setTimeout(()=>{clean();reject(new Error(`Video metadata timed out: ${id}`));},30000);
      cancelLoad=()=>{clean();resolve(false);};
      video.addEventListener('loadedmetadata',done,{once:true});video.addEventListener('error',bad,{once:true});video.load();
    });
    if(!loaded||token!==request)return false;
    currentVoice=id; window.clock=getClock();
    video.currentTime=Math.min(semanticTime(pending.position,getClock()),Math.max(0,video.duration-.001));
    video.playbackRate=rate;
    const resume=pending.playing;pending=null;cancelLoad=null;
    updateCaptions();refreshChapters();$('#take').disabled=false;
    if(resume)await video.play().catch(()=>{});
    return true;
  }
  function seekCue(id) {
    if(!course.cues.some(cue=>cue.id===id))throw new Error(`Unknown cue ${id}`);
    const position={cueId:id,progress:0,region:'cue'};
    if(pending)pending.position=position;
    else video.currentTime=semanticTime(position,getClock());
    refreshChapters();updateCaptions();
  }
  function setCaption(language) {
    if(language!=='off'&&!manifest.captionLanguages.includes(language))throw new Error(`Unknown captions ${language}`);
    selectedCaption=language;$('#caption').value=language;updateCaptions();
  }
  function setRate(value) {if(!Number.isFinite(value)||value<=0)throw new Error('Invalid playback rate');rate=value;video.playbackRate=rate;$('#speed').value=String(rate);}
  function renderLab(previous=null,rebuild=false) {
    adapter.validateState(labState);assertJson(labState);
    const cue=course.cues.find(item=>item.id===(imported?.cueId||course.cues[0].id));
    $('#board').innerHTML=adapter.render(copy(labState),{mode:'lab',cue,progress:imported?.progress||0});
    const values=adapter.metrics(copy(labState));
    $('#metrics').innerHTML=values.map(value=>`<div class="metric" data-metric="${esc(value.id)}"><span>${esc(value.label)}</span><strong>${esc(Number.isInteger(value.value)?value.value:Number(value.value.toFixed(2)))} <small>${esc(value.unit||'')}</small></strong></div>`).join('');
    const message=adapter.feedback(copy(labState),previous?copy(previous):null);
    $('#feedback').textContent=message.text;$('#feedback').dataset.tone=message.tone;
    const controls=adapter.controls(copy(labState));
    if(rebuild) {
      $('#lab-controls').innerHTML='';
      for(const control of controls) {
        const label=document.createElement('label');label.className='lab-control';
        const row=document.createElement('span');row.className='label';
        const name=document.createElement('span');name.textContent=control.label;
        const output=document.createElement('output');output.dataset.output=control.id;
        row.append(name,output);
        const input=document.createElement('input');input.type='range';input.dataset.control=control.id;input.setAttribute('aria-label',control.label);
        input.addEventListener('input',()=>dispatch({type:'set',id:control.id,value:Number(input.value)}));
        label.append(row,input);$('#lab-controls').append(label);
      }
    }
    for(const control of controls) {
      const input=[...document.querySelectorAll('[data-control]')].find(element=>element.dataset.control===control.id);
      if(!input)throw new Error('Adapter control IDs changed without a new import');
      input.min=control.min;input.max=control.max;input.step=control.step;input.value=control.value;
      input.closest('label').querySelector('output').textContent=Number(control.value.toFixed(2));
    }
    for(const result of document.querySelectorAll('.result'))result.textContent='';
  }
  function dispatch(action) { const previous=copy(labState);const next=adapter.reduce(copy(labState),copy(action));assertJson(next);adapter.validateState(next);labState=copy(next);renderLab(previous);return copy(labState); }
  function adopt(snapshot) {
    imported=importSnapshot(snapshot,course,adapter); labState=copy(imported.state);resetState=copy(labState);
    $('#lab-origin').textContent=`Transferred video state · ${course.cues.find(c=>c.id===imported.cueId).title} · ${Math.round(imported.progress*100)}% through the scene`;
    renderLab(null,true);return copy(imported);
  }
  function takeScene(scroll=true) {
    if(pending)throw new Error('Wait for the selected voice to load');
    if(video.error)throw new Error('Video playback failed; choose a working voice/source before transferring a scene');
    video.pause();const snapshot=snapshotAt(video.currentTime,getClock(),course,adapter);adopt(snapshot);
    if(scroll)$('#lab').scrollIntoView({behavior:'smooth',block:'start'});
    return snapshot;
  }
  function resetLab(){labState=copy(resetState);renderLab(null,true);return copy(labState);}
  function gradeExercise(id) {
    const exercise=course.exercises.find(item=>item.id===id);if(!exercise)throw new Error('Unknown exercise');
    const result=adapter.grade(copy(labState),copy(exercise));
    if(typeof result.pass!=='boolean'||typeof result.feedback!=='string')throw new Error('Invalid grade response');
    const node=[...document.querySelectorAll('[data-result]')].find(item=>item.dataset.result===id);
    node.textContent=result.feedback;node.classList.toggle('pass',result.pass);return result;
  }
  for(const track of manifest.tracks)$('#voice').add(new Option(track.label||track.id,track.id));
  for(const language of manifest.captionLanguages)$('#caption').add(new Option(languageNames[language]||language,language));
  const chapters=new Map();for(const cue of course.cues)if(!chapters.has(cue.chapter))chapters.set(cue.chapter,cue);
  for(const [chapter,cue] of chapters) {
    const button=document.createElement('button');button.className='chapter';button.dataset.chapter=chapter;button.dataset.cue=cue.id;
    button.innerHTML=`<span class="number">${esc(chapter)}</span><span>${esc(cue.title)}</span>`;
    button.addEventListener('click',()=>seekCue(cue.id));$('#chapters').append(button);
  }
  for(const exercise of course.exercises) {
    const panel=document.createElement('article');panel.className='exercise';
    const prompt=document.createElement('h3');prompt.textContent=exercise.prompt;
    const check=document.createElement('button');check.textContent='Check my model';check.dataset.exercise=exercise.id;check.addEventListener('click',()=>gradeExercise(exercise.id));
    const result=document.createElement('p');result.className='result';result.dataset.result=exercise.id;result.setAttribute('aria-live','polite');
    panel.append(prompt,check,result);$('#exercises').append(panel);
  }
  $('#mentor-avatar').innerHTML=`<svg viewBox="-105 -80 210 210" aria-hidden="true">${scientist(0,true)}</svg>`;
  $('#voice').addEventListener('change',()=>selectVoice($('#voice').value).catch(showError));
  $('#caption').addEventListener('change',()=>setCaption($('#caption').value));
  $('#speed').addEventListener('change',()=>setRate(Number($('#speed').value)));
  $('#take').addEventListener('click',()=>takeScene());$('#reset').addEventListener('click',resetLab);
  video.addEventListener('timeupdate',()=>{refreshChapters();updateCaptions();});video.addEventListener('seeked',updateCaptions);
  video.addEventListener('error',()=>{
    if(pending)return; // The metadata loader reports its own source-specific failure.
    $('#take').disabled=true;
    showError(new Error(`Video playback failed: ${video.error?.message||'the browser could not decode this media'}. Try another voice or browser.`));
  });
  document.addEventListener('fullscreenchange',updateCaptions);video.addEventListener('webkitbeginfullscreen',updateCaptions);video.addEventListener('webkitendfullscreen',updateCaptions);
  const pointAction=event=>{
    if(!adapter.pointerAction)return;
    const rect=$('#board').getBoundingClientRect();
    const action=adapter.pointerAction(copy(labState),{x:(event.clientX-rect.left)/rect.width,y:(event.clientY-rect.top)/rect.height});
    if(action)dispatch(action);
  };
  $('#board').addEventListener('pointerdown',event=>{if(!adapter.pointerAction)return;pointer=event.pointerId;$('#board').setPointerCapture(pointer);pointAction(event);});
  $('#board').addEventListener('pointermove',event=>{if(pointer===event.pointerId)pointAction(event);});
  for(const name of ['pointerup','pointercancel'])$('#board').addEventListener(name,event=>{if(pointer===event.pointerId){pointer=null;if($('#board').hasPointerCapture(event.pointerId))$('#board').releasePointerCapture(event.pointerId);}});
  renderLab(null,true);
  window.buildIdentity=manifest.buildIdentity;window.clock=getClock();
  window.studio={course,manifest,adapter,clocks,get clock(){return getClock();},get voice(){return currentVoice;},get loading(){return Boolean(pending);},get state(){return copy(labState);},get imported(){return copy(imported);},get captions(){return selectedCaption;},snapshotAt:(time,voice=currentVoice)=>snapshotAt(time,clocks.get(voice),course,adapter),importSnapshot:adopt,takeScene,dispatch,resetLab,gradeExercise,selectVoice,seekCue,setCaption,setRate};
  await selectVoice(currentVoice);window.ready=true;
} catch(error) {showError(error);console.error(error);}
