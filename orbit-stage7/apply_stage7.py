#!/usr/bin/env python3
"""ORBIT Stage 7: safer mobile wallet signing and a no-broadcast wallet diagnostic.

Applies only to the existing ORBIT source after Stage 6. This script does not
execute transactions, install packages, restart, deploy, publish, or push Git.
"""
from pathlib import Path
from datetime import datetime, timezone
import shutil, sys, re

ROOT = Path.cwd() / 'artifacts/orbit-launchpad/original/orbit-solana-launchpad'
CHAIN = ROOT / 'web/src/chain.ts'
APP = ROOT / 'web/src/App.tsx'
MARKER = '// ORBIT_STAGE7_MOBILE_SIGNING'


def replace1(s, old, new, label):
    n = s.count(old)
    if n != 1:
        raise ValueError(f'{label}: expected 1 matching fragment; found {n}. No files changed.')
    return s.replace(old, new, 1)


def run():
    if not CHAIN.is_file() or not APP.is_file():
        raise ValueError('Expected ORBIT workspace not found. Use /home/runner/workspace.')
    chain, app = CHAIN.read_text(), APP.read_text()
    if MARKER in chain:
        if 'ORBIT_STAGE7_WALLET_TEST' in app:
            print('Stage 7 already installed; no changes.')
            return
        raise ValueError('Partial Stage 7 installation detected; no changes.')
    if 'ORBIT_STAGE6_SIGNING_PREFLIGHT' not in chain or 'ORBIT_STAGE5_LAUNCH_DIAGNOSTICS' not in app:
        raise ValueError('Stages 5 and 6 must be installed first; no changes.')

    chain = replace1(chain,
        "import {Keypair,PublicKey,VersionedTransaction} from '@solana/web3.js';",
        "import {Keypair,PublicKey,VersionedTransaction,Transaction,TransactionMessage,SystemProgram} from '@solana/web3.js';",
        'web3 imports')

    chain = replace1(chain,
        " return Raydium.load({owner,connection,cluster:cluster(config) as any,signAllTransactions:wallet?.signAllTransactions?.bind(wallet),disableFeatureCheck:true,disableLoadToken:true,blockhashCommitment:'confirmed'});",
        """ // ORBIT_STAGE7_MOBILE_SIGNING
 // Mobile wallet injection can support signTransaction without reliably
 // supporting signAllTransactions. Use one explicit signature request per
 // transaction on mobile; never retry a failed signing request automatically.
 const mobile=typeof navigator!=='undefined' && /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
 const signAll=mobile && wallet?.signTransaction
  ? async <T extends Transaction|VersionedTransaction>(txs:T[]):Promise<T[]>=>{
     const signed:T[]=[];
     for(const tx of txs){signed.push(await wallet.signTransaction!(tx));}
     return signed;
    }
  : wallet?.signAllTransactions?.bind(wallet);
 return Raydium.load({owner,connection,cluster:cluster(config) as any,signAllTransactions:signAll,disableFeatureCheck:true,disableLoadToken:true,blockhashCommitment:'confirmed'});""",
        'SDK mobile wallet signature transport')

    needle = 'export async function launchToken(connection:Connection,config:AppConfig,wallet:WalletContextState,input:{name:string;symbol:string;uri:string}){'
    helper = """// A wallet-only diagnostic. An unsigned 0-lamport, self-directed transfer
// is created locally, but is NEVER broadcast. The wallet must still approve
// signing. This diagnostic cannot create a token or charge any network fee.
export async function checkWalletSigning(connection:Connection,config:AppConfig,wallet:WalletContextState):Promise<void>{
 if(config.network!=='devnet')throw new Error('The signature test is restricted to Devnet.');
 if(!wallet.publicKey||!wallet.signTransaction)throw new Error('The connected wallet does not support signing a single transaction.');
 const block=await connection.getLatestBlockhash('confirmed');
 const instruction=SystemProgram.transfer({fromPubkey:wallet.publicKey,toPubkey:wallet.publicKey,lamports:0});
 const message=new TransactionMessage({payerKey:wallet.publicKey,recentBlockhash:block.blockhash,instructions:[instruction]}).compileToV0Message();
 const tx=new VersionedTransaction(message);
 const signed=await wallet.signTransaction(tx);
 const sig=signed.signatures?.[0];
 if(!sig||!sig.some(v=>v!==0))throw new Error('Wallet returned a transaction without the fee-payer signature.');
 // Intentionally NO sendTransaction, sendRawTransaction, or execute() here.
}

"""
    chain = replace1(chain, needle, helper + needle, 'Wallet-only signature diagnostic')

    imports = re.findall(r"import \{([^}]+)\} from './chain';",app)
    if len(imports)!=1 or 'checkWalletSigning' in imports[0] or 'launchToken' not in imports[0]:
        raise ValueError('Expected one existing import from chain.ts containing launchToken.')
    app = replace1(app,
        "import {"+imports[0]+"} from './chain';",
        "import {"+imports[0].rstrip()+",checkWalletSigning} from './chain';",
        'App wallet test import')

    creator_at=app.index('function Creator(')
    details_at=app.index('function TokenDetails(',creator_at)
    sec=app[creator_at:details_at]
    if 'ORBIT_STAGE7_WALLET_TEST' in sec:
        raise ValueError('Stage 7 UI already installed, unexpected chain state')

    sec=replace1(sec,
        ' async function create(e:React.FormEvent){',
        """ // ORBIT_STAGE7_WALLET_TEST: no broadcast; requires a wallet approval.
 async function testWalletSignature(){
  if(busy)return;
  setBusy(true);
  setLaunchError('');
  try{
   await checkWalletSigning(connection,config,wallet);
   setLaunchError('Wallet signature test: PASSED. Phantom signed a Devnet version-0 transaction locally. Nothing was sent to Solana. A failing launch may involve transaction-specific instructions or the Raydium SDK.');
   notify('Wallet signature test passed. No transaction was sent.');
  }catch(err){
   const e=err as any;
   setLaunchError(`Wallet signature test: FAILED (no transaction sent).\\n${String(e?.name||'Error')}: ${String(e?.message||err)}\\nIf this failed in a Replit browser, open ORBIT inside the official Phantom in-app browser and verify Testnet Mode is set to Solana Devnet.`);
   notify('Wallet signature test failed. No transaction was sent.');
  }finally{setBusy(false)}
 }
 async function create(e:React.FormEvent){""",
        'Create form wallet-only signature handler')

    marker = "{wallet.publicKey?<button className=\"button green-button full\" type=\"submit\""
    sec=replace1(sec, marker,
        "{wallet.publicKey&&config.network==='devnet'&&<button className=\"button full\" type=\"button\" disabled={busy} onClick={testWalletSignature}>Test wallet signature (no broadcast)</button>}"+marker,
        'Create form wallet-only test button')
    app=app[:creator_at]+sec+app[details_at:]

    assert MARKER in chain and 'ORBIT_STAGE7_WALLET_TEST' in app, 'markers missing'
    assert chain.count('signed.push(await wallet.signTransaction!')==1, 'mobile signing count mismatch'
    assert chain.count('export async function checkWalletSigning(')==1, 'wallet test count mismatch'
    assert app.count('onClick={testWalletSignature}')==1, 'button count mismatch'
    # Do not mutate either target until all patches and assertions have passed.
    dest=ROOT/'.orbit-backups'/('stage7-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    dest.mkdir(parents=True,exist_ok=False)
    shutil.copy2(CHAIN,dest/'chain.ts')
    shutil.copy2(APP,dest/'App.tsx')
    CHAIN.write_text(chain)
    APP.write_text(app)
    print('STAGE 7 PATCH: INSTALLED')
    print('Mobile Raydium SDK: uses single-transaction signing sequentially')
    print('Wallet signing diagnostic: requires wallet approval but never broadcasts')
    print('Backup:',dest)
    print('No process restart, package install, Git push, token creation or Republish')

if __name__=='__main__':
    try: run()
    except Exception as e:
        print('STAGE 7 STOPPED:',e,file=sys.stderr)
        sys.exit(1)
