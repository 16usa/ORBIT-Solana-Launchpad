#!/usr/bin/env python3
"""Offline read-only checks for ORBIT Stage 3 (does not call RPC)."""
from pathlib import Path
import tomllib

root=Path.cwd()
api=root/'artifacts/api-server/.replit-artifact/artifact.toml'
source=root/'artifacts/orbit-launchpad/original/orbit-solana-launchpad'
assert api.is_file() and (source/'web/src/App.tsx').is_file(), 'Run from ORBIT workspace root.'
data=tomllib.loads(api.read_text())
services=data['services']
assert len(services)==1
prod=services[0]['production']['run']['env']
for key,value in {
 'SOLANA_CLUSTER':'devnet',
 'RPC_URL':'https://api.devnet.solana.com',
 'VITE_RPC_URL':'https://api.devnet.solana.com',
 'PUBLIC_BASE_URL':'https://orbit-solana-launchpad.replit.app',
 'RAYDIUM_PROGRAM_ID':'DRay6fNdQ5J82H7xV6uq2aV3mNrUZ1J4PgSKsWgptcm6',
 'ENABLE_MAINNET_TRADING':'false',
}.items():
 assert prod.get(key)==value, f'Expected production {key}={value!r}'
assert prod.get('PORT')=='8080', 'API must remain on its configured port.'
app=(source/'web/src/App.tsx').read_text()
component=(source/'web/src/OrbitWalletButton.tsx').read_text()
assert 'OrbitWalletButton' in app and 'WalletMultiButton' not in app
assert 'https://phantom.com/ul/browse/' in component
assert 'encodeURIComponent(currentUrl)' in component and 'encodeURIComponent(ref)' in component
assert "WalletReadyState.Installed" in component and '<WalletMultiButton />' in component
api_source=(source/'server/app.mjs').read_text()
assert "cluster==='devnet'" in api_source
assert "process.env.ENABLE_MAINNET_TRADING==='true'" in api_source
assert "'/api/network-status'" in api_source
print('ORBIT Stage 3 offline checks: PASS (production env, wallet UX, Devnet guards)')
