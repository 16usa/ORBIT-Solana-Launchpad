#!/usr/bin/env python3
"""Read-only verification of Stage 24 anchors."""
import os
from pathlib import Path
root=Path(os.environ.get('ORBIT_SOURCE_ROOT','/home/runner/workspace/artifacts/orbit-launchpad/original/orbit-solana-launchpad'))
f=(root/'web/src/OrbitLive.tsx').read_text()
b=(root/'server/live.mjs').read_text()
checks={
 'frontend lifecycle marker':'ORBIT_STAGE24_LIVE_SESSION_LIFECYCLE' in f,
 'server lifecycle marker':'ORBIT_STAGE24_LIVE_SESSION_LIFECYCLE' in b,
 'no automatic server-end during effect cleanup':"if(publish)postJson('/api/live/end'" not in f,
 'explicit server-end remains':"await postJson('/api/live/end'" in f,
 'pending session keepalive':"const keepalive=()=>postJson('/api/live/heartbeat'" in f,
 'active only after media':"adminKey:session.adminKey,active:true" in f,
 'not visible before media':'s.active===true).map(publicLive)' in b,
 'not joinable before media':'s.active!==true' in b,
 '5-minute non-connected session allowance':'>300_000' in b,
}
for label,ok in checks.items():print(('PASS' if ok else 'FAIL')+' | '+label)
if not all(checks.values()): raise SystemExit('Stage 24 incomplete')
print('STAGE 24 VERIFIED (static contract checks; run full Replit test/typecheck/build next)')
