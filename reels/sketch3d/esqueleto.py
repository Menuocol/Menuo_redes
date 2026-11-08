"""Sketch 3D «Yo pidiendo la cuenta un viernes» (1080x1920, 30 fps). Three.js en Chrome headless (SwiftShader).
Uso: python3 esqueleto.py <salida.mp4> [--voz voz.mp3] [--muestras hoja.jpg]
"""
import os, sys, json, pathlib, subprocess, shutil, argparse, math
import numpy as np
from playwright.sync_api import sync_playwright

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
from reel2 import KIT, SCR, SR, qr_svg  # noqa
import qrcode

FPS, DUR = 30, 19.6
THREE = (AQUI / 'node_modules/three/build/three.min.js').as_uri()
LOGO_B = (KIT / 'menuo-logo-blanco.svg').as_uri()
LOGO_T = (KIT / 'menuo-logo-tinta.svg').as_uri()

def qr_matrix(url):
    q = qrcode.QRCode(border=1); q.add_data(url); q.make()
    return [[1 if v else 0 for v in row] for row in q.get_matrix()]

HTML = r"""<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,100..900&family=Azeret+Mono:wght@500;700&display=swap">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#000}
#c{position:relative;width:1080px;height:1920px;overflow:hidden;font-family:Archivo,Arial,sans-serif;color:#FDFDFF}
#cv{position:absolute;inset:0;width:1080px;height:1920px}
.abs{position:absolute}
.hl{font-weight:900;font-stretch:104%;text-transform:uppercase;letter-spacing:-.035em;line-height:.95}
.mark{background:#C9FB00;color:#1A1B1F;padding:0 .1em;border-radius:.1em}
#cap{left:60px;right:60px;top:200px;font-size:84px;text-align:left;text-shadow:0 6px 30px rgba(0,0,0,.45)}
#hora{left:0;right:0;top:470px;display:flex;justify-content:center}
#hora span{font-family:'Azeret Mono',monospace;font-weight:700;font-size:46px;letter-spacing:.04em;padding:14px 28px;border-radius:999px;background:#1A1B1F;color:#C9FB00;box-shadow:0 20px 40px -16px rgba(0,0,0,.6)}
.bub{position:absolute;padding:20px 30px 24px;border-radius:34px;background:#FDFDFF;color:#1A1B1F;font-weight:900;font-size:46px;letter-spacing:-.02em;white-space:nowrap;box-shadow:0 20px 40px -16px rgba(0,0,0,.55);transform-origin:50% 100%}
.bub:after{content:'';position:absolute;left:50%;bottom:-20px;margin-left:-16px;border:16px solid transparent;border-top:22px solid #FDFDFF;border-bottom:0}
#vhs{inset:0;opacity:0;background:repeating-linear-gradient(0deg,rgba(255,255,255,.07) 0 2px,transparent 2px 6px)}
#vhs b{position:absolute;left:60px;top:220px;font-family:'Azeret Mono',monospace;font-weight:700;font-size:64px;color:#FDFDFF;text-shadow:3px 0 #F42902,-3px 0 #00e5ff}
#fin{inset:0;opacity:0;background:rgba(244,41,2,.94);display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:0 70px}
#fin .pill{margin-top:56px;padding:26px 44px;border-radius:999px;background:#C9FB00;color:#1A1B1F;font-family:'Azeret Mono',monospace;font-weight:700;font-size:34px;text-transform:uppercase}
</style></head><body><div id="c"><canvas id="cv" width="1080" height="1920"></canvas>
<div id="cap" class="abs hl"></div>
<div id="hora" class="abs"><span></span></div>
<div id="bub1" class="bub">¡La cuenta, por favor!</div>
<div id="bub2" class="bub">¿Con tarjeta?</div>
<div id="bub2a" class="bub">¡Listo, ya llegué!</div>
<div id="bub4" class="bub">¿Hola? ¿Alguien?</div>
<div id="bub5" class="bub">Ya no siento el brazo…</div>
<div id="bub6" class="bub" style="font-size:40px">Díganle a mi mamá…<br>que la quiero.</div>
<div id="bub3" class="bub" style="background:#C9FB00">¡Listo!</div>
<div id="pago" class="abs" style="left:290px;top:1080px;width:500px;padding:34px 30px;border-radius:40px;background:#C9FB00;color:#1A1B1F;text-align:center;opacity:0;box-shadow:0 30px 60px -20px rgba(0,0,0,.6)"><div style="width:110px;height:110px;border-radius:50%;background:#1A1B1F;margin:0 auto;display:flex;align-items:center;justify-content:center"><svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#C9FB00" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg></div><div class="hl" style="font-size:64px;margin-top:18px">¡Pagado!</div><div style="font-family:'Azeret Mono',monospace;font-weight:700;font-size:26px;margin-top:10px">NEQUI · $44.000 · MESA 4</div></div>
<div id="vhs" class="abs"><b>◀◀ REBOBINEMOS</b></div>
<div id="fin" class="abs"><img src="__LOGO_B__" style="width:380px"><div class="hl" style="font-size:96px;margin-top:60px">Pide y paga<br>desde la mesa.</div>
<div class="pill">Mándaselo a tu restaurante favorito</div><div style="font-family:'Azeret Mono',monospace;font-weight:700;font-size:30px;margin-top:34px">@menuo.app</div></div>
</div>
<script src="__THREE__"></script>
<script>
const QR=__QR__;
THREE.ColorManagement.legacyMode=false;
const R=new THREE.WebGLRenderer({canvas:document.getElementById('cv'),antialias:true,preserveDrawingBuffer:true});
R.outputEncoding=THREE.sRGBEncoding;R.shadowMap.enabled=true;R.shadowMap.type=THREE.PCFSoftShadowMap;R.setPixelRatio(1);R.setSize(1080,1920,false);
const S=new THREE.Scene();S.background=new THREE.Color('#1A1B1F');
const CAM=new THREE.PerspectiveCamera(36,1080/1920,.1,60);
const cl=x=>Math.min(1,Math.max(0,x)), lerp=(a,b,t)=>a+(b-a)*t, ss=(a,b,t)=>{t=cl((t-a)/(b-a));return t*t*(3-2*t);};
const eo=x=>1-Math.pow(1-cl(x),3), eb=x=>{x=cl(x);const c1=1.9,c3=c1+1;return 1+c3*Math.pow(x-1,3)+c1*Math.pow(x-1,2);};
const M=(c,r=.6,o={})=>new THREE.MeshStandardMaterial(Object.assign({color:c,roughness:r,metalness:0},o));
function mesh(g,m,p=[0,0,0],sh=true){const x=new THREE.Mesh(g,m);x.position.set(...p);x.castShadow=sh;x.receiveShadow=true;return x;}
// luces
S.add(new THREE.HemisphereLight('#ffe9dc','#3a1a12',.75));
const key=new THREE.DirectionalLight('#fff4e8',1.6);key.position.set(3.5,7,5);key.castShadow=true;key.shadow.mapSize.set(1536,1536);
Object.assign(key.shadow.camera,{left:-5,right:5,top:6,bottom:-2,near:1,far:20});key.shadow.radius=4;S.add(key);
const lamp=new THREE.PointLight('#ffb36b',1.1,9,1.6);lamp.position.set(0,3.9,.2);S.add(lamp);
// sala
const wallM=M('#3b2723',.9);S.add(mesh(new THREE.PlaneGeometry(16,10),wallM,[0,4,-3.2],false));
const floor=mesh(new THREE.PlaneGeometry(16,16),M('#5c3a26',.85),[0,0,0],false);floor.rotation.x=-Math.PI/2;S.add(floor);
const trim=mesh(new THREE.BoxGeometry(16,.25,.1),M('#F42902',.6),[0,.9,-3.12],false);S.add(trim);
// ventana
const winFrame=mesh(new THREE.BoxGeometry(1.9,2.3,.12),M('#1A1B1F',.6),[-2.15,3.1,-3.12],false);S.add(winFrame);
const winM=new THREE.MeshBasicMaterial({color:'#0b1030'});const win=mesh(new THREE.PlaneGeometry(1.65,2.05),winM,[-2.15,3.1,-3.05],false);S.add(win);
S.add(mesh(new THREE.BoxGeometry(.08,2.05,.06),M('#1A1B1F'),[-2.15,3.1,-3.0],false));S.add(mesh(new THREE.BoxGeometry(1.65,.08,.06),M('#1A1B1F'),[-2.15,3.1,-3.0],false));
// reloj
const clk=new THREE.Group();clk.position.set(1.65,3.55,-3.1);S.add(clk);
const face=mesh(new THREE.CylinderGeometry(.55,.55,.08,48),M('#FDFDFF',.4),[0,0,0],false);face.rotation.x=Math.PI/2;clk.add(face);
const rim=mesh(new THREE.TorusGeometry(.56,.06,12,48),M('#F42902',.5),[0,0,.03],false);clk.add(rim);
function hand(len,w,c){const g=new THREE.Group();const m=mesh(new THREE.BoxGeometry(w,len,.03),M(c),[0,len/2-.04,0],false);g.add(m);g.position.z=.07;clk.add(g);return g;}
const hH=hand(.3,.06,'#1A1B1F'),hM=hand(.45,.04,'#1A1B1F');
for(let i=0;i<12;i++){const d=mesh(new THREE.BoxGeometry(.03,.08,.02),M('#1A1B1F'),[Math.sin(i*Math.PI/6)*.45,Math.cos(i*Math.PI/6)*.45,.05],false);d.rotation.z=-i*Math.PI/6;clk.add(d);}
// planta
const plant=new THREE.Group();plant.position.set(2.45,0,-2.4);S.add(plant);
plant.add(mesh(new THREE.CylinderGeometry(.32,.24,.6,24),M('#c2643a',.8),[0,.3,0]));
const leafM=M('#2f8f4e',.7);[[0,1,0,.42],[.25,1.35,.05,.32],[-.22,1.3,0,.34],[.05,1.65,0,.3],[-.1,1.95,.05,.24],[.18,2.2,0,.2]].forEach(([x,y,z,r])=>plant.add(mesh(new THREE.SphereGeometry(r,20,16),leafM,[x,y,z])));
plant.add(mesh(new THREE.CylinderGeometry(.04,.05,2.2,8),M('#3d6b2e'),[0,1.2,0]));
// mesa
const table=new THREE.Group();S.add(table);
table.add(mesh(new THREE.CylinderGeometry(1.25,1.25,.07,48),M('#F42902',.75),[0,1.02,0]));
table.add(mesh(new THREE.CylinderGeometry(1.32,1.25,.22,48,1,true),M('#d92402',.8,{side:THREE.DoubleSide}),[0,.9,0]));
table.add(mesh(new THREE.CylinderGeometry(.08,.08,.9,12),M('#1A1B1F'),[0,.45,0]));
table.add(mesh(new THREE.CylinderGeometry(.5,.5,.05,24),M('#1A1B1F'),[0,.03,0]));
// vaso y plato
table.add(mesh(new THREE.CylinderGeometry(.13,.11,.32,24),M('#cfe8ff',.1,{transparent:true,opacity:.55}),[.65,1.22,.25]));
table.add(mesh(new THREE.CylinderGeometry(.42,.38,.04,32),M('#FDFDFF',.3),[-.15,1.08,.35]));
// QR de mesa (porta-QR)
function texCanvas(w,h,draw){const c=document.createElement('canvas');c.width=w;c.height=h;const x=c.getContext('2d');draw(x,w,h);const t=new THREE.CanvasTexture(c);t.encoding=THREE.sRGBEncoding;t.anisotropy=4;return {t,c,x,draw};}
const qrTex=texCanvas(256,340,(x,w,h)=>{x.fillStyle='#FDFDFF';x.fillRect(0,0,w,h);x.fillStyle='#F42902';x.fillRect(0,0,w,46);x.fillStyle='#FDFDFF';x.font='900 30px Archivo';x.textAlign='center';x.fillText('MENUO',w/2,33);
  const n=QR.length,s=200/n;x.fillStyle='#1A1B1F';QR.forEach((r,i)=>r.forEach((v,j)=>{if(v)x.fillRect(28+j*s,64+i*s,s+.5,s+.5);}));x.font='800 24px Archivo';x.fillText('Escanea y paga',w/2,300);x.font='700 18px Azeret Mono';x.fillStyle='#F42902';x.fillText('MESA 4',w/2,326);});
const tent=new THREE.Group();tent.position.set(.55,1.06,-.15);tent.rotation.y=-.35;table.add(tent);
const tentFront=mesh(new THREE.PlaneGeometry(.38,.5),new THREE.MeshStandardMaterial({map:qrTex.t,roughness:.5}),[0,.24,0]);tentFront.rotation.x=-.18;tent.add(tentFront);
tent.add(mesh(new THREE.BoxGeometry(.4,.02,.2),M('#1A1B1F'),[0,0,-.05]));
// silla
const chair=new THREE.Group();chair.position.set(0,0,-1.25);S.add(chair);
chair.add(mesh(new THREE.BoxGeometry(1.1,.1,.9),M('#1A1B1F',.6),[0,.85,0]));chair.add(mesh(new THREE.BoxGeometry(1.1,1.5,.1),M('#1A1B1F',.6),[0,1.6,-.42]));
// ---------------- cliente
const skin='#e9b48d';
function persona(shirt,hair){
  const g=new THREE.Group();
  const body=mesh(new THREE.CapsuleGeometry(.48,.7,10,28),M(shirt,.65),[0,1.55,0]);g.add(body);
  const head=new THREE.Group();head.position.set(0,2.64,0);g.add(head);
  const skinM=M(skin,.55);const hd=mesh(new THREE.SphereGeometry(.46,40,32),skinM);head.add(hd);
  const hairM=M(hair,.7);const hr=mesh(new THREE.SphereGeometry(.475,40,32,0,Math.PI*2,0,Math.PI*.42),hairM,[0,.03,-.02]);hr.rotation.x=-.25;head.add(hr);
  const eyes=[],pupils=[],lids=[];
  [-.17,.17].forEach(x=>{const e=mesh(new THREE.SphereGeometry(.13,24,18),M('#ffffff',.25),[x,.06,.36]);head.add(e);eyes.push(e);
    const p=mesh(new THREE.SphereGeometry(.065,16,12),M('#111111',.2),[x,.05,.48]);head.add(p);pupils.push(p);
    const l=mesh(new THREE.SphereGeometry(.137,24,18,0,Math.PI*2,0,Math.PI/2),skinM,[x,.06,.36]);head.add(l);lids.push(l);});
  const brows=[-.17,.17].map(x=>{const b=mesh(new THREE.BoxGeometry(.18,.04,.04),hairM,[x,.25,.42]);head.add(b);return b;});
  const mouth=new THREE.Group();mouth.position.set(0,-.17,.42);head.add(mouth);
  const lip=mesh(new THREE.TorusGeometry(.13,.03,8,24,Math.PI),M('#4a1610',.5));lip.rotation.z=Math.PI;mouth.add(lip);
  const nose=mesh(new THREE.SphereGeometry(.06,16,12),skinM,[0,-.04,.46]);head.add(nose);
  function arm(side){const a=new THREE.Group();a.position.set(side*.5,2.02,0);g.add(a);
    a.add(mesh(new THREE.CapsuleGeometry(.12,.55,6,16),M(shirt,.65),[0,-.33,0]));const hnd=mesh(new THREE.SphereGeometry(.13,20,16),skinM,[0,-.72,0]);a.add(hnd);a.hand=hnd;return a;}
  return {g,body,head,eyes,pupils,lids,brows,mouth,lip,armR:arm(-1),armL:arm(1),skinM,hairM,shirtM:body.material};
}
const P=persona('#C9FB00','#2b1b14');P.g.position.set(0,0,-.95);S.add(P.g);
const beard=mesh(new THREE.SphereGeometry(.4,32,24,0,Math.PI*2,Math.PI*.45,Math.PI*.55),M('#2b1b14',.8),[0,-.08,.06]);P.head.add(beard);
// telaraña
const webM=new THREE.LineBasicMaterial({color:'#ffffff',transparent:true,opacity:0});
const webG=new THREE.BufferGeometry();const wp=[];for(let i=0;i<9;i++){const a=i/8*Math.PI*.9;wp.push(-.9,3.2,-.95,-.9+Math.cos(a)*-.6,3.2-Math.sin(a)*.9,-.95);}
for(let k=1;k<4;k++)for(let i=0;i<8;i++){const a1=i/8*Math.PI*.9,a2=(i+1)/8*Math.PI*.9,r=k*.2;wp.push(-.9-Math.cos(a1)*r,3.2-Math.sin(a1)*r*1.5,-.95,-.9-Math.cos(a2)*r,3.2-Math.sin(a2)*r*1.5,-.95);}
webG.setAttribute('position',new THREE.Float32BufferAttribute(wp,3));const web=new THREE.LineSegments(webG,webM);S.add(web);
// teléfono en la mano derecha
const phTex=texCanvas(200,400,()=>{});
function drawPhone(state){const x=phTex.x,w=200,h=400;if(state==='ok'){x.fillStyle='#C9FB00';x.fillRect(0,0,w,h);x.fillStyle='#1A1B1F';x.beginPath();x.arc(100,150,48,0,7);x.fill();
  x.strokeStyle='#C9FB00';x.lineWidth=12;x.lineCap='round';x.beginPath();x.moveTo(78,152);x.lineTo(95,170);x.lineTo(124,134);x.stroke();x.font='900 40px Archivo';x.textAlign='center';x.fillText('¡PAGADO!',100,250);x.font='700 18px Azeret Mono';x.fillText('NEQUI · $44.000',100,284);}
  else{x.fillStyle='#F42902';x.fillRect(0,0,w,h);x.fillStyle='#FDFDFF';x.font='900 30px Archivo';x.textAlign='center';x.fillText('MESA 4',100,70);x.fillStyle='#FDFDFF';x.fillRect(16,110,168,170);x.fillStyle='#1A1B1F';x.font='800 20px Archivo';x.fillText('Total',100,160);x.font='900 34px Archivo';x.fillText('$44.000',100,205);
  x.fillStyle='#1A1B1F';x.fillRect(16,310,168,54);x.fillStyle='#C9FB00';x.font='800 24px Archivo';x.fillText('Pagar',100,345);}
  phTex.t.needsUpdate=true;}
const phone=new THREE.Group();const phBody=mesh(new THREE.BoxGeometry(.32,.6,.04),M('#1A1B1F',.3));phone.add(phBody);
const phScr=mesh(new THREE.PlaneGeometry(.28,.55),new THREE.MeshBasicMaterial({map:phTex.t}),[0,0,.022],false);phone.add(phScr);
phone.position.set(0,-.86,0);phone.visible=false;P.armL.add(phone);
// rayo de escaneo
const beam=mesh(new THREE.CylinderGeometry(.015,.015,1,8),new THREE.MeshBasicMaterial({color:'#C9FB00',transparent:true,opacity:0}),[0,0,0],false);S.add(beam);
// ---------------- esqueleto
const boneM=M('#efe7d4',.6);const holeM=M('#120c0a',.9);
const SK=new THREE.Group();SK.position.copy(P.g.position);S.add(SK);SK.visible=false;
const skull=new THREE.Group();skull.position.set(0,2.66,0);SK.add(skull);
skull.add(mesh(new THREE.SphereGeometry(.42,36,28),boneM,[0,.05,0]));
[-.15,.15].forEach(x=>skull.add(mesh(new THREE.SphereGeometry(.12,20,16),holeM,[x,.07,.33])));
skull.add(mesh(new THREE.ConeGeometry(.05,.1,3),holeM,[0,-.08,.4]));
const teeth=mesh(new THREE.BoxGeometry(.32,.06,.12),boneM,[0,-.2,.28]);skull.add(teeth);
const jaw=new THREE.Group();SK.add(jaw);const jawU=mesh(new THREE.TorusGeometry(.17,.05,10,24,Math.PI),boneM);jawU.rotation.x=Math.PI/2;jawU.rotation.z=Math.PI;jaw.add(jawU);
for(let i=0;i<5;i++)jaw.add(mesh(new THREE.BoxGeometry(.045,.06,.04),boneM,[-.1+i*.05,.05,.15+Math.abs(i-2)*-.03]));const jawHome=new THREE.Vector3(0,2.36,.12);
SK.add(mesh(new THREE.CylinderGeometry(.06,.06,1.2,10),boneM,[0,1.7,-.12]));
for(let i=0;i<4;i++){const r=mesh(new THREE.TorusGeometry(.38-i*.03,.035,8,30,Math.PI*1.4),boneM,[0,2.08-i*.17,0]);r.rotation.set(Math.PI/2,0,-Math.PI*.2);r.rotation.z=Math.PI*.8;SK.add(r);}
SK.add(mesh(new THREE.BoxGeometry(.9,.07,.07),boneM,[0,2.2,0]));
function boneArm(side){const a=new THREE.Group();a.position.set(side*.46,2.18,0);SK.add(a);a.add(mesh(new THREE.CylinderGeometry(.045,.045,.7,8),boneM,[0,-.38,0]));
  a.add(mesh(new THREE.SphereGeometry(.07,12,10),boneM,[0,-.75,0]));[-.05,0,.05].forEach(x=>a.add(mesh(new THREE.CylinderGeometry(.018,.018,.18,6),boneM,[x,-.86,0])));return a;}
const skR=boneArm(-1),skL=boneArm(1);
// polvo / confeti
const dust=[];for(let i=0;i<40;i++){const d=mesh(new THREE.SphereGeometry(.06+Math.random()*.08,10,8),M('#f4efe6',.9,{transparent:true,opacity:0}),[0,0,0],false);d.v=new THREE.Vector3((Math.random()-.5)*3,(Math.random())*2.2,(Math.random()-.2)*2);S.add(d);dust.push(d);}
const confC=['#C9FB00','#F42902','#FDFDFF','#1A1B1F','#ffd23f'];const conf=[];
let seed=7;const rnd=()=>{seed=(seed*16807)%2147483647;return seed/2147483647;};
for(let i=0;i<90;i++){const c=mesh(new THREE.BoxGeometry(.07,.11,.01),new THREE.MeshStandardMaterial({color:confC[i%5],roughness:.5,side:THREE.DoubleSide}),[0,0,0],false);
  c.v=new THREE.Vector3((rnd()-.5)*5,2.5+rnd()*3,(rnd()-.1)*2.5);c.w=new THREE.Vector3(rnd()*12,rnd()*12,rnd()*12);c.visible=false;S.add(c);conf.push(c);}
// ---------------- mesero
const W=persona('#FDFDFF','#1A1B1F');W.g.scale.setScalar(1.05);S.add(W.g);
W.g.add(mesh(new THREE.BoxGeometry(.9,.85,.1),M('#1A1B1F',.7),[0,1.25,.48]));
const bow=new THREE.Group();bow.position.set(0,2.0,.5);W.g.add(bow);[-1,1].forEach(s=>{const b=mesh(new THREE.ConeGeometry(.08,.16,4),M('#F42902'),[s*.08,0,0]);b.rotation.z=s*Math.PI/2;bow.add(b);});
const datTex=texCanvas(220,170,()=>{});
function drawDat(st){const x=datTex.x;x.fillStyle=st==='err'?'#F42902':'#7fd3a8';x.fillRect(0,0,220,170);x.fillStyle=st==='err'?'#FDFDFF':'#0d2b1d';x.textAlign='center';
  if(st==='err'){x.font='900 34px Archivo';x.fillText('SIN SEÑAL',110,100);x.font='700 16px Azeret Mono';x.fillText('ERROR 404',110,135);}else{x.font='800 26px Azeret Mono';x.fillText('INSERTE',110,75);x.fillText('TARJETA',110,110);}datTex.t.needsUpdate=true;}
const dat=new THREE.Group();dat.add(mesh(new THREE.BoxGeometry(.36,.6,.1),M('#2a2b30',.4)));
dat.add(mesh(new THREE.PlaneGeometry(.3,.23),new THREE.MeshBasicMaterial({map:datTex.t}),[0,.13,.052],false));
for(let i=0;i<9;i++)dat.add(mesh(new THREE.BoxGeometry(.07,.05,.02),M('#d8d8de',.5),[-.09+(i%3)*.09,-.06-Math.floor(i/3)*.07,.055],false));
dat.position.set(0,-.86,.05);W.armL.add(dat);
// ---------------- estado por tiempo
const CAP=[[0,7.2,'Yo pidiendo<br>la cuenta<br>un <span class="mark">viernes:</span>'],[7.6,8.75,'Y cuando por fin<br>llega el <span class="mark">mesero…</span>'],[13.4,17.0,'<span class="mark">Con Menuo:</span>']];
const HORA=[[0,2.4,'8:00 P. M.'],[2.4,3.5,'8:47 P. M.'],[3.5,4.6,'11:58 P. M.'],[4.6,5.7,'4:12 A. M.'],[5.7,8.4,'3 SEMANAS DESPUÉS'],[13.4,14.6,'8:00 P. M.'],[14.6,17.0,'8:01 P. M.']];
let capPrev='',horaPrev='',phState='',datState='';
const v3=new THREE.Vector3();
function anchor(el,obj,dy,t0,t1,t){if(t<t0||t>=t1){el.style.opacity=0;return;}obj.getWorldPosition(v3);v3.y+=dy;v3.project(CAM);
  const x=(v3.x*.5+.5)*1080,y=(-v3.y*.5+.5)*1920;const k=eb((t-t0)/.25),ko=cl((t1-t)/.15);el.style.opacity=Math.min(1,k*2)*ko;
  el.style.left=Math.max(30,Math.min(1080-30-el.offsetWidth,x-el.offsetWidth/2))+'px';el.style.top=(y-el.offsetHeight-30)+'px';el.style.transform=`scale(${.5+.5*k})`;}
window.render=function(t){
  const rew=t>=12.0&&t<13.4, men=t>=13.4;
  const s=rew?lerp(12.0,.4,eo((t-12.0)/1.4)):(men?0:t);   // tiempo de la historia de espera
  const u=t-13.4;                                          // tiempo de la rama Menuo
  // --- cliente vs esqueleto
  const esq=!men&&s>=7.25;P.g.visible=!esq;SK.visible=esq;
  // brazo levantado / cansado
  let armR=-.15;if(!men){armR=lerp(-.15,-2.75,eo((s-.08)/.3));armR=lerp(armR,-2.05,ss(3.5,4.1,s))+Math.sin(s*9)*.06*ss(3.6,4.2,s);}
  let armL=.15,armRx=0;
  let armLx=0;
  if(men){armLx=lerp(0,-1.15,eo((u-.1)/.4));armL=lerp(.15,-.05,eo((u-.1)/.4));const cel=ss(2.8,3.05,u);armR=lerp(-.15,-2.75,cel);armL=lerp(armL,2.75,cel);armLx=lerp(armLx,0,cel);}
  P.armR.rotation.set(armRx,0,armR);P.armL.rotation.set(armLx,0,armL);phone.rotation.x=Math.PI/2-armLx;
  // cara
  const tired=men?0:ss(3.4,4.4,s), sad=men?0:ss(2.6,3.6,s);
  P.head.rotation.z=men?Math.sin(u*10)*.08*ss(2.85,3.05,u)*(1-ss(4.3,4.6,u)):tired*.22;
  P.head.rotation.x=men?0:tired*.12;
  const smile=men?1:lerp(1,-1,sad);P.lip.rotation.z=smile>=0?Math.PI:0;P.lip.scale.set(1,Math.max(.25,Math.abs(smile)),1);P.mouth.position.y=smile>=0?-.17:-.24;
  const blink=(Math.abs(((t*1.0)%3.1)-1.5)<.06)?1:0;const lid=men?blink:Math.max(blink,tired*.55);
  P.lids.forEach(l=>{l.scale.set(1,lerp(.02,1,lid),1);l.rotation.x=Math.PI*.5*(1-lid)*0-.0;l.visible=lid>.02;});
  P.brows.forEach((b,i)=>{b.rotation.z=(i?-1:1)*(men?.15:lerp(.0,-.35,sad));b.position.y=.25+(men?.04:0);});
  const look=men?.0:Math.sin(s*1.3)*.03;P.pupils.forEach((p,i)=>{p.position.x=(i?.17:-.17)+look;});
  beard.scale.setScalar(men?.001:lerp(.001,1,ss(3.9,6.6,s)));beard.visible=beard.scale.x>.01;
  const grey=men?0:ss(5.6,7.1,s);P.shirtM.color.set('#C9FB00').lerp(new THREE.Color('#8a8a7a'),grey);P.skinM.color.set(skin).lerp(new THREE.Color('#a9a39a'),grey);
  P.g.position.y=men?Math.abs(Math.sin(u*9))*.18*ss(2.8,2.95,u)*(1-ss(4.3,4.6,u)):0;
  webM.opacity=men?0:ss(5.4,6.2,s)*.75;
  // esqueleto: mandíbula que se cae
  skR.rotation.z=-2.2+Math.sin(t*1.5)*.03;skL.rotation.z=.2;
  if(t>=11.4&&!rew&&!men){const d=t-11.4;let y=2.36-4.9*d*d;let bounce=0;if(y<1.1){const d2=d-Math.sqrt(1.26/4.9);y=1.1+Math.abs(Math.sin(d2*9))*.25*Math.exp(-d2*5);bounce=1;}
    jaw.position.set(.05+d*.25,y,.17+Math.min(d,.45)*.6);jaw.rotation.set(d*3,0,d*2);}else{jaw.position.copy(jawHome);jaw.rotation.set(0,0,0);}
  skull.rotation.z=esq?Math.sin(t*1.2)*.04:0;
  // polvo (puf)
  const pd=s-7.2;dust.forEach(d=>{if(!men&&pd>=0&&pd<1.1){d.material.opacity=(1-pd/1.1)*.9;d.position.set(P.g.position.x+d.v.x*pd*.8,1.9+d.v.y*pd*.7,P.g.position.z+d.v.z*pd*.6);d.scale.setScalar(1+pd*2);}else d.material.opacity=0;});
  // reloj, ventana, planta
  let hrs=8+ (men?(u>1.2?1/60:0):0);if(!men)hrs+=Math.pow(cl((s-2.4)/4.8),1.6)*500+ (s>2.4?0:0);
  hM.rotation.z=-((hrs%1)*Math.PI*2);hH.rotation.z=-((hrs%12)/12*Math.PI*2);
  if(!men&&s>2.4&&s<7.2){const ph=Math.sin((s-2.4)*7)*.5+.5;winM.color.set('#0b1030').lerp(new THREE.Color('#ffb066'),ph*.5).lerp(new THREE.Color('#8fd3ff'),Math.max(0,ph-.6)*2);}else winM.color.set('#0b1030');
  plant.scale.setScalar(men?1:lerp(1,2.3,ss(2.4,7.0,s)));
  // mesero
  let wx=-8,wz=-2.3,wy=0,wry=Math.PI/2;
  if(!men&&!rew){if(t>=2.9&&t<4.0){wx=lerp(-4.2,4.2,(t-2.9)/1.1);wz=-2.0;wry=Math.PI/2;}else if(t>=5.0&&t<5.9){wx=lerp(4.2,-4.2,(t-5.0)/.9);wz=-2.0;wry=-Math.PI/2;}
    else if(t>=8.6){wx=lerp(4,.92,eo((t-8.6)/.55));wz=.3;wry=lerp(-Math.PI/2,-.5,ss(8.9,9.15,t));}
    wy=((t>=2.9&&t<5.9)||(t>=8.6&&t<9.15))?Math.abs(Math.sin(t*22))*.12:0;}
  W.g.position.set(wx,wy,wz);W.g.rotation.y=wry;const wa=-1.2*ss(9.85,10.15,t);W.armL.rotation.set(wa,0,.12);dat.rotation.x=-wa+.1;W.armR.rotation.set(Math.sin(t*22)*.6*(wy>0?1:0),0,-.15);
  W.lip.rotation.z=Math.PI;W.lids.forEach(l=>l.visible=false);
  const ds=t>=10.75?'err':'ok';if(ds!==datState){drawDat(ds);datState=ds;}
  // teléfono y QR
  phone.visible=men&&u>.15&&u<2.85;const pst=u>=1.15?'ok':'pay';if(pst!==phState){drawPhone(pst);phState=pst;}
  if(men&&u>.55&&u<1.15){const a=new THREE.Vector3(),b=new THREE.Vector3();phone.getWorldPosition(a);tentFront.getWorldPosition(b);
    beam.position.copy(a).add(b).multiplyScalar(.5);beam.scale.set(1,a.distanceTo(b),1);beam.lookAt(b);beam.rotateX(Math.PI/2);beam.material.opacity=.9*Math.sin((u-.55)/.6*Math.PI);}else beam.material.opacity=0;
  // confeti
  const cu=u-2.8;conf.forEach(c=>{if(men&&cu>=0&&cu<3){c.visible=true;c.position.set(c.v.x*cu*.6,2.4+c.v.y*cu-4.5*cu*cu*.5,-.6+c.v.z*cu*.5);if(c.position.y<.05)c.position.y=.05;c.rotation.set(c.w.x*cu,c.w.y*cu,c.w.z*cu);}else c.visible=false;});
  // cámara
  let cp=new THREE.Vector3(0,2.45,lerp(7.0,6.3,ss(0,7,t))),la=new THREE.Vector3(0,2.3,-.7);
  if(!men&&!rew&&t>=10.65&&t<11.15){const dp=new THREE.Vector3();dat.getWorldPosition(dp);const k=eo((t-10.65)/.25);cp.lerp(dp.clone().add(new THREE.Vector3(-.15,.1,1.5)),k);la.lerp(dp,k);}
  if(!men&&!rew&&t>=11.15){const k=eo((t-11.15)/.2)*(1-ss(11.95,12.0,t));cp.lerp(new THREE.Vector3(.1,2.6,3.0),k);la.lerp(new THREE.Vector3(.05,2.25,-.95),k);}
  if(rew){cp.x+=Math.sin(t*60)*.05;cp.y+=Math.cos(t*47)*.04;}
  if(men){cp.set(0,2.2,5.6);la.set(.2,1.6,-.4);const k=eo((u-.5)/.5)*(1-ss(1.8,2.4,u));cp.lerp(new THREE.Vector3(.75,2.0,3.4),k);la.lerp(new THREE.Vector3(.5,1.45,-.4),k);}
  if(t>=17.0){const k=eo((t-17.0)/.5);cp.z+=k*1.2;}
  CAM.position.copy(cp);CAM.lookAt(la);
  R.render(S,CAM);
  // --- capa 2D
  const cap=CAP.find(c=>t>=c[0]&&t<c[1]);const capEl=document.getElementById('cap');const ct=cap?cap[2]:'';if(ct!==capPrev){capEl.innerHTML=ct;capPrev=ct;}
  capEl.style.opacity=cap?(cap[0]===0?1:Math.min(1,eo((t-cap[0])/.18)*1.2)):0;
  const ho=HORA.find(c=>t>=c[0]&&t<c[1]);const hEl=document.querySelector('#hora span');const htxt=ho?ho[2]:'';if(htxt!==horaPrev){hEl.textContent=htxt;horaPrev=htxt;}
  document.getElementById('hora').style.opacity=ho&&!rew?1:0;document.getElementById('hora').style.top=(men?330:1250)+'px';document.getElementById('hora').style.transform=ho?`scale(${.85+.15*eb((t-ho[0])/.22)})`:'';
  anchor(document.getElementById('bub1'),P.head,.55,.25,2.4,t);
  anchor(document.getElementById('bub2a'),W.head,.6,8.75,9.95,t);anchor(document.getElementById('bub2'),W.head,.6,10.0,10.7,t);
  anchor(document.getElementById('bub4'),P.head,.55,2.5,3.7,t);anchor(document.getElementById('bub5'),P.head,.55,3.8,5.2,t);anchor(document.getElementById('bub6'),P.head,.55,5.25,7.2,t);
  anchor(document.getElementById('bub3'),P.head,.6,16.2,17.0,t);
  const pg=document.getElementById('pago');const kp=eb((u-1.15)/.3);pg.style.opacity=men&&u>=1.15&&t<17.0?1:0;pg.style.transform=`scale(${.5+.5*kp}) rotate(-3deg)`;
  const vh=document.getElementById('vhs');vh.style.opacity=rew?1:0;document.getElementById('cv').style.filter=rew?'saturate(.4) contrast(1.2) hue-rotate(-12deg)':(t>=17.0?`blur(${eo((t-17.0)/.4)*12}px)`:'none');
  const fin=document.getElementById('fin');const kf=eo((t-17.05)/.35);fin.style.opacity=t>=17.05?kf:0;fin.style.transform=`translateY(${(1-kf)*80}px)`;
};
(async()=>{await document.fonts.ready;drawPhone('pay');drawDat('ok');qrTex.draw(qrTex.x,256,340);qrTex.t.needsUpdate=true;
  await Promise.all([...document.images].map(i=>i.decode().catch(()=>{})));window.render(0);window.__ok=true;})();
</script></body></html>"""

def pagina():
    h = HTML.replace('__THREE__', THREE).replace('__LOGO_B__', LOGO_B).replace('__QR__', json.dumps(qr_matrix('https://menuo.com.co')))
    tmp = SCR / 'sketch3d'; tmp.mkdir(parents=True, exist_ok=True)
    p = tmp / 'esqueleto.html'; p.write_text(h, encoding='utf-8'); return p, tmp

def abrir(pw, page):
    b = pw.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--allow-file-access-from-files', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
    pg = b.new_page(viewport={'width': 1080, 'height': 1920})
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
    pg.goto(page.as_uri(), wait_until='networkidle')
    try: pg.wait_for_function('window.__ok===true', timeout=40000)
    except Exception: print('ERRORES', errs); raise
    if errs: print('avisos:', errs[:5])
    return b, pg

# ---------------------------------------------------------------- sonido (sintetizado)
def sonido(tramos):
    """tramos: lista de (archivo, desde, hasta, en_t)."""
    n = int(DUR * SR); a = np.zeros(n, np.float32); rng = np.random.default_rng(3)
    def put(x, t, g=1.0):
        i = int(t * SR); j = min(n, i + len(x)); a[i:j] += x[:j - i] * g
    T = lambda d: np.arange(int(d * SR)) / SR
    def tick():
        x = rng.standard_normal(int(.012 * SR)) * np.exp(-T(.012) * 500); return x * .5
    t, step = 2.4, .5   # tic-tac que se acelera
    while t < 7.15:
        put(tick(), t, .32); step = max(.07, step * .9); t += step
    x = rng.standard_normal(int(.45 * SR)); x = np.convolve(x, np.ones(40) / 40, 'same') * np.exp(-T(.45) * 7); put(x, 7.2, 1.4)   # puf
    for k in range(3):   # grillos
        for j in range(3):
            tt = T(.035); put(np.sin(2 * np.pi * 4700 * tt) * np.hanning(len(tt)) * .18, 7.55 + k * .3 + j * .06)
    for k, f in enumerate([880, 440]):   # datáfono: error
        tt = T(.16); put(np.sign(np.sin(2 * np.pi * f * tt)) * .16 * np.exp(-tt * 6), 10.75 + k * .19)
    tt = T(.7); f = 170 + 140 * np.sin(2 * np.pi * 9 * tt) * np.exp(-tt * 4)   # boing
    put(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 3.5) * .55, 11.62)
    tt = T(1.4); f = 900 - 600 * tt / 1.4   # rebobinado
    put((np.sin(2 * np.pi * np.cumsum(f) / SR) * .1 + rng.standard_normal(len(tt)) * .04) * np.hanning(len(tt)), 12.0)
    for k, f in enumerate([1046.5, 1568]):   # pagado
        tt = T(.9); put((np.sin(2 * np.pi * f * tt) + .3 * np.sin(4 * np.pi * f * tt)) * np.exp(-tt * 5) * .22, 14.55 + k * .11)
    for k in range(10):   # confeti
        tt = T(.03); put(rng.standard_normal(len(tt)) * np.exp(-tt * 200) * .22, 16.22 + rng.random() * .5)
    cache = {}
    for archivo, d0, d1, t0 in tramos:
        if archivo not in cache:
            v = subprocess.run(['ffmpeg', '-v', 'error', '-i', archivo, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
            cache[archivo] = np.frombuffer(v, np.float32)
        seg = cache[archivo][int(d0 * SR):int(d1 * SR)].copy(); fd = int(.015 * SR)
        seg[:fd] *= np.linspace(0, 1, fd); seg[-fd:] *= np.linspace(1, 0, fd)
        put(seg, t0, 1.0)
    pk = np.max(np.abs(a)); a = a / pk * .95 if pk > .95 else a
    return a

def render(out, voz_t=None, hoja=None):
    page, tmp = pagina()
    if hoja:
        from PIL import Image, ImageDraw
        ts = [.5, 3.0, 4.4, 6.2, 7.6, 9.2, 10.3, 10.9, 11.6, 12.6, 14.0, 14.8, 15.8, 16.5, 18.0]
        with sync_playwright() as pw:
            b, pg = abrir(pw, page); ims = []
            for t in ts:
                pg.evaluate(f'window.render({t})'); f = tmp / f'm{t:05.2f}.jpg'; pg.screenshot(path=str(f), type='jpeg', quality=80); ims.append((t, f))
            b.close()
        W, H, cols = 270, 480, 7; rows = (len(ims) + cols - 1) // cols
        sh = Image.new('RGB', (W * cols, (H + 24) * rows), 'white'); d = ImageDraw.Draw(sh)
        for k, (t, f) in enumerate(ims):
            x, y = (k % cols) * W, (k // cols) * (H + 24); sh.paste(Image.open(f).resize((W, H)), (x, y)); d.text((x + 5, y + H + 5), f'{t:.1f}s', fill='black')
        sh.save(hoja, quality=82); print('hoja', hoja); return
    frames = tmp / 'f'; shutil.rmtree(frames, ignore_errors=True); frames.mkdir()
    n = int(DUR * FPS)
    with sync_playwright() as pw:
        b, pg = abrir(pw, page)
        for i in range(n):
            pg.evaluate(f'window.render({i / FPS:.4f})'); pg.screenshot(path=str(frames / f'f{i:04d}.jpg'), type='jpeg', quality=90)
        b.close()
    wav = tmp / 'audio.wav'
    a = sonido(voz_t or [])
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-', str(wav)], input=a.tobytes(), check=True)
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-framerate', str(FPS), '-i', str(frames / 'f%04d.jpg'), '-i', str(wav), '-map', '0:v', '-map', '1:a',
                    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-ac', '2', '-shortest', '-movflags', '+faststart', out], check=True)
    print('ok', out, n, 'cuadros')

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--muestras', action='store_true')
    ap.add_argument('--roger'); ap.add_argument('--adam')
    a = ap.parse_args()
    vt = []
    if a.roger:  # cliente / narrador
        vt += [(a.roger, 0.0, 2.30, .12), (a.roger, 2.76, 4.10, 2.5), (a.roger, 4.58, 6.10, 3.8), (a.roger, 6.50, 8.58, 5.2),
               (a.roger, 8.92, 10.45, 11.98), (a.roger, 10.75, 13.55, 13.5), (a.roger, 13.66, 14.38, 16.32), (a.roger, 14.42, 16.45, 17.2)]
    if a.adam:   # mesero
        vt += [(a.adam, 0.0, 1.38, 8.7), (a.adam, 1.72, 2.40, 10.0)]
    if a.muestras: render(None, hoja=a.out)
    else: render(a.out, vt)
