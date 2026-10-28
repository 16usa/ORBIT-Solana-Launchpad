#!/usr/bin/env python3
"""ORBIT stage 2: devnet readiness and safe pool-lifecycle routing.
   Applies only to audited ORBIT project files. No installs, restarts, Git actions.
"""
from pathlib import Path
from datetime import datetime, timezone
import shutil
import sys

ROOTS = [Path.cwd() / 'artifacts/orbit-launchpad/original/orbit-solana-launchpad',
         Path.cwd() / 'original/orbit-solana-launchpad', Path.cwd()]

def one(src, old, new, label):
    count = src.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected 1 source occurrence, got {count}; source may have changed or patch already installed')
    return src.replace(old, new, 1)


def patch(root):
    paths = {k: root / k for k in [
        'server/app.mjs','web/src/api.ts','web/src/chain.ts',
        'web/src/App.tsx','tests/server.test.mjs']}
    for name,p in paths.items():
        if not p.is_file():
            raise RuntimeError(f'Cannot find {name} in ORBIT source: {root}')
    data={key:p.read_text(encoding='utf-8') for key,p in paths.items()}
    k='server/app.mjs'
    data[k]=one(data[k],
"  if(pathname.startsWith('/api/') && !hitRate(req))return error(res,429,'Rate limited');",
"""  if(pathname.startsWith('/api/') && !hitRate(req))return error(res,429,'Rate limited');
  // Live, non-cached Devnet preflight. Does not sign transactions or expose credentials.
  if(pathname==='/api/network-status' && req.method==='GET'){
   const programId=process.env.RAYDIUM_PROGRAM_ID||'';
   const base={network:cluster,rpcReachable:false,programDeployed:false,ready:false,slot:null};
   if(!validMint(programId))return json(res,200,{...base,reason:'Set a valid RAYDIUM_PROGRAM_ID in Replit environment settings.'});
   if(!launchEnabled)return json(res,200,{...base,reason:launchBlockReason});
   try{
    const [slot,info]=await Promise.all([
     rpcCall(rpcUrl,'getSlot',[{commitment:'confirmed'}]),
     rpcCall(rpcUrl,'getAccountInfo',[programId,{encoding:'base64',commitment:'confirmed'}]),
    ]);
    const programDeployed=Boolean(info?.value?.executable);
    return json(res,200,{...base,rpcReachable:true,programDeployed,ready:programDeployed,slot,
      reason:programDeployed?'RPC and program reachable. LaunchLab config and wallet readiness still require verification.':'Allowlisted Raydium program is missing or not executable on this network.'});
   }catch(err){
    return json(res,200,{...base,reason:'Devnet RPC request failed: '+String(err?.message||err).slice(0,160)});
   }
  }""",'Server: RPC health preflight')
    k='web/src/api.ts'
    data[k]=one(data[k],
"export type Launch={mint:string;poolId:string;creator:string;programId:string;txSignature:string;metadataId:string;network:string;name:string;symbol:string;image:string;description:string;createdAt:string;verified:boolean;confidence:string};",
"""export type NetworkStatus={network:string;rpcReachable:boolean;programDeployed:boolean;ready:boolean;slot:number|null;reason:string};
export type Launch={mint:string;poolId:string;creator:string;programId:string;txSignature:string;metadataId:string;network:string;name:string;symbol:string;image:string;description:string;createdAt:string;verified:boolean;confidence:string};""",'Client: preflight type')

    k='web/src/chain.ts'
    data[k]=one(data[k],
" const price=Curve.getPrice({poolInfo:p,curveType:p.configInfo.curveType,decimalA:p.mintDecimalsA,decimalB:p.mintDecimalsB});\n const raisedSol=Number(p.realB.toString())/1e9,targetSol=Number(p.totalFundRaisingB.toString())/1e9;\n return {priceSol:Number(price.toString()),raisedSol,targetSol,progress:targetSol>0?Math.max(0,Math.min(100,raisedSol/targetSol*100)):0,status:Number(p.status),poolId:poolId.toBase58(),decimals:p.mintDecimalsA,updated:Date.now()};",
""" const status=Number(p.status); // 0 funding, 1 waiting for migration, 2 migrated.
 // A graduated token no longer has an executable curve price. Never present stale curve data as a live quote.
 const price=status===0 ? Number(Curve.getPrice({poolInfo:p,curveType:p.configInfo.curveType,decimalA:p.mintDecimalsA,decimalB:p.mintDecimalsB}).toString()) : 0;
 const raisedSol=Number(p.realB.toString())/1e9,targetSol=Number(p.totalFundRaisingB.toString())/1e9;
 return {priceSol:price,raisedSol,targetSol,progress:targetSol>0?Math.max(0,Math.min(100,raisedSol/targetSol*100)):0,status,poolId:poolId.toBase58(),decimals:p.mintDecimalsA,updated:Date.now()};""", 'Chain: graduated price guard')
    data[k]=one(data[k],
" const configId=getPdaLaunchpadConfigId(programId,NATIVE_MINT,0,0).publicKey;\n const cfg=await connection.getAccountInfo(configId,'confirmed');if(!cfg)throw new Error('Raydium LaunchLab configuration is unavailable on this network. Do not submit a transaction.');\n const configInfo=LaunchpadConfig.decode(cfg.data);",
""" // The default 0/0 config need not exist. Operators may provide an explicitly reviewed config ID.
 const selected=import.meta.env.VITE_RAYDIUM_LAUNCH_CONFIG_ID;
 const configId=selected?new PublicKey(selected):getPdaLaunchpadConfigId(programId,NATIVE_MINT,0,0).publicKey;
 const cfg=await connection.getAccountInfo(configId,'confirmed');
 if(!cfg)throw new Error('LaunchLab config '+configId.toBase58()+' is unavailable on '+config.network+'. Set VITE_RAYDIUM_LAUNCH_CONFIG_ID to a verified SOL config.');
 if(!cfg.owner.equals(programId))throw new Error('The configured LaunchLab account is not owned by the expected Raydium program');
 const configInfo=LaunchpadConfig.decode(cfg.data);
 if(!configInfo.mintB.equals(NATIVE_MINT))throw new Error('This LaunchLab config does not use SOL. ORBIT currently supports SOL launches only.');""", 'Chain: verified config')
    # Reuse one LaunchLab configuration verifier in both onchain creation and the UI preflight.
    data[k]=one(data[k],
" // The default 0/0 config need not exist. Operators may provide an explicitly reviewed config ID.\n const selected=import.meta.env.VITE_RAYDIUM_LAUNCH_CONFIG_ID;\n const configId=selected?new PublicKey(selected):getPdaLaunchpadConfigId(programId,NATIVE_MINT,0,0).publicKey;\n const cfg=await connection.getAccountInfo(configId,'confirmed');\n if(!cfg)throw new Error('LaunchLab config '+configId.toBase58()+' is unavailable on '+config.network+'. Set VITE_RAYDIUM_LAUNCH_CONFIG_ID to a verified SOL config.');\n if(!cfg.owner.equals(programId))throw new Error('The configured LaunchLab account is not owned by the expected Raydium program');\n const configInfo=LaunchpadConfig.decode(cfg.data);\n if(!configInfo.mintB.equals(NATIVE_MINT))throw new Error('This LaunchLab config does not use SOL. ORBIT currently supports SOL launches only.');",
" const {configId,configInfo}=await verifyLaunchConfig(connection,config);", 'Chain: use verified config in launch')
    data[k]=one(data[k],
"export async function launchToken(connection:Connection,config:AppConfig,wallet:WalletContextState,input:{name:string;symbol:string;uri:string}){",
"""export async function verifyLaunchConfig(connection:Connection,config:AppConfig){
 if(!config.launchEnabled)throw new Error(config.launchBlockReason||'Token creation is disabled');
 const programId=program(config);
 const selected=import.meta.env.VITE_RAYDIUM_LAUNCH_CONFIG_ID;
 const configId=selected?new PublicKey(selected):getPdaLaunchpadConfigId(programId,NATIVE_MINT,0,0).publicKey;
 const cfg=await connection.getAccountInfo(configId,'confirmed');
 if(!cfg)throw new Error('LaunchLab config '+configId.toBase58()+' is unavailable on '+config.network+'. Set VITE_RAYDIUM_LAUNCH_CONFIG_ID to a verified SOL config.');
 if(!cfg.owner.equals(programId))throw new Error('The configured LaunchLab account is not owned by the expected Raydium program');
 const configInfo=LaunchpadConfig.decode(cfg.data);
 if(!configInfo.mintB.equals(NATIVE_MINT))throw new Error('This LaunchLab config does not use SOL. ORBIT currently supports SOL launches only.');
 return {configId,configInfo};
}
export async function launchToken(connection:Connection,config:AppConfig,wallet:WalletContextState,input:{name:string;symbol:string;uri:string}){""", 'Chain: shared config verifier')
    data[k]=one(data[k],
" const raydium=await sdk(connection,config,wallet);const mintA=new PublicKey(item.mint),programId=new PublicKey(item.programId);\n const p=await raydium.launchpad.getRpcPoolInfo({poolId:new PublicKey(item.poolId)});\n const platformData=await connection.getAccountInfo(p.platformId,'confirmed');if(!platformData)throw new Error('Platform fee configuration not found');",
""" if(item.network!==config.network)throw new Error('Token network does not match the connected Solana network');
 const mintA=new PublicKey(item.mint),programId=new PublicKey(item.programId);
 if(!programId.equals(program(config)))throw new Error('This token belongs to a different launch program');
 const expectedPool=getPdaLaunchpadPoolId(programId,mintA,NATIVE_MINT).publicKey;
 if(!expectedPool.equals(new PublicKey(item.poolId)))throw new Error('Pool address does not match the canonical token PDA');
 const raydium=await sdk(connection,config,wallet);
 const p=await raydium.launchpad.getRpcPoolInfo({poolId:expectedPool});
 if(Number(p.status)!==0)throw new Error('Bonding curve is closed. Wait for migration or use a supported swap route.');
 if(!p.mintA.equals(mintA)||!p.mintB.equals(NATIVE_MINT))throw new Error('Live pool mints do not match the requested token/SOL pair');
 if(p.mintDecimalsB!==9)throw new Error('Unexpected SOL decimals in pool');
 const platformData=await connection.getAccountInfo(p.platformId,'confirmed');
 if(!platformData)throw new Error('Platform fee configuration not found');
 if(!platformData.owner.equals(programId))throw new Error('Platform config owner does not match the launch program');""", 'Chain: pool pre-trade checks')
    data[k]=one(data[k],"buyAmount:new BN(amountBaseUnits(amount,9)),slippage:new BN(slippageBps)","buyAmount:new BN(amountBaseUnits(amount,p.mintDecimalsB)),slippage:new BN(slippageBps)", 'Chain: quote decimals')

    k='web/src/App.tsx'
    data[k]=one(data[k],
"import {AppConfig,Launch,callApi,postJson,shorten,ago} from './api';",
"import {AppConfig,Launch,NetworkStatus,callApi,postJson,shorten,ago} from './api';", 'UI: network type')
    data[k]=one(data[k],
"import {PoolView,getPool,launchToken,curveTrade,migratedTrade} from './chain';",
"import {PoolView,getPool,verifyLaunchConfig,launchToken,curveTrade,migratedTrade} from './chain';",'UI: verifier import')
    data[k]=one(data[k],
" const [file,setFile]=useState<File|null>(null);const [imagePreview,setImagePreview]=useState('');const [busy,setBusy]=useState(false);const [receipt,setReceipt]=useState('');const [advanced,setAdvanced]=useState(false);",
""" const [file,setFile]=useState<File|null>(null);const [imagePreview,setImagePreview]=useState('');const [busy,setBusy]=useState(false);const [receipt,setReceipt]=useState('');const [advanced,setAdvanced]=useState(false);
 const [rpcStatus,setRpcStatus]=useState<NetworkStatus|null>(null);const [checking,setChecking]=useState(false);
 async function checkRpc(){setChecking(true);try{setRpcStatus(await callApi<NetworkStatus>('/api/network-status'))}catch(e){notify('RPC check failed: '+(e as Error).message)}finally{setChecking(false)}}""", 'UI: preflight state')
    data[k]=one(data[k],
" async function checkRpc(){setChecking(true);try{setRpcStatus(await callApi<NetworkStatus>('/api/network-status'))}catch(e){notify('RPC check failed: '+(e as Error).message)}finally{setChecking(false)}}",
""" async function checkRpc(){setChecking(true);try{
  const status=await callApi<NetworkStatus>('/api/network-status');
  if(!status.ready){setRpcStatus(status);return}
  try{const verified=await verifyLaunchConfig(connection,config);
   setRpcStatus({...status,reason:'SOL LaunchLab config verified: '+verified.configId.toBase58()});}
  catch(e){setRpcStatus({...status,ready:false,reason:(e as Error).message})}
 }catch(e){notify('RPC check failed: '+(e as Error).message)}finally{setChecking(false)}}""",'UI: full config preflight')
    data[k]=one(data[k],
" setBusy(true);setReceipt('');try{\n  const uploaded=await postJson<{id:string}>('/api/media'",
""" setBusy(true);setReceipt('');try{
  const network=await callApi<NetworkStatus>('/api/network-status');setRpcStatus(network);
  if(!network.ready)throw new Error(network.reason||'Devnet RPC or Raydium program is not ready');
  const uploaded=await postJson<{id:string}>('/api/media'""", 'UI: check before upload')
    data[k]=one(data[k],
"  if(!network.ready)throw new Error(network.reason||'Devnet RPC or Raydium program is not ready');\n  const uploaded=await postJson<{id:string}>('/api/media'",
"""  if(!network.ready)throw new Error(network.reason||'Devnet RPC or Raydium program is not ready');
  await verifyLaunchConfig(connection,config);
  const uploaded=await postJson<{id:string}>('/api/media'""", 'UI: no uploads before config preflight')
    data[k]=one(data[k],
"<div className=\"panel-label\">Launch settings</div><div className=\"property\"><span>Network</span>",
"""<div className="panel-label">Launch settings</div><div className="property"><span>Network</span>""", 'UI: launch sidebar anchor')  # explicit verify only
    data[k]=one(data[k],
"<div className=\"property\"><span>Fee</span><b>Set by the protocol</b></div><Banner>All network fees",
"""<div className="property"><span>Fee</span><b>Set by the protocol</b></div><div className="property"><span>RPC / Program</span><b>{rpcStatus?(rpcStatus.ready?'Ready for config check': 'Unavailable'):'Not checked'}</b></div><button className="button full" type="button" onClick={checkRpc} disabled={checking}>{checking?'Checking network…':'Check Devnet connection'}</button>{rpcStatus&&<p className={rpcStatus.ready?'micro-note':'warning-text'}>{rpcStatus.reason}{rpcStatus.slot!==null?` · Slot ${rpcStatus.slot}`:''}</p>}<Banner>All network fees""", 'UI: show preflight')
    # Automatic routing by verified on-chain pool lifecycle instead of unsafe manual selection
    data[k]=one(data[k],
"const [side,setSide]=useState<'buy'|'sell'>('buy');const [route,setRoute]=useState<'curve'|'jupiter'>('curve');const [amount,setAmount]=useState('0.1');",
"const [side,setSide]=useState<'buy'|'sell'>('buy');const [amount,setAmount]=useState('0.1');", 'UI: remove manual route state')
    data[k]=one(data[k],
" const display=useMemo(()=>item,[item]);if(!display)return",
""" const route=pool?.status===0?'curve':pool?.status===2?'jupiter':null;
 const routeEnabled=route==='curve' || (route==='jupiter' && config.network==='mainnet-beta' && config.mainnetTradingEnabled && config.tradeEnabled);
 const poolStatus=pool?.status===0?'Bonding curve active':pool?.status===1?'Waiting for migration':pool?.status===2?'Migrated to AMM':'Loading pool status';
 const display=useMemo(()=>item,[item]);if(!display)return""", 'UI: automatic route derived from pool status')
    data[k]=one(data[k],
"async function trade(){if(!display){notify('Token not found');return}if(!wallet.publicKey){notify('Connect wallet');return}if(config.network==='mainnet-beta'&&!config.mainnetTradingEnabled){notify('Mainnet trading is disabled until reviewed');return}if(route==='jupiter'&&!config.tradeEnabled){notify('Jupiter swaps are not enabled');return}setBusy(true);",
"""async function trade(){if(!display){notify('Token not found');return}if(!wallet.publicKey){notify('Connect wallet');return}if(!route||!routeEnabled){notify(poolStatus+'. Trading is unavailable for this token on this network.');return}if(config.network==='mainnet-beta'&&!config.mainnetTradingEnabled){notify('Mainnet trading is disabled until reviewed');return}setBusy(true);""", 'UI: fail closed for untradeable pools')
    data[k]=one(data[k],
"<label>Route <select value={route} onChange={e=>setRoute(e.target.value as any)}><option value=\"curve\">Bonding curve (before migration)</option><option value=\"jupiter\">Jupiter (after migration)</option></select></label>",
"""<div className="property"><span>Pool status</span><b>{poolStatus}</b></div><div className="property"><span>Trading route</span><b>{route==='curve'?'Raydium bonding curve':route==='jupiter'?'Jupiter (post-migration)':'Unavailable'}</b></div>{pool?.status===1&&<Banner>Curve trading has ended. Migration is pending; no trades can be submitted here.</Banner>}{pool?.status===2&&!routeEnabled&&<Banner>This token graduated. A supported post-migration swap route is not available on this network.</Banner>}""", 'UI: safe status instead of manual route selector')
    data[k]=one(data[k],
"disabled={busy||!wallet.publicKey||config.network==='mainnet-beta'&&!config.mainnetTradingEnabled||route==='jupiter'&&!config.tradeEnabled}",
"disabled={busy||!wallet.publicKey||!routeEnabled||config.network==='mainnet-beta'&&!config.mainnetTradingEnabled}", 'UI: locked route button')
    data[k]=one(data[k],
"{pool?`${pool.priceSol.toExponential(5)} SOL`:'No data'}",
"{pool?(pool.status===0?`${pool.priceSol.toExponential(5)} SOL`:'Not on bonding curve'):'No data'}", 'UI: no fake curve price after migration')
    data[k]=one(data[k],
"const update=async()=>{for(const l of items.slice(0,15))",
"const update=async()=>{for(const l of (route.page==='token' && items.find(t=>t.mint===route.mint) ? [items.find(t=>t.mint===route.mint)!, ...items.filter(t=>t.mint!==route.mint).slice(0,14)] : items.slice(0,15)))", 'UI: always update selected token even past top 15')
    data[k]=one(data[k],
" },[items,connection,config]);",
" },[items,connection,config,route.page,route.mint]);", 'UI: selected token invalidation')
    data[k]=one(data[k],
"[...old.slice(-60),p.priceSol]",
"p.status===0 && Number.isFinite(p.priceSol) ? [...old.slice(-60),p.priceSol] : old", 'UI: ignore migrated/invalid quote in session chart')

    k='tests/server.test.mjs'
    data[k] += """
test('Live network preflight fails closed for an unconfigured program without contacting RPC',async()=>{
 const old=process.env.RAYDIUM_PROGRAM_ID;
 process.env.RAYDIUM_PROGRAM_ID='invalid';
 const server=makeServer();await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 try{
  const res=await fetch(`http://127.0.0.1:${server.address().port}/api/network-status`);
  assert.equal(res.status,200);
  const body=await res.json();
  assert.equal(body.ready,false);
  assert.equal(body.rpcReachable,false);
  assert.equal(body.programDeployed,false);
  assert.match(body.reason,/RAYDIUM_PROGRAM_ID/);
 }finally{
  await new Promise(resolve=>server.close(resolve));
  if(old===undefined)delete process.env.RAYDIUM_PROGRAM_ID;
  else process.env.RAYDIUM_PROGRAM_ID=old;
 }
});
"""
    return {paths[k]:v for k,v in data.items()}


def main():
    root=next((p for p in ROOTS if (p/'server/app.mjs').exists() and (p/'web/src/App.tsx').exists()),None)
    if root is None:
        print('ERROR: Run from the existing ORBIT Replit workspace, not another project.',file=sys.stderr)
        return 2
    try:
        changed=patch(root)
    except Exception as exc:
        print('ERROR:', exc, file=sys.stderr)
        return 3
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup=root/'.orbit-backups'/('stage2-'+stamp)
    for path in changed:
        dest=backup/path.relative_to(root)
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,dest)
    for path,content in changed.items():
        path.write_text(content,encoding='utf-8')
        print('Patched:',path.relative_to(root))
    print('Backups:', backup)
    print('No packages installed, no process restarted, no Git commit or push.')
    return 0
if __name__=='__main__':
    raise SystemExit(main())
