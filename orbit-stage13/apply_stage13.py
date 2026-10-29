#!/usr/bin/env python3
"""Stage 13: Add legacy vs V0 inspection without changing launchToken.
No wallet signing, sending, restarts, pushes, or publish actions.
"""
from pathlib import Path
from datetime import datetime, timezone
import os, shutil, sys, tempfile

ROOT = Path.cwd() / 'artifacts/orbit-launchpad/original/orbit-solana-launchpad'
CHAIN = ROOT / 'web/src/chain.ts'
APP = ROOT / 'web/src/App.tsx'
TAG = 'ORBIT_STAGE13_LEGACY_READONLY'
INSPECT = (Path(__file__).parent / 'legacy_code.txt').read_text(encoding='utf-8')

def make_chain(s):
    if s.count('// ORBIT_STAGE12_READONLY_AUDIT') != 1 or s.count('// ORBIT_STAGE11_ALT_RESOLUTION') != 1:
        raise ValueError('Expected Stage 12 chain.ts not found')
    if TAG in s:
        raise ValueError('Stage 13 already partly installed; no changes made')
    pos = '// ORBIT_STAGE10_VERIFIED_DEVNET_LAUNCH'
    if s.count(pos) != 1:
        raise ValueError('Expected launchToken anchor not found')
    return s.replace(pos, INSPECT + pos, 1)

def make_app(s):
    if s.count('inspectRaydiumLaunch') != 2 or s.count('async function inspectRaydium()') != 1:
        raise ValueError('Expected Stage 12 App.tsx not found')
    if TAG in s:
        raise ValueError('Stage 13 already partly installed; no changes made')
    imp = 'inspectRaydiumLaunch'
    s = s.replace('inspectRaydiumLaunch} from', 'inspectRaydiumLaunch,inspectRaydiumLegacy} from', 1)
    anchor = ' async function create(e:React.FormEvent)'
    if s.count(anchor) != 1:
        raise ValueError('Cannot find create handler')
    handler = ''' // ORBIT_STAGE13_LEGACY_READONLY
 async function inspectLegacy(){
  if(busy)return;
  setBusy(true);setLaunchError('');
  try{
   const report=await inspectRaydiumLegacy(connection,config,wallet);
   setLaunchError(report.slice(0,6500));
   notify('Legacy comparison finished. No wallet signature requested.');
  }catch(err){
   setLaunchError('Legacy read-only comparison failed.\\n'+String((err as Error)?.message||err));
   notify('Legacy comparison failed; no transaction was sent.');
  }finally{setBusy(false)}
 }
'''
    s = s.replace(anchor, handler + anchor, 1)
    target = 'onClick={inspectRaydium}>Inspect Raydium launch (read-only; no wallet prompt)</button>'
    if s.count(target) != 1:
        raise ValueError('Expected Stage 12 Inspect button not found')
    new = target + "}" + '''{wallet.publicKey&&config.network==='devnet'&&<button className="button full" type="button" disabled={busy} onClick={inspectLegacy}>Inspect LEGACY launch (read-only; no wallet prompt)</button>}'''
    s = s.replace(target + "}", new, 1)
    return s

def atomic(path, data):
    with tempfile.NamedTemporaryFile('w',encoding='utf8',dir=path.parent,prefix='.orbit13-',delete=False) as f:
        f.write(data)
        name=f.name
    os.replace(name, path)

def main():
    if not CHAIN.is_file() or not APP.is_file():
        raise ValueError('Run from /home/runner/workspace and check ORBIT project path')
    c=CHAIN.read_text(encoding='utf8'); a=APP.read_text(encoding='utf8')
    if TAG in c and TAG in a:
        print('STAGE 13 ALREADY INSTALLED');return
    if TAG in c or TAG in a:
        raise ValueError('Stage 13 partially installed; no changes made')
    nc=make_chain(c); na=make_app(a)
    # No changes to live creation or existing Stage 12 read-only method.
    for marker in ['export async function launchToken(', 'export async function curveTrade(']:
        if c[c.index(marker):] != nc[nc.index(marker):]:
            raise ValueError('Safety check failed: existing launch/trade functions changed')
    backup=ROOT/'.orbit-backups'/('stage13-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    backup.mkdir(parents=True, exist_ok=False)
    shutil.copy2(CHAIN, backup/'chain.ts'); shutil.copy2(APP, backup/'App.tsx')
    try:
        atomic(CHAIN,nc);atomic(APP,na)
    except BaseException:
        shutil.copy2(backup/'chain.ts',CHAIN);shutil.copy2(backup/'App.tsx',APP)
        raise
    print('STAGE 13 INSTALLED: read-only legacy inspector')
    print('Backup:',backup)
    print('NO signing, sending, automated restart, push or Republish')

if __name__=='__main__':
    try:main()
    except Exception as e:
        print('STAGE 13 STOPPED:',e,file=sys.stderr)
        sys.exit(1)
