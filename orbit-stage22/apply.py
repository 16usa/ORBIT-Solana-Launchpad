#!/usr/bin/env python3
"""Install live streaming Stage 22. Does not restart any process or publish."""
from pathlib import Path
import shutil, re, sys

HERE=Path(__file__).resolve().parent
workspace=Path('/home/runner/workspace')
if not workspace.is_dir(): workspace=Path.cwd()
root=workspace/'artifacts/orbit-launchpad/original/orbit-solana-launchpad'
if not root.is_dir():
    print('STAGE 22 STOPPED: cannot locate ORBIT source at',root)
    sys.exit(1)
app=root/'web/src/App.tsx';server=root/'server/app.mjs';tests=root/'tests/server.test.mjs'
for f in [app,server,tests]:
    if not f.is_file(): raise SystemExit(f'STAGE 22 STOPPED: source file missing: {f}')
frontend=app.read_text();backend=server.read_text()
if 'import OrbitLive from' not in frontend:
    anchor="import './styles.css';"
    if anchor not in frontend: raise SystemExit('STAGE 22 STOPPED: App.tsx styles import not found')
    frontend=frontend.replace(anchor,anchor+"\nimport OrbitLive from './OrbitLive';",1)
if "if(h.startsWith('live/'))" not in frontend:
    anchor="if(h.startsWith('token/'))return {page:'token',mint:h.slice(6)};"
    if anchor not in frontend: raise SystemExit('STAGE 22 STOPPED: route parser changed; no changes made')
    frontend=frontend.replace(anchor,anchor+"if(h.startsWith('live/'))return {page:'live',mint:h.slice(5)};",1)
if "<OrbitLive directRoom={route.mint}/>" not in frontend:
    # Narrowly target only the Live placeholder, not the Page/Menu layout from newer stages.
    needle="{route.page==='live'&&<><div className=\"page-heading\""
    start=frontend.find(needle)
    if start<0:raise SystemExit('STAGE 22 STOPPED: Live placeholder not found; no changes made')
    end=frontend.find("</>}</>",start)
    # Prior builds used a one-line fragment ending </></> after the Empty widget; use a non-greedy anchored pattern.
    pat=r"\{route\.page==='live'&&<>.*?heading=\"Live streaming is not available yet\".*?</>\}"
    hits=list(re.finditer(pat,frontend,re.S))
    if len(hits)!=1:raise SystemExit(f'STAGE 22 STOPPED: expected 1 Live placeholder, found {len(hits)}; no changes made')
    frontend=frontend[:hits[0].start()]+"{route.page==='live'&&<OrbitLive directRoom={route.mint}/>}"+frontend[hits[0].end():]
if "import {makeLiveHandler} from './live.mjs';" not in backend:
    anchor="import { randomUUID } from 'node:crypto';"
    if anchor not in backend: raise SystemExit('STAGE 22 STOPPED: server import anchor missing; no changes made')
    backend=backend.replace(anchor,anchor+"\nimport {makeLiveHandler} from './live.mjs';",1)
if 'const handleLiveRoute=makeLiveHandler' not in backend:
    anchor='export function makeServer(){'
    if anchor not in backend: raise SystemExit('STAGE 22 STOPPED: server factory anchor missing; no changes made')
    backend=backend.replace(anchor,'const handleLiveRoute=makeLiveHandler({dataDir,json,error,readJson});\n'+anchor,1)
if "if(pathname.startsWith('/api/live'))return await handleLiveRoute(req,res,u);" not in backend:
    pat=r"(if\(pathname\.startsWith\('/api/'\) && !hitRate\(req\)\)return error\(res,429,'Rate limited'\);)"
    if len(re.findall(pat,backend))!=1: raise SystemExit('STAGE 22 STOPPED: API rate limiter anchor changed; no changes made')
    backend=re.sub(pat,r"\1\n  if(pathname.startsWith('/api/live'))return await handleLiveRoute(req,res,u);",backend,count=1)
# Stage 22 adds tests using Node built-in crypto; no test dependencies.
test_code=(HERE/'live.test.mjs').read_text()
unit_target=root/'tests/live.test.mjs'
changes={app:frontend,server:backend,root/'server/live.mjs':(HERE/'live.mjs').read_text(),root/'web/src/OrbitLive.tsx':(HERE/'OrbitLive.tsx').read_text(),root/'web/src/orbit-live.css':(HERE/'orbit-live.css').read_text(),unit_target:test_code}
# Backup existing editable files only, one copy per stage.
for f in [app,server]:
    bak=f.with_name(f.name+'.before-stage22')
    if not bak.exists():shutil.copy2(f,bak)
for f,content in changes.items():
    f.parent.mkdir(parents=True,exist_ok=True)
    if not f.exists() or f.read_text()!=content:f.write_text(content)
print('STAGE 22 INSTALLED: LiveKit player, wallet-auth API, tests, live UI')
print('NEXT: pnpm --filter @workspace/orbit-launchpad add livekit-client@2.23.0 livekit-server-sdk@2.19.2')
print('NOTE: LIVEKIT_URL / LIVEKIT_API_KEY / LIVEKIT_API_SECRET must be configured on the API server.')
print('No restarts, GitHub pushes or deployments performed.')
