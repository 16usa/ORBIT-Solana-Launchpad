import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,rmSync} from 'node:fs';
import os from 'node:os';
import path from 'node:path';
process.env.DATA_DIR=mkdtempSync(path.join(os.tmpdir(),'orbit-api-'));
process.env.SOLANA_CLUSTER='devnet';
const {makeServer}=await import('../server/app.mjs');
const server=makeServer();
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const base=`http://127.0.0.1:${server.address().port}`;
test.after(async()=>{await new Promise(resolve=>server.close(resolve));rmSync(process.env.DATA_DIR,{recursive:true,force:true})});
test('health and config expose only non-secret fields',async()=>{
 let r=await fetch(base+'/api/health');assert.equal(r.status,200);assert.equal((await r.json()).network,'devnet');
 r=await fetch(base+'/api/config');const cfg=await r.json();assert.equal(r.status,200);assert.equal(cfg.network,'devnet');assert.ok(!('JUPITER_API_KEY' in cfg));
});
test('empty catalog never inserts simulated prices or coins',async()=>{
 const r=await fetch(base+'/api/launches');assert.equal(r.status,200);assert.deepEqual((await r.json()).items,[]);
});
test('invalid launch is rejected before RPC or store mutation',async()=>{
 const r=await fetch(base+'/api/launches',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({mint:'not-a-real-mint'})});assert.equal(r.status,400);
});
test('metadata cannot be issued without an uploaded image',async()=>{
 const r=await fetch(base+'/api/metadata',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({name:'Test Coin',symbol:'TEST',imageId:'12345678-1234-1234-1234-123456789abc'})});assert.equal(r.status,400);
});
test('routing of unknown API returns JSON 404',async()=>{
 const r=await fetch(base+'/api/unknown');assert.equal(r.status,404);assert.ok((await r.json()).error);
});
