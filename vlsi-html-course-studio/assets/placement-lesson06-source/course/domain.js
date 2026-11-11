// Course arithmetic and an instrumented adaptation of Yongfu Li's placement-core.js.
// Source revision 003bcd49e3794e6cfd2680181cdbd347d673ad07; attribution in assets/course-sources.json.
export const cells=['A','B','C','D','E','F'];
export const movable=['B','C','E','F'];
export const nets=[['A','B'],['C','D'],['A','C'],['B','D'],['A','B','C','D'],['E','F']];
export const crowded={A:{x:0,y:0},B:{x:1,y:1},C:{x:1.5,y:1},D:{x:8,y:8},E:{x:1,y:1.5},F:{x:1.5,y:1.5}};
export const distributed={A:{x:0,y:0},B:{x:6,y:1},C:{x:1,y:6},D:{x:8,y:8},E:{x:3,y:3},F:{x:5,y:5}};
export const referenceStarter={A:{x:0,y:0},B:{x:8,y:0},C:{x:0,y:8},D:{x:8,y:8},E:{x:4,y:4},F:{x:0,y:4}};
export const clone=p=>structuredClone(p);
export const clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x));
export const smooth=x=>{x=clamp(x);return x*x*(3-2*x)};
export const interpolatePositions=(a,b,t)=>Object.fromEntries(cells.map(id=>[id,{x:a[id].x+(b[id].x-a[id].x)*t,y:a[id].y+(b[id].y-a[id].y)*t}]));
export const binOf=p=>(p.y>=4?2:0)+(p.x>=4?1:0);
export function netBounds(net,positions){
 const ids=typeof net==='number'?nets[net]:net,xs=ids.map(id=>positions[id].x),ys=ids.map(id=>positions[id].y);
 const minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys);
 return {minX,maxX,minY,maxY,width:maxX-minX,height:maxY-minY,hpwl:maxX-minX+maxY-minY};
}
export function metrics(p,capacity=2){
 const perNet=nets.map(n=>netBounds(n,p).hpwl),counts=[0,0,0,0];
 Object.values(p).forEach(v=>counts[binOf(v)]++);
 return {hpwl:perNet.reduce((a,b)=>a+b,0),overflow:counts.reduce((a,b)=>a+Math.max(0,b-capacity),0),counts,perNet,capacity};
}
const neighbors=Object.fromEntries(cells.map(id=>[id,[...new Set(nets.filter(n=>n.includes(id)).flat().filter(n=>n!==id))]]));
function forceStep(p,alpha=.14,centerPull=.025){
 const next=clone(p);
 for(const id of movable){const n=neighbors[id],x=n.reduce((a,k)=>a+p[k].x,0)/n.length,y=n.reduce((a,k)=>a+p[k].y,0)/n.length;next[id]={x:p[id].x+alpha*(x-p[id].x)+centerPull*(4-p[id].x),y:p[id].y+alpha*(y-p[id].y)+centerPull*(4-p[id].y)}}
 return next;
}
function quadraticStep(p){const next=clone(p);for(const id of cells){if(!movable.includes(id))continue;const n=neighbors[id],x=n.reduce((a,k)=>a+next[k].x,0)/n.length,y=n.reduce((a,k)=>a+next[k].y,0)/n.length;next[id]={x:.45*x+.55*next[id].x,y:.45*y+.55*next[id].y}}return next}
function spreadStep(p,weight){
 const next=clone(p),m=metrics(p,1),arrows=[];
 for(const id of movable){const bin=binOf(p[id]),count=m.counts[bin];if(count<=1)continue;const center={x:(bin%2+.5)*4,y:(Math.floor(bin/2)+.5)*4};let dx=p[id].x-center.x,dy=p[id].y-center.y;if(Math.abs(dx)+Math.abs(dy)<1e-6){dx=((id.charCodeAt(0)*3)%5)-2;dy=((id.charCodeAt(0)*7)%5)-2}const len=Math.hypot(dx,dy)||1;next[id].x+=weight*dx/len*(count-1)*.4;next[id].y+=weight*dy/len*(count-1)*.4;arrows.push({id,from:clone(p[id]),to:clone(next[id]),center})}
 return {positions:next,arrows};
}
export function referenceTrace(weight=.55){
 if(!Number.isFinite(weight)||weight<0||weight>2)throw new RangeError('Density weight must be between 0 and 2.');
 let p=clone(referenceStarter);const trace=[];
 const push=(id,phase,iteration,arrows=[])=>trace.push({id,phase,iteration,positions:clone(p),capacity:1,metrics:metrics(p,1),arrows,weight});
 push('starter','starter',0);
 for(let i=1;i<=6;i++){p=forceStep(p);push(`force-${i}`,'force',i)}
 for(let i=1;i<=3;i++){p=quadraticStep(p);push(`quadratic-${i}`,'quadratic',i)}
 for(let i=1;i<=12;i++){const step=spreadStep(p,weight);p=step.positions;push(`spread-${i}`,'spread',i,step.arrows);const before=clone(p);p=forceStep(p,.06,.01);push(`reconnect-${i}`,'reconnect',i,movable.map(id=>({id,from:before[id],to:p[id]})))}
 return trace;
}
