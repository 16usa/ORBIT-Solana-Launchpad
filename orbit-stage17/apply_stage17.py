#!/usr/bin/env python3
"""ORBIT Stage 17: canonical, no-broadcast verification of Phantom modified legacy tx.
Run from /home/runner/workspace. Only edits local no-broadcast diagnostic.
Does not restart, publish, push, or send a transaction.
"""
from pathlib import Path
from datetime import datetime,timezone
import os,shutil,sys,tempfile

ROOT=Path.cwd()/'artifacts/orbit-launchpad/original/orbit-solana-launchpad'
CHAIN=ROOT/'web/src/chain.ts'
TAG='ORBIT_STAGE17_CANONICAL_LEGACY_MATCH'
OLD_IMPORT="import {Keypair,PublicKey,VersionedTransaction,Transaction,TransactionMessage,SystemProgram} from '@solana/web3.js';"
NEW_IMPORT="import {Keypair,PublicKey,VersionedTransaction,Transaction,TransactionInstruction,TransactionMessage,SystemProgram} from '@solana/web3.js';"
OLD_COMPARE="""  const originalRaydiumUnchanged=tail.length===beforeInstructions.length&&
   tail.every((ix,i)=>ix.program===beforeInstructions[i].program&&
    ix.accounts===beforeInstructions[i].accounts&&
    ix.data===beforeInstructions[i].data);"""
NEW_COMPARE="""  // ORBIT_STAGE17_CANONICAL_LEGACY_MATCH
  // Some wallets deserialize/rebuild instructions and normalize AccountMeta
  // flags. Do NOT trust a relaxed comparison: reconstruct the exact *message*
  // from the original instruction and the two bounded ComputeBudget extras.
  const originalProgramSame=tail.length===beforeInstructions.length&&
   tail.every((ix,i)=>ix.program===beforeInstructions[i].program);
  const originalAddressesSame=tail.length===beforeInstructions.length&&
   tail.every((ix,i)=>{
    const before=beforeInstructions[i].accounts.split('|').filter(Boolean).map(x=>x.split(':')[0]);
    const after=ix.accounts.split('|').filter(Boolean).map(x=>x.split(':')[0]);
    return before.length===after.length&&before.every((a,j)=>a===after[j]);
   });
  const originalDataSame=tail.length===beforeInstructions.length&&
   tail.every((ix,i)=>ix.data===beforeInstructions[i].data);
  const flagsDifferent=tail.length===beforeInstructions.length&&
   tail.some((ix,i)=>ix.accounts!==beforeInstructions[i].accounts);"""
OLD_POST="""  const allowedBudget=computeOnly&&cuLimit!==null&&cuPrice!==null&&
   cuLimit>=110_000&&cuLimit<=400_000&&cuPrice<=1_000_000n&&
   (BigInt(cuLimit)*cuPrice+999_999n)/1_000_000n<=1_000_000n;
  if(!samePayer||!sameHash||!originalRaydiumUnchanged||!allowedBudget){
   throw new Error('Stage 16: unexpected wallet changes; NO broadcast. '+
    'Payer unchanged='+samePayer+', blockhash unchanged='+sameHash+
    ', Raydium instruction (program/accounts/data) unchanged='+originalRaydiumUnchanged+
    ', two recognized bounded ComputeBudget instructions='+allowedBudget+
    '. Before/after instruction count='+beforeInstructions.length+'/'+afterInstructions.length+
    '. Do not bypass any wallet security warning.');
  }"""
NEW_POST="""  const allowedBudget=computeOnly&&cuLimit!==null&&cuPrice!==null&&
   cuLimit>=110_000&&cuLimit<=400_000&&cuPrice<=1_000_000n&&
   (BigInt(cuLimit)*cuPrice+999_999n)/1_000_000n<=1_000_000n;
  // Recreate the expected message using the ORIGINAL (pre-wallet) account
  // metadata, ORIGINAL Raydium data, and EXACT wallet-returned ComputeBudget
  // instructions. The wallet's serialized message must match byte-for-byte.
  // This covers account access privileges, signer layout and instruction data.
  let canonicalMessageSame=false;
  if(allowedBudget&&samePayer&&sameHash&&originalProgramSame&&
     originalAddressesSame&&originalDataSame&&beforeInstructions.length===1){
   const orig=beforeInstructions[0];
   const keys=orig.accounts.split('|').filter(Boolean).map(raw=>{
    const colon=raw.lastIndexOf(':');
    const flags=raw.slice(colon+1);
    return {pubkey:new PublicKey(raw.slice(0,colon)),
     isSigner:flags.includes('s'),isWritable:flags.includes('w')};
   });
   const data=Uint8Array.from(orig.data.split(',').filter(Boolean).map(Number)) as any;
   const expectedTx=new Transaction({feePayer:payer,recentBlockhash:beforeBlockhash});
   expectedTx.add(...extra,new TransactionInstruction({
    programId:new PublicKey(orig.program),keys,data
   }));
   const reconstructed=expectedTx.serializeMessage();
   canonicalMessageSame=reconstructed.length===actual.length&&
    reconstructed.every((b,i)=>b===actual[i]);
  }
  const originalRaydiumUnchanged=originalProgramSame&&originalAddressesSame&&
   originalDataSame&&canonicalMessageSame;
  if(!samePayer||!sameHash||!originalRaydiumUnchanged||!allowedBudget){
   throw new Error('Stage 17: returned LEGACY transaction differs from expected canonical message; NO broadcast. '+
    'Payer unchanged='+samePayer+', blockhash unchanged='+sameHash+
    ', Raydium program same='+originalProgramSame+
    ', ordered account addresses same='+originalAddressesSame+
    ', Raydium instruction data same='+originalDataSame+
    ', raw account flags differ='+flagsDifferent+
    ', canonical message byte-exact='+canonicalMessageSame+
    ', two recognized bounded ComputeBudget instructions='+allowedBudget+
    '. Before/after instruction count='+beforeInstructions.length+'/'+afterInstructions.length+
    '. Do not bypass any wallet security warning.');
  }"""
OLD_MESSAGE="Phantom inserted exactly two bounded ComputeBudget instructions before an IDENTICAL Raydium instruction. "
NEW_MESSAGE="Wallet added two bounded ComputeBudget instructions; reconstructed canonical message matches exactly. "

def main():
    if not CHAIN.is_file():raise ValueError('Run from /home/runner/workspace; ORBIT chain.ts not found')
    source=CHAIN.read_text(encoding='utf8')
    if TAG in source:
        if source.count(TAG)!=1 or NEW_POST not in source:raise ValueError('Partial/inconsistent Stage17 installation')
        print('STAGE 17 ALREADY INSTALLED');return
    if 'ORBIT_STAGE16_PHANTOM_COMPUTE_BUDGET_VERIFY' not in source or 'ORBIT_STAGE14_LEGACY_SIGN_ONLY' not in source:
        raise ValueError('Stage 16 LEGACY diagnostic missing; no changes made')
    begin='export async function testRaydiumLegacySigning('
    end='export async function launchToken('
    if source.count(begin)!=1 or source.count(end)!=1 or source.count(OLD_IMPORT)!=1:
        raise ValueError('Unexpected ORBIT source layout; no changes made')
    start=source.index(begin);finish=source.index(end,start)
    old=source[start:finish]
    if any(old.count(x)!=1 for x in [OLD_COMPARE,OLD_POST,OLD_MESSAGE]):
        raise ValueError('Expected Stage16 comparison not found; no changes made')
    changed=old.replace(OLD_COMPARE,NEW_COMPARE,1).replace(OLD_POST,NEW_POST,1).replace(OLD_MESSAGE,NEW_MESSAGE,1)
    candidate=source[:start]+changed+source[finish:]
    candidate=candidate.replace(OLD_IMPORT,NEW_IMPORT,1)
    if candidate.count(TAG)!=1 or candidate[candidate.index(end):]!=source[source.index(end):]:
        raise ValueError('Live launch/trade code protection failed')
    backup=ROOT/'.orbit-backups'/('stage17-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    backup.mkdir(parents=True,exist_ok=False)
    shutil.copy2(CHAIN,backup/'chain.ts')
    with tempfile.NamedTemporaryFile('w',encoding='utf8',dir=CHAIN.parent,prefix='.orbit17-',delete=False) as f:
        f.write(candidate);name=f.name
    os.replace(name,CHAIN)
    print('STAGE 17 INSTALLED. Backup:',backup/'chain.ts')
    print('Only testRaydiumLegacySigning modified; live launch untouched. No broadcast, restart, Git push or Republish.')
if __name__=='__main__':
    try:main()
    except Exception as exc:print('STAGE 17 STOPPED:',exc,file=sys.stderr);sys.exit(1)
