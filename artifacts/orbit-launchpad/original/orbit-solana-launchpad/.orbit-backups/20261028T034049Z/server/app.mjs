import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { randomUUID } from 'node:crypto';
import { parseLaunchInput, metadataInput, mkdir, loadStore, saveStore, mediaBytes, rpcCall, formatPublicUrl, headersJson, validMint } from './core.mjs';

try {process.loadEnvFile(path.resolve('.env'));} catch(e){if(e.code!=='ENOENT')throw e;}
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const dataDir=path.resolve(process.env.DATA_DIR||path.join(root,'data'));
const siteDist=path.resolve(root,'dist');
const port=Number(process.env.PORT||3000);
const cluster=process.env.SOLANA_CLUSTER==='mainnet-beta'?'mainnet-beta':'devnet';
const rpcUrl=process.env.RPC_URL||(cluster==='devnet'?'https://api.devnet.solana.com':'https://api.mainnet-beta.solana.com');
const rpcPublic=process.env.VITE_RPC_URL||(cluster==='devnet'?'https://api.devnet.solana.com':'https://api.mainnet-beta.solana.com');
const publicBase=formatPublicUrl(process.env.PUBLIC_BASE_URL||'');
const launchesFile=path.join(dataDir,'launches.json');
const metadir=path.join(dataDir,'metadata');
const mediaDir=path.join(dataDir,'media');
mkdir(metadir);mkdir(mediaDir);

const rate=new Map();
function json(res,status,body){res.writeHead(status,headersJson());res.end(JSON.stringify(body));}
function error(res,status,message){json(res,status,{error:message});}
function readJson(req,max=7_000_000){return new Promise((resolve,reject)=>{let input='';req.on('data',c=>{input+=c;if(input.length>max){req.destroy();reject(new Error('Request too large'))}});req.on('end',()=>{try{resolve(JSON.parse(input))}catch{reject(new Error('Malformed JSON'))}});req.on('error',reject)})}
function file(res,p,type){try{const buf=fs.readFileSync(p);const html=type.startsWith('text/html');res.writeHead(200,{'content-type':type,'x-content-type-options':'nosniff','cache-control':html?'no-store':'public, max-age=3600',...(html?{'content-security-policy':"default-src 'self'; connect-src 'self' https: wss:; img-src 'self' https: data: blob:; media-src 'self' https: blob:; font-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"}:{})});res.end(buf)}catch{error(res,404,'Not found')}}
function onlyGet(req,res){if(req.method!=='GET'){error(res,405,'Method not allowed');return false}return true}
function hitRate(req){const ip=req.socket.remoteAddress||'unknown';const t=Date.now();const slot=rate.get(ip)||{time:t,count:0};if(t-slot.time>60_000){slot.time=t;slot.count=0}slot.count++;rate.set(ip,slot);if(rate.size>5000)rate.clear();return slot.count<=80}
async function checkChain(input){
 const [status,mintInfo,poolInfo,transaction] = await Promise.all([
   rpcCall(rpcUrl,'getSignatureStatuses',[[input.txSignature],{searchTransactionHistory:true}]),
   rpcCall(rpcUrl,'getAccountInfo',[input.mint,{encoding:'base64',commitment:'confirmed'}]),
   rpcCall(rpcUrl,'getAccountInfo',[input.poolId,{encoding:'base64',commitment:'confirmed'}]),
   rpcCall(rpcUrl,'getTransaction',[input.txSignature,{encoding:'jsonParsed',commitment:'confirmed',maxSupportedTransactionVersion:0}])
 ]);
 const signature=status?.value?.[0];
 if(!signature || signature.err || !['confirmed','finalized'].includes(signature.confirmationStatus))throw new Error('On-chain transaction is not confirmed');
 if(!transaction?.transaction?.message||transaction.meta?.err)throw new Error('Cannot verify launch transaction');
 const accounts=transaction.transaction.message.accountKeys||[];
 const publicKeys=accounts.map(k=>typeof k==='string'?k:k.pubkey);
 if(![input.mint,input.poolId,input.creator,input.programId].every(k=>publicKeys.includes(k)))throw new Error('Launch transaction does not reference supplied addresses');
 const creator=accounts.find(k=>(typeof k==='string'?k:k.pubkey)===input.creator);
 if(!creator||typeof creator==='string'||!creator.signer)throw new Error('Creator did not sign the launch transaction');
 if(!mintInfo?.value || !poolInfo?.value)throw new Error('Mint or pool missing on chain');
 if(!['TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA','TokenzQdBNbLqP5VEhdkAS6EPFZ6LKruL4y3Yz9KP'].includes(mintInfo.value.owner))throw new Error('Account is not an SPL mint');
 if(poolInfo.value.owner!==input.programId)throw new Error('Pool program owner mismatch');
 const allowed=process.env.RAYDIUM_PROGRAM_ID;
 if(cluster==='mainnet-beta' && !allowed)throw new Error('RAYDIUM_PROGRAM_ID allowlist is required on mainnet');
 if(allowed && input.programId!==allowed)throw new Error('Program is not allowlisted');
 return {verified:true,confidence:allowed?'allowlisted-launch-accounts':'transaction-accounts'};
}
export function makeServer(){return http.createServer(async(req,res)=>{
 try{
  const u=new URL(req.url||'/', 'http://localhost');const pathname=u.pathname;
  if(pathname==='/api/health'){return json(res,200,{ok:true,network:cluster});}
  if(pathname==='/api/config'){return json(res,200,{network:cluster,rpc:rpcPublic,publicBase,tradeEnabled:!!process.env.JUPITER_API_KEY,raydiumProgramAllowlisted:!!process.env.RAYDIUM_PROGRAM_ID});}
  if(pathname==='/api/launches'&&req.method==='GET'){
   const all=loadStore(launchesFile,[]);
   return json(res,200,{items:all.slice(0,100)});
  }
  if(/^\/api\/launches\/[A-Za-z0-9]+$/.test(pathname)&&req.method==='GET'){
   const mint=pathname.split('/').at(-1);return json(res,200,{item:loadStore(launchesFile,[]).find(l=>l.mint===mint)||null});
  }
  if(pathname.startsWith('/api/') && !hitRate(req))return error(res,429,'Rate limited');
  if(pathname==='/api/media'&&req.method==='POST'){
   const body=await readJson(req);const {bytes,ext}=mediaBytes(body.base64);const id=randomUUID();fs.writeFileSync(path.join(mediaDir,id+'.'+ext),bytes,{flag:'wx'});
   return json(res,201,{id,uri:publicBase?`${publicBase}/media/${id}.${ext}`:null,extension:ext});
  }
  if(pathname==='/api/metadata'&&req.method==='POST'){
   const m=metadataInput(await readJson(req,10_000));const files=fs.readdirSync(mediaDir);const filename=files.find(v=>v.startsWith(m.imageId+'.'));
   if(!filename) return error(res,400,'Upload image first');
   if(!publicBase) return error(res,503,'PUBLIC_BASE_URL (public HTTPS URL) is required for on-chain metadata');
   const id=randomUUID();const jsonMeta={name:m.name,symbol:m.symbol,description:m.description,image:`${publicBase}/media/${filename}`,external_url:m.website||'',properties:{category:'image'},extensions:{website:m.website||'',twitter:m.twitter||'',telegram:m.telegram||''}};
   fs.writeFileSync(path.join(metadir,id+'.json'),JSON.stringify(jsonMeta,null,2),{flag:'wx'});
   return json(res,201,{id,uri:`${publicBase}/metadata/${id}.json`,metadata:jsonMeta});
  }
  if(pathname==='/api/launches' && req.method==='POST'){
   const v=parseLaunchInput(await readJson(req,4000));const metadataFile=path.join(metadir,v.metadataId+'.json');
   if(!fs.existsSync(metadataFile))return error(res,400,'Metadata missing');
   const verified=await checkChain(v);
   const all=loadStore(launchesFile,[]);
   const prev=all.find(a=>a.mint===v.mint);
   if(prev)return json(res,200,{item:prev});
   const m=JSON.parse(fs.readFileSync(metadataFile,'utf8'));
   const item={...v,...verified,network:cluster,name:m.name,symbol:m.symbol,image:m.image,description:m.description,createdAt:new Date().toISOString()};
   all.unshift(item);saveStore(launchesFile,all.slice(0,50000));return json(res,201,{item});
  }
  // Jupiter V2 API proxies: wallet signs client-side; server never receives a secret key.
  if(pathname==='/api/swap/order'&&req.method==='GET'){
   if(cluster!=='mainnet-beta'||!process.env.JUPITER_API_KEY)return error(res,503,'Mainnet Jupiter API not configured');
   const p=new URLSearchParams();for(const key of ['inputMint','outputMint','amount','taker']){
    const val=u.searchParams.get(key)||'';
    if(key==='amount'?!/^\d{1,20}$/.test(val):!validMint(val))return error(res,400,'Invalid '+key);
    p.set(key,val);
   }
   const r=await fetch('https://api.jup.ag/swap/v2/order?'+p,{headers:{'x-api-key':process.env.JUPITER_API_KEY},signal:AbortSignal.timeout(18000)});
   return json(res,r.status,await r.json());
  }
  if(pathname==='/api/swap/execute'&&req.method==='POST'){
   if(cluster!=='mainnet-beta'||!process.env.JUPITER_API_KEY)return error(res,503,'Mainnet Jupiter API not configured');
   const b=await readJson(req,18000);
   if(!b||typeof b.requestId!=='string'||typeof b.signedTransaction!=='string'||!/^[-_A-Za-z0-9+/=]{100,16000}$/.test(b.signedTransaction))return error(res,400,'Invalid signed swap payload');
   const r=await fetch('https://api.jup.ag/swap/v2/execute',{method:'POST',headers:{'content-type':'application/json','x-api-key':process.env.JUPITER_API_KEY},body:JSON.stringify({requestId:b.requestId,signedTransaction:b.signedTransaction}),signal:AbortSignal.timeout(30000)});
   return json(res,r.status,await r.json());
  }
  const media=pathname.match(/^\/media\/([a-f0-9-]{36})\.(png|jpg|gif|webp)$/);
  if(media&&onlyGet(req,res))return file(res,path.join(mediaDir,media[1]+'.'+media[2]),({'png':'image/png','jpg':'image/jpeg','gif':'image/gif','webp':'image/webp'})[media[2]]);
  const meta=pathname.match(/^\/metadata\/([a-f0-9-]{36})\.json$/);
  if(meta&&onlyGet(req,res))return file(res,path.join(metadir,meta[1]+'.json'),'application/json');
  if(pathname.startsWith('/api/'))return error(res,404,'API endpoint not found');
  // Production UI: static files from `npm run build`. Does not expose server-side config.
  if(!fs.existsSync(siteDist))return error(res,404,'UI not built. Use npm run dev or npm run build.');
  const target=path.resolve(siteDist,'.'+pathname);
  if(target!==siteDist&&!target.startsWith(siteDist+path.sep))return error(res,400,'Bad path');
  const chosen=fs.existsSync(target)&&fs.statSync(target).isFile()?target:path.join(siteDist,'index.html');
  const extension=path.extname(chosen).toLowerCase();
  const types={'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'application/javascript; charset=utf-8','.svg':'image/svg+xml','.png':'image/png','.woff2':'font/woff2','.ico':'image/x-icon'};
  return file(res,chosen,types[extension]||'application/octet-stream');
 }catch(e){console.error('[API]',e?.message||e);error(res,/Invalid|missing|Malformed|larger|too long|required|Upload|mismatch|unconfirmed|not confirmed|not allowlisted/i.test(e?.message||'')?400:502,e?.message||'Server error')}
 });}
if(process.argv[1] && fileURLToPath(import.meta.url)===path.resolve(process.argv[1])){
 const srv=makeServer();srv.listen(port,'0.0.0.0',()=>console.log(`Orbit API on http://0.0.0.0:${port} (${cluster})`));
}
