#!/usr/bin/env python3
"""ORBIT Stage 9: diagnose Phantom signing with wallet-first co-signing.

No network requests or signing occur during installation. Existing launch flow
remains unchanged. The diagnostic never broadcasts or creates a token.
"""
from pathlib import Path
from datetime import datetime, timezone
import shutil
import sys

ROOT = Path.cwd() / 'artifacts/orbit-launchpad/original/orbit-solana-launchpad'
CHAIN = ROOT/'web/src/chain.ts'
APP = ROOT/'web/src/App.tsx'
MARK = 'ORBIT_STAGE9_WALLET_FIRST_COSIGN'


def replace_one(s, before, after, label):
    hits = s.count(before)
    if hits != 1:
        raise ValueError(f'{label}: expected one source match, found {hits}. No files changed.')
    return s.replace(before, after, 1)


def run():
    if not CHAIN.is_file() or not APP.is_file():
        raise ValueError('ORBIT workspace not found. Run in /home/runner/workspace.')
    chain, app = CHAIN.read_text(), APP.read_text()
    if MARK in chain:
        if 'Test Raydium wallet-first signature (no broadcast)' in app:
            print('Stage 9 is already installed. No changes.')
            return
        raise ValueError('Partial Stage 9 installation. No changes.')
    if '// ORBIT_STAGE8_RAYDIUM_NO_BROADCAST' not in chain or 'ORBIT_STAGE8_RAYDIUM_TEST_UI' not in app:
        raise ValueError('Stage 8 is required. No changes.')
    before = chain.index('// ORBIT_STAGE8_RAYDIUM_NO_BROADCAST')
    after = chain.index('export async function launchToken(', before)
    part = chain[before:after]
    part = replace_one(part,
        ''' const tx=built.transactions[0];
 if(!(tx instanceof VersionedTransaction))
  throw new Error('Expected a V0 launch transaction; Raydium returned another format.');
 const n=tx.message.header.numRequiredSignatures;''',
        ''' // ORBIT_STAGE9_WALLET_FIRST_COSIGN
 // Some mobile wallets reject partially-signed multi-signer transactions.
 // Take ONLY the message from Raydium and start with zero signatures.
 // Let Phantom sign the wallet slot, then sign the ephemeral mint locally.
 // This is a diagnostic and is NEVER submitted to Solana.
 const sdkTx=built.transactions[0];
 if(!(sdkTx instanceof VersionedTransaction))
  throw new Error('Expected a V0 launch transaction; Raydium returned another format.');
 const sdkSignatures=sdkTx.signatures.filter(sig=>sig.some(b=>b!==0)).length;
 const tx=new VersionedTransaction(sdkTx.message);
 const n=tx.message.header.numRequiredSignatures;''',
        'Clone unsigned V0 message')
    part = replace_one(part,
        ''' // The create transaction also requires a new mint keypair signature.
 // This keypair is ephemeral and never stored, uploaded or transmitted.
 if(signers.some(k=>k.equals(mint.publicKey)))tx.sign([mint]);
 const bytes=tx.serialize().length;''',
        ''' // The new mint keypair is never sent to the wallet or server.
 // Unlike Stage 8, do NOT pre-sign before Phantom sees the transaction.
 const mintIndex=signers.findIndex(k=>k.equals(mint.publicKey));
 if(mintIndex<0)throw new Error('The Raydium transaction does not request the new mint signature.');
 const walletIndex=signers.findIndex(k=>k.equals(walletKey));
 if(walletIndex<0)throw new Error('The connected wallet is not a signer.');
 const bytes=tx.serialize().length;''',
        'Remove pre-signed mint')
    part = replace_one(part,
        ''' let signed:VersionedTransaction;
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
 return 'Raydium V0 transaction: BUILT ('+bytes+' bytes, '+n+' signers; '+built.transactions.length+' SDK transaction(s)). First transaction simulation: PASSED. Phantom signed the actual launch transaction locally: PASSED. No transaction sent, no token created.';''',
        ''' const expectedMessage=tx.message.serialize();
 let signed:VersionedTransaction;
 try{signed=await wallet.signTransaction(tx) as VersionedTransaction;}
 catch(e){
  const err=e as any;
  throw new Error('Unsigned Raydium launch signing failed. Phantom may reject the launch instructions or multi-signer format (not just pre-signing). Required signers: '+n+'; transaction bytes: '+bytes+'; SDK supplied '+sdkSignatures+' signature(s). Wallet error: '+String(err?.name||'Error')+' — '+String(err?.message||e)+(err?.cause?.message?' | Cause: '+err.cause.message:''));
 }
 if(!(signed instanceof VersionedTransaction))
  throw new Error('Wallet returned a different transaction type.');
 const actualMessage=signed.message.serialize();
 if(actualMessage.length!==expectedMessage.length||actualMessage.some((v,i)=>v!==expectedMessage[i]))
  throw new Error('Wallet changed the Raydium message. The diagnostic refused to co-sign.');
 const walletSig=signed.signatures?.[walletIndex]?.slice();
 if(!walletSig||!walletSig.some(b=>b!==0))
  throw new Error('Wallet did not sign its required signer slot.');
 signed.sign([mint]); // Mint keypair co-signs AFTER wallet approval.
 const mintSig=signed.signatures?.[mintIndex];
 if(!mintSig||!mintSig.some(b=>b!==0))
  throw new Error('Local mint signature was not added.');
 if(signed.signatures[walletIndex].some((v,i)=>v!==walletSig[i]))
  throw new Error('Local mint co-signing modified the wallet signature.');
 // No execute, submit, send, registration, or metadata writes anywhere here.
 return 'Raydium V0 transaction: BUILT ('+bytes+' bytes, '+n+' signers; '+built.transactions.length+' SDK transaction(s); SDK originally had '+sdkSignatures+' signature(s)). Simulation: PASSED. Unsigned Raydium message accepted by Phantom: PASSED. Local mint co-signature added afterward: PASSED. No transaction sent and no token created.';''',
        'New wallet-first signature handling')
    chain = chain[:before]+part+chain[after:]
    app = replace_one(app,
        'Test Raydium launch signature (no broadcast)',
        'Test Raydium wallet-first signature (no broadcast)',
        'Rename diagnostic button')
    # Strict validation *before* writing anything.
    assert chain.count(MARK)==1
    assert app.count('Test Raydium wallet-first signature (no broadcast)')==1
    helper=chain.split('// ORBIT_STAGE8_RAYDIUM_NO_BROADCAST',1)[1].split('export async function launchToken(',1)[0]
    for forbidden in ['await execute(', '.sendTransaction(', '.sendRawTransaction(', 'sendAndConfirm:', '/api/launches', 'await postJson(']:
        assert forbidden not in helper, forbidden
    assert helper.index('await wallet.signTransaction(tx)') < helper.index('signed.sign([mint])')
    backup=ROOT/'.orbit-backups'/('stage9-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    backup.mkdir(parents=True, exist_ok=False)
    shutil.copy2(CHAIN,backup/'chain.ts')
    shutil.copy2(APP,backup/'App.tsx')
    CHAIN.write_text(chain)
    APP.write_text(app)
    print('ORBIT Stage 9 installed: wallet-first multi-signer no-broadcast diagnostic.')
    print('Backup:',backup)
    print('Existing Create Token execution unchanged; no transfers, restarts, Git push or Republish.')

if __name__=='__main__':
    try: run()
    except Exception as exc:
        print('ORBIT STAGE 9 STOPPED:',exc,file=sys.stderr)
        sys.exit(1)
