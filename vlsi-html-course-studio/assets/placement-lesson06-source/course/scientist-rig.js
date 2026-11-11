import {scientistArt} from './scientist-art.js';

// CC0 j4p4n head + an original articulated companion body. No external runtime assets.
const ink='#243d4d', coat='#53788c', coatLight='#6b91a3', skin='#efc095';
const clamp=n=>Math.max(0,Math.min(1,n));
const ease=n=>{n=clamp(n);return n*n*(3-2*n)};
const lerp=(a,b,p)=>a+(b-a)*p;
const path=(d,fill,extra='')=>`<path d="${d}" fill="${fill}" stroke="${ink}" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round" ${extra}/>`;

function head({x=40,y=0,t=0,mouth=0,tilt=0,scale=1}){
  let svg=scientistArt
    .replace('viewBox="20 0 100 173"','viewBox="20 0 78 72"')
    .replace('width="300"','width="160"').replace('height="519"','height="148"');
  // A closed smile, always. Speech gently lifts the moustache; no jaw, teeth or tongue.
  // The source's path14910 is its toothy smile. Replace it once, without stacking faces.
  const speech=clamp(mouth), lift=.24*speech, curl=.7*speech;
  svg=svg.replace(/<path\b(?=[^>]*id="path14910")[^>]*\/>/,
    `<path data-mouth="closed" d="M62 67.4 Q69 69 76.5 66.8" fill="none" stroke="#785b48" stroke-width=".65" stroke-linecap="round"/>
    <g class="moustache" transform="translate(0 ${-lift})" fill="#f7f6ee" stroke="#72716b" stroke-width=".5" stroke-linejoin="round">
      <path transform="rotate(${-curl} 69 61.5)" d="M69 61.5 C65 59 60 62 55.7 66 Q60.7 66.5 63 64.8 L62.8 66.2 Q67.4 65.7 69 62.8Z"/>
      <path transform="rotate(${curl} 69 61.5)" d="M69 61.5 C72 58.6 76.6 59.6 80.3 63.6 Q77 65.3 74.4 63.8 L75 65.3 Q71.1 65.3 69 62.8Z"/>
    </g>`);
  // Root SVG clips all original legs and torso. Hair, glasses and face stay sourced.
  return `<g transform="translate(${x} ${y}) scale(${scale}) rotate(${tilt} 80 135)">${svg}</g>`;
}

function hand(kind='open',side=1){
  if(kind==='point'||kind==='think'){
    const tip=kind==='think'?38:29;
    return `<g>${path(`M-9 0 L-10 16 Q-8 23 2 21 L8 18 L9 5 L6-3 L5-${tip} Q1-${tip+5}-1-${tip} L-1-8 L-4-13 Q-9-16-10-11 L-7 0Z`,skin)}<path d="M0 3 L6 3 M-1 8 L6 8" stroke="#b78361" stroke-width="1.2" fill="none"/></g>`;
  }
  if(kind==='two')return `<g>${path('M-9 0 L-11 15 Q-9 24 1 23 L10 17 L10 5 L6-5 L8-31 Q5-36 2-32 L-1-10 L-5-33 Q-9-36-11-31 L-7-7 L-12-14 Q-17-16-18-11 L-11 4Z',skin)}<path d="M0 2 L7 7 M-1 10 L7 12" stroke="#b78361" stroke-width="1.2" fill="none"/></g>`;
  if(kind==='fist')return path('M-10 0 L-11 15 Q-8 23 3 21 L11 15 L10 1 L5-5 L-3-5Z',skin);
  return `<g>${path('M-9 0 L-13-9 Q-14-15-10-16 L-5-7 L-7-23 Q-7-29-3-28 L1-11 L1-29 Q3-34 6-29 L8-10 L11-25 Q15-29 16-23 L14-5 L18-15 Q23-17 22-10 L17 10 Q12 24 2 23 Q-8 21-9 9Z',skin)}<path d="M-4 3 Q4-1 10 6" stroke="#b78361" stroke-width="1.4" fill="none"/></g>`;
}

// Two-bone inverse kinematics: position the wrist first, then solve the elbow.
// The signed bend is fixed per gesture, so the elbow cannot flip while interpolating.
export function solveArm(side,wrist,bend=side){
  const sx=side<0?69:171,sy=164,L1=73,L2=65;
  let dx=wrist[0]-sx,dy=wrist[1]-sy,d=Math.hypot(dx,dy)||.001;
  const reach=Math.max(Math.abs(L1-L2)+.1,Math.min(L1+L2-.1,d));
  dx*=reach/d;dy*=reach/d;d=reach;
  const along=(L1*L1-L2*L2+d*d)/(2*d),across=Math.sqrt(Math.max(0,L1*L1-along*along));
  const ex=sx+dx/d*along-dy/d*across*bend,ey=sy+dy/d*along+dx/d*across*bend;
  const wx=sx+dx,wy=sy+dy,upper=Math.atan2(ex-sx,ey-sy)*180/Math.PI;
  const lower=Math.atan2(wx-ex,wy-ey)*180/Math.PI;
  return {upper,elbow:lower-upper,shoulder:[sx,sy],joint:[ex,ey],wrist:[wx,wy]};
}

function arm({side=1,wrist,kind='open',palm=0,bend=side}){
  const {upper,elbow,wrist:actual}=solveArm(side,wrist,bend),sx=side<0?69:171;
  return `<g class="rig-arm" data-side="${side}" data-wrist="${actual.join(',')}" transform="translate(${sx} 164) rotate(${-upper})">
    ${path('M-16 0 Q-18 32-14 74 L14 74 Q18 31 16 0Z',coat)}
    <path d="M-10 10 L-9 64" stroke="${coatLight}" stroke-width="5" stroke-linecap="round"/>
    <g transform="translate(0 73) rotate(${-elbow})">
      ${path('M-14 0 L-13 57 Q0 64 13 57 L14 0Z',coat)}
      <path d="M-8 7 L-8 47" stroke="${coatLight}" stroke-width="4" stroke-linecap="round"/>
      ${path('M-13 52 L-13 63 L13 63 L13 52Z','#f6f2df')}
      <g transform="translate(0 65) rotate(${palm+upper+elbow})">${hand(kind,side)}</g>
    </g>
  </g>`;
}

function leg(side,upper,knee){
  const sx=side<0?99:141;
  return `<g transform="translate(${sx} 289) rotate(${-upper})">
    ${path('M-21 0 L-18 83 L17 83 L20 0Z','#59656e')}
    <g transform="translate(0 80) rotate(${-knee})">
      ${path('M-18 0 L-16 78 L15 78 L17 0Z','#64717a')}
      <path d="M9 9 L8 69" stroke="#7c8890" stroke-width="4" stroke-linecap="round"/>
      ${path(side<0?'M-16 75 Q-29 77-34 88 Q-36 96-23 97 L17 96 L17 76Z':'M-16 76 L-17 96 L25 97 Q38 95 34 87 Q28 77 15 75Z','#334d5b')}
      <path d="M-18 94 L18 94" stroke="#1c3342" stroke-width="3"/>
    </g>
  </g>`;
}

const poses={
  welcome:{left:[-25,222],right:[265,222],lh:'open',rh:'open',lp:-75,rp:75,head:-1},
  point:{left:[56,297],right:[290,145],lh:'fist',rh:'point',lp:0,rp:65,head:3},
  count:{left:[56,297],right:[240,126],lh:'fist',rh:'two',lp:0,rp:0,head:0},
  think:{left:[56,297],right:[185,162],lh:'fist',rh:'think',lp:0,rp:-60,head:-4},
  spread:{left:[-54,205],right:[294,205],lh:'open',rh:'open',lp:-90,rp:90,head:0},
  balance:{left:[-41,197],right:[281,197],lh:'open',rh:'open',lp:-90,rp:90,head:0},
  wave:{left:[56,297],right:[240,122],lh:'fist',rh:'open',lp:0,rp:5,head:2},
  walk:{left:[56,297],right:[184,297],lh:'fist',rh:'fist',lp:0,rp:0,head:0},
};
const rest={left:[56,297],right:[184,297]};
// Smooth wrist paths follow a shallow arc. Both hands share one progress clock.
const reachTarget=(start,end,p)=>[lerp(start[0],end[0],p),lerp(start[1],end[1],p)-Math.sin(Math.PI*p)*10];

/**
 * Deterministic puppet. Full-body local nominal canvas: 240 x 480.
 * Extended hands may reach x=-65..305; leave that margin for spread/balance.
 * Head mode: 160 x 160. `progress` moves wrist targets from rest along an arc;
 * optional `fromPose` starts at another authored pose for a continuous gesture.
 * Holding poses are time-invariant. Only deliberate waving/walking are cyclic.
 */
export function ScientistRig({x=0,y=0,scale=1,t=0,mode='full',pose='welcome',fromPose=null,progress=1,mouth=0,look='right'}={}){
  const p=ease(progress),s=poses[pose]||poses.welcome,source=poses[fromPose];
  const headTilt=lerp(source?.head||0,s.head,p)+(look==='left'?-2:look==='right'?1:0);
  if(mode==='head')return `<g class="scientist-rig scientist-head" transform="translate(${x} ${y}) scale(${scale})">${head({x:0,y:3,t,mouth,tilt:headTilt})}</g>`;
  const walking=pose==='walk'?p:0,cycle=Math.sin(t*7),counter=Math.sin(t*7+Math.PI);
  const left=reachTarget(source?.left||rest.left,s.left,p),right=reachTarget(source?.right||rest.right,s.right,p);
  if(pose==='wave')right[0]+=Math.sin(t*4)*8*p;
  if(walking){left[0]+=counter*18*p;right[0]+=cycle*18*p;left[1]-=Math.abs(counter)*5*p;right[1]-=Math.abs(cycle)*5*p}
  const leftPalm=lerp(source?.lp||0,s.lp,p),rightPalm=lerp(source?.rp||0,s.rp,p);
  const leftHand=source&&p<.4?source.lh:s.lh,rightHand=source&&p<.4?source.rh:s.rh;
  const rightInFront=pose==='think'||(fromPose==='think'&&p<.65);
  const bounce=walking?Math.abs(Math.sin(t*7))*4:0;
  return `<g class="scientist-rig scientist-full" data-pose="${pose}" transform="translate(${x} ${y-bounce}) scale(${scale})">
    <ellipse cx="120" cy="470" rx="58" ry="9" fill="#b9b196" opacity=".25"/>
    ${leg(-1,cycle*16*walking,Math.max(0,-cycle)*19*walking)}${leg(1,counter*16*walking,Math.max(0,-counter)*19*walking)}
    ${arm({side:-1,wrist:left,kind:leftHand,palm:leftPalm})}
    ${rightInFront?'':arm({side:1,wrist:right,kind:rightHand,palm:rightPalm,bend:s.rb||1})}
    ${path('M84 139 Q120 125 156 139 L174 165 L165 298 Q143 308 120 299 Q98 308 75 298 L65 165Z',coat)}
    ${path('M104 134 L120 164 L136 134 L141 144 L128 211 L111 211 L99 144Z','#f8f4e5')}
    ${path('M115 153 L125 153 L128 172 L122 222 L113 206 L112 172Z','#2d655e')}
    ${path('M99 140 L119 220 L89 188 L99 179 L84 155Z',coatLight)}
    ${path('M141 140 L121 220 L151 188 L141 179 L156 155Z',coatLight)}
    <path d="M120 220 V298 M87 251 H108 M134 251 H155" stroke="${ink}" stroke-width="2" fill="none"/>
    <circle cx="125" cy="240" r="2.7" fill="#213e4e"/><circle cx="125" cy="271" r="2.7" fill="#213e4e"/>
    ${head({x:40,y:-1,t,mouth,tilt:headTilt})}
    ${rightInFront?arm({side:1,wrist:right,kind:rightHand,palm:rightPalm,bend:s.rb||1}):''}
  </g>`;
}
