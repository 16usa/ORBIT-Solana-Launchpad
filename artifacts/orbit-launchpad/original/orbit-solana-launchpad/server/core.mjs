import { createHash, randomUUID } from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';

export const MINT_RE = /^[1-9A-HJ-NP-Za-km-z]{32,44}$/;
export function validMint(value){return typeof value==='string' && MINT_RE.test(value);}
export function cleanText(value, max){return typeof value==='string'?value.trim().slice(0,max):'';}
export function parseLaunchInput(input){
 if(!input || !validMint(input.mint) || !validMint(input.poolId) || !validMint(input.creator) || !validMint(input.programId)) throw new Error('Invalid mint, pool, creator or program address');
 if(typeof input.txSignature!=='string' || !/^[1-9A-HJ-NP-Za-km-z]{64,90}$/.test(input.txSignature)) throw new Error('Invalid transaction signature');
 if(typeof input.metadataId!=='string' || !/^[a-f0-9-]{36}$/.test(input.metadataId)) throw new Error('Invalid metadata id');
 return Object.fromEntries(['mint','poolId','creator','programId','txSignature','metadataId'].map(k=>[k,input[k]]));
}
export function metadataInput(input){
 const name=cleanText(input?.name,32),symbol=cleanText(input?.symbol,10), description=cleanText(input?.description,800);
 if(typeof input?.name!=='string'||input.name.trim().length>32||typeof input?.symbol!=='string'||input.symbol.trim().length>10)throw new Error('Name or ticker is too long');
 if(name.length<2 || !/^[a-zA-Z0-9_]{2,10}$/.test(symbol)) throw new Error('Name (2–32) and ticker (2–10, A-Z/0-9/_) required');
 if(typeof input?.imageId!=='string' || !/^[a-f0-9-]{36}$/.test(input.imageId))throw new Error('Valid uploaded image required');
 const socials={};
 for(const key of ['website','twitter','telegram']){
  const raw=cleanText(input?.[key],220);
  if(raw){let url;try{url=new URL(raw)}catch{throw new Error('Invalid '+key+' URL')}
   if(!['https:','http:'].includes(url.protocol) || url.username || url.password || (url.hostname==='localhost' && process.env.NODE_ENV==='production'))throw new Error('Invalid '+key+' URL');
   socials[key]=url.href;
  }
 }
 return {name,symbol,description,imageId:input.imageId,...socials};
}
export function mkdir(folder){fs.mkdirSync(folder,{recursive:true});}
export function loadStore(file, fallback){try{return JSON.parse(fs.readFileSync(file,'utf8'))}catch(e){if(e.code==='ENOENT')return fallback; throw e}}
export function saveStore(file,value){mkdir(path.dirname(file));const tmp=file+'.'+randomUUID()+'.tmp';fs.writeFileSync(tmp,JSON.stringify(value,null,2),{mode:0o600});fs.renameSync(tmp,file);}
export function mediaBytes(value){
 if(typeof value!=='string' || value.length>7_000_000 || value.length<20 || !/^[A-Za-z0-9+/=]+$/.test(value))throw new Error('Invalid image payload');
 const bytes=Buffer.from(value,'base64'); if(bytes.length>5_000_000)throw new Error('Image larger than 5 MB');
 if(bytes.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10])))return {bytes, ext:'png',mime:'image/png'};
 if(bytes.subarray(0,3).equals(Buffer.from([255,216,255])))return {bytes,ext:'jpg',mime:'image/jpeg'};
 if(bytes.subarray(0,6).toString('ascii')==='GIF87a'||bytes.subarray(0,6).toString('ascii')==='GIF89a')return {bytes,ext:'gif',mime:'image/gif'};
 if(bytes.subarray(0,4).toString()==='RIFF'&&bytes.subarray(8,12).toString()==='WEBP')return {bytes,ext:'webp',mime:'image/webp'};
 throw new Error('PNG/JPEG/GIF/WEBP only');
}
export async function rpcCall(url,method,params){
 const r=await fetch(url,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({jsonrpc:'2.0',id:1,method,params}),signal:AbortSignal.timeout(15000)});
 if(!r.ok)throw new Error('RPC HTTP '+r.status);
 const json=await r.json();if(json.error)throw new Error(json.error.message??'RPC error');return json.result;
}
export function formatPublicUrl(base){
 if(!base)return '';
 const uri=new URL(base);
 if(uri.protocol!=='https:' && !/^http:\/\/localhost(?::\d+)?$/.test(base)) throw new Error('PUBLIC_BASE_URL must use HTTPS');
 return uri.href.replace(/\/$/,'');
}
export function headersJson(extra={}){return {'content-type':'application/json; charset=utf-8','cache-control':'no-store','x-content-type-options':'nosniff',...extra};}
export function stableHash(value){return createHash('sha256').update(value).digest('hex').slice(0,12);}
