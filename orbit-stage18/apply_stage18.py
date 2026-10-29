#!/usr/bin/env python3
"""Install Stage 18 into existing ORBIT Replit workspace, with no automatic run/push/redeploy."""
from pathlib import Path
from datetime import datetime, timezone
import os, sys, shutil, tempfile, hashlib

ROOT=Path('/home/runner/workspace/artifacts/orbit-launchpad/original/orbit-solana-launchpad')
# Alternate fixture for offline testing only, never used in Replit.
if os.environ.get('ORBIT_STAGE18_FIXTURE_ROOT'):
    ROOT=Path(os.environ['ORBIT_STAGE18_FIXTURE_ROOT'])
SRC=ROOT/'web/src/chain.ts'
PAYLOAD=Path(__file__).with_name('live_legacy_launch.ts.txt')
MARK='ORBIT_STAGE18_DEVNET_LEGACY_REAL_LAUNCH'
START='export async function launchToken('
END='export async function curveTrade('

def check():
    if not SRC.is_file():raise RuntimeError('ORBIT chain.ts not found. Run in the existing ORBIT workspace.')
    text=SRC.read_text()
    if MARK in text:
        if text.count(MARK)!=1 or 'skipPreflight:false' not in text or 'canonicalMessageSame' not in text:
            raise RuntimeError('Partial Stage 18 installation; manual review required.')
        print('STAGE 18 ALREADY INSTALLED');return
    for marker in ['ORBIT_STAGE17_CANONICAL_LEGACY_MATCH','ORBIT_STAGE14_LEGACY_SIGN_ONLY','ORBIT_STAGE10_VERIFIED_DEVNET_LAUNCH']:
        if marker not in text:raise RuntimeError(f'{marker} missing. Stage 17 installation is required. No changes made.')
    if text.count(START)!=1 or text.count(END)!=1:
        raise RuntimeError('Unexpected launch function markers. No changes made.')
    old=text[text.index(START):text.index(END)]
    for token in ['tx.message.recentBlockhash=bh.blockhash','sendRawTransaction(','ORBIT_STAGE11_ALT_RESOLUTION']:
        if token not in old:raise RuntimeError(f'Expected Stage 11 live launch check missing ({token}). No changes made.')
    new=PAYLOAD.read_text(encoding='utf-8')
    for token in ['ORBIT_STAGE18_DEVNET_LEGACY_REAL_LAUNCH','txVersion:TxVersion.LEGACY','sigVerify:false','skipPreflight:false','canonicalMessageSame','signed.verifySignatures(true)','getGenesisHash()']:
        if token=='sigVerify:false':continue
        if token not in new:raise RuntimeError(f'Missing safety check in payload ({token}).')
    modified=text[:text.index(START)]+new+'\n'+text[text.index(END):]
    if modified.count(MARK)!=1 or modified[modified.index(END):]!=text[text.index(END):]:
        raise RuntimeError('Trade code mutation detected. No changes made.')
    # Also ensure original legacy signing-only diagnostic remains intact.
    prefix_start=text.index('export async function testRaydiumLegacySigning(')
    launch_start=text.index(START)
    if modified[prefix_start:modified.index('// ORBIT_STAGE18_DEVNET_LEGACY_REAL_LAUNCH')]!=text[prefix_start:launch_start]:
        raise RuntimeError('Diagnostic function would change. No changes made.')
    backup_dir=ROOT/'.orbit-backups'/('stage18-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    backup_dir.mkdir(parents=True,exist_ok=False)
    backup=backup_dir/'chain.ts'
    shutil.copy2(SRC,backup)
    with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=SRC.parent,prefix='.orbit18-',delete=False) as f:
        f.write(modified);tmp=Path(f.name)
    os.replace(tmp,SRC)
    print('STAGE 18 INSTALLED')
    print('Original file backup:',backup)
    print('Devnet-only legacy live launch. Still requires individual Phantom confirmation.')
    print('No RPC transaction, server restart, Git push, or Republish performed by this installer.')

if __name__=='__main__':
    try:check()
    except Exception as exc:
        print('STAGE 18 STOPPED:',exc,file=sys.stderr)
        sys.exit(1)
