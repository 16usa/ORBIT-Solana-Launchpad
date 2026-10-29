#!/usr/bin/env python3
"""ORBIT Stage 24: fix Safari LiveKit session ending on React StrictMode and startup delays.
No restarting, republishing, wallet transactions, or GitHub actions.
"""
import os,sys,shutil
from pathlib import Path
ROOT=Path(os.environ.get('ORBIT_SOURCE_ROOT','/home/runner/workspace/artifacts/orbit-launchpad/original/orbit-solana-launchpad'))
FRONT=ROOT/'web/src/OrbitLive.tsx'
BACK=ROOT/'server/live.mjs'
MARK='ORBIT_STAGE24_LIVE_SESSION_LIFECYCLE'

def swap(s, old, new, name):
    n=s.count(old)
    if n!=1: raise RuntimeError(f'STAGE 24 STOPPED: {name}: expected one exact anchor, got {n}: {old[:105]!r}')
    return s.replace(old,new,1)

def main():
    if not FRONT.is_file() or not BACK.is_file():raise RuntimeError('STAGE 24 STOPPED: ORBIT LiveKit source missing')
    f=FRONT.read_text();b=BACK.read_text()
    if MARK in f and MARK in b:print('STAGE 24 ALREADY INSTALLED. No changes.');return
    if MARK in f or MARK in b:raise RuntimeError('STAGE 24 STOPPED: partial installation; inspect before retry')
    if 'ORBIT_STAGE23_SAFARI_HANDOFF' not in f or 'ORBIT_STAGE23_SAFARI_HANDOFF' not in b:
        raise RuntimeError('STAGE 24 STOPPED: install Stage 23 Safari patch first; no changes made')

    # A React StrictMode effect cleanup is NOT an explicit user instruction to end the broadcast.
    # In Dev, React does setup -> cleanup -> setup and the previous code deleted the server session.
    f=swap(f,
        "   if(publish)postJson('/api/live/end',{id:session.stream.id,adminKey:session.adminKey}).catch(()=>{});",
        "   // "+MARK+": only the explicit End stream button closes the server room.\n   // Component cleanup disconnects the local participant; the API removes abandoned streams after heartbeat expiry.",
        'OrbitLive.tsx cleanup')
    f=swap(f,
        "     // Safari media permission must be requested from an explicit button tap.\n     setNotice('Studio connected. Tap Start camera & microphone to go live.');",
        """     // Safari media permission must be requested from an explicit button tap.
     // Begin *private* keepalive now. The stream is not listed until camera/mic publish succeeds.
     const keepalive=()=>postJson('/api/live/heartbeat',{id:session.stream.id,adminKey:session.adminKey}).catch(()=>setNotice('Studio disconnected from API. Return to Phantom for a fresh link if this persists.'));
     await postJson('/api/live/heartbeat',{id:session.stream.id,adminKey:session.adminKey});
     if(disposed)return;
     heartbeatRef.current=setInterval(keepalive,15000);
     setNotice('Studio connected. Tap Start camera & microphone to go live.');""",
        'OrbitLive.tsx initialization')
    f=swap(f,
        "   await postJson('/api/live/heartbeat',{id:session.stream.id,adminKey:session.adminKey});\n   const pulse=()=>postJson('/api/live/heartbeat',{id:session.stream.id,adminKey:session.adminKey}).catch(()=>setNotice('Heartbeat failed — broadcast may have ended.'));\n   heartbeatRef.current=setInterval(pulse,15000);",
        "   await postJson('/api/live/heartbeat',{id:session.stream.id,adminKey:session.adminKey,active:true});",
        'OrbitLive.tsx first active heartbeat')
    f=swap(f,
        'Closing this page ends your stream.',
        'Leaving the page stops sending video; abandoned sessions expire automatically.',
        'OrbitLive.tsx session message')

    # Important: heartbeat alone is not a live broadcast; only a successful camera+mic start marks it live.
    b=swap(b,
        "const drafts=new Map();const streams=new Map();",
        "const drafts=new Map();const streams=new Map();\n// "+MARK+": 'active' becomes true only after Safari publishes camera/mic.",
        'live.mjs map declaration')
    b=swap(b,
        "for(const [k,s] of streams)if(s.lastSeen && t-s.lastSeen>80_000 || !s.lastSeen && t-new Date(s.createdAt).getTime()>90_000)streams.delete(k);",
        "for(const [k,s] of streams)if((s.lastSeen && t-s.lastSeen>80_000) || (!s.lastSeen && t-new Date(s.createdAt).getTime()>300_000))streams.delete(k);",
        'live.mjs expired session cleanup')
    b=swap(b,
        "filter(s=>s.lastSeen>0).map(publicLive)",
        "filter(s=>s.lastSeen>0&&s.active===true).map(publicLive)",
        'live.mjs list')
    b=swap(b,
        "   s.lastSeen=Date.now();return json(res,200,{ok:true});",
        "   s.lastSeen=Date.now();if(b.active===true)s.active=true;return json(res,200,{ok:true});",
        'live.mjs heartbeat')
    b=swap(b,
        "   if(!s||!s.lastSeen)return error(res,404,'Stream is not live');",
        "   if(!s||!s.lastSeen||s.active!==true)return error(res,404,'Stream is not live');",
        'live.mjs join')

    # Full validation is complete before writing anything; then write via atomic replacement.
    for p,data in ((FRONT,f),(BACK,b)):
        backup=p.with_name(p.name+'.before-stage24')
        if not backup.exists():shutil.copy2(p,backup)
        tmp=p.with_name(p.name+'.stage24.tmp')
        tmp.write_text(data)
        os.replace(tmp,p)
    print('STAGE 24 INSTALLED: StrictMode safe, 15s private heartbeat, broadcast marked live only after media starts.')
    print('No restart, push or Republish performed. Restart API yourself after test passes.')

if __name__=='__main__':
    try:main()
    except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
