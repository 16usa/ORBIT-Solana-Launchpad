#!/usr/bin/env python3
"""ORBIT Stage 3: Devnet production environment + mobile Phantom UX.

Applies only to the existing ORBIT Replit workspace. No npm installs,
process restarts, git operations, deployments, or on-chain transactions.
"""
from pathlib import Path
from datetime import datetime, timezone
import sys, shutil, re, os, tempfile, tomllib

SITE = 'https://orbit-solana-launchpad.replit.app'
PROGRAM = 'DRay6fNdQ5J82H7xV6uq2aV3mNrUZ1J4PgSKsWgptcm6'
ROOT = Path.cwd().resolve()
SRC = ROOT / 'artifacts/orbit-launchpad/original/orbit-solana-launchpad'
ART = ROOT / 'artifacts/api-server/.replit-artifact/artifact.toml'

WALLET_COMPONENT = '''import React from 'react';
import { useWallet } from '@solana/wallet-adapter-react';
import { WalletMultiButton } from '@solana/wallet-adapter-react-ui';
import { WalletReadyState } from '@solana/wallet-adapter-base';

// Phantom on iOS requires its in-app browser; an empty wallet picker in Safari
// is not a connection method. Keep Wallet Standard autodetection untouched.
export default function OrbitWalletButton({ showHint = false }: { showHint?: boolean }) {
  const { wallets, connected } = useWallet();
  const isMobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
  const availableWallet = wallets.some(({ readyState }) => readyState === WalletReadyState.Installed || readyState === WalletReadyState.Loadable);

  if (connected || availableWallet) return <WalletMultiButton />;

  // The browse link opens the current page inside Phantom; it does NOT grant
  // account access or sign transactions, which still require wallet approval.
  if (isMobile) {
    const currentUrl = window.location.href;
    const ref = window.location.origin;
    const url = `https://phantom.com/ul/browse/${encodeURIComponent(currentUrl)}?ref=${encodeURIComponent(ref)}`;
    return <div className="orbit-wallet-action">
      <a className="wallet-adapter-button orbit-phantom-link" href={url} rel="noreferrer" aria-label="Open ORBIT in Phantom wallet browser">Open in Phantom</a>
      {showHint && <p className="orbit-wallet-hint">On iPhone, open this site inside Phantom's browser to connect. If the button doesn't open Phantom, open the Phantom app and paste this site's address into its search bar.</p>}
    </div>;
  }

  return <div className="orbit-wallet-action">
    <a className="wallet-adapter-button orbit-phantom-link" href="https://phantom.com/download" target="_blank" rel="noreferrer">Get Phantom</a>
    {showHint && <p className="orbit-wallet-hint">Install a Solana wallet extension, then reload ORBIT and choose your wallet. Never share a recovery phrase.</p>}
  </div>;
}
'''

STYLE = '''
/* ORBIT Stage 3: mobile wallet fallback, no fake wallet choices */
.orbit-wallet-action{display:flex;flex-direction:column;align-items:center;gap:6px;max-width:100%}
.orbit-wallet-action .orbit-phantom-link{display:inline-flex!important;align-items:center;justify-content:center;text-decoration:none!important;white-space:nowrap}
.orbit-wallet-hint{font-size:12px;line-height:1.5;color:#a8abb2;max-width:370px;margin:4px auto 10px;text-align:center}
@media(max-width:600px){.header .orbit-wallet-action .orbit-phantom-link{font-size:11px!important;padding:0 9px!important}}
'''

README = '''# ORBIT Stage 3 — Devnet production configuration and mobile wallet fallback

Applies to your existing **ORBIT** Replit workspace only. This is not a new site.

## Changes

- Sets **non-secret** API production environment variables in `artifacts/api-server/.replit-artifact/artifact.toml`: `SOLANA_CLUSTER=devnet`, `RPC_URL`, `VITE_RPC_URL`, `RAYDIUM_PROGRAM_ID`, `PUBLIC_BASE_URL=https://orbit-solana-launchpad.replit.app`, and `ENABLE_MAINNET_TRADING=false`.
- Fixes the blank mobile wallet-picker experience: when no Solana wallet is detected, the wallet button directs the user to ORBIT inside Phantom's in-app browser. A normal wallet selector remains when compatible wallets are actually detected.
- Adds explanatory wallet guidance to account and trading panels; no seed phrases, private key requests, simulated wallet sessions, or automatic signatures.
- Includes offline regression checks for Stage 3 deployment settings, mobile wallet deep-link target, and unchanged Devnet restrictions.

## Install via Replit Shell (only)

Unzip `orbit_stage3.zip` at the workspace root and run:

```sh
cd /home/runner/workspace
unzip -o orbit_stage3.zip -d .
python3 orbit-stage3/apply_stage3.py
python3 orbit-stage3/verify_stage3.py
pnpm --filter @workspace/orbit-launchpad run test
pnpm --filter @workspace/orbit-launchpad run check:syntax
pnpm --filter @workspace/orbit-launchpad run typecheck
pnpm --filter @workspace/orbit-launchpad run build
```

The installer **does not restart or stop processes, run package installation, git push, or publish**. It creates a backup under `.orbit-backups/stage3-*` and only changes specific ORBIT files. If any check fails, **do not publish**; inspect the error.

## IMPORTANT: make the production config live

Replit's published deployment has a separate process/environment. After successful tests, **manually publish/redeploy ORBIT** in Replit. Building the source alone does not change the existing `.replit.app` deployment.

Verify the live production settings *after* publication:

```sh
curl -fsS https://orbit-solana-launchpad.replit.app/api/config
curl -fsS https://orbit-solana-launchpad.replit.app/api/network-status
```

`/api/config` should show `network: devnet`, `publicBase: https://orbit-solana-launchpad.replit.app` and `raydiumProgramAllowlisted: true`. An RPC error or missing on-chain LaunchLab configuration will still block launch; test inside Phantom on Devnet. **No real token creation, buy, or sell has been verified by this patch.**

## Safety / limitations

- API and images are still saved on Replit's **ephemeral filesystem**. Token metadata may disappear after a redeploy. **Do not use this version for mainnet or valuable tokens.** Permanent storage and independent security audit are required before launch.
- If Replit Publishing has manually configured environment values/secrets that override files, update those through Publishing settings; the script does not read or modify them.
- `RAYDIUM_PROGRAM_ID` is the previously used Devnet value. The code checks on-chain readiness separately; inclusion in configuration does **not** prove the program/configuration can execute token launches.
- The Phantom browse deep link requires the user to click. If deep linking does not work, open the site URL directly in Phantom's in-app browser.
- This patch does not make the empty Explore list populate automatically or enable livestreams, historical candles or mainnet trading.
'''

VERIFY = '''#!/usr/bin/env python3
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
'''

class PatchError(Exception):
    pass

def once(s, old, new, label):
    count=s.count(old)
    if count!=1:
        raise PatchError(f'{label}: expected exactly 1 matching source, found {count}. Files left unchanged.')
    return s.replace(old,new,1)

def patch_plan():
    if not (SRC/'server/app.mjs').is_file() or not (SRC/'web/src/App.tsx').is_file() or not ART.is_file():
        raise PatchError('This is not the expected ORBIT Replit workspace. Run from /home/runner/workspace.')
    configs=ART.read_text(encoding='utf-8')
    try:
        parsed=tomllib.loads(configs)
        prod=parsed['services'][0]['production']['run']['env']
    except (ValueError, KeyError, IndexError) as e:
        raise PatchError(f'Unexpected production API configuration: {e}') from e
    if prod.get('PORT')!='8080' or prod.get('NODE_ENV')!='production':
        raise PatchError('API production PORT/NODE_ENV differs from expected layout. No files changed.')
    # Stop instead of overwriting custom deployment settings of unknown provenance.
    targets={
        'SOLANA_CLUSTER':'devnet',
        'RPC_URL':'https://api.devnet.solana.com',
        'VITE_RPC_URL':'https://api.devnet.solana.com',
        'PUBLIC_BASE_URL':SITE,
        'RAYDIUM_PROGRAM_ID':PROGRAM,
        'ENABLE_MAINNET_TRADING':'false',
    }
    for name,value in targets.items():
        existing=prod.get(name)
        if existing is not None and existing!=value:
            raise PatchError(f'Existing production {name}={existing!r} is different. Refusing to overwrite custom values.')
    env_section='[services.production.run.env]'
    if configs.count(env_section)!=1:
        raise PatchError('Expected exactly one production env section')
    lines=configs.splitlines(keepends=True)
    i=next(n for n,line in enumerate(lines) if line.strip()==env_section)
    end=i+1
    while end<len(lines) and not lines[end].lstrip().startswith('['):end+=1
    addition=''.join(f'{k} = "{v}"\n' for k,v in targets.items() if k not in prod)
    lines.insert(end, addition)
    newconf=''.join(lines)
    try:
        check=tomllib.loads(newconf)['services'][0]['production']['run']['env']
        if any(check.get(k)!=v for k,v in targets.items()):raise PatchError('Invalid produced environment config')
    except ValueError as e:
        raise PatchError(f'Produced TOML invalid: {e}') from e
    patches={ART:newconf}
    ui=SRC/'web/src/App.tsx'
    app=ui.read_text(encoding='utf-8')
    if "import OrbitWalletButton from './OrbitWalletButton';" in app:
        # Re-running an already-applied patch is safe.
        if 'WalletMultiButton' in app:raise PatchError('Mixed wallet components in App.tsx')
    else:
        app=once(app,"import {WalletMultiButton} from '@solana/wallet-adapter-react-ui';","import OrbitWalletButton from './OrbitWalletButton';",'App wallet import')
        uses=app.count('<WalletMultiButton/>')
        if uses<3:
            raise PatchError(f'Expected at least 3 wallet buttons, found {uses}. Source may have changed.')
        app=app.replace('<WalletMultiButton/>','<OrbitWalletButton showHint/>')
        # No hint in narrow header. The hint belongs on the create/trade/profile panels.
        app=once(app,'<IconButton onClick={openSearch} title="Search"><Search size={19}/></IconButton><OrbitWalletButton showHint/>',
                      '<IconButton onClick={openSearch} title="Search"><Search size={19}/></IconButton><OrbitWalletButton/>','Header stays compact')
    patches[ui]=app
    component=SRC/'web/src/OrbitWalletButton.tsx'
    if component.is_file() and component.read_text(encoding='utf-8')!=WALLET_COMPONENT:
        raise PatchError('OrbitWalletButton.tsx exists with different content, refusing to overwrite.')
    patches[component]=WALLET_COMPONENT
    css=SRC/'web/src/styles.css'
    oldcss=css.read_text(encoding='utf-8')
    if '/* ORBIT Stage 3: mobile wallet fallback' not in oldcss:
        patches[css]=oldcss.rstrip()+'\n'+STYLE
    else:
        patches[css]=oldcss
    return patches

def main():
    try:changes=patch_plan()
    except Exception as e:
        print(f'STAGE 3 ERROR: {e}',file=sys.stderr)
        return 3
    updates={path:data for path,data in changes.items() if not path.exists() or path.read_text(encoding='utf-8')!=data}
    if not updates:
        print('ORBIT Stage 3 already installed; no files changed.')
        return 0
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup=SRC/'.orbit-backups'/('stage3-'+stamp)
    for path in updates:
        if path.is_file():
            dest=backup/path.relative_to(ROOT)
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(path,dest)
    # Plan verified before writes. Write via atomic replace to avoid partial files.
    for path,content in updates.items():
        path.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=path.parent,delete=False) as f:
            temp=Path(f.name);f.write(content)
        os.replace(temp,path)
        print('Patched:',path.relative_to(ROOT))
    print('Backup:', backup)
    print('No dependencies installed, no process restarted, no Git push, no production publish.')
    return 0
if __name__=='__main__':
    raise SystemExit(main())
