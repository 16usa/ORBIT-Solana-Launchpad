#!/usr/bin/env python3
from pathlib import Path
root=Path.cwd()/'artifacts/orbit-launchpad/original/orbit-solana-launchpad'
chain=(root/'web/src/chain.ts').read_text()
app=(root/'web/src/App.tsx').read_text()
mark='ORBIT_STAGE12_READONLY_AUDIT'
assert chain.count(mark)==1 and app.count(mark)==1, 'Stage 12 missing or duplicated'
new=chain[chain.index(mark):chain.index('// ORBIT_STAGE10_VERIFIED_DEVNET_LAUNCH')]
assert 'export async function inspectRaydiumLaunch(' in new
assert 'sigVerify:false' in new and 'simulateTransaction(tx' in new
assert not any(x in new for x in ('wallet.signTransaction(', 'wallet.signAllTransactions(', 'sendRawTransaction(', 'sendTransaction(', 'execute({', 'postJson(')), 'Unsafe call in audit'
assert 'export async function launchToken(' in chain
assert 'ORBIT_STAGE11_ALT_RESOLUTION' in chain
assert 'onClick={inspectRaydium}' in app and 'onClick={testRaydiumSigning}' not in app
assert 'checkRaydiumLaunchSigning' not in app
print('STAGE 12 VERIFIED: read-only audit installed; launchToken retained; no signing or broadcast inside audit.')
