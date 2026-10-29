#!/usr/bin/env python3
"""Install a read-only Raydium Devnet preflight report into ORBIT Stage 11.

Only edits web/src/chain.ts and web/src/App.tsx. Never runs node, restarts,
pushes, downloads, invokes wallet signing, submits, or publishes.
"""
from pathlib import Path
from datetime import datetime, timezone
import os, sys, shutil, tempfile

ROOT = Path.cwd() / 'artifacts/orbit-launchpad/original/orbit-solana-launchpad'
CHAIN = ROOT / 'web/src/chain.ts'
APP = ROOT / 'web/src/App.tsx'
TAG = 'ORBIT_STAGE12_READONLY_AUDIT'
AUDIT = (Path(__file__).parent / 'inspect_code.txt').read_text(encoding='utf-8')


def patch_chain(data: str) -> str:
    if 'ORBIT_STAGE11_ALT_RESOLUTION' not in data or 'ORBIT_STAGE10_VERIFIED_DEVNET_LAUNCH' not in data:
        raise ValueError('Stage 11 source missing: no changes made')
    if data.count('export async function launchToken(') != 1:
        raise ValueError('Expected one launchToken() implementation')
    anchor = '// ORBIT_STAGE10_VERIFIED_DEVNET_LAUNCH'
    if data.count(anchor) != 1:
        raise ValueError('Expected one Stage 10 insertion point')
    if TAG in data:
        raise ValueError('Partial Stage 12 detected; no changes made')
    return data.replace(anchor, AUDIT + anchor, 1)


def patch_app(data: str) -> str:
    if TAG in data:
        raise ValueError('Partial Stage 12 App detected; no changes made')
    old_import = 'requireLaunchPlatform,checkWalletSigning,checkRaydiumLaunchSigning'
    new_import = 'requireLaunchPlatform,checkWalletSigning,inspectRaydiumLaunch'
    if data.count(old_import) != 1:
        raise ValueError('Expected one Stage 9 import')
    data = data.replace(old_import, new_import, 1)
    anchor_start = ' // ORBIT_STAGE8_RAYDIUM_TEST_UI:'
    anchor_end = ' async function create(e:React.FormEvent)'
    if data.count(anchor_start) != 1 or data.count(anchor_end) != 1:
        raise ValueError('Unexpected Creator() layout; no changes made')
    start = data.index(anchor_start)
    end = data.index(anchor_end, start)
    segment = data[start:end]
    if 'async function testRaydiumSigning()' not in segment or 'checkRaydiumLaunchSigning(' not in segment:
        raise ValueError('Unexpected old signing handler; no changes made')
    handler = ''' // ORBIT_STAGE12_READONLY_AUDIT
 // Inspect a Raydium launch WITHOUT asking Phantom to sign.
 async function inspectRaydium(){
  if(busy)return;
  setBusy(true);setLaunchError('');
  try{
   const report=await inspectRaydiumLaunch(connection,config,wallet);
   setLaunchError(report.slice(0,6500));
   notify('Read-only Raydium audit completed. No wallet prompt.');
  }catch(err){
   setLaunchError('Read-only Raydium audit failed. No transaction sent.\\n'+String((err as Error)?.message||err));
   notify('Raydium audit failed; no transaction sent.');
  }finally{setBusy(false)}
 }
'''
    data = data[:start] + handler + data[end:]
    old_button = 'onClick={testRaydiumSigning}>Test Raydium wallet-first signature (no broadcast)</button>'
    new_button = 'onClick={inspectRaydium}>Inspect Raydium launch (read-only; no wallet prompt)</button>'
    if data.count(old_button) != 1:
        raise ValueError('Expected one Stage 9 Raydium signing button')
    return data.replace(old_button, new_button, 1)


def atomic_write(path: Path, data: str):
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent, prefix='.orbit-stage12-', delete=False) as fp:
        fp.write(data)
        tmp = Path(fp.name)
    os.replace(tmp, path)


def main():
    if not CHAIN.is_file() or not APP.is_file():
        raise FileNotFoundError('ORBIT project not found. Run from /home/runner/workspace.')
    chain = CHAIN.read_text(encoding='utf-8')
    app = APP.read_text(encoding='utf-8')
    if TAG in chain and TAG in app:
        print('STAGE 12 ALREADY INSTALLED; nothing changed')
        return
    if TAG in chain or TAG in app:
        raise ValueError('Partial Stage 12 already present. Inspect source manually; no changes made.')
    new_chain = patch_chain(chain)
    new_app = patch_app(app)
    if chain[chain.index('export async function launchToken('):] != new_chain[new_chain.index('export async function launchToken('):]:
        raise ValueError('Safety check: existing token launch path changed unexpectedly')
    backup = ROOT / '.orbit-backups' / ('stage12-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    backup.mkdir(parents=True, exist_ok=False)
    shutil.copy2(CHAIN, backup/'chain.ts')
    shutil.copy2(APP, backup/'App.tsx')
    try:
        atomic_write(CHAIN, new_chain)
        atomic_write(APP, new_app)
    except Exception:
        shutil.copy2(backup/'chain.ts', CHAIN)
        shutil.copy2(backup/'App.tsx', APP)
        raise
    print('STAGE 12 INSTALLED')
    print('Backup:', backup)
    print('Read-only diagnostic only. Original launchToken unchanged.')
    print('NO wallet prompts, transaction sending, process restart, Git push, or Republish.')

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('STAGE 12 STOPPED:', exc, file=sys.stderr)
        sys.exit(1)
