#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
workspace=Path('/home/runner/workspace')
if not workspace.is_dir():workspace=Path.cwd()
root=workspace/'artifacts/orbit-launchpad/original/orbit-solana-launchpad'
checks={
 'web/src/App.tsx':['import OrbitLive from',"if(h.startsWith('live/'))",'<OrbitLive directRoom={route.mint}/>'],
 'web/src/OrbitLive.tsx':['livekit-client','/api/live/start','/api/live/join','signMessage','room.connect'],
 'web/src/orbit-live.css':['.orbit-live-stage','.orbit-live-controls'],
 'server/app.mjs':["import {makeLiveHandler} from './live.mjs';",'handleLiveRoute(req,res,u)'],
 'server/live.mjs':['verifyEd25519','canPublish:publish','/api/live/heartbeat','/api/live/report'],
 'tests/live.test.mjs':['Live authorization validates true Ed25519']}
for name,markers in checks.items():
 p=root/name
 if not p.is_file() or any(m not in p.read_text() for m in markers):
  raise SystemExit('STAGE 22 VERIFY FAILED: '+name)
for name in ['server/app.mjs','server/live.mjs']:
 result=subprocess.run(['node','--check',str(root/name)],capture_output=True,text=True)
 if result.returncode:raise SystemExit('STAGE 22 SYNTAX FAILED: '+name+'\n'+result.stderr)
print('STAGE 22 VERIFIED: routes, HTML UI, authorization and Node syntax present.')
print('Next: install dependencies, run tests, typecheck and build in Replit.')
