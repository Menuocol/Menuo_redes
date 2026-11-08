// Muñecos estilo juguete montados sobre el esqueleto de Quaternius (CC0) para usar sus animaciones.
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import * as SkeletonUtils from 'three/addons/utils/SkeletonUtils.js';
const L=new GLTFLoader();export const ld=u=>new Promise((r,j)=>L.load(u,r,undefined,j));
let BASE=null,CLIPS=null;
export async function init(){BASE=await ld('ubc/Base Characters/Godot - UE/Superhero_Male_FullBody.gltf');const ual=await ld('ual/Unreal-Godot/UAL1_Standard.glb');CLIPS=Object.fromEntries(ual.animations.map(a=>[a.name,a]));return CLIPS;}
const M=(c,r=.55,o={})=>new THREE.MeshStandardMaterial(Object.assign({color:c,roughness:r,metalness:0},o));
function sh(m){m.castShadow=true;m.receiveShadow=true;return m;}
const V=()=>new THREE.Vector3();
export function toy(o){
  const g=SkeletonUtils.clone(BASE.scene);const bones={};let sk=null;
  g.traverse(x=>{if(x.isSkinnedMesh){x.visible=false;sk=x.skeleton;} if(x.isBone)bones[x.name]=x;});
  g.updateMatrixWorld(true);
  const P=n=>bones[n].getWorldPosition(V());
  const skin=M(o.piel||'#e9b48d',.5), shirt=M(o.camisa,.62), pants=M(o.pantalon,.7), shoe=M(o.zapatos||'#1A1B1F',.45), sleeve=o.manga==='larga'?shirt:skin;
  function seg(boneName,a,b,r,mat,ext=0){const pa=P(a),pb=P(b);const d=pb.clone().sub(pa);const len=d.length();const geo=new THREE.CapsuleGeometry(r,Math.max(.01,len+ext-2*r*.4),8,18);
    const m=sh(new THREE.Mesh(geo,mat));m.position.copy(pa.clone().add(pb).multiplyScalar(.5));m.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),d.normalize());g.add(m);g.updateMatrixWorld(true);bones[boneName].attach(m);return m;}
  function at(boneName,mesh,pos){mesh.position.copy(pos);g.add(mesh);g.updateMatrixWorld(true);bones[boneName].attach(mesh);return mesh;}
  // tronco
  const pel=P('pelvis'),s1=P('spine_01'),s3=P('spine_03'),nk=P('neck_01'),hd=P('Head');
  seg('pelvis','pelvis','spine_01',.175,pants,.14);
  const chest=seg('spine_02','spine_01','neck_01',.185,shirt,-.02);
  seg('neck_01','neck_01','Head',.065,skin,.04);
  // brazos y piernas
  for(const s of ['l','r']){seg('upperarm_'+s,'upperarm_'+s,'lowerarm_'+s,.078,o.manga==='larga'?shirt:shirt,.02);seg('lowerarm_'+s,'lowerarm_'+s,'hand_'+s,.066,sleeve,.0);
    const hp=P('hand_'+s).clone().lerp(P('middle_01_'+s),.6);at('hand_'+s,sh(new THREE.Mesh(new THREE.SphereGeometry(.078,18,14),skin)),hp);
    seg('thigh_'+s,'thigh_'+s,'calf_'+s,.1,pants,.04);seg('calf_'+s,'calf_'+s,'foot_'+s,.085,pants,.02);
    const fp=P('foot_'+s),bp=P('ball_'+s);const shoeM=sh(new THREE.Mesh(new THREE.CapsuleGeometry(.075,.16,6,14),shoe));shoeM.position.copy(fp.clone().lerp(bp,.55)).add(new THREE.Vector3(0,-.04,0));
    shoeM.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),bp.clone().sub(fp).setY(0).normalize());g.add(shoeM);g.updateMatrixWorld(true);bones['foot_'+s].attach(shoeM);}
  // cabeza de caricatura
  const head=new THREE.Group();head.position.copy(hd).add(new THREE.Vector3(0,.13,.0));
  const R=.2;head.add(sh(new THREE.Mesh(new THREE.SphereGeometry(R,40,30),skin)));
  const hairM=M(o.colorPelo||'#2b1b14',.7);
  const cap=sh(new THREE.Mesh(new THREE.SphereGeometry(R*1.04,40,30,0,Math.PI*2,0,Math.PI*(o.pelo==='largo'?.5:.42)),hairM));cap.rotation.x=-.28;cap.position.set(0,.012,-.008);head.add(cap);
  if(o.pelo==='largo'){head.add(sh(new THREE.Mesh(new THREE.CapsuleGeometry(R*.82,R*1.2,8,18),hairM)).translateY(-R*.55).translateZ(-R*.42));}
  if(o.pelo==='rapado'){cap.scale.set(1,.92,1);}
  const eyes=[],pupils=[],lids=[];
  [-.075,.075].forEach(x=>{eyes.push(head.add(sh(new THREE.Mesh(new THREE.SphereGeometry(.056,22,16),M('#ffffff',.2)))).children.at(-1));eyes.at(-1).position.set(x,.03,R*.8);
    const p=new THREE.Mesh(new THREE.SphereGeometry(.03,16,12),M('#121212',.15));p.position.set(x,.025,R*.8+.04);head.add(p);pupils.push(p);
    const l=new THREE.Mesh(new THREE.SphereGeometry(.059,22,16,0,Math.PI*2,0,Math.PI/2),skin);l.position.set(x,.03,R*.8);l.visible=false;head.add(l);lids.push(l);});
  const brows=[-.075,.075].map(x=>{const b=new THREE.Mesh(new THREE.BoxGeometry(.075,.016,.016),hairM);b.position.set(x,.105,R*.92);head.add(b);return b;});
  if(o.pestanas)[-.075,.075].forEach(x=>{const b=new THREE.Mesh(new THREE.BoxGeometry(.085,.012,.012),M('#111')); b.position.set(x,.083,R*.98);head.add(b);});
  const nose=new THREE.Mesh(new THREE.SphereGeometry(.026,14,10),skin);nose.position.set(0,-.02,R*.98);head.add(nose);
  const lip=new THREE.Mesh(new THREE.TorusGeometry(.05,.012,8,20,Math.PI),M('#4a1610',.5));lip.rotation.z=Math.PI;lip.position.set(0,-.065,R*.93);head.add(lip);
  const mo=new THREE.Mesh(new THREE.SphereGeometry(.042,18,12),M('#2a0c08',.6));mo.position.set(0,-.085,R*.9);mo.scale.set(1,.05,.45);head.add(mo);
  if(o.aretes)[-1,1].forEach(s=>{const e=new THREE.Mesh(new THREE.SphereGeometry(.022,12,10),M('#C9FB00',.3));e.position.set(s*R*.97,-.05,0);head.add(e);});
  const sweat=new THREE.Mesh(new THREE.SphereGeometry(.018,12,10),M('#9fd8ff',.1,{transparent:true,opacity:.9}));sweat.scale.set(1,1.5,1);sweat.position.set(R*.75,.08,R*.55);sweat.visible=false;head.add(sweat);
  g.add(head);g.updateMatrixWorld(true);bones['Head'].attach(head);
  // extras
  if(o.delantal){const ap=sh(new THREE.Mesh(new THREE.BoxGeometry(.36,.55,.025),M('#1A1B1F',.75)));at('pelvis',ap,pel.clone().add(new THREE.Vector3(0,-.16,.17)));}
  if(o.corbatin){const bw=new THREE.Group();[-1,1].forEach(s=>{const b=new THREE.Mesh(new THREE.ConeGeometry(.022,.045,4),M('#F42902'));b.rotation.z=s*Math.PI/2;b.position.x=s*.022;bw.add(b);});at('neck_01',bw,nk.clone().add(new THREE.Vector3(0,-.01,.1)));}
  // animación
  const mixer=new THREE.AnimationMixer(g);const acts={};let cur=null;
  function clip(name,t){if(!acts[name])acts[name]=mixer.clipAction(CLIPS[name]);const a=acts[name];if(cur!==a){Object.values(acts).forEach(x=>x.stop());a.play();cur=a;}
    a.time=((t%a.getClip().duration)+a.getClip().duration)%a.getClip().duration;mixer.update(0);}
  const q=new THREE.Quaternion(),pq=new THREE.Quaternion();
  function rotW(name,axis,ang){const b=bones[name];b.updateWorldMatrix(true,false);b.getWorldQuaternion(q);b.parent.getWorldQuaternion(pq);
    const r=new THREE.Quaternion().setFromAxisAngle(axis.clone().normalize(),ang);b.quaternion.copy(pq.clone().invert().multiply(r).multiply(q));}
  const _a=new THREE.Vector3(),_c=new THREE.Vector3();
  function aim(name,child,dirLocal,k=1){g.updateMatrixWorld(true);const b=bones[name];b.getWorldPosition(_a);bones[child].getWorldPosition(_c);
    const cur=_c.clone().sub(_a).normalize();const gq=g.getWorldQuaternion(new THREE.Quaternion());const dir=dirLocal.clone().normalize().applyQuaternion(gq);
    const qd=new THREE.Quaternion().setFromUnitVectors(cur,dir);const qk=new THREE.Quaternion().slerp(qd,Math.min(1,Math.max(0,k)));
    b.getWorldQuaternion(q);b.parent.getWorldQuaternion(pq);b.quaternion.copy(pq.clone().invert().multiply(qk).multiply(q));b.updateMatrixWorld(true);}
  function turnHead(ang,k=1){g.updateMatrixWorld(true);rotW('Head',new THREE.Vector3(0,1,0),ang*k);}
  function talk(v){mo.scale.set(1,THREE.MathUtils.lerp(.05,1,Math.min(1,Math.max(0,v))),.45);lip.visible=v<.08;}
  return {g,bones,head,eyes,pupils,lids,brows,mo,lip,sweat,mixer,clip,rotW,aim,turnHead,talk};
}
