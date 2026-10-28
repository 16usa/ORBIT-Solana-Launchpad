import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync, rmSync} from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {mediaBytes,parseLaunchInput,metadataInput,formatPublicUrl,loadStore,saveStore,validMint} from '../server/core.mjs';

const EXAMPLE='11111111111111111111111111111111';
const S='2'.repeat(88);
test('base58 address constraints',()=>{
 assert.ok(validMint(EXAMPLE));assert.ok(!validMint('../config'));assert.ok(!validMint('0'.repeat(44)));
});
test('launch record requires on-chain identifiers',()=>{
 assert.deepEqual(parseLaunchInput({mint:EXAMPLE,poolId:EXAMPLE,creator:EXAMPLE,programId:EXAMPLE,txSignature:S,metadataId:'12345678-1234-1234-1234-123456789abc'}),{
 mint:EXAMPLE,poolId:EXAMPLE,creator:EXAMPLE,programId:EXAMPLE,txSignature:S,metadataId:'12345678-1234-1234-1234-123456789abc'});
 assert.throws(()=>parseLaunchInput({mint:'hi'}),/Invalid/);
});
test('metadata sanitization, field constraints and invalid URLs',()=>{
 assert.deepEqual(metadataInput({name:'  Orb ',symbol:'ORB',imageId:'12345678-1234-1234-1234-123456789abc',website:'https://example.com'}).name,'Orb');
 assert.throws(()=>metadataInput({name:'Hi',symbol:'LONG_SYMBOL_123',imageId:'12345678-1234-1234-1234-123456789abc'}));
 assert.throws(()=>metadataInput({name:'Hi',symbol:'H',imageId:'12345678-1234-1234-1234-123456789abc'}));
 assert.throws(()=>metadataInput({name:'Hi',symbol:'HI',imageId:'12345678-1234-1234-1234-123456789abc',website:'javascript:alert(1)'}));
});
test('media only accepts known image signatures',()=>{
 const png=Buffer.concat([Buffer.from([137,80,78,71,13,10,26,10]),Buffer.alloc(20)]).toString('base64');
 assert.equal(mediaBytes(png).ext,'png');
 assert.throws(()=>mediaBytes(Buffer.from('not an image etc').toString('base64')));
});
test('metadata public URL enforces HTTPS and normalizes trailing slash',()=>{
 assert.equal(formatPublicUrl('https://example.com/'),'https://example.com');
 assert.throws(()=>formatPublicUrl('http://example.com'));
});
test('store writes atomically and restores unchanged',()=>{
 const dir=mkdtempSync(path.join(os.tmpdir(),'orbit-store-'));
 try{const f=path.join(dir,'d.json');assert.deepEqual(loadStore(f,[]),[]);saveStore(f,[{hello:'world'}]);assert.deepEqual(loadStore(f,[]),[{hello:'world'}]);}finally{rmSync(dir,{recursive:true,force:true})}
});
