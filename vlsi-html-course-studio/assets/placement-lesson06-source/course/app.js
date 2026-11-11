import {createPlayer} from './player.js';
import {mountLab} from './lab.js';
import {mountExercises} from './exercises.js';

try{
 const [script,manifest]=await Promise.all(['content/script.json','media/manifest.json'].map(path=>fetch(path).then(r=>{if(!r.ok)throw new Error(path);return r.json()})));
 const clocks=Object.fromEntries(await Promise.all(manifest.tracks.map(async track=>[track.id,await fetch(track.timing).then(r=>r.json())])));
 let lab;
 const player=createPlayer({script,manifest,clocks,onTransfer:state=>lab.takeState(state)});
 lab=mountLab(document.querySelector('#lab-root'),{onReplay:cueId=>player.goToCue(cueId)});
 mountExercises(document.querySelector('#exercise-root'),{onTry:state=>{lab.takeState(state);document.querySelector('#lab').scrollIntoView()},onReplay:cueId=>player.goToCue(cueId),getLabState:()=>lab.getState()});
 document.querySelectorAll('[data-replay]').forEach(button=>button.onclick=()=>player.goToCue(button.dataset.replay));
 document.querySelector('#print-notes').onclick=()=>window.print();
 window.course={player,lab,script,manifest,clocks};window.courseReady=true;
}catch(error){
 console.error(error);
 document.querySelector('#video-status').textContent=location.protocol==='file:'?'To open this lesson, run START_COURSE.cmd and use the localhost address.':'The lesson data could not load. Check that all website folders were copied, then reload.';
}
