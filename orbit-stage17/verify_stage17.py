#!/usr/bin/env python3
"""Static local guard check; it does not contact a network or wallet."""
from pathlib import Path
p=Path.cwd()/'artifacts/orbit-launchpad/original/orbit-solana-launchpad/web/src/chain.ts'
s=p.read_text()
beg=s.index('export async function testRaydiumLegacySigning(')
end=s.index('export async function launchToken(',beg)
t=s[beg:end]
assert t.count('ORBIT_STAGE17_CANONICAL_LEGACY_MATCH')==1
assert 'const expectedTx=new Transaction(' in t
assert 'canonicalMessageSame=reconstructed.length===actual.length' in t
assert 'signed.verifySignatures(true)' in t
assert 'const walletSig=signed.signatures.find(' in t
assert 'NO transaction broadcast' in t
assert 'sendRawTransaction(' not in t
assert 'sendTransaction(' not in t
assert 'postJson(' not in t
assert 'execute(' not in t
assert 'sendAndConfirm' not in t
assert 'ORBIT_STAGE10_VERIFIED_DEVNET_LAUNCH' in s
print('STAGE 17 VERIFIED: no-broadcast diagnostic only; live launch guard present.')
