"""Falso documental 3D «LA CUENTA» (1080x1920, 30 fps). Three.js en Chrome headless (SwiftShader).
Uso: python3 documental.py <voces.mp3> <salida.mp4> [--muestras hoja.jpg]
voces.mp3 = los 4 bloques (narrador, Camilo, Sebas, Lucía) en un solo archivo, en ese orden.
"""
import sys, json, pathlib, subprocess, shutil, argparse
import numpy as np
from playwright.sync_api import sync_playwright

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
from reel2 import KIT, SCR, SR  # noqa
import qrcode

FPS = 30
THREE = (AQUI / 'node_modules/three/build/three.min.js').as_uri()
LOGO_B = (KIT / 'menuo-logo-blanco.svg').as_uri()

# tramos del archivo de voces (segundos en el archivo) -> (hablante, desde, hasta, en_t, subtítulo)
# Detectados por silencios en el archivo que mandó Santy (44,4 s).
TRAMOS = [
    ('narrador', 0.00, 2.05, 0.10, 'Esta es la historia de una cuenta…'),
    ('narrador', 2.42, 4.75, 2.40, '…que tardó cuarenta minutos en llegar.'),
    ('camilo', 16.45, 18.32, 4.85, 'Yo solo quería pagar e irme.'),
    ('camilo', 18.52, 20.05, 6.85, 'Tenía el carro mal parqueado.'),
    ('camilo', 20.47, 21.12, 8.60, '¡Sebas!'),
    ('camilo', 21.29, 22.68, 9.25, '¿Me traes la cuenta, porfa?'),
    ('sebas', 27.56, 28.58, 10.70, '¡Ya voy, ya voy!'),
    ('narrador', 5.14, 7.02, 11.85, 'Sebas tenía doce mesas…'),
    ('narrador', 7.25, 8.85, 13.85, '…y un solo datáfono.'),
    ('sebas', 28.79, 31.45, 15.55, 'El datáfono vive en la caja. Yo vivo corriendo.'),
    ('sebas', 31.71, 33.66, 19.05, 'Ehh… ¿me haces transferencia?'),
    ('camilo', 23.09, 23.86, 21.15, '¿Y el carro?'),
    ('narrador', 9.13, 11.68, 22.05, 'La grúa fue más rápida que la cuenta.'),
    ('lucia', 38.01, 42.07, 24.75, 'Y mientras tanto, en la puerta, había gente esperando mesa.'),
    ('lucia', 42.45, 44.40, 29.00, 'Ahí dije: no más.'),
    ('narrador', 12.04, 13.15, 31.15, 'Viernes siguiente.'),
    ('camilo', 24.20, 24.93, 32.35, '¿Escaneo…'),
    ('camilo', 25.07, 25.69, 33.15, '…y ya?'),
    ('sebas', 33.96, 35.74, 34.05, 'Ahora cada mesa paga sola.'),
    ('sebas', 35.91, 37.77, 35.95, 'Y yo, por fin, atiendo.'),
    ('camilo', 25.96, 27.41, 37.95, 'Y el carro sigue ahí.'),
    ('narrador', 13.38, 14.04, 39.55, 'Menuo.'),
    ('narrador', 14.32, 16.06, 40.40, 'Pide y paga desde la mesa.'),
]
DUR = 42.9

HTML = r"""<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,100..900&family=Azeret+Mono:wght@500;700&display=swap">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#000}
#c{position:relative;width:1080px;height:1920px;overflow:hidden;font-family:Archivo,Arial,sans-serif;color:#FDFDFF}
#cv{position:absolute;inset:0;width:1080px;height:1920px}
.abs{position:absolute}
.hl{font-weight:900;font-stretch:104%;text-transform:uppercase;letter-spacing:-.035em;line-height:.92}
.mono{font-family:'Azeret Mono',monospace}
#vig{inset:0;background:radial-gradient(120% 80% at 50% 45%,rgba(0,0,0,0) 55%,rgba(0,0,0,.45) 100%);pointer-events:none}
#titulo{left:0;right:0;top:330px;text-align:center}
#titulo .k{font-family:'Azeret Mono',monospace;font-weight:700;font-size:30px;letter-spacing:.3em;color:#C9FB00}
#titulo .t{font-size:200px;margin-top:18px;text-shadow:0 10px 50px rgba(0,0,0,.6)}
#chip{left:0;right:0;top:250px;display:flex;justify-content:center}
#chip span{font-family:'Azeret Mono',monospace;font-weight:700;font-size:40px;letter-spacing:.06em;padding:14px 28px;border-radius:999px;background:#1A1B1F;color:#C9FB00;box-shadow:0 20px 40px -16px rgba(0,0,0,.6)}
#lt{left:56px;top:1030px;padding:22px 30px 24px;border-radius:24px;background:rgba(26,27,31,.84)}
#lt .n{font-size:76px}
#lt .bar{width:120px;height:10px;background:#C9FB00;border-radius:6px;margin:14px 0 14px}
#lt .r{font-family:'Azeret Mono',monospace;font-weight:700;font-size:30px;letter-spacing:.06em;text-transform:uppercase}
#sub{left:60px;right:60px;top:1290px;display:flex;justify-content:center;text-align:center}
#sub span{font-weight:800;font-size:50px;line-height:1.28;padding:.06em .3em .1em;border-radius:14px;background:rgba(26,27,31,.82);-webkit-box-decoration-break:clone;box-decoration-break:clone}
#sub span.narr{font-style:italic;font-weight:700;background:rgba(26,27,31,.6);color:#f1efe8}
#pago{left:290px;top:1020px;width:500px;padding:34px 30px;border-radius:40px;background:#C9FB00;color:#1A1B1F;text-align:center;opacity:0;box-shadow:0 30px 60px -20px rgba(0,0,0,.6)}
#fin{inset:0;opacity:0;background:rgba(244,41,2,.95);display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:0 70px}
#fin .pill{margin-top:56px;padding:26px 44px;border-radius:999px;background:#C9FB00;color:#1A1B1F;font-family:'Azeret Mono',monospace;font-weight:700;font-size:36px;text-transform:uppercase}
#flash{inset:0;background:#000;opacity:0}
</style></head><body><div id="c"><canvas id="cv" width="1080" height="1920"></canvas>
<div id="vig" class="abs"></div>
<div id="titulo" class="abs" style="opacity:0"><div class="k">UN DOCUMENTAL MENUO</div><div class="t hl">La<br>cuenta</div></div>
<div id="chip" class="abs" style="opacity:0"><span></span></div>
<div id="lt" class="abs" style="opacity:0"><div class="n hl"></div><div class="bar"></div><div class="r"></div></div>
<div id="sub" class="abs" style="opacity:0"><span></span></div>
<div id="pago" class="abs"><div style="width:110px;height:110px;border-radius:50%;background:#1A1B1F;margin:0 auto;display:flex;align-items:center;justify-content:center"><svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#C9FB00" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg></div><div class="hl" style="font-size:64px;margin-top:18px">¡Pagado!</div><div class="mono" style="font-weight:700;font-size:26px;margin-top:10px">NEQUI · MESA 4 · 8:03 P. M.</div></div>
<div id="fin" class="abs"><img src="__LOGO_B__" style="width:380px"><div class="hl" style="font-size:96px;margin-top:60px">Pide y paga<br>desde la mesa.</div>
<div class="pill">Escríbenos DEMO por DM</div><div class="mono" style="font-weight:700;font-size:30px;margin-top:34px">@menuo.app</div></div>
<div id="flash" class="abs"></div>
</div>
<script src="__THREE__"></script>
<script>
const D=__DATA__;
THREE.ColorManagement.legacyMode=false;
const R=new THREE.WebGLRenderer({canvas:document.getElementById('cv'),antialias:true,preserveDrawingBuffer:true});
R.outputEncoding=THREE.sRGBEncoding;R.shadowMap.enabled=true;R.shadowMap.type=THREE.PCFSoftShadowMap;R.setPixelRatio(1);R.setSize(1080,1920,false);
const S=new THREE.Scene();S.background=new THREE.Color('#141518');
const CAM=new THREE.PerspectiveCamera(36,1080/1920,.1,120);
const cl=x=>Math.min(1,Math.max(0,x)), lerp=(a,b,t)=>a+(b-a)*t, ss=(a,b,t)=>{t=cl((t-a)/(b-a));return t*t*(3-2*t);};
const eo=x=>1-Math.pow(1-cl(x),3), eb=x=>{x=cl(x);const c1=1.9,c3=c1+1;return 1+c3*Math.pow(x-1,3)+c1*Math.pow(x-1,2);};
const M=(c,r=.6,o={})=>new THREE.MeshStandardMaterial(Object.assign({color:c,roughness:r,metalness:0},o));
function mesh(g,m,p=[0,0,0],sh=true){const x=new THREE.Mesh(g,m);x.position.set(...p);x.castShadow=sh;x.receiveShadow=true;return x;}
function texCanvas(w,h,draw){const c=document.createElement('canvas');c.width=w;c.height=h;const x=c.getContext('2d');const t=new THREE.CanvasTexture(c);t.encoding=THREE.sRGBEncoding;t.anisotropy=4;return {t,c,x,draw,redo(){draw(x,w,h);t.needsUpdate=true;}};}
function glowTex(){const c=document.createElement('canvas');c.width=c.height=128;const x=c.getContext('2d');const g=x.createRadialGradient(64,64,0,64,64,64);g.addColorStop(0,'rgba(255,255,255,1)');g.addColorStop(.35,'rgba(255,255,255,.5)');g.addColorStop(1,'rgba(255,255,255,0)');x.fillStyle=g;x.fillRect(0,0,128,128);const t=new THREE.CanvasTexture(c);return t;}
const GLOW=glowTex();
// luces globales
S.add(new THREE.HemisphereLight('#ffe9dc','#3a1a12',.7));
function keyLight(x,y,z,tx,tz){const k=new THREE.DirectionalLight('#fff4e8',1.5);k.position.set(x,y,z);k.target.position.set(tx,0,tz);S.add(k.target);k.castShadow=true;k.shadow.mapSize.set(1024,1024);
  Object.assign(k.shadow.camera,{left:-5,right:5,top:6,bottom:-2,near:1,far:25});k.shadow.radius=4;S.add(k);return k;}
keyLight(3.5,7,5,0,0);keyLight(33.5,7,5,30,0);keyLight(-36.5,8,6,-40,0);
// ---------------- persona
const skin='#e9b48d';
function persona(o){
  const g=new THREE.Group();
  const body=mesh(new THREE.CapsuleGeometry(.48,.7,10,28),M(o.shirt,.65),[0,1.55,0]);g.add(body);
  const head=new THREE.Group();head.position.set(0,2.64,0);g.add(head);
  const skinM=M(o.skin||skin,.55);head.add(mesh(new THREE.SphereGeometry(.46,40,32),skinM));
  const hairM=M(o.hair,.7);const hr=mesh(new THREE.SphereGeometry(.475,40,32,0,Math.PI*2,0,Math.PI*(o.long?.5:.42)),hairM,[0,.03,-.02]);hr.rotation.x=-.25;head.add(hr);
  if(o.long){head.add(mesh(new THREE.CapsuleGeometry(.36,.5,8,20),hairM,[0,-.25,-.22]));}
  const eyes=[],pupils=[],lids=[];
  [-.17,.17].forEach(x=>{const e=mesh(new THREE.SphereGeometry(.13,24,18),M('#ffffff',.25),[x,.06,.36]);head.add(e);eyes.push(e);
    const p=mesh(new THREE.SphereGeometry(.065,16,12),M('#111111',.2),[x,.05,.48]);head.add(p);pupils.push(p);
    const l=mesh(new THREE.SphereGeometry(.137,24,18,0,Math.PI*2,0,Math.PI/2),skinM,[x,.06,.36]);l.visible=false;head.add(l);lids.push(l);});
  if(o.lashes)[-.17,.17].forEach(x=>{const b=mesh(new THREE.BoxGeometry(.2,.03,.03),M('#1A1B1F'),[x,.2,.43]);head.add(b);});
  const brows=[-.17,.17].map(x=>{const b=mesh(new THREE.BoxGeometry(.18,.04,.04),hairM,[x,.25,.42]);head.add(b);return b;});
  const lip=mesh(new THREE.TorusGeometry(.12,.028,8,24,Math.PI),M('#4a1610',.5),[0,-.15,.42]);lip.rotation.z=Math.PI;head.add(lip);
  const mo=mesh(new THREE.SphereGeometry(.1,20,14),M('#2a0c08',.6),[0,-.2,.41]);mo.scale.set(1,.05,.4);head.add(mo);
  head.add(mesh(new THREE.SphereGeometry(.06,16,12),skinM,[0,-.04,.46]));
  const sweat=mesh(new THREE.SphereGeometry(.05,12,10),M('#9fd8ff',.1,{transparent:true,opacity:.9}),[.33,.22,.3]);sweat.scale.set(1,1.5,1);sweat.visible=false;head.add(sweat);
  function arm(side){const a=new THREE.Group();a.position.set(side*.5,2.02,0);g.add(a);
    a.add(mesh(new THREE.CapsuleGeometry(.12,.55,6,16),M(o.sleeve||o.shirt,.65),[0,-.33,0]));const h=mesh(new THREE.SphereGeometry(.13,20,16),skinM,[0,-.72,0]);a.add(h);a.hand=h;return a;}
  const P={g,body,head,eyes,pupils,lids,brows,lip,mo,sweat,armR:arm(-1),armL:arm(1)};
  if(o.apron){g.add(mesh(new THREE.BoxGeometry(.85,.8,.1),M('#1A1B1F',.7),[0,1.25,.45]));const bow=new THREE.Group();bow.position.set(0,2.05,.47);g.add(bow);
    [-1,1].forEach(s=>{const b=mesh(new THREE.ConeGeometry(.08,.16,4),M('#F42902'),[s*.08,0,0]);b.rotation.z=s*Math.PI/2;bow.add(b);});}
  if(o.blazer){g.add(mesh(new THREE.CapsuleGeometry(.5,.6,10,28,),M('#1A1B1F',.7),[0,1.5,-.03]));g.add(mesh(new THREE.ConeGeometry(.22,.5,3),M(o.shirt,.6),[0,1.95,.36]));}
  return P;
}
function talk(P,v,smile=1){P.mo.scale.set(1,lerp(.05,1,cl(v)),.4);P.lip.visible=v<.08;P.lip.scale.y=smile;}
// ---------------- RESTAURANTE (x=0)
S.add(mesh(new THREE.PlaneGeometry(18,10),M('#3b2723',.9),[0,4,-4.5],false));
const fl=mesh(new THREE.PlaneGeometry(18,14),M('#5c3a26',.85),[0,0,0],false);fl.rotation.x=-Math.PI/2;S.add(fl);
S.add(mesh(new THREE.BoxGeometry(18,.25,.1),M('#F42902',.6),[0,.9,-4.42],false));
// ventana con vista a la calle
const winM=new THREE.MeshBasicMaterial({color:'#0b1030'});
S.add(mesh(new THREE.BoxGeometry(2.4,2.4,.12),M('#1A1B1F',.6),[-2.1,3.1,-4.42],false));S.add(mesh(new THREE.PlaneGeometry(2.15,2.15),winM,[-2.1,3.1,-4.35],false));
const lampR=new THREE.PointLight('#ffb36b',1.1,9,1.6);lampR.position.set(0,3.9,.2);S.add(lampR);
// reloj
const clk=new THREE.Group();clk.position.set(1.8,3.6,-4.4);S.add(clk);
const fc=mesh(new THREE.CylinderGeometry(.5,.5,.08,40),M('#FDFDFF',.4),[0,0,0],false);fc.rotation.x=Math.PI/2;clk.add(fc);clk.add(mesh(new THREE.TorusGeometry(.51,.06,12,40),M('#F42902',.5),[0,0,.03],false));
const hH=new THREE.Group();hH.position.z=.07;hH.add(mesh(new THREE.BoxGeometry(.06,.28,.03),M('#1A1B1F'),[0,.1,0],false));clk.add(hH);
const hM=new THREE.Group();hM.position.z=.08;hM.add(mesh(new THREE.BoxGeometry(.04,.42,.03),M('#1A1B1F'),[0,.17,0],false));clk.add(hM);
// mesa
const table=new THREE.Group();S.add(table);
table.add(mesh(new THREE.CylinderGeometry(1.25,1.25,.07,48),M('#F42902',.75),[0,1.02,0]));
table.add(mesh(new THREE.CylinderGeometry(1.32,1.25,.22,48,1,true),M('#d92402',.8,{side:THREE.DoubleSide}),[0,.9,0]));
table.add(mesh(new THREE.CylinderGeometry(.08,.08,.9,12),M('#1A1B1F'),[0,.45,0]));table.add(mesh(new THREE.CylinderGeometry(.5,.5,.05,24),M('#1A1B1F'),[0,.03,0]));
table.add(mesh(new THREE.CylinderGeometry(.42,.38,.04,32),M('#FDFDFF',.3),[-.15,1.08,.35]));
table.add(mesh(new THREE.CylinderGeometry(.13,.11,.32,24),M('#cfe8ff',.1,{transparent:true,opacity:.55}),[.75,1.22,.3]));
const qrTex=texCanvas(256,340,(x,w,h)=>{x.fillStyle='#FDFDFF';x.fillRect(0,0,w,h);x.fillStyle='#F42902';x.fillRect(0,0,w,46);x.fillStyle='#FDFDFF';x.font='900 30px Archivo';x.textAlign='center';x.fillText('MENUO',w/2,33);
  const n=D.QR.length,s=200/n;x.fillStyle='#1A1B1F';D.QR.forEach((r,i)=>r.forEach((v,j)=>{if(v)x.fillRect(28+j*s,64+i*s,s+.5,s+.5);}));x.font='800 24px Archivo';x.fillText('Escanea y paga',w/2,300);x.font='700 18px Azeret Mono';x.fillStyle='#F42902';x.fillText('MESA 4',w/2,326);});
const tent=new THREE.Group();tent.position.set(.55,1.06,-.15);tent.rotation.y=-.35;table.add(tent);
const tentFront=mesh(new THREE.PlaneGeometry(.38,.5),new THREE.MeshStandardMaterial({map:qrTex.t,roughness:.5}),[0,.24,0]);tentFront.rotation.x=-.18;tent.add(tentFront);tent.add(mesh(new THREE.BoxGeometry(.4,.02,.2),M('#1A1B1F'),[0,0,-.05]));
const chair=new THREE.Group();chair.position.set(0,0,-1.25);S.add(chair);
chair.add(mesh(new THREE.BoxGeometry(1.1,.1,.9),M('#1A1B1F',.6),[0,.85,0]));chair.add(mesh(new THREE.BoxGeometry(1.1,1.5,.1),M('#1A1B1F',.6),[0,1.6,-.42]));
// otras mesas al fondo
[[-2.4,-3.0,'#FDFDFF'],[2.5,-3.2,'#F42902']].forEach(([x,z,c])=>{const t=new THREE.Group();t.position.set(x,0,z);S.add(t);t.add(mesh(new THREE.CylinderGeometry(.9,.9,.07,32),M('#F42902',.75),[0,1.02,0]));
  t.add(mesh(new THREE.CylinderGeometry(.07,.07,.9,10),M('#1A1B1F'),[0,.45,0]));const p=persona({shirt:c,hair:'#2b1b14'});p.g.position.set(0,0,-.75);p.g.scale.setScalar(.9);t.add(p.g);});
const CA=persona({shirt:'#C9FB00',hair:'#2b1b14'});CA.g.position.set(0,0,-.95);S.add(CA.g);           // Camilo en la mesa
const SE=persona({shirt:'#FDFDFF',hair:'#1A1B1F',apron:true});S.add(SE.g);                             // Sebas en el restaurante
const tray=new THREE.Group();tray.add(mesh(new THREE.CylinderGeometry(.42,.42,.03,28),M('#c9c9cf',.3)));[[-.15,0],[.12,.1],[.05,-.15]].forEach(([x,z])=>tray.add(mesh(new THREE.CylinderGeometry(.07,.06,.22,16),M('#ffd27a',.2,{transparent:true,opacity:.85}),[x,.12,z])));
tray.position.set(0,-.78,.25);SE.armR.add(tray);
const datTex=texCanvas(220,170,(x,w,h)=>{const e=datTex.err;x.fillStyle=e?'#F42902':'#7fd3a8';x.fillRect(0,0,w,h);x.fillStyle=e?'#FDFDFF':'#0d2b1d';x.textAlign='center';
  if(e){x.font='900 34px Archivo';x.fillText('SIN SEÑAL',110,98);x.font='700 16px Azeret Mono';x.fillText('INTENTE DE NUEVO',110,132);}else{x.font='800 26px Azeret Mono';x.fillText('INSERTE',110,75);x.fillText('TARJETA',110,110);}});
const dat=new THREE.Group();dat.add(mesh(new THREE.BoxGeometry(.36,.6,.1),M('#2a2b30',.4)));dat.add(mesh(new THREE.PlaneGeometry(.3,.23),new THREE.MeshBasicMaterial({map:datTex.t}),[0,.13,.052],false));
for(let i=0;i<9;i++)dat.add(mesh(new THREE.BoxGeometry(.07,.05,.02),M('#d8d8de',.5),[-.09+(i%3)*.09,-.06-Math.floor(i/3)*.07,.055],false));
dat.position.set(0,-.86,.05);SE.armL.add(dat);
// teléfono de Camilo
const phone=new THREE.Group();phone.add(mesh(new THREE.BoxGeometry(.32,.6,.04),M('#1A1B1F',.3)));phone.position.set(0,-.86,0);phone.visible=false;CA.armL.add(phone);
const beam=mesh(new THREE.CylinderGeometry(.015,.015,1,8),new THREE.MeshBasicMaterial({color:'#C9FB00',transparent:true,opacity:0}),[0,0,0],false);S.add(beam);
// ---------------- SET DE ENTREVISTAS (x=30)
const IX=30;
S.add(mesh(new THREE.PlaneGeometry(14,10),M('#2a201d',.95),[IX,4,-3.2],false));
const ifl=mesh(new THREE.PlaneGeometry(14,12),M('#3a2a22',.9),[IX,0,0],false);ifl.rotation.x=-Math.PI/2;S.add(ifl);
const bokehC=['#ffb36b','#ff7a45','#ffd9a0','#F42902','#ffe8c2'];let sd=11;const rr=()=>{sd=(sd*16807)%2147483647;return sd/2147483647;};
for(let i=0;i<26;i++){const sp=new THREE.Sprite(new THREE.SpriteMaterial({map:GLOW,color:bokehC[i%5],transparent:true,opacity:.35+rr()*.35,depthWrite:false}));const s=.4+rr()*.9;sp.scale.set(s,s,1);sp.position.set(IX-4+rr()*8,1.6+rr()*4.2,-3.0+rr()*.3);S.add(sp);}
const iplant=new THREE.Group();iplant.position.set(IX+1.5,0,-1.6);S.add(iplant);iplant.add(mesh(new THREE.CylinderGeometry(.3,.22,.55,20),M('#c2643a',.8),[0,.28,0]));
[[0,1,0,.4],[.22,1.35,.05,.3],[-.2,1.3,0,.32],[.05,1.62,0,.28]].forEach(([x,y,z,r])=>iplant.add(mesh(new THREE.SphereGeometry(r,18,14),M('#2f8f4e',.7),[x,y,z])));
const ichair=new THREE.Group();ichair.position.set(IX,0,-.25);S.add(ichair);ichair.add(mesh(new THREE.BoxGeometry(1.1,.12,.9),M('#7a3b26',.7),[0,.85,0]));ichair.add(mesh(new THREE.BoxGeometry(1.1,1.6,.12),M('#7a3b26',.7),[0,1.6,-.42]));
const ilamp=new THREE.PointLight('#ffc48a',.9,8,1.5);ilamp.position.set(IX+1.8,3.2,1.2);S.add(ilamp);
const CI=persona({shirt:'#C9FB00',hair:'#2b1b14'});const SI=persona({shirt:'#FDFDFF',hair:'#1A1B1F',apron:true});const LI=persona({shirt:'#F42902',hair:'#4a2a1a',long:true,lashes:true});[-.45,.45].forEach(x=>LI.head.add(mesh(new THREE.SphereGeometry(.06,12,10),M('#C9FB00',.3),[x,-.12,.05])));
[CI,SI,LI].forEach(p=>{p.g.position.set(IX,0,0);p.g.rotation.y=.28;p.g.visible=false;S.add(p.g);});
// ---------------- CALLE (x=-40)
const EX=-40;
const road=mesh(new THREE.PlaneGeometry(30,14),M('#2b2c31',.9),[EX,0,2],false);road.rotation.x=-Math.PI/2;S.add(road);
const walk=mesh(new THREE.BoxGeometry(30,.18,2.4),M('#8d8a86',.9),[EX,.09,-1.2]);S.add(walk);
const curb=mesh(new THREE.BoxGeometry(30,.2,.22),M('#f2c230',.6),[EX,.1,.05]);S.add(curb);
for(let i=-6;i<7;i++)S.add(mesh(new THREE.BoxGeometry(1.2,.02,.15),M('#e8e2d0',.8),[EX+i*2.4,.011,3.2],false));
const fac=mesh(new THREE.BoxGeometry(30,9,.4),M('#4a2c25',.9),[EX,4.5,-2.6]);S.add(fac);
S.add(mesh(new THREE.BoxGeometry(3.4,2.6,.1),M('#1A1B1F'),[EX+.8,2.1,-2.38],false));
S.add(mesh(new THREE.PlaneGeometry(3.1,2.3),new THREE.MeshBasicMaterial({color:'#ffcf8a'}),[EX+.8,2.1,-2.32],false));
const signTex=texCanvas(512,128,(x,w,h)=>{x.fillStyle='#F42902';x.fillRect(0,0,w,h);x.fillStyle='#FDFDFF';x.font='900 70px Archivo';x.textAlign='center';x.fillText('RESTAURANTE',w/2,90);});

const streetL=new THREE.PointLight('#ffcf8a',1.2,10,1.5);streetL.position.set(EX+.8,2.4,-.6);S.add(streetL);
const nostop=new THREE.Group();nostop.position.set(EX-1.7,0,-.25);S.add(nostop);nostop.add(mesh(new THREE.CylinderGeometry(.04,.04,2.2,8),M('#9a9aa0'),[0,1.1,0]));
const nsTex=texCanvas(128,128,(x)=>{x.fillStyle='#1e5bd8';x.beginPath();x.arc(64,64,62,0,7);x.fill();x.strokeStyle='#e8231d';x.lineWidth=14;x.beginPath();x.arc(64,64,55,0,7);x.stroke();x.beginPath();x.moveTo(25,25);x.lineTo(103,103);x.stroke();});
const ns=mesh(new THREE.CircleGeometry(.32,32),new THREE.MeshBasicMaterial({map:nsTex.t}),[0,2.2,.05],false);nostop.add(ns);
function carro(color){const c=new THREE.Group();c.add(mesh(new THREE.BoxGeometry(2.0,.55,1.05),M(color,.4),[0,.55,0]));c.add(mesh(new THREE.BoxGeometry(1.1,.48,.95),M(color,.4),[-.1,1.05,0]));
  c.add(mesh(new THREE.BoxGeometry(1.0,.38,.97),M('#9fc7e8',.1),[-.1,1.06,0]));
  [[-.65,.5],[.65,.5],[-.65,-.5],[.65,-.5]].forEach(([x,z])=>{const w=mesh(new THREE.CylinderGeometry(.24,.24,.18,20),M('#151515',.8),[x,.26,z]);w.rotation.x=Math.PI/2;c.add(w);});
  c.add(mesh(new THREE.BoxGeometry(.05,.12,.25),M('#fff6c0',.2,{emissive:'#fff2a0',emissiveIntensity:.8}),[1.0,.62,.3]));c.add(mesh(new THREE.BoxGeometry(.05,.12,.25),M('#fff6c0',.2,{emissive:'#fff2a0',emissiveIntensity:.8}),[1.0,.62,-.3]));return c;}
const car=carro('#C9FB00');S.add(car);
const grua=new THREE.Group();S.add(grua);
grua.add(mesh(new THREE.BoxGeometry(1.4,1.3,1.25),M('#f39c1e',.5),[1.6,.95,0]));grua.add(mesh(new THREE.BoxGeometry(1.2,.75,1.15),M('#9fc7e8',.1),[1.75,1.35,0]));
grua.add(mesh(new THREE.BoxGeometry(2.2,.45,1.25),M('#e8e8ea',.5),[-.2,.6,0]));const beacon=mesh(new THREE.BoxGeometry(.5,.14,.25),M('#ff8a00',.3,{emissive:'#ff7a00',emissiveIntensity:1}),[1.6,1.68,0]);grua.add(beacon);
[[-.8,.55],[.2,.55],[1.6,.55],[-.8,-.55],[.2,-.55],[1.6,-.55]].forEach(([x,z])=>{const w=mesh(new THREE.CylinderGeometry(.3,.3,.2,20),M('#151515',.8),[x,.3,z]);w.rotation.x=Math.PI/2;grua.add(w);});
const boom=mesh(new THREE.BoxGeometry(1.6,.14,.14),M('#e8e8ea',.4),[-1.2,1.2,0]);boom.rotation.z=-.5;grua.add(boom);
// ---------------- estado por tiempo
const SHOTS=D.SHOTS, CHIPS=D.CHIPS, LT=D.LT, SUBS=D.SUBS, ENV=D.ENV, T=D.T;
let chipPrev='',ltPrev='',subPrev='',datPrev=null;
function env(name,t){const a=ENV[name];const i=Math.round(t*30);return a&&i>=0&&i<a.length?a[i]:0;}
function shotAt(t){let s=SHOTS[0];for(const x of SHOTS)if(t>=x[0])s=x;return s;}
window.render=function(t){
  const sh=shotAt(t), name=sh[1], st=t-sh[0];
  // visibilidad de entrevistados
  CI.g.visible=name==='entCamilo'||name==='entCamilo2';SI.g.visible=name==='entSebas'||name==='entSebas2';LI.g.visible=name==='entLucia';
  // boca y ojos
  const ec=env('camilo',t),es=env('sebas',t),el=env('lucia',t);
  talk(CA,ec,1);talk(CI,ec,1);talk(SE,es,1);talk(SI,es,1);talk(LI,el,1);
  [CA,CI,SE,SI,LI].forEach(p=>{const b=(Math.abs(((t+p.g.position.x*.37)%3.3)-1.6)<.06);p.lids.forEach(l=>{l.visible=b;});});
  // ---- restaurante: Camilo en la mesa
  let rz=-.15,rl=.15,rlx=0;
  if(t<T.next){ // primera noche
    rz=t>=T.pide-0.1?lerp(-.15,-2.75,eo((t-T.pide+.1)/.3)):-.15;
    if(t>=T.grua0)rz=-.15;
    CA.head.rotation.y=(t>=T.carro-0.2&&t<T.grua0+.1)?lerp(0,-.9,eo((t-T.carro+.2)/.3)):0;
    CA.brows.forEach((b,i)=>b.rotation.z=(i?-1:1)*(t>=T.dat?-.3:0));
  }else{ // viernes siguiente
    const u=t-T.next;CA.head.rotation.y=0;
    rlx=lerp(0,-1.15,eo((t-T.scan+.5)/.4));rl=lerp(.15,-.05,eo((t-T.scan+.5)/.4));
    CA.brows.forEach((b,i)=>b.rotation.z=(i?-1:1)*.12);
  }
  CA.armR.rotation.set(0,0,rz);CA.armL.rotation.set(rlx,0,rl);phone.rotation.x=Math.PI/2-rlx;phone.visible=t>=T.next&&t>T.scan-.5;
  if(t>=T.scan&&t<T.ok){const a=new THREE.Vector3(),b=new THREE.Vector3();phone.getWorldPosition(a);tentFront.getWorldPosition(b);beam.position.copy(a).add(b).multiplyScalar(.5);beam.scale.set(1,a.distanceTo(b),1);beam.lookAt(b);beam.rotateX(Math.PI/2);beam.material.opacity=.9;}else beam.material.opacity=0;
  // reloj: 8:02 → 8:25 → 8:42 ; viernes siguiente 8:02
  let hrs=8+2/60;if(t<T.next){hrs+=lerp(0,23/60,ss(T.sebasEnt,T.dat,t))+lerp(0,17/60,ss(T.dat+1,T.carro,t));}
  hM.rotation.z=-((hrs%1)*Math.PI*2);hH.rotation.z=-((hrs%12)/12*Math.PI*2);
  // ---- Sebas en el restaurante
  let sx=-8,sz=-1.9,sry=Math.PI/2,sy=0,trayOn=true,datOn=false,sa=0;
  if(t>=T.sebasPasa&&t<T.sebasPasa+1.8){const k=(t-T.sebasPasa)/1.8;sx=lerp(-3.4,3.4,k);sy=Math.abs(Math.sin(t*20))*.1;SE.head.rotation.y=-.9*ss(.2,.4,k)*(1-ss(.7,.9,k));}
  else if(t>=T.dat-0.9&&t<T.next){sx=lerp(3.5,.95,eo((t-T.dat+.9)/.55));sz=.3;sry=lerp(-Math.PI/2,-.5,ss(T.dat-.45,T.dat-.2,t));sy=t<T.dat-.35?Math.abs(Math.sin(t*20))*.1:0;trayOn=false;datOn=true;sa=-1.2*ss(T.dat-.3,T.dat,t);SE.head.rotation.y=0;}
  SE.g.position.set(sx,sy,sz);SE.g.rotation.y=sry;tray.visible=trayOn;dat.visible=datOn;SE.armL.rotation.set(sa,0,.12);dat.rotation.x=-sa+.1;SE.armR.rotation.set(trayOn?-1.4:0,0,trayOn?-.2:-.15);
  SE.sweat.visible=t>=T.dat;SE.sweat.position.y=.22-((t*1.3)%1)*.3;
  const derr=t>=T.dat+.25;if(derr!==datPrev){datTex.err=derr;datTex.redo();datPrev=derr;}
  // ---- entrevistas
  SI.sweat.visible=name==='entSebas';SI.sweat.position.y=.22-((t*1.3)%1)*.3;
  [CI,SI,LI].forEach(p=>{p.head.rotation.z=Math.sin(t*1.7)*.03;p.g.position.y=Math.sin(t*2.2)*.01;});
  SI.brows.forEach((b,i)=>b.rotation.z=(i?-1:1)*(name==='entSebas'?-.3:.15));
  CI.armR.rotation.set(0,0,-.15);CI.armL.rotation.set(name==='entCamilo2'?-.6:0,0,name==='entCamilo2'?2.3:.15);
  LI.brows.forEach((b,i)=>b.rotation.z=(i?-1:1)*(t>=T.noMas?-.35:0));LI.armR.rotation.set(t>=T.noMas?-.9:0,0,-.15);
  // ---- calle: carro y grúa
  let cx=EX+.4,cy=0,crz=0,cry=.18,gx=EX+30;
  if(t>=T.grua0){const g=t-T.grua0;gx=lerp(EX+3.0,EX+10,ss(.9,2.7,g));cx=gx-2.6;crz=-.3*eo(g/.6);cy=.45*eo(g/.6);cry=lerp(.18,0,eo(g/.6));}
  car.position.set(cx,cy+.12,.55);car.rotation.set(0,cry,crz);grua.position.set(gx,0,.65);beacon.material.emissiveIntensity=.4+.8*Math.abs(Math.sin(t*8));
  if(t>=T.next)car.position.set(EX+.4,.12,.55),car.rotation.set(0,.18,0);
  // ---- cámara por toma
  const cp=new THREE.Vector3(),la=new THREE.Vector3();
  if(name==='calle'){cp.set(EX+.1,2.2,lerp(10.5,9.0,eo(st/4.5)));la.set(EX+.1,1.75,0);}
  else if(name==='grua'){cp.set(gx-6.8,2.7,4.6);la.set(gx-.7,1.0,.6);}
  else if(name.startsWith('ent')){const w=Math.sin(t*.6)*.04;cp.set(IX+1.05+w,2.6,5.6-st*.08);la.set(IX+.45,2.25,0);}
  else if(name==='mesa'||name==='mesa2'){cp.set(0,2.45,lerp(6.6,6.1,eo(st/3)));la.set(0,2.3,-.7);}
  else if(name==='datafono'){const dp=new THREE.Vector3();dat.getWorldPosition(dp);const k=eo((st-.25)/.35);cp.set(0,2.45,6.2).lerp(dp.clone().add(new THREE.Vector3(-.35,.35,2.4)),k);la.set(0,2.3,-.7).lerp(dp.clone().add(new THREE.Vector3(-.15,.35,0)),k);}
  else if(name==='ventana'){cp.set(.6,2.7,3.4);la.set(-.4,2.6,-1.2);}
  else if(name==='qr'){const k=eo(st/.5);cp.set(0,2.4,5.6).lerp(new THREE.Vector3(.75,2.0,3.4),k);la.set(.2,1.9,-.4).lerp(new THREE.Vector3(.5,1.45,-.4),k);}
  else {cp.set(0,2.45,6.3);la.set(0,2.3,-.7);}
  CAM.position.copy(cp);CAM.lookAt(la);
  R.render(S,CAM);
  // ---- capa 2D
  const tt=document.getElementById('titulo');tt.style.opacity=t<T.ent1-.15?1:0;tt.style.transform=`scale(${1.06-.06*eo(t/1.2)})`;
  const ch=CHIPS.find(c=>t>=c[0]&&t<c[1]);const ce=document.getElementById('chip');const ctxt=ch?ch[2]:'';if(ctxt!==chipPrev){ce.querySelector('span').textContent=ctxt;chipPrev=ctxt;}
  ce.style.opacity=ch?1:0;ce.style.transform=ch?`scale(${.85+.15*eb((t-ch[0])/.25)})`:'';
  const lt=LT.find(c=>t>=c[0]&&t<c[1]);const le=document.getElementById('lt');const ltt=lt?lt[2]+'|'+lt[3]:'';if(ltt!==ltPrev){le.querySelector('.n').textContent=lt?lt[2]:'';le.querySelector('.r').textContent=lt?lt[3]:'';ltPrev=ltt;}
  if(lt){const k=eo((t-lt[0])/.3),ko=cl((lt[1]-t)/.2);le.style.opacity=Math.min(k,ko);le.style.transform=`translateX(${(1-k)*-60}px)`;}else le.style.opacity=0;
  const sb=SUBS.find(c=>t>=c[0]-.05&&t<c[1]+.15);const se=document.getElementById('sub');const stx=sb?sb[2]+sb[3]:'';
  if(stx!==subPrev){const sp=se.querySelector('span');sp.textContent=sb?sb[2]:'';sp.className=sb&&sb[3]==='narrador'?'narr':'';subPrev=stx;}
  se.style.opacity=sb?1:0;
  const pg=document.getElementById('pago');const kp=eb((t-T.ok)/.3);pg.style.opacity=t>=T.ok&&t<T.ent3?1:0;pg.style.transform=`scale(${.5+.5*kp}) rotate(-3deg)`;
  const fin=document.getElementById('fin');const kf=eo((t-T.fin)/.35);fin.style.opacity=t>=T.fin?kf:0;fin.style.transform=`translateY(${(1-kf)*80}px)`;
  document.getElementById('cv').style.filter=t>=T.fin?`blur(${eo((t-T.fin)/.4)*12}px)`:'none';
  // corte con parpadeo negro corto entre tomas
  let fk=0;SHOTS.forEach(x=>{const d=t-x[0];if(x[0]>0&&d>=0&&d<.08)fk=1-d/.08;});document.getElementById('flash').style.opacity=fk*.55;
};
(async()=>{await document.fonts.ready;qrTex.redo();signTex.redo();nsTex.redo();datTex.err=false;datTex.redo();
  await Promise.all([...document.images].map(i=>i.decode().catch(()=>{})));window.render(0);window.__ok=true;})();
</script></body></html>"""

def plan():
    """Tiempos clave (segundos del video) derivados de dónde cae cada tramo de voz."""
    at = {i: tr[3] for i, tr in enumerate(TRAMOS)}
    dur = {i: tr[2] - tr[1] for i, tr in enumerate(TRAMOS)}
    T = dict(ent1=4.75, pide=8.6, sebasPasa=10.3, sebasEnt=11.7, dat=18.55, carro=21.05, grua0=21.95, ent3=24.65,
             noMas=29.2, next=31.05, scan=32.45, ok=33.55, ent4=33.95, ent5=37.85, fin=39.45)
    SHOTS = [(0, 'calle'), (4.75, 'entCamilo'), (8.45, 'mesa'), (11.7, 'entSebas'), (18.25, 'datafono'),
             (21.0, 'ventana'), (21.95, 'grua'), (24.65, 'entLucia'), (31.05, 'mesa2'), (32.2, 'qr'),
             (33.95, 'entSebas2'), (37.85, 'entCamilo2'), (39.45, 'fin')]
    CHIPS = [(8.45, 11.7, '8:02 P. M.'), (18.25, 21.0, '8:25 P. M.'), (21.0, 24.65, '8:42 P. M.'), (31.05, 33.95, 'VIERNES SIGUIENTE · 8:02 P. M.')]
    LT = [(4.95, 8.45, 'Camilo', 'Cliente · mesa 4'), (11.9, 18.25, 'Sebas', 'Mesero · 12 mesas'), (24.85, 31.05, 'Lucía', 'Dueña del restaurante'),
          (34.1, 37.85, 'Sebas', 'Mesero'), (38.0, 39.45, 'Camilo', 'Cliente feliz')]
    SUBS = [(tr[3], tr[3] + (tr[2] - tr[1]), tr[4], tr[0]) for tr in TRAMOS if tr[3] < T['fin']]
    return T, SHOTS, CHIPS, LT, SUBS

def envolventes(voz):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', voz, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32)
    n = int(DUR * FPS) + 2
    E = {k: np.zeros(n) for k in ('camilo', 'sebas', 'lucia', 'narrador')}
    hop = SR // FPS
    for hab, d0, d1, t0, _ in TRAMOS:
        seg = x[int(d0 * SR):int(d1 * SR)]
        m = len(seg) // hop
        if m == 0: continue
        rms = np.sqrt(np.mean(seg[:m * hop].reshape(m, hop) ** 2, axis=1))
        v = np.clip((20 * np.log10(rms + 1e-9) + 42) / 22, 0, 1)
        i0 = int(round(t0 * FPS)); j = min(n, i0 + m)
        E[hab][i0:j] = np.maximum(E[hab][i0:j], v[:j - i0])
    return {k: [round(float(a), 3) for a in v] for k, v in E.items()}

def qr_matrix(url):
    q = qrcode.QRCode(border=1); q.add_data(url); q.make()
    return [[1 if v else 0 for v in row] for row in q.get_matrix()]

def pagina(voz):
    T, SHOTS, CHIPS, LT, SUBS = plan()
    data = dict(T=T, SHOTS=SHOTS, CHIPS=CHIPS, LT=LT, SUBS=SUBS, ENV=envolventes(voz), QR=qr_matrix('https://menuo.com.co'))
    h = HTML.replace('__THREE__', THREE).replace('__LOGO_B__', LOGO_B).replace('__DATA__', json.dumps(data, ensure_ascii=False))
    tmp = SCR / 'documental'; tmp.mkdir(parents=True, exist_ok=True)
    p = tmp / 'documental.html'; p.write_text(h, encoding='utf-8'); return p, tmp, T

def abrir(pw, page):
    b = pw.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--allow-file-access-from-files', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
    pg = b.new_page(viewport={'width': 1080, 'height': 1920})
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
    pg.goto(page.as_uri(), wait_until='networkidle')
    try: pg.wait_for_function('window.__ok===true', timeout=60000)
    except Exception: print('ERRORES', errs); raise
    if errs: print('avisos:', errs[:5])
    return b, pg

def sonido(voz, T):
    n = int(DUR * SR); a = np.zeros(n, np.float32); rng = np.random.default_rng(5)
    def put(x, t, g=1.0):
        i = int(t * SR); j = min(n, i + len(x)); a[i:j] += x[:j - i] * g
    Tm = lambda d: np.arange(int(d * SR)) / SR
    def ruido(d, k):  # ruido suavizado
        x = rng.standard_normal(int(d * SR)); return np.convolve(x, np.ones(k) / k, 'same')
    # golpe grave del título
    tt = Tm(1.6); put(np.sin(2 * np.pi * 48 * tt) * np.exp(-tt * 2.2) * .5, 0.05)
    # ambiente: calle (0–4.75, 21.95–24.65) y restaurante (resto)
    for s0, s1, k, g in [(0, 4.75, 300, .25), (21.95, 24.65, 300, .25), (8.45, 11.7, 30, .05), (18.25, 21.95, 30, .05), (31.05, 33.95, 30, .05)]:
        x = ruido(s1 - s0, k); x *= np.minimum(1, np.minimum(Tm(s1 - s0) / .2, (s1 - s0 - Tm(s1 - s0)) / .2)); put(x, s0, g)
    # datáfono: bip-bop de error
    for k, f in enumerate([880, 440]):
        tt = Tm(.16); put(np.sign(np.sin(2 * np.pi * f * tt)) * .14 * np.exp(-tt * 6), T['dat'] + .25 + k * .19)
    # grúa: motor + pitido de reversa
    tt = Tm(2.7); put((np.sin(2 * np.pi * 55 * tt) + .5 * np.sin(2 * np.pi * 110 * tt)) * .12 * np.hanning(len(tt)), T['grua0'])
    for k in range(5):
        tt = Tm(.22); put(np.sin(2 * np.pi * 1050 * tt) * .1, T['grua0'] + .1 + k * .45)
    # pagado
    for k, f in enumerate([1046.5, 1568]):
        tt = Tm(.9); put((np.sin(2 * np.pi * f * tt) + .3 * np.sin(4 * np.pi * f * tt)) * np.exp(-tt * 5) * .2, T['ok'] + k * .11)
    # voces
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', voz, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32)
    for hab, d0, d1, t0, _ in TRAMOS:
        seg = x[int(d0 * SR):int(d1 * SR)].copy(); fd = int(.015 * SR)
        seg[:fd] *= np.linspace(0, 1, fd); seg[-fd:] *= np.linspace(1, 0, fd); put(seg, t0, 1.0)
    pk = np.max(np.abs(a)); a = a / pk * .95 if pk > .95 else a
    return a

def render(voz, out, hoja=None):
    page, tmp, T = pagina(voz)
    if hoja:
        from PIL import Image, ImageDraw
        ts = [0, 2.0, 5.5, 8.9, 10.9, 12.6, 16.5, 18.6, 19.6, 21.3, 22.8, 23.9, 26.0, 29.5, 31.4, 32.7, 34.0, 36.0, 38.5, 41.0]
        with sync_playwright() as pw:
            b, pg = abrir(pw, page); ims = []
            for t in ts:
                pg.evaluate(f'window.render({t})'); f = tmp / f'm{t:05.2f}.jpg'; pg.screenshot(path=str(f), type='jpeg', quality=80); ims.append((t, f))
            b.close()
        W, H, cols = 240, 427, 7; rows = (len(ims) + cols - 1) // cols
        sh = Image.new('RGB', (W * cols, (H + 22) * rows), 'white'); d = ImageDraw.Draw(sh)
        for k, (t, f) in enumerate(ims):
            x, y = (k % cols) * W, (k // cols) * (H + 22); sh.paste(Image.open(f).resize((W, H)), (x, y)); d.text((x + 5, y + H + 4), f'{t:.1f}s', fill='black')
        sh.save(hoja, quality=82); print('hoja', hoja); return
    frames = tmp / 'f'; shutil.rmtree(frames, ignore_errors=True); frames.mkdir()
    n = int(DUR * FPS)
    with sync_playwright() as pw:
        b, pg = abrir(pw, page)
        for i in range(n):
            pg.evaluate(f'window.render({i / FPS:.4f})'); pg.screenshot(path=str(frames / f'f{i:04d}.jpg'), type='jpeg', quality=90)
        b.close()
    wav = tmp / 'audio.wav'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-', str(wav)], input=sonido(voz, T).tobytes(), check=True)
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-framerate', str(FPS), '-i', str(frames / 'f%04d.jpg'), '-i', str(wav), '-map', '0:v', '-map', '1:a',
                    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-ac', '2', '-shortest', '-movflags', '+faststart', out], check=True)
    print('ok', out, n, 'cuadros')

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('voz'); ap.add_argument('out'); ap.add_argument('--muestras', action='store_true')
    a = ap.parse_args()
    if a.muestras: render(a.voz, None, hoja=a.out)
    else: render(a.voz, a.out)
