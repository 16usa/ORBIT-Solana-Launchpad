#!/usr/bin/env python3
"""Stage16: Verify Phantom-added ComputeBudget instructions, no broadcast."""
from pathlib import Path
from datetime import datetime,timezone
import os,shutil,sys,tempfile
ROOT=Path.cwd()/'artifacts/orbit-launchpad/original/orbit-solana-launchpad'
CHAIN=ROOT/'web/src/chain.ts'
TAG='ORBIT_STAGE16_PHANTOM_COMPUTE_BUDGET_VERIFY'
START=' const actual=signed.serializeMessage();\n if(actual.length!==expected.length||actual.some((v,i)=>v!==expected[i])){'
END=' const walletSig=signed.signatures.find(s=>s.publicKey.equals(payer))?.signature;'
REPLACEMENT=(Path(__file__).parent/'stage16_legacy_validation.txt').read_text(encoding='utf-8')
def main():
    if not CHAIN.is_file():raise ValueError('Run from /home/runner/workspace (ORBIT chain.ts not found)')
    source=CHAIN.read_text(encoding='utf-8')
    if TAG in source:
        if source.count(TAG)!=1 or REPLACEMENT not in source:raise ValueError('Partial/incorrect Stage16 patch: unchanged')
        print('STAGE 16 ALREADY INSTALLED');return
    if 'ORBIT_STAGE15_RETURNED_MESSAGE_DIFF' not in source or 'ORBIT_STAGE14_LEGACY_SIGN_ONLY' not in source:
        raise ValueError('Stage 15 and Stage 14 code required; no changes made')
    f='export async function testRaydiumLegacySigning('
    end='export async function launchToken('
    if source.count(f)!=1 or source.count(end)!=1:raise ValueError('Unexpected source; no changes')
    begin_idx=source.index(f);end_idx=source.index(end)
    section=source[begin_idx:end_idx]
    if section.count(START)!=1 or section.count(END)!=1:raise ValueError('Stage15 original code not found, no changes')
    i=section.index(START);j=section.index(END,i)+len(END)
    candidate=source[:begin_idx]+section[:i]+REPLACEMENT+section[j:]+source[end_idx:]
    if source[end_idx:] != candidate[candidate.index(end):]:raise ValueError('LIVE launch function changed unexpectedly')
    # Extend the sign-only success report with the validated priority-fee details.
    return_old="  'Wallet signed the Raydium legacy transaction. Temporary mint co-signed locally.\\n'+"
    return_new=return_old+"\n  phantomPriorityNote+'\\n'+"
    ret=candidate[begin_idx:candidate.index(end)]
    if ret.count(return_old)!=1:raise ValueError('Stage14 return anchor missing; no changes')
    candidate=candidate[:begin_idx]+ret.replace(return_old,return_new,1)+candidate[candidate.index(end):]
    if candidate.count(TAG)!=1 or candidate.count(END)!=1:raise ValueError('Patch validation failed')
    backup=ROOT/'.orbit-backups'/('stage16-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    backup.mkdir(parents=True,exist_ok=False)
    shutil.copy2(CHAIN,backup/'chain.ts')
    with tempfile.NamedTemporaryFile('w',encoding='utf8',dir=CHAIN.parent,prefix='.orbit16-',delete=False) as tmp:
        tmp.write(candidate);name=tmp.name
    os.replace(name,CHAIN)
    print('STAGE 16 INSTALLED. Original:',backup/'chain.ts')
    print('Only no-broadcast LEGACY signature test modified; no restart, Git push, or Republish.')
if __name__=='__main__':
    try:main()
    except Exception as exc:print('STAGE 16 STOPPED:',exc,file=sys.stderr);sys.exit(1)
