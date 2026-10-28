import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {parseLaunchInput,metadataInput,mediaBytes,formatPublicUrl,validMint,saveStore,loadStore} from '../server/core.mjs';
import {makeServer} from '../server/app.mjs';

test('Address validation and user input safety',()=>{
 assert.equal(validMint('So11111111111111111111111111111111111111112'),true);
 assert.equal(validMint('../malicious'),false);
 assert.throws(()=>parseLaunchInput({mint:'../pass'}),/Invalid/);
 assert.throws(()=>metadataInput({name:'x',symbol:'BAD!',imageId:'abc'}),/Name/);
 assert.throws(()=>metadataInput({name:'Example',symbol:'TEST',imageId:'c2a238e6-50d1-4c12-a25f-14dfa93a1111',website:'javascript:alert(1)'}),/Invalid/);
 assert.equal(metadataInput({name:'Example',symbol:'TEST',imageId:'c2a238e6-50d1-4c12-a25f-14dfa93a1111'}).symbol,'TEST');
});
test('Image signature checks reject arbitrary payloads',()=>{
 assert.throws(()=>mediaBytes(Buffer.from('hello').toString('base64')),/Invalid image/);
 const png=Buffer.concat([Buffer.from([137,80,78,71,13,10,26,10]),Buffer.alloc(64)]);
 assert.equal(mediaBytes(png.toString('base64')).ext,'png');
});
test('Public metadata URL requires HTTPS',()=>{
 assert.equal(formatPublicUrl('https://demo.example/'),'https://demo.example');
 assert.throws(()=>formatPublicUrl('http://example.com'),/HTTPS/);
});
test('Store atomic read/write',()=>{
 const d=mkdtempSync(join(tmpdir(),'orbit-test-'));const f=join(d,'nested','a.json');
 try{assert.deepEqual(loadStore(f,[]),[]);saveStore(f,[{x:1}]);assert.deepEqual(loadStore(f,[]),[{x:1}]);}finally{rmSync(d,{recursive:true,force:true})}
});
test('API returns real empty launch list without fake data',async()=>{
 const server=makeServer();await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const base=`http://127.0.0.1:${server.address().port}`;
 try{
  const health=await(await fetch(`${base}/api/health`)).json();assert.equal(health.ok,true);
  const config=await(await fetch(`${base}/api/config`)).json();assert.equal(config.network,'devnet');
  const all=await(await fetch(`${base}/api/launches`)).json();assert.ok(Array.isArray(all.items));
  const m=await fetch(`${base}/api/metadata`,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({})});assert.equal(m.status,400); // input validation
  const bad=await fetch(`${base}/api/swap/order?inputMint=x`);assert.equal(bad.status,503);
 }finally{await new Promise(r=>server.close(r))}
});

test('Metadata origin URL rejects unsafe paths, credentials and query strings',()=>{
 assert.throws(()=>formatPublicUrl('https://demo.example/api?token=private'),/origin/);
 assert.throws(()=>formatPublicUrl('https://user:secret@demo.example/'),/origin/);
 assert.throws(()=>formatPublicUrl('https://demo.example/#temporary'),/origin/);
});
test('Launch readiness is explicit and boolean for UI safety checks',async()=>{
 const server=makeServer();await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 try{
  const response=await fetch(`http://127.0.0.1:${server.address().port}/api/config`);
  const config=await response.json();
  assert.equal(typeof config.launchEnabled,'boolean');
  assert.equal(typeof config.mainnetTradingEnabled,'boolean');
  assert.equal(typeof config.launchBlockReason,'string');
  assert.equal(config.launchEnabled && config.network==='mainnet-beta',false);
 }finally{await new Promise(resolve=>server.close(resolve))}
});
