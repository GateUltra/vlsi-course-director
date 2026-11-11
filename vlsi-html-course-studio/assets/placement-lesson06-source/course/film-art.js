// Code-native illustration primitives. All animation is a pure function of cue progress.
import {ScientistRig} from './scientist-rig.js';
export const palette={ink:'#253f50',green:'#397f75',coral:'#c56870',gold:'#ba8536',blue:'#6987bf',paper:'#fff9ec'};
export const esc=s=>String(s??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
export const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v));
export const ease=v=>{v=clamp(v);return v*v*(3-2*v)};
export const R=(x,y,w,h,c='#fffdf7',a='')=>`<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="${c}" ${a}/>`;
export const T=(x,y,s,size=24,c=palette.ink,a='')=>`<text x="${x}" y="${y}" font-size="${size}" fill="${c}" ${a}>${esc(s)}</text>`;
export const line=(x,y,x2,y2,c=palette.green,w=3,a='')=>`<path d="M${x} ${y}L${x2} ${y2}" fill="none" stroke="${c}" stroke-width="${w}" stroke-linecap="round" ${a}/>`;
export const panel=(x,y,w,h,c='#fffdf7')=>R(x+4,y+7,w,h,'#c7bea2','rx="24" opacity=".22"')+R(x,y,w,h,c,'rx="24" stroke="#b5c7b2" stroke-width="2"');
export const tag=(x,y,s,c=palette.green)=>T(x,y,s,17,c,'letter-spacing="2" font-weight="700"');
export function headline(a,b){return T(86,268,a,64,palette.ink,'font-weight="700" letter-spacing="-2"')+T(86,344,b,64,palette.green,'font-weight="700" letter-spacing="-2"');}
export function bubble(x,y,w,title,lines=[],tone=palette.green){return `<g class="film-bubble">${panel(x,y,w,145)}<path d="M${x} ${y+68}l-23 22 23 9" fill="#fffdf7" stroke="#b5c7b2" stroke-width="2"/>${T(x+24,y+42,title,25,tone,'font-weight="700"')}${lines.map((s,i)=>T(x+24,y+83+i*32,s,23,'#527369')).join('')}</g>`;}
export function teacher(s,{mode='head',pose='point',x=103,y=739,scale=1,progress=1,fromPose}={}){
  // This is a small expressive moustache, not phoneme lip-sync. A direct per-voice
  // render may supply a measured envelope; retimed cue pictures use the same subtle motion.
  const p=s.progress??0;
  const envelope=s.mouth??(Math.sin(p*54)**2*.36*(p<.95?1:0));
  return ScientistRig({x,y,scale,mode,pose,fromPose,progress,t:p*8,mouth:envelope});
}
export function metric(x,y,label,value,color,sub,w=245){return panel(x,y,w,166)+R(x,y,w,7,color,'rx="3"')+tag(x+22,y+39,label,'#526b66')+T(x+22,y+105,value,52,color,'font-weight="700"')+T(x+22,y+142,sub,17,'#60776d');}
export function littleChip(progress=0,{x=1020,y=230,size=700}={}){
  const p=ease(progress),c=['#6ca99a','#e4b34f','#db8b94','#7d9dc8'],sx=size/700;
  let out=R(25,25,650,650,'#a4b9a6','rx="54"')+R(42,42,616,616,'#f2f2da','rx="45" stroke="#527b6d" stroke-width="3"');
  for(let i=0;i<15;i++)for(let side=0;side<4;side++)out+=`<g transform="rotate(${side*90} 350 350)">${R(80+i*38,4,15,44,'#d6b96f','rx="3" stroke="#b8984e"')}</g>`;
  for(let row=0;row<9;row++)for(let col=0;col<10;col++){
    const q=ease((progress*1.6-(row+col)*.025));
    const cx=82+col*54,cy=90+row*61,dx=(1-q)*(col-4.5)*12,dy=(1-q)*(row-4)*12;
    out+=`<g opacity="${.15+.85*q}" transform="translate(${dx} ${dy})">${R(cx,cy,42,43,c[(row*3+col)%4],'rx="7" stroke="#608476" stroke-width="1"')}${R(cx+5,cy+6,29,5,'#fff','rx="2" opacity=".25"')}</g>`;
  }
  for(let k=0;k<7;k++){
    const yy=114+k*70, xx=104+k*73;
    out+=`<path d="M90 ${yy}H${xx}V${650-yy/2}H610" fill="none" stroke="#fffbea" stroke-width="3" stroke-opacity=".5" stroke-dasharray="${1000*p} 1000"/>`;
  }
  out+=T(350,635,'MANY CELLS. ONE CONNECTED SYSTEM.',15,'#43675d','text-anchor="middle" letter-spacing="1.3"');
  return `<g transform="translate(${x} ${y}) scale(${sx})">${out}</g>`;
}
export function pipeline(progress=0,active=1){
 const labels=['FLOORPLAN','PLACE','LEGALIZE','ROUTE'],notes=['Choose the spaces','Choose cell positions','Align rows; remove overlap','Build physical wires'];
 return labels.map((label,i)=>{const x=95+i*445,on=ease(progress*5-i*.4),color=i===active?palette.green:'#93aa96';return `<g opacity="${.4+.6*on}" transform="translate(0 ${(1-on)*25})">${panel(x,440,390,220,i===active?'#e1efe3':'#fffdf7')}${tag(x+28,484,`${String(i+1).padStart(2,'0')} / ${label}`,color)}${T(x+28,540,notes[i],24)}${i===0?R(x+30,568,88,53,'#e5c684','rx="5"')+R(x+128,568,210,53,'#bfd3c2','rx="5"'):i===1?Array.from({length:7},(_,j)=>R(x+30+j*45,578+(j%2)*12,30,27,['#7cae9e','#d4a24b','#cc8190'][j%3],'rx="5"')).join(''):i===2?Array.from({length:7},(_,j)=>R(x+30+j*45,585,30,27,'#7cae9e','rx="3"')).join(''):`<path d="M${x+35} 595H${x+120}V570H${x+240}V610H${x+340}" fill="none" stroke="#ba8536" stroke-width="5"/>`}${i<3?T(x+409,563,'→',32,'#748d7c'):''}</g>`}).join('');
}
export function slots(progress,{capacity=2,count=5,x=100,y=460,w=800}={}){
 const cell=82,gap=48,start=x+35;
 let out=panel(x,y,w,230)+tag(x+28,y+42,`ONE REGION · ${capacity} PLACES`);
 for(let i=0;i<count;i++){
  const on=ease(progress*4-i*.25),good=i<capacity,color=good?'#8bb99b':'#de8d94';
  out+=`<g opacity="${on}" transform="translate(0 ${(1-on)*-25})">${R(start+i*(cell+gap),y+78,cell,74,color,'rx="13" stroke="#658575" stroke-width="2"')}${T(start+i*(cell+gap)+cell/2,y+127,String(i+1),30,'#fff','text-anchor="middle" font-weight="700"')}</g>`;
 }
 out+=T(x+38,y+202,`${Math.min(count,capacity)} fit`,26,palette.green,'font-weight="700"')+T(x+w-30,y+202,`${Math.max(0,count-capacity)} extra = overflow`,26,palette.coral,'text-anchor="end" font-weight="700"');
 return out;
}
export function phaseRail(phase,iteration=0,y=410){
 const phases=[['force','PULL','6 force updates'],['quadratic','REFINE','3 averaging updates'],['spread','SPREAD','density push'],['reconnect','RECONNECT','gentle wire pull']];
 return phases.map(([id,name,sub],i)=>{const x=96+(i%2)*410,yy=y+Math.floor(i/2)*112,hot=phase===id;return R(x,yy,390,94,hot?'#e0eddf':'#fffdf7',`rx="15" stroke="${hot?'#6e9e86':'#c6d0b7'}" stroke-width="2"`)+T(x+20,yy+37,name,24,hot?palette.green:'#728271','font-weight="700"')+T(x+20,yy+69,sub,20,'#5c7568')}).join('')+T(103, y+260,iteration?`DENSITY ROUND ${iteration} / 12`:'First shorten connections; then alternate.',21,'#507468','letter-spacing="1"');
}
