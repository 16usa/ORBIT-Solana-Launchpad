#!/usr/bin/env python3
"""ORBIT Stage14: Test LEGACY signing without broadcasting or modifying launchToken.
Runs from /home/runner/workspace. Idempotent, backs up both modified files.
"""
from pathlib import Path
from datetime import datetime, timezone
import os, shutil, sys, tempfile

ROOT = Path.cwd() / 'artifacts/orbit-launchpad/original/orbit-solana-launchpad'
CHAIN = ROOT / 'web/src/chain.ts'
APP = ROOT / 'web/src/App.tsx'
TAG = 'ORBIT_STAGE14_LEGACY_SIGN_ONLY'
CODE = (Path(__file__).parent / 'legacy_sign_code.txt').read_text(encoding='utf-8')

def patch_chain(s):
    if s.count('// ORBIT_STAGE13_LEGACY_READONLY') != 1 or s.count('// ORBIT_STAGE12_READONLY_AUDIT') != 1:
        raise ValueError('Stage 13/12 chain source is required')
    if s.count('export async function launchToken(') != 1:
        raise ValueError('Cannot locate live launch function')
    anchor = '// ORBIT_STAGE10_VERIFIED_DEVNET_LAUNCH'
    if s.count(anchor) != 1:
        raise ValueError('Expected Stage 10 code missing')
    if TAG in s:
        raise ValueError('Unexpected partial Stage 14 installation')
    candidate = s.replace(anchor, CODE + anchor, 1)
    if s[s.index(anchor):] != candidate[candidate.index(anchor):]:
        raise ValueError('Live launch/trade code was unexpectedly altered')
    return candidate

def patch_app(s):
    if s.count('// ORBIT_STAGE13_LEGACY_READONLY') != 1:
        raise ValueError('Stage 13 UI required')
    if TAG in s:
        raise ValueError('Unexpected partial Stage 14 installation')
    import_anchor = 'inspectRaydiumLegacy} from'
    if s.count(import_anchor) != 1:
        raise ValueError('Stage 13 import not located')
    s = s.replace(import_anchor, 'inspectRaydiumLegacy,testRaydiumLegacySigning} from', 1)
    anchor = ' async function create(e:React.FormEvent)'
    if s.count(anchor) != 1:
        raise ValueError('Create handler not found')
    handler = ''' // ORBIT_STAGE14_LEGACY_SIGN_ONLY
 // This requires an explicit wallet approval but NEVER sends any transaction.
 async function testLegacySignature(){
  if(busy)return;
  setBusy(true);setLaunchError('');
  try{
   const report=await testRaydiumLegacySigning(connection,config,wallet);
   setLaunchError(report);
   notify('Legacy signing passed; no transaction sent.');
  }catch(err){
   setLaunchError('Legacy signing test FAILED (no broadcast).\\n'+String((err as Error)?.message||err));
   notify('Legacy signature not obtained. No transaction sent.');
  }finally{setBusy(false)}
 }
'''
    s = s.replace(anchor, handler + anchor, 1)
    button = 'onClick={inspectLegacy}>Inspect LEGACY launch (read-only; no wallet prompt)</button>}'
    if s.count(button) != 1:
        raise ValueError('Stage 13 button not found')
    new = button + '''{wallet.publicKey&&config.network==='devnet'&&<button className="button full" type="button" disabled={busy} onClick={testLegacySignature}>Test LEGACY wallet signature (no broadcast)</button>}'''
    return s.replace(button, new, 1)

def atomic(path, body):
    with tempfile.NamedTemporaryFile('w',encoding='utf8',dir=path.parent,prefix='.orbit14-',delete=False) as f:
        f.write(body); tmp=f.name
    os.replace(tmp,path)

def main():
    if not CHAIN.is_file() or not APP.is_file():
        raise ValueError('Run from /home/runner/workspace in existing ORBIT project')
    c=CHAIN.read_text(encoding='utf8'); a=APP.read_text(encoding='utf8')
    if TAG in c and TAG in a:
        print('STAGE 14 ALREADY INSTALLED');return
    if TAG in c or TAG in a:
        raise ValueError('Stage 14 partially installed; no changes made')
    nc=patch_chain(c); na=patch_app(a)
    backup=ROOT/'.orbit-backups'/('stage14-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    backup.mkdir(parents=True,exist_ok=False)
    shutil.copy2(CHAIN,backup/'chain.ts');shutil.copy2(APP,backup/'App.tsx')
    try:
        atomic(CHAIN,nc); atomic(APP,na)
    except BaseException:
        shutil.copy2(backup/'chain.ts',CHAIN);shutil.copy2(backup/'App.tsx',APP)
        raise
    print('STAGE 14 INSTALLED: LEGACY sign-only diagnostic')
    print('Backup:',backup)
    print('No real creation path changes. No wallet prompts from installer, no broadcast, restart, Git push or Republish.')

if __name__=='__main__':
    try:main()
    except Exception as e:
        print('STAGE 14 STOPPED:',e,file=sys.stderr);sys.exit(1)
