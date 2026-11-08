// «LA CUENTA» v2: muñecos tipo juguete con animaciones de Quaternius (CC0) + utilería KayKit (CC0) + postproceso.
import * as THREE from 'three';
import {RoundedBoxGeometry} from 'three/addons/geometries/RoundedBoxGeometry.js';
import {EffectComposer} from 'three/addons/postprocessing/EffectComposer.js';
import {RenderPass} from 'three/addons/postprocessing/RenderPass.js';
import {ShaderPass} from 'three/addons/postprocessing/ShaderPass.js';
import {UnrealBloomPass} from 'three/addons/postprocessing/UnrealBloomPass.js';
import {BokehPass} from 'three/addons/postprocessing/BokehPass.js';
import {FilmPass} from 'three/addons/postprocessing/FilmPass.js';
import {GammaCorrectionShader} from 'three/addons/shaders/GammaCorrectionShader.js';
import {init,toy,ld} from './toy.js';
const D=window.DATA;
THREE.ColorManagement.legacyMode=false;
const R=new THREE.WebGLRenderer({canvas:document.getElementById('cv'),antialias:true,preserveDrawingBuffer:true});
R.outputEncoding=THREE.LinearEncoding;R.shadowMap.enabled=true;R.shadowMap.type=THREE.PCFSoftShadowMap;R.setPixelRatio(1);R.setSize(1080,1920,false);
const S=new THREE.Scene();S.background=new THREE.Color('#120f0e');
const CAM=new THREE.PerspectiveCamera(32,1080/1920,.05,200);
const cl=x=>Math.min(1,Math.max(0,x)), lerp=(a,b,t)=>a+(b-a)*t, ss=(a,b,t)=>{t=cl((t-a)/(b-a));return t*t*(3-2*t);};
const eo=x=>1-Math.pow(1-cl(x),3), eb=x=>{x=cl(x);const c1=1.9,c3=c1+1;return 1+c3*Math.pow(x-1,3)+c1*Math.pow(x-1,2);};
const M=(c,r=.6,o={})=>new THREE.MeshStandardMaterial(Object.assign({color:c,roughness:r,metalness:0},o));
const V3=(x,y,z)=>new THREE.Vector3(x,y,z);
function mesh(g,m,p=[0,0,0],sh=true){const x=new THREE.Mesh(g,m);x.position.set(...p);x.castShadow=sh;x.receiveShadow=true;return x;}
function shadowAll(o){o.traverse(x=>{if(x.isMesh){x.castShadow=true;x.receiveShadow=true;}});return o;}
function texCanvas(w,h,draw){const c=document.createElement('canvas');c.width=w;c.height=h;const x=c.getContext('2d');const t=new THREE.CanvasTexture(c);t.encoding=THREE.sRGBEncoding;t.anisotropy=4;return {t,x,redo(){draw(x,w,h);t.needsUpdate=true;}};}
function glowTex(){const c=document.createElement('canvas');c.width=c.height=128;const x=c.getContext('2d');const g=x.createRadialGradient(64,64,0,64,64,64);g.addColorStop(0,'rgba(255,255,255,1)');g.addColorStop(.35,'rgba(255,255,255,.55)');g.addColorStop(1,'rgba(255,255,255,0)');x.fillStyle=g;x.fillRect(0,0,128,128);return new THREE.CanvasTexture(c);}
const GLOW=glowTex();
const KK='rest/KayKit_Restaurant_Bits_1.0_FREE/Assets/gltf/';
const kcache={};async function kk(n){if(!kcache[n])kcache[n]=await ld(KK+n+'.gltf');return shadowAll(kcache[n].scene.clone(true));}
function place(o,sc,x,y,z,ry=0){o.scale.setScalar(sc);o.rotation.y=ry;o.position.set(0,0,0);o.updateMatrixWorld(true);const b=new THREE.Box3().setFromObject(o);const c=b.getCenter(V3());
  o.position.set(x-c.x,y-b.min.y,z-c.z);S.add(o);return o;}
await init();
// ---------------- luces
S.add(new THREE.HemisphereLight('#ffe6d6','#2a140e',.38));
function key(x,y,z,tx,tz,i=1.6){const k=new THREE.DirectionalLight('#fff1e2',i);k.position.set(x,y,z);k.target.position.set(tx,0,tz);S.add(k.target);k.castShadow=true;k.shadow.mapSize.set(1536,1536);
  Object.assign(k.shadow.camera,{left:-4,right:4,top:4,bottom:-1,near:.5,far:20});k.shadow.radius=5;k.shadow.bias=-.0004;S.add(k);return k;}
key(2.5,5.5,4.5,0,0,1.05);key(32.5,5.5,4.5,30,0,.95);key(-37,7,6,-40,0,.8);
// ---------------- RESTAURANTE (x=0)
const floorTex=texCanvas(512,512,(x,w,h)=>{x.fillStyle='#6b4430';x.fillRect(0,0,w,h);for(let i=0;i<8;i++){x.fillStyle=i%2?'#734a34':'#66402c';x.fillRect(0,i*64,w,62);}x.fillStyle='rgba(0,0,0,.15)';for(let i=0;i<8;i++)x.fillRect(0,i*64+62,w,2);});
floorTex.redo();floorTex.t.wrapS=floorTex.t.wrapT=THREE.RepeatWrapping;floorTex.t.repeat.set(6,6);
const fl=mesh(new THREE.PlaneGeometry(16,12),M('#ffffff',.85,{map:floorTex.t}),[0,0,-1],false);fl.rotation.x=-Math.PI/2;S.add(fl);
const backWall=mesh(new THREE.PlaneGeometry(16,8),M('#4a2c25',.95),[0,4,-3.9],false);S.add(backWall);
S.add(mesh(new THREE.BoxGeometry(16,1.0,.06),M('#F42902',.7),[0,.5,-3.86],false));
// ventana con la calle de noche detrás
const winBack=mesh(new THREE.PlaneGeometry(2.2,1.6),new THREE.MeshBasicMaterial({color:'#0d1430'}),[-2.2,1.85,-3.86],false);S.add(winBack);
for(let i=0;i<6;i++){const sp=new THREE.Sprite(new THREE.SpriteMaterial({map:GLOW,color:['#ffcf8a','#ff8a3d','#9fc7ff'][i%3],transparent:true,opacity:.6,depthWrite:false}));sp.scale.set(.35,.35,1);sp.position.set(-3+i*.32,1.4+(i%2)*.4,-3.84);S.add(sp);}
S.add(mesh(new THREE.BoxGeometry(2.4,.12,.15),M('#1A1B1F'),[-2.2,2.71,-3.84],false));S.add(mesh(new THREE.BoxGeometry(2.4,.12,.15),M('#1A1B1F'),[-2.2,1.0,-3.84],false));
S.add(mesh(new THREE.BoxGeometry(.12,1.8,.15),M('#1A1B1F'),[-3.36,1.85,-3.84],false));S.add(mesh(new THREE.BoxGeometry(.12,1.8,.15),M('#1A1B1F'),[-1.04,1.85,-3.84],false));S.add(mesh(new THREE.BoxGeometry(.08,1.6,.12),M('#1A1B1F'),[-2.2,1.85,-3.82],false));
// cocina: puerta
place(await kk('door_A'),.75,2.4,0,-3.75);
// reloj
const clk=new THREE.Group();clk.position.set(.9,2.55,-3.85);S.add(clk);
const fc=mesh(new THREE.CylinderGeometry(.32,.32,.05,40),M('#FDFDFF',.4),[0,0,0],false);fc.rotation.x=Math.PI/2;clk.add(fc);clk.add(mesh(new THREE.TorusGeometry(.33,.04,12,40),M('#F42902',.5),[0,0,.02],false));
const hH=new THREE.Group();hH.position.z=.05;hH.add(mesh(new THREE.BoxGeometry(.04,.18,.02),M('#1A1B1F'),[0,.07,0],false));clk.add(hH);
const hM=new THREE.Group();hM.position.z=.055;hM.add(mesh(new THREE.BoxGeometry(.025,.27,.02),M('#1A1B1F'),[0,.11,0],false));clk.add(hM);
// lámparas colgantes
const lamps=[];[[-1.6,-1.6],[0,-.3],[1.9,-1.9]].forEach(([x,z])=>{const g=new THREE.Group();g.position.set(x,2.15,z);S.add(g);g.add(mesh(new THREE.CylinderGeometry(.006,.006,1.6,6),M('#111'),[0,.8,0],false));
  g.add(mesh(new THREE.ConeGeometry(.2,.18,24,1,true),M('#1A1B1F',.5,{side:THREE.DoubleSide}),[0,0,0],false));g.add(mesh(new THREE.SphereGeometry(.06,12,10),new THREE.MeshBasicMaterial({color:'#ffd9a0'}),[0,-.06,0],false));
  const l=new THREE.PointLight('#ffb36b',.45,5,1.8);l.position.set(0,-.12,0);g.add(l);lamps.push(g);});
// mesa principal
const mesa=place(await kk('table_round_A_small'),.75,0,0,0);
const tableTop=new THREE.Box3().setFromObject(mesa).max.y;
place(await kk('chair_A'),.75,0,0,-.66,0);
const plato=place(await kk('plate'),.32,-.2,tableTop,.18);place(await kk('food_burger'),.26,-.2,tableTop+.02,.18);
place(await kk('ketchup'),.2,.28,tableTop,-.18);place(await kk('mustard'),.2,.36,tableTop,-.08);
S.add(mesh(new THREE.CylinderGeometry(.04,.034,.13,20),M('#cfe8ff',.05,{transparent:true,opacity:.5}),[.3,tableTop+.065,.25]));
const qrTex=texCanvas(256,340,(x,w,h)=>{x.fillStyle='#FDFDFF';x.fillRect(0,0,w,h);x.fillStyle='#F42902';x.fillRect(0,0,w,46);x.fillStyle='#FDFDFF';x.font='900 30px Archivo';x.textAlign='center';x.fillText('MENUO',w/2,33);
  const n=D.QR.length,s=200/n;x.fillStyle='#1A1B1F';D.QR.forEach((r,i)=>r.forEach((v,j)=>{if(v)x.fillRect(28+j*s,64+i*s,s+.5,s+.5);}));x.font='800 24px Archivo';x.fillText('Escanea y paga',w/2,300);x.font='700 18px Azeret Mono';x.fillStyle='#F42902';x.fillText('MESA 4',w/2,326);});
const tent=new THREE.Group();tent.position.set(.12,tableTop,-.22);tent.rotation.y=-.25;S.add(tent);
const tentFront=mesh(new THREE.PlaneGeometry(.15,.2),new THREE.MeshStandardMaterial({map:qrTex.t,roughness:.5}),[0,.1,0]);tentFront.rotation.x=-.15;tent.add(tentFront);tent.add(mesh(new THREE.BoxGeometry(.16,.01,.08),M('#1A1B1F'),[0,0,-.02]));
// mesas del fondo con comensales
const fondo=[];for(const [x,z,ry,camisa,pelo] of [[-2.1,-2.3,.5,'#FDFDFF','#3a2416'],[2.0,-2.5,-.6,'#3b6fd8','#1a1010']]){
  place(await kk('table_round_A_small'),.75,x,0,z);const cz=z-.66*Math.cos(ry),cx=x-.66*Math.sin(ry);place(await kk('chair_A'),.75,cx,0,cz,ry);
  place(await kk('plate'),.32,x+.1,tableTop,z+.1);
  const p=toy({camisa,pantalon:'#2b2b33',zapatos:'#222',colorPelo:pelo,piel:x<0?'#d9a07a':'#8a5a3c'});p.g.position.set(cx,0,cz);p.g.rotation.y=ry;S.add(p.g);fondo.push(p);}
// ---------------- PERSONAJES
const CA=toy({camisa:'#C9FB00',pantalon:'#2f4f7a',zapatos:'#f4f4f4',piel:'#e9b48d',colorPelo:'#3a2416'});S.add(CA.g);
const SE=toy({camisa:'#FDFDFF',pantalon:'#1A1B1F',zapatos:'#111',manga:'larga',piel:'#a8714c',colorPelo:'#151010',pelo:'rapado',delantal:true,corbatin:true});S.add(SE.g);
const LU=toy({camisa:'#F42902',pantalon:'#1A1B1F',zapatos:'#111',piel:'#c98e66',colorPelo:'#2a1810',pelo:'largo',pestanas:true,aretes:true});S.add(LU.g);
// utilería en manos
function attachTo(p,bone,obj,pos,rot){p.bones[bone].add(obj);obj.position.copy(pos);if(rot)obj.rotation.set(...rot);return obj;}
const tray=new THREE.Group();tray.add(mesh(new THREE.CylinderGeometry(.2,.2,.015,28),M('#c9c9cf',.3)));[[-.07,0],[.06,.05],[.02,-.08]].forEach(([x,z])=>tray.add(mesh(new THREE.CylinderGeometry(.035,.03,.11,16),M('#ffd27a',.2,{transparent:true,opacity:.85}),[x,.06,z])));
const datTex=texCanvas(220,170,(x,w,h)=>{const e=datTex.err;x.fillStyle=e?'#F42902':'#7fd3a8';x.fillRect(0,0,w,h);x.fillStyle=e?'#FDFDFF':'#0d2b1d';x.textAlign='center';
  if(e){x.font='900 34px Archivo';x.fillText('SIN SEÑAL',110,98);x.font='700 16px Azeret Mono';x.fillText('INTENTE DE NUEVO',110,132);}else{x.font='800 26px Azeret Mono';x.fillText('INSERTE',110,75);x.fillText('TARJETA',110,110);}});
const dat=new THREE.Group();dat.scale.setScalar(1.7);dat.add(mesh(new THREE.BoxGeometry(.12,.2,.035),M('#2a2b30',.4)));dat.add(mesh(new THREE.PlaneGeometry(.1,.077),new THREE.MeshBasicMaterial({map:datTex.t}),[0,.045,.018],false));
for(let i=0;i<9;i++)dat.add(mesh(new THREE.BoxGeometry(.024,.016,.008),M('#d8d8de',.5),[-.03+(i%3)*.03,-.02-Math.floor(i/3)*.024,.019],false));
const phone=new THREE.Group();phone.scale.setScalar(1.5);phone.add(mesh(new THREE.BoxGeometry(.075,.15,.01),M('#1A1B1F',.3)));phone.add(mesh(new THREE.PlaneGeometry(.066,.135),new THREE.MeshBasicMaterial({color:'#F42902'}),[0,0,.006],false));
S.add(tray);S.add(dat);S.add(phone);
const beam=mesh(new THREE.CylinderGeometry(.005,.005,1,8),new THREE.MeshBasicMaterial({color:'#C9FB00',transparent:true,opacity:0}),[0,0,0],false);S.add(beam);
// ---------------- SET DE ENTREVISTAS (x=30)
const IX=30;
S.add(mesh(new THREE.PlaneGeometry(12,8),M('#2a1d1a',.95),[IX,4,-3],false));
const ifl=mesh(new THREE.PlaneGeometry(12,10),M('#3a2a22',.9),[IX,0,0],false);ifl.rotation.x=-Math.PI/2;S.add(ifl);
let sd=11;const rr=()=>{sd=(sd*16807)%2147483647;return sd/2147483647;};
for(let i=0;i<30;i++){const sp=new THREE.Sprite(new THREE.SpriteMaterial({map:GLOW,color:['#ffb36b','#ff7a45','#ffd9a0','#F42902','#ffe8c2'][i%5],transparent:true,opacity:.4+rr()*.4,depthWrite:false}));const s=.25+rr()*.6;sp.scale.set(s,s,1);sp.position.set(IX-3+rr()*6,.6+rr()*2.6,-2.8+rr()*.3);S.add(sp);}
place(await kk('chair_A'),.75,IX,0,-.05,0);
const ip=new THREE.Group();ip.position.set(IX+.9,0,-1.2);S.add(ip);ip.add(mesh(new THREE.CylinderGeometry(.2,.15,.38,20),M('#c2643a',.8),[0,.19,0]));
[[0,.68,0,.27],[.15,.9,.04,.2],[-.14,.86,0,.22],[.03,1.08,0,.19]].forEach(([x,y,z,r])=>ip.add(mesh(new THREE.SphereGeometry(r,18,14),M('#2f8f4e',.7),[x,y,z])));
const il=new THREE.PointLight('#ffc48a',.45,6,1.6);il.position.set(IX+1.2,2.0,1.0);S.add(il);
// ---------------- CALLE (x=-40)
const EX=-40;
const road=mesh(new THREE.PlaneGeometry(30,14),M('#2b2c31',.9),[EX,0,2],false);road.rotation.x=-Math.PI/2;S.add(road);
S.add(mesh(new THREE.BoxGeometry(30,.15,2.4),M('#8d8a86',.9),[EX,.075,-1.2]));S.add(mesh(new THREE.BoxGeometry(30,.16,.18),M('#f2c230',.6),[EX,.08,.05]));
for(let i=-6;i<7;i++)S.add(mesh(new THREE.BoxGeometry(1.1,.01,.12),M('#e8e2d0',.8),[EX+i*2.4,.006,2.6],false));
S.add(mesh(new THREE.BoxGeometry(30,7,.4),M('#4a2c25',.9),[EX,3.5,-2.6]));
S.add(mesh(new THREE.BoxGeometry(2.6,1.8,.08),M('#1A1B1F'),[EX-.6,1.5,-2.38],false));S.add(mesh(new THREE.PlaneGeometry(2.4,1.6),new THREE.MeshBasicMaterial({color:'#b98a52'}),[EX-.6,1.5,-2.33],false));
const puerta=await kk('door_A');place(puerta,.75,EX+1.4,.15,-2.25);
const sl=new THREE.PointLight('#ffcf8a',.6,8,1.5);sl.position.set(EX-.4,2.0,-.8);S.add(sl);
const nostop=new THREE.Group();nostop.position.set(EX-2.2,.15,-.25);S.add(nostop);nostop.add(mesh(new THREE.CylinderGeometry(.025,.025,1.7,8),M('#9a9aa0'),[0,.85,0]));
const nsTex=texCanvas(128,128,(x)=>{x.fillStyle='#1e5bd8';x.beginPath();x.arc(64,64,62,0,7);x.fill();x.strokeStyle='#e8231d';x.lineWidth=14;x.beginPath();x.arc(64,64,55,0,7);x.stroke();x.beginPath();x.moveTo(25,25);x.lineTo(103,103);x.stroke();});
nostop.add(mesh(new THREE.CircleGeometry(.22,32),new THREE.MeshBasicMaterial({map:nsTex.t}),[0,1.7,.03],false));
function carro(color){const c=new THREE.Group();c.add(mesh(new RoundedBoxGeometry(1.7,.48,.88,4,.12),M(color,.35),[0,.48,0]));c.add(mesh(new RoundedBoxGeometry(.95,.42,.8,4,.12),M(color,.35),[-.1,.88,0]));
  c.add(mesh(new RoundedBoxGeometry(.86,.32,.82,3,.08),M('#9fc7e8',.08),[-.1,.9,0]));
  [[-.55,.42],[.55,.42],[-.55,-.42],[.55,-.42]].forEach(([x,z])=>{const w=mesh(new THREE.CylinderGeometry(.2,.2,.14,22),M('#151515',.8),[x,.22,z]);w.rotation.x=Math.PI/2;c.add(w);});
  [.25,-.25].forEach(z=>c.add(mesh(new THREE.SphereGeometry(.06,12,10),M('#fff6c0',.2,{emissive:'#fff2a0',emissiveIntensity:1.5}),[.85,.55,z],false)));return c;}
const car=carro('#C9FB00');S.add(car);
const grua=new THREE.Group();S.add(grua);
grua.add(mesh(new RoundedBoxGeometry(1.2,1.1,1.05,4,.1),M('#f39c1e',.45),[1.4,.82,0]));grua.add(mesh(new RoundedBoxGeometry(1.0,.6,.98,3,.08),M('#9fc7e8',.08),[1.52,1.15,0]));
grua.add(mesh(new RoundedBoxGeometry(1.9,.38,1.05,3,.06),M('#e8e8ea',.5),[-.15,.52,0]));const beacon=mesh(new RoundedBoxGeometry(.42,.12,.22,2,.04),M('#ff8a00',.3,{emissive:'#ff7a00',emissiveIntensity:1}),[1.4,1.44,0]);grua.add(beacon);
[[-.7,.47],[.15,.47],[1.4,.47],[-.7,-.47],[.15,-.47],[1.4,-.47]].forEach(([x,z])=>{const w=mesh(new THREE.CylinderGeometry(.25,.25,.16,22),M('#151515',.8),[x,.26,z]);w.rotation.x=Math.PI/2;grua.add(w);});
const boom=mesh(new THREE.BoxGeometry(1.4,.1,.1),M('#e8e8ea',.4),[-1.0,1.02,0]);boom.rotation.z=-.5;grua.add(boom);
// ---------------- POSTPROCESO
const composer=new EffectComposer(R);composer.addPass(new RenderPass(S,CAM));
const bokeh=new BokehPass(S,CAM,{focus:2.6,aperture:.0016,maxblur:.008});composer.addPass(bokeh);
const bloom=new UnrealBloomPass(new THREE.Vector2(540,960),.16,.45,.92);composer.addPass(bloom);
const film=new FilmPass(.22,0,0,false);composer.addPass(film);
composer.addPass(new ShaderPass(GammaCorrectionShader));
// ---------------- LÍNEA DE TIEMPO
const T=D.T,SHOTS=D.SHOTS,CHIPS=D.CHIPS,LT=D.LT,SUBS=D.SUBS,ENV=D.ENV;
let chipPrev='',ltPrev='',subPrev='',datPrev=null;
const env=(n,t)=>{const a=ENV[n];const i=Math.round(t*30);return a&&i>=0&&i<a.length?a[i]:0;};
function shotAt(t){let s=SHOTS[0];for(const x of SHOTS)if(t>=x[0])s=x;return s;}
const OFF=V3(0,-50,0);
function hand(p,s,obj,off){const b=p.bones['hand_'+s];b.updateMatrixWorld(true);obj.position.copy(b.localToWorld(off.clone()));obj.quaternion.copy(p.g.getWorldQuaternion(new THREE.Quaternion()));}
function blink(p,t,seed){const b=(Math.abs(((t+seed)%3.3)-1.6)<.06);p.lids.forEach(l=>l.visible=b);}
window.render=function(t){
  const sh=shotAt(t),name=sh[1],st=t-sh[0];
  const ec=env('camilo',t),es=env('sebas',t),el=env('lucia',t);
  [CA,SE,LU].forEach(p=>{p.g.visible=false;});tray.position.copy(OFF);dat.position.copy(OFF);phone.position.copy(OFF);
  // fondo
  fondo.forEach((p,i)=>{p.clip(i?'Sitting_Talking_Loop':'Sitting_Idle_Loop',t+i*1.7);p.talk(0);blink(p,t,i);});
  // reloj
  let hrs=8+2/60;if(t<T.next)hrs+=lerp(0,23/60,ss(T.sebasEnt,T.dat,t))+lerp(0,17/60,ss(T.dat+1,T.carro,t));
  hM.rotation.z=-((hrs%1)*Math.PI*2);hH.rotation.z=-((hrs%12)/12*Math.PI*2);
  // calle
  let cx=EX-.2,cy=0,crz=0,cry=.12,gx=EX+30;
  if(t>=T.grua0&&t<T.next){const g=t-T.grua0;gx=lerp(EX+2.4,EX+9,ss(.9,2.7,g));cx=gx-2.25;crz=-.28*eo(g/.6);cy=.38*eo(g/.6);cry=lerp(.12,0,eo(g/.6));}
  car.position.set(cx,cy+.15,.5);car.rotation.set(0,cry,crz);grua.position.set(gx,0,.6);beacon.material.emissiveIntensity=.5+1.2*Math.abs(Math.sin(t*8));
  // ---- personajes por toma
  if(name==='calle'){CA.g.visible=true;CA.g.position.set(lerp(EX-1.4,EX+1.2,ss(.6,4.4,t)),.15,-.6);CA.g.rotation.y=Math.PI/2;CA.clip('Walk_Loop',t);CA.talk(0);blink(CA,t,0);}
  if(name==='entCamilo'||name==='entCamilo2'){CA.g.visible=true;CA.g.position.set(IX,0,.02);CA.g.rotation.y=.32;CA.clip('Sitting_Talking_Loop',t);CA.talk(ec);blink(CA,t,0);
    if(name==='entCamilo2'){CA.aim('upperarm_l','lowerarm_l',V3(.5,1,.25),eo(st/.4));CA.aim('lowerarm_l','hand_l',V3(.2,1,.2),eo(st/.4));}}
  if(name==='mesa'||name==='datafono'||name==='ventana'||name==='mesa2'||name==='qr'){CA.g.visible=true;CA.g.position.set(0,0,-.62);CA.g.rotation.y=0;
    CA.clip(name==='mesa'&&t>T.pide+1.4?'Sitting_Idle_Loop':(ec>.05?'Sitting_Talking_Loop':'Sitting_Idle_Loop'),t);CA.talk(ec);blink(CA,t,0);
    if(name==='mesa'){const k=eo((t-T.pide+.15)/.3);CA.aim('upperarm_r','lowerarm_r',V3(-.35,1,.12),k);CA.aim('lowerarm_r','hand_r',V3(-.15,1,.1),k);}
    if(name==='datafono'){CA.turnHead(.75,eo(st/.4));}
    if(name==='ventana'){CA.turnHead(-1.0,eo(st/.25));}
    if(name==='qr'||name==='mesa2'){const k=name==='qr'?eo((st)/.4):0;CA.aim('upperarm_l','lowerarm_l',V3(.15,-.25,1),k);CA.aim('lowerarm_l','hand_l',V3(-.05,-.55,1),k);
      if(name==='qr'){hand(CA,'l',phone,V3(0,0,0));phone.rotateX(-Math.PI/2+.3);}}}
  // Sebas
  if(name==='mesa'&&t>=T.sebasPasa){SE.g.visible=true;const k=(t-T.sebasPasa)/1.9;SE.g.position.set(lerp(-2.6,2.6,k),0,-1.45);SE.g.rotation.y=Math.PI/2;SE.clip('Walk_Formal_Loop',t*1.15);SE.talk(es);blink(SE,t,.7);
    SE.turnHead(.9,ss(.15,.35,k)*(1-ss(.65,.85,k)));SE.aim('upperarm_r','lowerarm_r',V3(-.3,-.6,.6),1);SE.aim('lowerarm_r','hand_r',V3(-.1,.05,1),1);hand(SE,'r',tray,V3(0,.02,0));}
  if(name==='entSebas'||name==='entSebas2'){SE.g.visible=true;SE.g.position.set(IX,0,.02);SE.g.rotation.y=.32;SE.clip('Sitting_Talking_Loop',t+.8);SE.talk(es);blink(SE,t,.7);
    SE.sweat.visible=name==='entSebas';SE.sweat.position.y=.08-((t*1.2)%1)*.12;SE.brows.forEach((b,i)=>b.rotation.z=(i?-1:1)*(name==='entSebas'?-.3:.12));}
  if(name==='datafono'){SE.g.visible=true;SE.g.position.set(.62,0,.12);SE.g.rotation.y=-2.3;SE.clip('Idle_Loop',t);SE.talk(es);blink(SE,t,.7);SE.sweat.visible=true;SE.sweat.position.y=.08-((t*1.2)%1)*.12;
    SE.aim('upperarm_r','lowerarm_r',V3(-.2,-.5,.8),1);SE.aim('lowerarm_r','hand_r',V3(-.15,.15,1),1);hand(SE,'r',dat,V3(0,.04,0));dat.position.add(V3(-.03,.12,-.06));dat.lookAt(V3(-.5,1.6,-1.6));}
  else SE.sweat.visible=SE.sweat.visible&&name.startsWith('entSebas');
  const derr=t>=T.dat+.25;if(derr!==datPrev){datTex.err=derr;datTex.redo();datPrev=derr;}
  // Lucía
  if(name==='entLucia'){LU.g.visible=true;LU.g.position.set(IX,0,.02);LU.g.rotation.y=.32;LU.clip('Sitting_Talking_Loop',t+2.1);LU.talk(el);blink(LU,t,1.3);LU.brows.forEach((b,i)=>b.rotation.z=(i?-1:1)*(t>=T.noMas?-.35:0));}
  // rayo del QR
  if(name==='qr'&&t>=T.scan&&t<T.ok){const a=phone.getWorldPosition(V3()),b=tentFront.getWorldPosition(V3());beam.position.copy(a).add(b).multiplyScalar(.5);beam.scale.set(1,a.distanceTo(b),1);beam.lookAt(b);beam.rotateX(Math.PI/2);beam.material.opacity=.9;}else beam.material.opacity=0;
  // ---- cámara
  const cp=V3(0,0,0),la=V3(0,0,0);let foco=null;
  const headW=p=>p.head.getWorldPosition(V3());
  if(name==='calle'){cp.set(EX+.3,2.1,lerp(9.2,8.2,eo(st/4.5)));la.set(EX+.3,1.0,-.6);}
  else if(name==='grua'){cp.set(gx-6.6,2.3,4.9);la.set(gx-.8,.65,.5);}
  else if(name.startsWith('ent')){const p=name.includes('Camilo')?CA:name.includes('Sebas')?SE:LU;p.g.updateMatrixWorld(true);const h=headW(p);const w=Math.sin(t*.6)*.02;
    cp.set(IX+.62+w,1.38,2.9-st*.03);la.set(IX+.22,1.18,0);foco=cp.distanceTo(h);}
  else if(name==='mesa'||name==='mesa2'){cp.set(0,1.45,lerp(3.3,3.0,eo(st/3)));la.set(0,.95,-.5);}
  else if(name==='datafono'){const dp=dat.getWorldPosition(V3());const k=eo((t-T.dat-.1)/.35);const base=V3(-.8,1.78,-1.4);cp.copy(base).lerp(dp.clone().add(base.clone().sub(dp).normalize().multiplyScalar(.95)),k);la.copy(dp).add(V3(.08,.08,0)).lerp(dp,k);}
  else if(name==='ventana'){cp.set(1.0,1.55,1.7);la.set(-1.0,1.4,-2.6);}
  else if(name==='qr'){const k=eo(st/.5);cp.set(0,1.45,3.0).lerp(V3(.85,1.55,.95),k);la.set(0,.95,-.5).lerp(V3(.12,.88,-.32),k);}
  else {cp.set(0,1.45,3.2);la.set(0,.95,-.5);}
  if(t>=T.fin){cp.z+=eo((t-T.fin)/.5)*.8;}
  CAM.position.copy(cp);CAM.lookAt(la);CAM.updateMatrixWorld(true);
  bokeh.enabled=!!foco;if(foco){bokeh.uniforms.focus.value=foco;}
  composer.render();
  // ---- capa 2D
  const tt=document.getElementById('titulo');tt.style.opacity=t<T.ent1-.15?1:0;tt.style.transform=`scale(${1.06-.06*eo(t/1.2)})`;
  const ch=CHIPS.find(c=>t>=c[0]&&t<c[1]);const ce=document.getElementById('chip');const ctxt=ch?ch[2]:'';if(ctxt!==chipPrev){ce.querySelector('span').textContent=ctxt;chipPrev=ctxt;}
  ce.style.opacity=ch?1:0;ce.style.transform=ch?`scale(${.85+.15*eb((t-ch[0])/.25)})`:'';
  const lt=LT.find(c=>t>=c[0]&&t<c[1]);const le=document.getElementById('lt');const ltt=lt?lt[2]+'|'+lt[3]:'';if(ltt!==ltPrev){le.querySelector('.n').textContent=lt?lt[2]:'';le.querySelector('.r').textContent=lt?lt[3]:'';ltPrev=ltt;}
  if(lt){const k=eo((t-lt[0])/.3),ko=cl((lt[1]-t)/.2);le.style.opacity=Math.min(k,ko);le.style.transform=`translateX(${(1-k)*-60}px)`;}else le.style.opacity=0;
  const sb=SUBS.find(c=>t>=c[0]-.05&&t<c[1]+.15);const se=document.getElementById('sub');const stx=sb?sb[2]+sb[3]:'';
  if(stx!==subPrev){const sp=se.querySelector('span');sp.textContent=sb?sb[2]:'';sp.className=sb&&sb[3]==='narrador'?'narr':'';subPrev=stx;}
  se.style.opacity=sb?1:0;
  const pg=document.getElementById('pago');const kp=eb((t-T.ok)/.3);pg.style.opacity=t>=T.ok&&t<T.ent4?1:0;pg.style.transform=`scale(${.5+.5*kp}) rotate(-3deg)`;
  const fin=document.getElementById('fin');const kf=eo((t-T.fin)/.35);fin.style.opacity=t>=T.fin?kf:0;fin.style.transform=`translateY(${(1-kf)*80}px)`;
  document.getElementById('cv').style.filter=t>=T.fin?`blur(${eo((t-T.fin)/.4)*12}px)`:'none';
  let fk=0;SHOTS.forEach(x=>{const d=t-x[0];if(x[0]>0&&d>=0&&d<.08)fk=1-d/.08;});document.getElementById('flash').style.opacity=fk*.55;
};
await document.fonts.ready;qrTex.redo();nsTex.redo();datTex.err=false;datTex.redo();
window.render(0);window.__ok=true;
