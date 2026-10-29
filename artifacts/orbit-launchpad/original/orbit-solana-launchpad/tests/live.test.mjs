import test from 'node:test';
import assert from 'node:assert/strict';
import {generateKeyPairSync,sign} from 'node:crypto';
import {liveTestHelpers} from '../server/live.mjs';
import {makeServer} from '../server/app.mjs';

const {base58Decode,verifySignature,safeTitle}=liveTestHelpers;
function b58(buf){const A='123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';let n=BigInt('0x'+Buffer.from(buf).toString('hex')),out='';while(n>0n){out=A[Number(n%58n)]+out;n/=58n}for(const c of buf){if(c!==0)break;out='1'+out}return out}
test('Live authorization validates true Ed25519 Solana signatures, not address alone',()=>{
 const {privateKey,publicKey}=generateKeyPairSync('ed25519');const raw=publicKey.export({format:'der',type:'spki'}).subarray(-32);
 const address=b58(raw),message='ORBIT Live authentication challenge 123';
 const signature=sign(null,Buffer.from(message),privateKey).toString('base64');
 assert.equal(base58Decode(address).length,32);
 assert.equal(verifySignature(address,message,signature),true);
 assert.equal(verifySignature(address,message+'x',signature),false);
 assert.equal(verifySignature(address,message,Buffer.alloc(64).toString('base64')),false);
});
test('Live stream titles are length-limited and stripped of control characters',()=>{
 assert.equal(safeTitle('Hi\nthere'),'Hi there');assert.equal(safeTitle('a'.repeat(900)).length,64);
});
test('Live API does not issue sessions or leak credentials before LiveKit config',async()=>{
 if(process.env.LIVEKIT_URL||process.env.LIVEKIT_API_KEY||process.env.LIVEKIT_API_SECRET)return;
 const srv=makeServer();await new Promise(ok=>srv.listen(0,'127.0.0.1',ok));
 const base='http://127.0.0.1:'+srv.address().port;
 try{
  const response=await fetch(base+'/api/live');const list=await response.json();assert.equal(response.status,200);assert.equal(list.enabled,false);assert.deepEqual(list.items,[]);
  const challenge=await fetch(base+'/api/live/challenge',{method:'POST',headers:{'content-type':'application/json'},body:'{}'});
  assert.equal(challenge.status,503);
 }finally{await new Promise(ok=>srv.close(ok))}
});
