#!/usr/bin/env python3
from pathlib import Path
import os
root = Path(os.environ.get('ORBIT_WORKSPACE', '/home/runner/workspace'))
src = root / 'artifacts/orbit-launchpad/original/orbit-solana-launchpad/web/src'
button = (src / 'OrbitWalletButton.tsx').read_text(encoding='utf-8')
css = (src / 'styles.css').read_text(encoding='utf-8')
assert button.count('ORBIT_STAGE20_WALLET_AVATAR') == 1, 'wallet component missing or duplicated'
assert css.count('ORBIT_STAGE20_WALLET_AVATAR') == 1, 'wallet styles missing or duplicated'
for item in ('Copy address', 'Change wallet', 'Disconnect', 'Set avatar', 'useWalletModal', 'localStorage.setItem', 'WalletMultiButton'):
    assert item in button, f'wallet feature missing: {item}'
for item in ('.orbit-account-avatar-trigger', '.orbit-account-dropdown', 'border-radius:50%'):
    assert item in css, f'avatar style missing: {item}'
print('STAGE 20 VERIFIED')
