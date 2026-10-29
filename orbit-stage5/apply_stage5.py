#!/usr/bin/env python3
"""ORBIT Stage 5: add readable diagnostics to DEVNET token creation UI.

No launch, wallet signature, process manipulation, deployment, or Git push.
"""
from pathlib import Path
from datetime import datetime, timezone
import shutil
import sys

ROOT = Path.cwd() / 'artifacts/orbit-launchpad/original/orbit-solana-launchpad'
APP = ROOT / 'web/src/App.tsx'
MARKER = 'ORBIT_STAGE5_LAUNCH_DIAGNOSTICS'


def once(s: str, a: str, b: str, label: str, required=True) -> str:
    n = s.count(a)
    if n == 0 and not required:
        return s
    if n != 1:
        raise RuntimeError(f'{label}: expected one occurrence, found {n}. No files changed.')
    return s.replace(a, b, 1)


def run():
    if not APP.is_file():
        raise RuntimeError('Cannot find ORBIT App.tsx. Run from Replit workspace root.')
    entire = APP.read_text('utf-8')
    if MARKER in entire:
        print('Stage 5 already installed. No changes made.')
        return
    first = entire.index('function Creator(')
    last = entire.index('function TokenDetails(', first)
    section = entire[first:last]
    # Stage 4 must be installed before diagnostic work; avoid hiding missing fixes.
    if 'await requireLaunchPlatform(connection,config,wallet.publicKey)' not in section:
        raise RuntimeError('Stage 4 preflight is not present in Creator. No changes made.')
    section = once(section,
        " const update=(k:string,v:string)=>setForm(p=>({...p,[k]:v}));",
        " // ORBIT_STAGE5_LAUNCH_DIAGNOSTICS\n const [launchError,setLaunchError]=useState('');\n const update=(k:string,v:string)=>setForm(p=>({...p,[k]:v}));",
        'Creator diagnostic state')
    section = once(section,
        " setBusy(true);setReceipt('');try{",
        " setBusy(true);setReceipt('');setLaunchError('');let stage='Preparing launch';try{",
        'Creator stage initializer')
    # Each phase is visible if an SDK, wallet, or network error occurs.
    phases = [
        ("  const network=await callApi<NetworkStatus>('/api/network-status');", 'Checking Solana Devnet'),
        ('  await requireLaunchPlatform(connection,config,wallet.publicKey);', 'Verifying Raydium PlatformConfig'),
        ("  const uploaded=await postJson<{id:string}>('/api/media'", 'Uploading token image'),
        ("  const meta=await postJson<{id:string;uri:string}>('/api/metadata'", 'Preparing token metadata'),
        ('  const tx=await launchToken(connection,config,wallet,', 'Building, signing or confirming Raydium launch'),
        ("  await postJson('/api/launches',pending);", 'Registering confirmed on-chain token'),
    ]
    for needle, title in phases:
        if section.count(needle) > 1:
            raise RuntimeError(f'Ambiguous phase: {title}. No changes made.')
        if section.count(needle) == 1:
            section = section.replace(needle, f"  stage='{title}';\n" + needle, 1)
    catch = "}catch(err){notify((err as Error).message)}finally{setBusy(false)}"
    replacement = """}catch(err){
  const problem=err as any;
  const cause=problem?.cause;
  const logs=Array.isArray(problem?.logs)?problem.logs:[];
  const text=[
   `Step: ${stage}`,
   `Error: ${String(problem?.name||'Unknown')}`,
   `Message: ${String(problem?.message||err)}`,
   cause?`Cause: ${String(cause?.message||cause)}`:'',
   problem?.reason?`Reason: ${String(problem.reason)}`:'',
   problem?.signature?`Transaction signature: ${String(problem.signature)}`:'',
   logs.length?`Logs: ${logs.slice(0,20).join('\\n')}`:'',
  ].filter(Boolean).join('\\n');
  console.error('[ORBIT Devnet launch error]',stage,err);
  setLaunchError(text.slice(0,3500));
  notify(String(problem?.message||'Token creation failed'));
 }finally{setBusy(false)}"""
    section = once(section, catch, replacement, 'Creator catch handler')
    # Render diagnostics beside the action, not just in a disappearing toast.
    jsx = "{receipt&&<p className=\"success-receipt\">Created token address: <code>{receipt}</code></p>}"
    extra = """{launchError&&<div role="alert" className="warning-text" style={{whiteSpace:'pre-wrap',overflowWrap:'anywhere',margin:'12px 0',fontSize:12}}><strong>Launch diagnostics</strong><br/>{launchError}<p style={{marginTop:10}}>If Phantom requested approval, check your Devnet transaction activity before attempting another launch.</p></div>}"""
    section = once(section, jsx, jsx + extra, 'Creator diagnostic display')
    modified = entire[:first] + section + entire[last:]
    if modified == entire:
        raise RuntimeError('No diagnostic changes created.')
    date = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backupdir = ROOT / '.orbit-backups' / ('stage5-'+date)
    backupdir.mkdir(parents=True, exist_ok=False)
    shutil.copy2(APP, backupdir / 'App.tsx')
    APP.write_text(modified, encoding='utf-8')
    print('Stage 5 diagnostic UI installed. Backup:', backupdir)
    print('Wallet signing, network transactions, running processes and GitHub untouched.')
    print('Next: run TypeScript and build checks, refresh DEV preview manually.')

if __name__ == '__main__':
    try:
        run()
    except Exception as e:
        print('Stage 5 install stopped:', e, file=sys.stderr)
        sys.exit(1)
