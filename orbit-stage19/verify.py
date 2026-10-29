#!/usr/bin/env python3
from pathlib import Path
import os,sys
root=Path(os.environ.get('ORBIT_STAGE19_FIXTURE_ROOT','/home/runner/workspace/artifacts/orbit-launchpad/original/orbit-solana-launchpad'))
p=root/'web/src/chain.ts'
s=p.read_text() if p.exists() else ''
if s.count('ORBIT_STAGE19_DEVNET_LEGACY_CURVE_TRADE')!=1 or s.count('ORBIT_STAGE18_DEVNET_LEGACY_REAL_LAUNCH')!=1:
    print('STAGE 19 VERIFY FAILED: markers missing/duplicated');sys.exit(1)
a=s.index('export async function curveTrade(');b=s.index('function b64(',a)
part=s[a:b]
checks=['txVersion:TxVersion.LEGACY','Stage 19 bonding-curve trading is Devnet-only','raydium.launchpad.buyToken(','raydium.launchpad.sellToken(',"if(!programId.equals(program(config)))",'sendAndConfirm:true']
if part.count('txVersion:TxVersion.LEGACY')!=2 or 'txVersion:TxVersion.V0' in part or any(x not in part for x in checks):
    print('STAGE 19 VERIFY FAILED: trade implementation inconsistent');sys.exit(1)
print('STAGE 19 VERIFIED: buy/sell use LEGACY on Devnet, launch untouched.')
