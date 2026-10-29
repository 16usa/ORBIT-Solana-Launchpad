#!/usr/bin/env python3
"""ORBIT Stage 6 — inspect launch transactions before asking Phantom to sign.

Applies only to previously installed Stage 4/5 workspace.
No signing, RPC transactions, restarts, process changes or Git push.
"""
from pathlib import Path
from datetime import datetime, timezone
import shutil
import sys

ROOT = Path.cwd() / 'artifacts/orbit-launchpad/original/orbit-solana-launchpad'
CHAIN = ROOT / 'web/src/chain.ts'
APP = ROOT / 'web/src/App.tsx'
MARKER = 'ORBIT_STAGE6_SIGNING_PREFLIGHT'


def replace_once(src: str, before: str, after: str, description: str) -> str:
    count = src.count(before)
    if count != 1:
        raise RuntimeError(f'{description}: expected one source occurrence, found {count}. No files were changed.')
    return src.replace(before, after, 1)


def run():
    if not CHAIN.is_file() or not APP.is_file():
        raise RuntimeError('ORBIT source files not found; run from /home/runner/workspace.')
    source = CHAIN.read_text('utf-8')
    app = APP.read_text('utf-8')
    if MARKER in source:
        print('ORBIT Stage 6 already installed. No changes made.')
        return
    if 'ORBIT_STAGE4_PLATFORM_PREFLIGHT' not in source or 'ORBIT_STAGE5_LAUNCH_DIAGNOSTICS' not in app:
        raise RuntimeError('Stages 4 and 5 are required. No changes made.')
    original = source

    before = " const raydium=await sdk(connection,config,wallet);\n const programId=program(config);const mint=Keypair.generate();"
    after = """ // ORBIT_STAGE6_SIGNING_PREFLIGHT: check wallet capability and test-SOL balance before constructing a transaction.
 const versionSupport=wallet.wallet?.adapter?.supportedTransactionVersions;
 if(versionSupport&&!versionSupport.has(0))throw new Error('The selected wallet cannot sign Solana version-0 transactions. Choose a wallet supporting version 0.');
 const balance=await connection.getBalance(wallet.publicKey,'confirmed');
 if(balance===0)throw new Error('This wallet has 0 SOL on Devnet. Fund it with test SOL, then retry. Do not use mainnet funds.');
 const raydium=await sdk(connection,config,wallet);
 const programId=program(config);const mint=Keypair.generate();"""
    source = replace_once(source,before,after,'Wallet and balance preflight')

    before = " const {execute,extInfo}=await raydium.launchpad.createLaunchpad({"
    after = " const {execute,extInfo,transactions}=await raydium.launchpad.createLaunchpad({"
    source = replace_once(source,before,after,'Raydium transaction access')

    before = """ const {txIds}=await execute({sequentially:true});
 if(!Array.isArray(txIds)||!txIds.length)throw new Error('No confirmed creation transaction returned');"""
    after = """ // Simulate the FIRST transaction only: later transactions may depend on it being confirmed.
 // Preflight simulation is not a wallet signature and never broadcasts a transaction.
 if(!Array.isArray(transactions)||transactions.length===0)throw new Error('Raydium did not build any launch transactions.');
 const first=transactions[0];
 if(first instanceof VersionedTransaction){
  const payer=first.message.staticAccountKeys[0];
  if(!payer?.equals(wallet.publicKey))throw new Error('Launch transaction fee payer differs from your connected wallet. Signing blocked.');
  let simulated;
  try{
   simulated=await connection.simulateTransaction(first,{sigVerify:false,replaceRecentBlockhash:true,commitment:'confirmed'});
  }catch(e){
   throw new Error(`Devnet transaction preflight RPC failed: ${e instanceof Error?e.message:String(e)}`,{cause:e});
  }
  if(simulated.value.err){
   const logs=(simulated.value.logs||[]).slice(-12).join(' | ');
   throw new Error(`Devnet launch simulation failed BEFORE wallet approval: ${JSON.stringify(simulated.value.err)}${logs?' | Program logs: '+logs:''}`);
  }
 }
 let txIds:string[];
 try{
  ({txIds}=await execute({sequentially:true}));
 }catch(e){
  const error=e as any;
  const name=String(error?.name||'');
  const message=String(error?.message||e);
  if(name.includes('WalletSign')||message==='Unexpected error'){
   const detail=String(error?.cause?.message||error?.reason||'');
   throw new Error(`Phantom or the wallet adapter could not sign the Devnet launch transaction (${name||'wallet error'}: ${message}). Check that Phantom Testnet Mode is enabled for Solana Devnet, that the wallet has Devnet SOL, and that no previous launch was confirmed. Do not keep retrying without checking transaction activity.${detail?' Details: '+detail:''}`,{cause:e});
  }
  throw e;
 }
 if(!Array.isArray(txIds)||!txIds.length)throw new Error('No confirmed creation transaction returned');"""
    source = replace_once(source,before,after,'Preflight simulation and signing error')

    assert MARKER in source
    assert source.count('connection.simulateTransaction(first')==1
    assert source.count('await execute({sequentially:true})')==1
    if original == source: raise RuntimeError('No changes generated.')
    backupdir = ROOT/'.orbit-backups'/('stage6-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    backupdir.mkdir(parents=True,exist_ok=False)
    shutil.copy2(CHAIN,backupdir/'chain.ts')
    CHAIN.write_text(source,encoding='utf-8')
    print('ORBIT Stage 6 installed: Devnet transaction preflight and wallet signing diagnostics.')
    print('Backup:',backupdir)
    print('No transactions sent, no wallet signed, no process restarted, no Git push, no Republish.')

if __name__=='__main__':
    try: run()
    except Exception as error:
        print('STAGE 6 INSTALL STOPPED:',error,file=sys.stderr)
        sys.exit(1)
