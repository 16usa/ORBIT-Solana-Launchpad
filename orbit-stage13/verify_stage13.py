#!/usr/bin/env python3
from pathlib import Path
r=Path.cwd()/'artifacts/orbit-launchpad/original/orbit-solana-launchpad'
c=(r/'web/src/chain.ts').read_text()
a=(r/'web/src/App.tsx').read_text()
assert c.count('ORBIT_STAGE13_LEGACY_READONLY')==1, 'Missing Stage 13 chain function'
assert a.count('ORBIT_STAGE13_LEGACY_READONLY')==1, 'Missing Stage 13 UI handler'
assert c.count('export async function inspectRaydiumLegacy(')==1
assert a.count('onClick={inspectLegacy}')==1
assert c.count('export async function launchToken(')==1
assert 'ORBIT_STAGE11_ALT_RESOLUTION' in c
segment=c.split('export async function inspectRaydiumLegacy(',1)[1].split('// ORBIT_STAGE10_VERIFIED_DEVNET_LAUNCH',1)[0]
for token in ['sendRawTransaction','sendTransaction','execute(','signTransaction(','tx.sign(','signed.serialize()']:
    assert token not in segment, 'Unexpected send/sign code: '+token
print('STAGE 13 VERIFIED: legacy read-only inspector, no transaction sending or signing')
