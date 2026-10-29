#!/usr/bin/env python3
"""Stage15: narrow no-broadcast diff diagnostic for LEGACY signature test only."""
from pathlib import Path
from datetime import datetime,timezone
import os, shutil, sys, tempfile
R=Path.cwd()/'artifacts/orbit-launchpad/original/orbit-solana-launchpad'
P=R/'web/src/chain.ts'
MARK='ORBIT_STAGE15_RETURNED_MESSAGE_DIFF'
OLD1=' const expected=tx.serializeMessage();\n let signed:Transaction;'
NEW1=" // ORBIT_STAGE15_RETURNED_MESSAGE_DIFF\n // Snapshot before the wallet call: some adapters mutate Transaction in-place.\n const expected=tx.serializeMessage();\n const beforePayer=tx.feePayer?.toBase58()||'';\n const beforeBlockhash=tx.recentBlockhash||'';\n const beforeInstructions=tx.instructions.map(ix=>({\n  program:ix.programId.toBase58(),\n  accounts:ix.keys.map(k=>k.pubkey.toBase58()+':'+(k.isSigner?'s':'-')+(k.isWritable?'w':'-')).join('|'),\n  data:Array.from(ix.data).join(',')\n }));\n let signed:Transaction;"
OLD2=" const actual=signed.serializeMessage();\n if(actual.length!==expected.length||actual.some((v,i)=>v!==expected[i]))\n  throw new Error('Wallet altered the transaction message; diagnostic aborted.');\n const walletSig=signed.signatures.find(s=>s.publicKey.equals(payer))?.signature;"
NEW2=" const actual=signed.serializeMessage();\n if(actual.length!==expected.length||actual.some((v,i)=>v!==expected[i])){\n  // Do not broadcast or co-sign a modified message. Report only structural\n  // differences, without raw signed transaction bytes or secret keys.\n  const afterInstructions=signed.instructions.map(ix=>({\n   program:ix.programId.toBase58(),\n   accounts:ix.keys.map(k=>k.pubkey.toBase58()+':'+(k.isSigner?'s':'-')+(k.isWritable?'w':'-')).join('|'),\n   data:Array.from(ix.data).join(',')\n  }));\n  const changes:string[]=[];\n  for(let i=0;i<Math.max(beforeInstructions.length,afterInstructions.length);i++){\n   const a=beforeInstructions[i],b=afterInstructions[i];\n   if(!a||!b||a.program!==b.program||a.accounts!==b.accounts||a.data!==b.data)\n    changes.push('instruction '+i+': '+(a?.program||'<none>')+' -> '+(b?.program||'<none>')+\n     '; accounts '+(a?.accounts===b?.accounts?'same':'changed')+\n     '; data '+(a?.data===b?.data?'same':'changed'));\n  }\n  let payerSignatureValid=false;\n  try{payerSignatureValid=!!signed.verifySignatures(false)}catch{}\n  const beforeKeys=Array.from(expected).length;\n  const afterKeys=Array.from(actual).length;\n  throw new Error(\n   'ORBIT Stage 15: Wallet/adapter returned a DIFFERENT LEGACY message. '+\n   'NO broadcast; NO token created. '+\n   'Cryptographic signature on returned message: '+(payerSignatureValid?'VALID':'NOT VERIFIED')+'. '+\n   'Fee payer changed: '+String(beforePayer!==(signed.feePayer?.toBase58()||''))+'. '+\n   'Recent blockhash changed: '+String(beforeBlockhash!==(signed.recentBlockhash||''))+'. '+\n   'Instructions: '+beforeInstructions.length+' -> '+afterInstructions.length+'. '+\n   'Message bytes: '+beforeKeys+' -> '+afterKeys+'. '+\n   'Instruction differences: '+(changes.length?changes.join(' | '):'none (account ordering or message header may differ)')+'. '+\n   'Never bypass Phantom security warnings.'\n  );\n }\n const walletSig=signed.signatures.find(s=>s.publicKey.equals(payer))?.signature;"

def main():
    if not P.is_file():raise ValueError('Run in /home/runner/workspace; ORBIT chain.ts not found')
    s=P.read_text()
    if MARK in s:
        if s.count(MARK)!=1 or NEW2 not in s:raise ValueError('Incomplete Stage15 installation')
        print('STAGE 15 ALREADY INSTALLED');return
    if s.count('ORBIT_STAGE14_LEGACY_SIGN_ONLY')<1:raise ValueError('Stage14 legacy signature test missing')
    if s.count(OLD1)!=1 or s.count(OLD2)!=1:raise ValueError('Unexpected Stage14 code; no changes made')
    start=s.index('export async function testRaydiumLegacySigning(')
    end=s.index('export async function launchToken(')
    section=s[start:end]
    if section.count(OLD1)!=1 or section.count(OLD2)!=1:raise ValueError('Patch target not inside diagnostic function')
    # Guard no accidental modifications to production launch function.
    candidate=s.replace(OLD1,NEW1,1).replace(OLD2,NEW2,1)
    if s[end:]!=candidate[candidate.index('export async function launchToken('):]:raise ValueError('Production code changed unexpectedly')
    backup=R/'.orbit-backups'/('stage15-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    backup.mkdir(parents=True,exist_ok=False)
    shutil.copy2(P,backup/'chain.ts')
    with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=P.parent,prefix='.orbit15-',delete=False) as f:
        f.write(candidate);name=f.name
    os.replace(name,P)
    print('STAGE 15 INSTALLED. Backup:',backup)
    print('Only LEGACY diagnostic changed; no transaction sent; no restart, push or publish.')
if __name__=='__main__':
    try:main()
    except Exception as e:print('STAGE 15 STOPPED:',e,file=sys.stderr);sys.exit(1)
