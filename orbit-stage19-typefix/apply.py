#!/usr/bin/env python3
"""Fix Stage 19's redundant Mainnet condition after the Devnet-only guard.
Edits only curveTrade(), makes a timestamped backup. No network calls/restarts.
"""
from pathlib import Path
from datetime import datetime, timezone
import os, sys, shutil, tempfile

ROOT=Path(os.environ.get('ORBIT_STAGE19_FIXTURE_ROOT','/home/runner/workspace/artifacts/orbit-launchpad/original/orbit-solana-launchpad'))
SRC=ROOT/'web/src/chain.ts'
START='export async function curveTrade('
END='function b64('
GUARD="if(config.network!=='devnet')throw new Error('Stage 19 bonding-curve trading is Devnet-only; Mainnet trades are disabled.');"
REDUNDANT="if(config.network==='mainnet-beta'&&!config.mainnetTradingEnabled)throw new Error('Mainnet trading is disabled until reviewed');"
MARKER='ORBIT_STAGE19_TYPEFIX_DEVNET_NARROWING'


def apply():
    if not SRC.is_file(): raise RuntimeError('chain.ts missing. No changes.')
    src=SRC.read_text(encoding='utf-8')
    if src.count(START)!=1 or src.count(END)!=1: raise RuntimeError('Unexpected source boundaries. No changes.')
    a=src.index(START);b=src.index(END,a)
    chunk=src[a:b]
    if chunk.count('ORBIT_STAGE19_DEVNET_LEGACY_CURVE_TRADE')!=1 or chunk.count(GUARD)!=1:
        raise RuntimeError('Stage 19 Devnet-only guard missing. No changes.')
    if chunk.count('txVersion:TxVersion.LEGACY')!=2 or 'txVersion:TxVersion.V0' in chunk:
        raise RuntimeError('Stage 19 LEGACY buy/sell missing. No changes.')
    if MARKER in chunk:
        if REDUNDANT in chunk:raise RuntimeError('Previous partial fix. No changes.')
        print('STAGE 19 TYPEFIX ALREADY INSTALLED')
        return
    if chunk.count(REDUNDANT)!=1:raise RuntimeError('Expected redundant Mainnet condition not found exactly once. No changes.')
    # The Devnet-only guard is always executed earlier: TS has narrowed config.network to 'devnet'.
    guard_pos=chunk.index(GUARD);old_pos=chunk.index(REDUNDANT)
    if guard_pos>old_pos:raise RuntimeError('Stage 19 Devnet-only guard is out of order. No changes.')
    updated=chunk.replace('  '+REDUNDANT+'\n', '  // '+MARKER+': the Devnet-only guard above makes Mainnet branch unreachable.\n',1)
    if updated==chunk:
        updated=chunk.replace(' '+REDUNDANT+'\n', ' // '+MARKER+': the Devnet-only guard above makes Mainnet branch unreachable.\n',1)
    if updated==chunk or REDUNDANT in updated:raise RuntimeError('Could not safely replace redundant condition. No changes.')
    new=src[:a]+updated+src[b:]
    folder=ROOT/'.orbit-backups'/('stage19-typefix-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    folder.mkdir(parents=True,exist_ok=False)
    shutil.copy2(SRC,folder/'chain.ts')
    with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=SRC.parent,prefix='.orbit-stage19-typefix-',delete=False) as fd:
        fd.write(new); tmp=Path(fd.name)
    try:os.replace(tmp,SRC)
    finally:
        if tmp.exists():tmp.unlink()
    print('STAGE 19 TYPEFIX INSTALLED')
    print('Original backup:',folder/'chain.ts')
    print('No process restart, Git push, deployment, wallet signing or transaction.')

if __name__=='__main__':
    try:apply()
    except Exception as err:
        print('STAGE 19 TYPEFIX STOPPED:',err,file=sys.stderr);sys.exit(1)
