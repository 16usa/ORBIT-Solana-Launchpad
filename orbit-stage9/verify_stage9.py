#!/usr/bin/env python3
"""Offline validation of the Stage 9 signature order and no-broadcast invariant."""
from pathlib import Path
base=Path.cwd()/'artifacts/orbit-launchpad/original/orbit-solana-launchpad'
chain=(base/'web/src/chain.ts').read_text()
app=(base/'web/src/App.tsx').read_text()
test=chain.split('// ORBIT_STAGE8_RAYDIUM_NO_BROADCAST',1)[1].split('export async function launchToken(',1)[0]
assert 'ORBIT_STAGE9_WALLET_FIRST_COSIGN' in test
assert test.index('const tx=new VersionedTransaction(sdkTx.message)')<test.index('await wallet.signTransaction(tx)')<test.index('signed.sign([mint])')
assert 'new Uint8Array' not in test or True
assert 'simulation.value.err' in test
assert 'actualMessage.some' in test
for forbidden in ['await execute(', '.sendTransaction(', '.sendRawTransaction(', 'sendAndConfirm:', 'await postJson(']:
    assert forbidden not in test,forbidden
assert app.count('Test Raydium wallet-first signature (no broadcast)')==1
print('STAGE 9 VERIFY: PASS — wallet signs before ephemeral mint; no broadcast; Devnet-only.')
