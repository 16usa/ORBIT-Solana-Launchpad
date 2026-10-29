#!/usr/bin/env python3
"""ORBIT Stage 19: Devnet bonding-curve trades use LEGACY transactions.
No network actions, server restarts, Git operations or deploys.
"""
from pathlib import Path
from datetime import datetime, timezone
import os
import shutil
import sys
import tempfile

ROOT = Path(os.environ.get('ORBIT_STAGE19_FIXTURE_ROOT', '/home/runner/workspace/artifacts/orbit-launchpad/original/orbit-solana-launchpad'))
SRC = ROOT / 'web/src/chain.ts'
START = 'export async function curveTrade('
END = 'function b64('
MARKER = 'ORBIT_STAGE19_DEVNET_LEGACY_CURVE_TRADE'
OLD = 'txVersion:TxVersion.V0'
NEW = 'txVersion:TxVersion.LEGACY'


def run():
    if not SRC.is_file():
        raise RuntimeError('Cannot find ORBIT chain.ts in this Replit workspace. No changes made.')
    original = SRC.read_text(encoding='utf8')
    if 'ORBIT_STAGE18_DEVNET_LEGACY_REAL_LAUNCH' not in original:
        raise RuntimeError('Stage 18 launch missing. Install and verify Stage 18 first. No changes made.')
    if original.count(START) != 1 or original.count(END) != 1:
        raise RuntimeError('Unexpected curveTrade boundaries. No changes made.')
    a = original.index(START)
    b = original.index(END, a)
    part = original[a:b]
    if MARKER in part:
        if part.count(MARKER)!=1 or part.count(NEW)!=2 or OLD in part:
            raise RuntimeError('Partial previous Stage 19 installation; review code manually.')
        print('STAGE 19 ALREADY INSTALLED')
        return
    if part.count(OLD) != 2:
        raise RuntimeError('Expected exactly two V0 trade builders (buy/sell). No changes made.')
    for req in ['raydium.launchpad.buyToken(', 'raydium.launchpad.sellToken(',
                'if(!programId.equals(program(config)))', 'if(!expectedPool.equals(',
                'if(Number(p.status)!==0)', 'sendAndConfirm:true',
                "item.network!==config.network"]:
        if req not in part:
            raise RuntimeError('Missing existing trade safety condition: '+req+'. No changes made.')
    # Important: modify only the trade function, never the tested launchToken.
    restricted = " if(config.network!=='devnet')throw new Error('Stage 19 bonding-curve trading is Devnet-only; Mainnet trades are disabled.');\n"
    if part.count('{\n') < 1:
        raise RuntimeError('Unexpected trade function formatting.')
    header, rest = part.split('{\n', 1)
    updated_part = header + '{\n' + ' // '+MARKER+'\n' + restricted + rest.replace(OLD,NEW)
    if updated_part.count(NEW)!=2 or OLD in updated_part:
        raise RuntimeError('Trade patch sanity check failed. No changes made.')
    changed = original[:a] + updated_part + original[b:]
    if changed[:a] != original[:a] or changed[changed.index(END):] != original[b:]:
        raise RuntimeError('Non-trade source would change. No changes made.')
    backup_dir = ROOT / '.orbit-backups' / ('stage19-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    backup_dir.mkdir(parents=True,exist_ok=False)
    backup = backup_dir / 'chain.ts'
    shutil.copy2(SRC,backup)
    with tempfile.NamedTemporaryFile('w',encoding='utf8',dir=SRC.parent,prefix='.orbit-stage19-',delete=False) as f:
        f.write(changed)
        tmp=Path(f.name)
    try:os.replace(tmp,SRC)
    finally:
        if tmp.exists():tmp.unlink()
    print('STAGE 19 INSTALLED: Buy and Sell Raydium SDK builders now use LEGACY on Devnet.')
    print('Source backup:',backup)
    print('No blockchain transaction, restart, Git push, or Republish performed.')
    print('Real trades still require a separate Phantom wallet approval.')

if __name__=='__main__':
    try:run()
    except Exception as e:
        print('STAGE 19 STOPPED:',e,file=sys.stderr)
        sys.exit(1)
