#!/usr/bin/env python3
"""ORBIT Stage 8: safe, no-broadcast Raydium launch transaction signature test.

Uses existing ORBIT Stage 7 files; never deploys, restarts, signs, broadcasts,
or creates a real token. Wallet signing happens only when the user later clicks
its diagnostic button inside ORBIT Development.
"""
from pathlib import Path
from datetime import datetime, timezone
import shutil
import sys

ROOT = Path.cwd() / 'artifacts/orbit-launchpad/original/orbit-solana-launchpad'
CHAIN = ROOT / 'web/src/chain.ts'
APP = ROOT / 'web/src/App.tsx'
MARK = '// ORBIT_STAGE8_RAYDIUM_NO_BROADCAST'


def replace_one(source, old, new, label):
    n = source.count(old)
    if n != 1:
        raise RuntimeError(f'{label}: expected exactly one match, found {n}. No files written.')
    return source.replace(old, new, 1)


def run():
    if not CHAIN.is_file() or not APP.is_file():
        raise RuntimeError('Not in ORBIT workspace. cd /home/runner/workspace first.')
    c, a = CHAIN.read_text(), APP.read_text()
    if MARK in c and 'ORBIT_STAGE8_RAYDIUM_TEST_UI' in a:
        print('ORBIT Stage 8 already installed — no changes.')
        return
    if MARK in c or 'ORBIT_STAGE8_RAYDIUM_TEST_UI' in a:
        raise RuntimeError('Partial Stage 8 detected. No changes made.')
    if '// ORBIT_STAGE7_MOBILE_SIGNING' not in c or 'ORBIT_STAGE7_WALLET_TEST' not in a:
        raise RuntimeError('Install ORBIT Stage 7 first. No changes made.')

    new_fn = '''// ORBIT_STAGE8_RAYDIUM_NO_BROADCAST
// Constructs the actual Raydium CreateLaunchpad V0 transaction, preflights
// the first transaction, and requests a wallet signature. No transaction is
// submitted, no metadata is uploaded, and the generated test mint is discarded.
// The URI is deliberately inert: this must NEVER be used for a real launch.
export async function checkRaydiumLaunchSigning(
 connection:Connection,config:AppConfig,wallet:WalletContextState
):Promise<string>{
 if(config.network!=='devnet')throw new Error('Raydium signing diagnostic is Devnet-only.');
 if(!config.launchEnabled)throw new Error(config.launchBlockReason||'Devnet launch is unavailable.');
 if(!wallet.publicKey||!wallet.signTransaction)throw new Error('Connect a wallet with signTransaction support.');
 const platformId=await requireLaunchPlatform(connection,config,wallet.publicKey);
 const {configId,configInfo}=await verifyLaunchConfig(connection,config);
 const raydium=await sdk(connection,config,wallet);
 const mint=Keypair.generate();
 const quote=await raydium.token.getTokenInfo(configInfo.mintB);
 const built=await raydium.launchpad.createLaunchpad({
  programId:program(config),mintA:mint.publicKey,
  name:'ORBIT Diagnostic Only',symbol:'ORBDIAG',
  uri:'https://example.com/orbit-diagnostic-never-published.json',
  decimals:6,migrateType:'cpmm',configId,configInfo,
  mintBDecimals:quote.decimals,createOnly:true,
  buyAmount:new BN(1000),slippage:new BN(100),
  extraSigners:[mint],txVersion:TxVersion.V0,platformId
 } as any);
 if(!Array.isArray(built.transactions)||built.transactions.length===0)
  throw new Error('Raydium SDK returned no launch transactions.');
 const tx=built.transactions[0];
 if(!(tx instanceof VersionedTransaction))
  throw new Error('Expected a V0 launch transaction; Raydium returned another format.');
 const n=tx.message.header.numRequiredSignatures;
 const signers=tx.message.staticAccountKeys.slice(0,n);
 const walletKey=wallet.publicKey;
 if(!signers[0]?.equals(walletKey))
  throw new Error('Raydium launch fee payer differs from the connected wallet.');
 if(!signers.some(k=>k.equals(walletKey)))
  throw new Error('Connected wallet is not listed as a required signer.');
 const unrecognized=signers.filter(k=>!k.equals(walletKey)&&!k.equals(mint.publicKey));
 if(unrecognized.length)
  throw new Error('Raydium requires an unexpected signer: '+unrecognized.map(k=>k.toBase58()).join(', '));
 // The create transaction also requires a new mint keypair signature.
 // This keypair is ephemeral and never stored, uploaded or transmitted.
 if(signers.some(k=>k.equals(mint.publicKey)))tx.sign([mint]);
 const bytes=tx.serialize().length;
 if(bytes>1232)throw new Error('Raydium transaction is oversized ('+bytes+' bytes).');
 const simulation=await connection.simulateTransaction(tx,{
  sigVerify:false,replaceRecentBlockhash:true,commitment:'confirmed'
 });
 if(simulation.value.err){
  const logs=(simulation.value.logs||[]).slice(-14).join(' | ');
  throw new Error('Raydium first transaction simulation failed: '+JSON.stringify(simulation.value.err)+(logs?' | '+logs:''));
 }
 let signed:VersionedTransaction;
 try{signed=await wallet.signTransaction(tx) as VersionedTransaction;}
 catch(e){
  const err=e as any;
  throw new Error('Phantom refused the *actual Raydium launch transaction* (without broadcast): '+String(err?.name||'Error')+' — '+String(err?.message||e)+(err?.cause?.message?' | Cause: '+err.cause.message:''));
 }
 if(!(signed instanceof VersionedTransaction))
  throw new Error('Wallet returned a different transaction type.');
 const walletSig=signed.signatures?.[0];
 if(!walletSig||!walletSig.some(b=>b!==0))
  throw new Error('The wallet did not sign the Raydium transaction fee payer.');
 // Intentionally no execute, sendTransaction, sendRawTransaction, or register.
 return 'Raydium V0 transaction: BUILT ('+bytes+' bytes, '+n+' signers; '+built.transactions.length+' SDK transaction(s)). First transaction simulation: PASSED. Phantom signed the actual launch transaction locally: PASSED. No transaction sent, no token created.';
}

'''
    c=replace_one(c,'export async function launchToken(',new_fn+'export async function launchToken(', 'Insert no-broadcast helper')
    import_needle="import {PoolView,getPool,verifyLaunchConfig,launchToken,curveTrade,migratedTrade,requireLaunchPlatform,checkWalletSigning} from './chain';"
    import_new="import {PoolView,getPool,verifyLaunchConfig,launchToken,curveTrade,migratedTrade,requireLaunchPlatform,checkWalletSigning,checkRaydiumLaunchSigning} from './chain';"
    a=replace_one(a,import_needle,import_new,'App chain.ts import')
    # Restrict UI changes to Creator component only.
    start=a.index('function Creator(')
    end=a.index('function TokenDetails(',start)
    creator=a[start:end]
    ui_helper=''' // ORBIT_STAGE8_RAYDIUM_TEST_UI: builds and signs a real Raydium tx locally without sending it.
 async function testRaydiumSigning(){
  if(busy)return;
  setBusy(true);setLaunchError('');
  try{
   const result=await checkRaydiumLaunchSigning(connection,config,wallet);
   setLaunchError('Raydium launch signing test: PASSED.\\n'+result);
   notify('Raydium launch signing test passed. No transaction sent.');
  }catch(err){
   const e=err as any;
   setLaunchError('Raydium launch signing test: FAILED (no transaction sent).\\n'+String(e?.name||'Error')+': '+String(e?.message||err));
   notify('Raydium launch test failed. No transaction sent.');
  }finally{setBusy(false)}
 }
'''
    creator=replace_one(creator,' async function create(e:React.FormEvent){',ui_helper+' async function create(e:React.FormEvent){','Creator diagnostic handler')
    needle="{wallet.publicKey&&config.network==='devnet'&&<button className=\"button full\" type=\"button\" disabled={busy} onClick={testWalletSignature}>Test wallet signature (no broadcast)</button>}"
    replacement=needle+"{wallet.publicKey&&config.network==='devnet'&&<button className=\"button full\" type=\"button\" disabled={busy} onClick={testRaydiumSigning}>Test Raydium launch signature (no broadcast)</button>}"
    creator=replace_one(creator,needle,replacement,'Creator no-broadcast button')
    a=a[:start]+creator+a[end:]
    assert MARK in c and 'ORBIT_STAGE8_RAYDIUM_TEST_UI' in a
    assert a.count('onClick={testRaydiumSigning}')==1
    check_section=c.split(MARK,1)[1].split('export async function launchToken(',1)[0]
    for forbidden in ['.sendTransaction(','.sendRawTransaction(', 'await execute(', 'sendAndConfirm:']:
        assert forbidden not in check_section,forbidden
    backup=ROOT/'.orbit-backups'/('stage8-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    backup.mkdir(parents=True,exist_ok=False)
    shutil.copy2(CHAIN,backup/'chain.ts')
    shutil.copy2(APP,backup/'App.tsx')
    CHAIN.write_text(c)
    APP.write_text(a)
    print('ORBIT Stage 8 installed; read-only Raydium launch signature test added.')
    print('Backup:',backup)
    print('No transaction, no package changes, no restart, no GitHub push, no Republish.')

if __name__=='__main__':
    try:run()
    except Exception as e:
        print('ORBIT STAGE 8 STOPPED:',e,file=sys.stderr)
        sys.exit(1)
