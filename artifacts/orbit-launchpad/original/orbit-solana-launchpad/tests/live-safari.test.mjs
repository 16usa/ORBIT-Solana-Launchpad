import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {resolve,dirname} from 'node:path';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const front=readFileSync(resolve(root,'web/src/OrbitLive.tsx'),'utf8');
const server=readFileSync(resolve(root,'server/live.mjs'),'utf8');
test('Handoff does not issue LiveKit credentials until Safari explicitly redeems the code',()=>{
 const prepare=server.split("if(p==='/api/live/prepare'")[1].split("if(p==='/api/live/redeem'")[0];
 assert.match(prepare,/verifySignature/);
 assert.match(prepare,/randomBytes\(32\)/);
 assert.doesNotMatch(prepare,/service\.createRoom|tokenFor\(/);
 const redeem=server.split("if(p==='/api/live/redeem'")[1].split("if(p==='/api/live/start'")[0];
 assert.match(redeem,/handoffs\.delete\(key\)/);
 assert.match(redeem,/service\.createRoom/);
 assert.match(redeem,/tokenFor\(/);
 assert.match(redeem,/req\.method==='POST'/);
});
test('Browser must not request camera or microphone in Phantom during handoff',()=>{
 const start=front.split(' const start=async()=>')[1].split(' const leave=')[0];
 assert.match(start,/wallet\.signMessage/);
 assert.match(start,/api\/live\/prepare/);
 assert.doesNotMatch(start,/getUserMedia|setCameraEnabled|api\/live\/start/);
});
test('Safari requires explicit click to activate video and clears code after redemption',()=>{
 assert.match(front,/onClick=\{redeem\}/);
 assert.match(front,/onClick=\{startCamera\}/);
 assert.match(front,/history\.replaceState/);
 assert.match(front,/api\/live\/heartbeat/);
});
