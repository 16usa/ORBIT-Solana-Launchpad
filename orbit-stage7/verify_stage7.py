#!/usr/bin/env python3
"""Static safety assertions for Stage 7; does not connect to a wallet or network."""
from pathlib import Path
root=Path.cwd()/'artifacts/orbit-launchpad/original/orbit-solana-launchpad'
chain=(root/'web/src/chain.ts').read_text()
app=(root/'web/src/App.tsx').read_text()
assert '// ORBIT_STAGE7_MOBILE_SIGNING' in chain
assert 'checkWalletSigning' in chain and 'onClick={testWalletSignature}' in app
assert 'signed.push(await wallet.signTransaction!' in chain
assert chain.count('const signed=await wallet.signTransaction(tx);')>=1
wallet_test=chain.split('export async function checkWalletSigning(',1)[1].split('export async function launchToken(',1)[0]
for prohibited in ['.sendRawTransaction(','.sendTransaction(','.execute(','.sendAndConfirm(']:
    assert prohibited not in wallet_test,prohibited
assert "if(config.network!=='devnet')throw" in wallet_test
assert 'NO sendTransaction' in wallet_test
assert "const mobile=typeof navigator!=='undefined'" in chain
print('Stage 7 static verification: PASS')
print('Wallet test never broadcasts; DEVNET only; mobile single-sign route enabled.')
