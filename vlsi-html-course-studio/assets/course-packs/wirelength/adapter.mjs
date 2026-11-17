export const apiVersion='1.0';
export const sceneIds=['introduce','measure','move'];
const clone=value=>structuredClone(value);
const clamp=value=>Math.max(0,Math.min(10,value));
const n=value=>Number(value.toFixed(2));
const ease=value=>{const p=Math.max(0,Math.min(1,value));return p*p*(3-2*p);};
export function initialState(){return {a:{x:2,y:2},b:{x:8,y:7},phase:'introduce',reveal:1};}
export function validateState(state){
  if(!state||!sceneIds.includes(state.phase)||!Number.isFinite(state.reveal)||state.reveal<0||state.reveal>1)throw new Error('Invalid wirelength state');
  for(const pin of ['a','b'])for(const axis of ['x','y'])if(!Number.isFinite(state[pin]?.[axis])||state[pin][axis]<0||state[pin][axis]>10)throw new Error('Pin outside the 0–10 board');
  if(state.a.x!==2||state.a.y!==2)throw new Error('A is fixed at (2,2)');
}
export function stateAt(cue,progress){
  if(!sceneIds.includes(cue.sceneId))throw new Error(`Unknown scene ${cue.sceneId}`);
  if(!Number.isFinite(progress)||progress<0||progress>1)throw new Error('Invalid cue progress');
  const state=initialState();state.phase=cue.sceneId;
  if(cue.sceneId==='introduce')state.reveal=.35+.65*ease(progress/.45);
  if(cue.sceneId==='move'){const p=ease(progress/.3);state.b.x=8-3*p;state.b.y=7-3*p;}
  return state;
}
export function metrics(state){validateState(state);const width=Math.abs(state.b.x-state.a.x),height=Math.abs(state.b.y-state.a.y);return [{id:'width',label:'Box width',value:width,unit:'units'},{id:'height',label:'Box height',value:height,unit:'units'},{id:'hpwl',label:'Estimated length',value:width+height,unit:'units'}];}
export function controls(state){return [{id:'bx',label:'B · horizontal position',value:state.b.x,min:0,max:10,step:.1},{id:'by',label:'B · vertical position',value:state.b.y,min:0,max:10,step:.1}];}
export function reduce(state,action){
  validateState(state);const next=clone(state);
  if(action.type==='set'){
    if(!['bx','by'].includes(action.id)||!Number.isFinite(action.value))throw new Error('Unknown or invalid control');
    next.b[action.id==='bx'?'x':'y']=clamp(action.value);
  }else if(action.type==='move'){
    if(!Number.isFinite(action.x)||!Number.isFinite(action.y))throw new Error('Invalid pointer action');next.b={x:clamp(action.x),y:clamp(action.y)};
  }else throw new Error(`Unsupported action ${action.type}`);
  next.phase='measure';next.reveal=1;return next;
}
export function pointerAction(state,point){return {type:'move',x:(point.x*1000-90)/45,y:(500-point.y*560)/45};}
export function feedback(state,previous){
  const length=metrics(state)[2].value;
  if(previous){const delta=length-metrics(previous)[2].value;if(Math.abs(delta)>1e-8)return {text:delta<0?`The estimated length fell by ${n(-delta)} units. Watch both sides of the box.`:`The estimated length rose by ${n(delta)} units. Which side became longer?`,tone:delta<0?'good':'warn'};}
  if(length>=4-1e-9&&length<=6+1e-9)return {text:'This position meets the exercise target. Can you find a different one?',tone:'good'};
  return {text:length<4?'The estimate is below 4. Try moving B a little farther away.':'Move B or adjust its coordinates. Add the box width and height after each change.',tone:'neutral'};
}
export function grade(state,exercise){
  validateState(state);const {minimum,maximum}=exercise.config;
  if(!Number.isFinite(minimum)||!Number.isFinite(maximum)||minimum>maximum)throw new Error('Invalid exercise target');
  const length=metrics(state)[2].value,pass=length>=minimum-1e-9&&length<=maximum+1e-9;
  return {pass,feedback:pass?`Yes. The estimated length is ${n(length)} units, within the target. Other positions can work too.`:`The length is ${length<minimum?'below':'above'} the ${minimum}–${maximum} target. Adjust B and check again.`};
}
export function render(state){
  validateState(state);const x=value=>90+45*value,y=value=>500-45*value;
  const ax=x(state.a.x),ay=y(state.a.y),bx=x(state.b.x),by=y(state.b.y),left=Math.min(ax,bx),top=Math.min(ay,by),w=Math.abs(ax-bx),h=Math.abs(ay-by);
  const values=metrics(state),length=values[2].value;
  const grid=Array.from({length:11},(_,i)=>`<path d="M${x(i)} 50V500 M90 ${y(i)}H540" stroke="#dce4d8" stroke-width="${i===0||i===10?2:1}"/>`).join('');
  const numberTicks=[0,2,4,6,8,10].map(i=>`<text x="${x(i)}" y="527" text-anchor="middle">${i}</text><text x="70" y="${y(i)+5}" text-anchor="end">${i}</text>`).join('');
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 560" width="1000" height="560" role="img" aria-label="Fixed pin A at 2,2; B at ${n(state.b.x)},${n(state.b.y)}. Estimated length ${n(length)}.">
    <rect x="70" y="30" width="490" height="490" rx="24" fill="#f4f6ec"/>
    ${grid}<g font-family="Arial,sans-serif" font-size="15" fill="#5c776d">${numberTicks}</g>
    <g opacity="${state.reveal}"><rect x="${left}" y="${top}" width="${Math.max(w,.5)}" height="${Math.max(h,.5)}" fill="#e8bc62" fill-opacity=".2" stroke="#d39b3e" stroke-width="2" stroke-dasharray="7 6"/>
    <path d="M${ax} ${ay}H${bx}V${by}" fill="none" stroke="#d4805f" stroke-width="6" stroke-linejoin="round"/>
    <text x="${left+w/2}" y="${Math.min(ay,by)-18}" text-anchor="middle" font-family="Arial,sans-serif" font-size="19" font-weight="700" fill="#a76b27">width ${n(values[0].value)}</text>
    <text x="${Math.max(ax,bx)+17}" y="${top+h/2}" font-family="Arial,sans-serif" font-size="18" font-weight="700" fill="#a76b27">${n(values[1].value)}</text></g>
    <circle cx="${ax}" cy="${ay}" r="19" fill="#2d7369" stroke="#fffdf6" stroke-width="5"/><text x="${ax}" y="${ay+6}" text-anchor="middle" font-family="Arial,sans-serif" font-size="17" font-weight="700" fill="white">A</text>
    <circle cx="${bx}" cy="${by}" r="20" fill="#cc7058" stroke="#fffdf6" stroke-width="5"/><text x="${bx}" y="${by+6}" text-anchor="middle" font-family="Arial,sans-serif" font-size="17" font-weight="700" fill="white">B</text>
    <rect x="625" y="72" width="315" height="390" rx="26" fill="#e4edde"/>
    <text x="653" y="116" font-family="Arial,sans-serif" font-size="15" letter-spacing="2" font-weight="700" fill="#427369">THE MEASUREMENT</text>
    <text x="653" y="177" font-family="Arial,sans-serif" font-size="27" font-weight="700" fill="#204e50">Width + height</text>
    <text x="653" y="250" font-family="Arial,sans-serif" font-size="44" font-weight="700" fill="#204e50">${n(values[0].value)} + ${n(values[1].value)}</text>
    <path d="M653 274H910" stroke="#b9cdb7" stroke-width="2"/>
    <text x="653" y="340" font-family="Arial,sans-serif" font-size="54" font-weight="700" fill="#cc7058">${n(length)}<tspan font-size="21" fill="#526e69"> units</tspan></text>
    <text x="653" y="389" font-family="Arial,sans-serif" font-size="17" fill="#526e69">A stays fixed.</text><text x="653" y="417" font-family="Arial,sans-serif" font-size="17" fill="#526e69">B is yours to move.</text>
  </svg>`;
}
