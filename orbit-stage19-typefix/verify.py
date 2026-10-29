#!/usr/bin/env python3
from pathlib import Path
import os,sys
ROOT=Path(os.environ.get('ORBIT_STAGE19_FIXTURE_ROOT','/home/runner/workspace/artifacts/orbit-launchpad/original/orbit-solana-launchpad'))
SRC=ROOT/'web/src/chain.ts'
try:
    s=SRC.read_text(encoding='utf-8')
    a=s.index('export async function curveTrade(')
    b=s.index('function b64(',a)
    t=s[a:b]
    checks=[
        'ORBIT_STAGE19_TYPEFIX_DEVNET_NARROWING' in t,
        t.count('ORBIT_STAGE19_DEVNET_LEGACY_CURVE_TRADE')==1,
        "if(config.network!=='devnet')" in t,
        t.count('txVersion:TxVersion.LEGACY')==2,
        'txVersion:TxVersion.V0' not in t,
        'if(config.network===\'mainnet-beta\'&&!config.mainnetTradingEnabled)' not in t,
        'raydium.launchpad.buyToken(' in t,
        'raydium.launchpad.sellToken(' in t,
        'if(!programId.equals(program(config)))' in t,
        'if(!expectedPool.equals(' in t,
    ]
    if not all(checks):raise RuntimeError('Stage 19 typefix verification failed')
    print('STAGE 19 TYPEFIX VERIFIED: TS2367 guard removed, Devnet restriction and LEGACY Buy/Sell preserved')
except Exception as err:
    print('STAGE 19 TYPEFIX VERIFY FAILED:',err,file=sys.stderr);sys.exit(1)
