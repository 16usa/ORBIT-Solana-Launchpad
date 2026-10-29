#!/usr/bin/env python3
"""Static checks only. No network requests or transaction signing."""
from pathlib import Path
root=Path.cwd()/'artifacts/orbit-launchpad/original/orbit-solana-launchpad'
c=(root/'web/src/chain.ts').read_text()
a=(root/'web/src/App.tsx').read_text()
assert '// ORBIT_STAGE8_RAYDIUM_NO_BROADCAST' in c
assert 'ORBIT_STAGE8_RAYDIUM_TEST_UI' in a
assert a.count('onClick={testRaydiumSigning}')==1
s=c.split('ORBIT_STAGE8_RAYDIUM_NO_BROADCAST',1)[1].split('export async function launchToken(',1)[0]
for forbidden in ['.sendRawTransaction(','.sendTransaction(', 'await execute(', 'sendAndConfirm:']:
    assert forbidden not in s,forbidden
assert 'await connection.simulateTransaction(tx' in s
assert 'await wallet.signTransaction(tx)' in s
assert 'DEVNET' in s.upper()
assert "uri:'https://example.com/orbit-diagnostic-never-published.json'" in s
assert 'tx.sign([mint])' in s
print('Stage 8 static validation: PASS')
print('No automatic broadcast, no process restart, Devnet-only diagnostic.')
