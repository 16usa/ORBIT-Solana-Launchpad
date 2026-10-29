#!/usr/bin/env python3
from pathlib import Path
ROOT=Path.cwd()/'artifacts/orbit-launchpad/original/orbit-solana-launchpad'
c=(ROOT/'web/src/chain.ts').read_text(encoding='utf8')
a=(ROOT/'web/src/App.tsx').read_text(encoding='utf8')
assert c.count('ORBIT_STAGE14_LEGACY_SIGN_ONLY')==1
assert a.count('ORBIT_STAGE14_LEGACY_SIGN_ONLY')==1
assert c.count('export async function testRaydiumLegacySigning(')==1
assert 'onClick={testLegacySignature}>Test LEGACY wallet signature (no broadcast)</button>' in a
assert c.count('export async function launchToken(')==1
# Must not send from the new diagnostic function.
segment=c.split('// ORBIT_STAGE14_LEGACY_SIGN_ONLY',1)[1].split('// ORBIT_STAGE10_VERIFIED_DEVNET_LAUNCH',1)[0]
for bad in ['connection.sendRawTransaction(', 'connection.sendTransaction(', 'postJson(', 'await execute(']:
    assert bad not in segment, bad
assert 'signed.partialSign(mint)' in segment
assert 'signed.verifySignatures(true)' in segment
print('STAGE 14 VERIFIED: sign-only diagnostic; original live launch retained')
