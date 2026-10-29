#!/usr/bin/env python3
"""ORBIT Stage 23: wallet signature in Phantom, one-time Safari LiveKit studio.
No service restarts, pushes, republish, or secret-file edits.
"""
from pathlib import Path
import os, shutil, sys, tempfile
HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get('ORBIT_SOURCE_ROOT', '/home/runner/workspace/artifacts/orbit-launchpad/original/orbit-solana-launchpad'))
LIVE = ROOT / 'web/src/OrbitLive.tsx'
SERVER = ROOT / 'server/live.mjs'
TEST = ROOT / 'tests/live-safari.test.mjs'
CSS = ROOT / 'web/src/orbit-live.css'
TAG='ORBIT_STAGE23_SAFARI_HANDOFF'

def replace_one(src, old, new, file):
    n = src.count(old)
    if n != 1:
        raise RuntimeError(f'STAGE 23 STOPPED: {file}: expected one patch anchor, found {n}: {old[:120]!r}')
    return src.replace(old,new,1)

def main():
    for path in (LIVE, SERVER, CSS):
        if not path.is_file(): raise RuntimeError(f'STAGE 23 STOPPED: missing {path}')
    front=LIVE.read_text();back=SERVER.read_text();styles=CSS.read_text()
    if TAG in front and TAG in back:
        print('STAGE 23 ALREADY INSTALLED: no changes made');return
    if TAG in front or TAG in back: raise RuntimeError('STAGE 23 STOPPED: partial installation detected')
    for marker in ('function LivePlayer(', 'const start=async()=>', "const join=useCallback(", 'function reportError(', 'export default function OrbitLive('):
        if marker not in front:raise RuntimeError('STAGE 23 STOPPED: unknown frontend revision; '+marker)
    for marker in ("if(p==='/api/live/start'&&req.method==='POST')", 'const drafts=new Map();const streams=new Map();', "if(p==='/api/live/heartbeat'&&req.method==='POST')"):
        if marker not in back: raise RuntimeError('STAGE 23 STOPPED: unknown API revision; '+marker)
    # Server: the signing challenge remains one-time; new handoff stores only hashes of bearer codes.
    back=replace_one(back,'const drafts=new Map();const streams=new Map();',
        "const drafts=new Map();const streams=new Map();\n// "+TAG+"\nconst handoffs=new Map(); // code SHA256 -> { wallet, title, expires }; RAM only, single-instance Devnet\nfunction handoffKey(code){return typeof code==='string'&&/^[a-f0-9]{64}$/.test(code)?sha(code).toString('hex'):'';}\n",'server/live.mjs')
    back=replace_one(back," const t=Date.now();for(const [k,c] of drafts)if(c.until<t)drafts.delete(k);",
        " const t=Date.now();for(const [k,c] of drafts)if(c.until<t)drafts.delete(k);\n for(const [k,c] of handoffs)if(c.expires<t)handoffs.delete(k);",'server/live.mjs')
    endpoint="""  // Stage 23: authorize with Phantom, but DO NOT start LiveKit or ask for media here.
  // Code in the Safari URL is a short-lived, single-use bearer credential, not a wallet secret.
  if(p==='/api/live/prepare'&&req.method==='POST'){
   if(!enabled())return error(res,503,'Live streaming is not configured');
   const b=await readJson(req,1400),c=drafts.get(b?.nonce);if(c)drafts.delete(b.nonce);
   if(!c||c.until<Date.now()||c.wallet!==b.wallet||!verifySignature(c.wallet,c.message,b.signature))return error(res,403,'Wallet authorization failed. Sign a new Phantom challenge.');
   const title=safeTitle(b.title);if(title.length<3)return error(res,400,'Stream title must be at least 3 characters');
   if([...streams.values()].some(s=>s.wallet===c.wallet))return error(res,409,'This wallet already has an active stream');
   if([...handoffs.values()].some(h=>h.wallet===c.wallet))return error(res,409,'A Safari handoff already exists for this wallet. Open the existing link or let it expire.');
   if(handoffs.size>=40)return error(res,429,'Too many pending broadcasts');
   const code=randomBytes(32).toString('hex'),expires=Date.now()+300_000;
   handoffs.set(handoffKey(code),{wallet:c.wallet,title,expires});
   res.setHeader('Cache-Control','no-store');
   return json(res,201,{code,expiresAt:new Date(expires).toISOString()});
  }
  // Must be POST, not GET. URL previews and link scanners cannot start a stream.
  if(p==='/api/live/redeem'&&req.method==='POST'){
   if(!enabled())return error(res,503,'Live streaming is not configured');
   const b=await readJson(req,500),key=handoffKey(b?.code);
   const h=key&&handoffs.get(key);if(key)handoffs.delete(key); // atomic, single use
   if(!h||h.expires<Date.now())return error(res,403,'This Safari handoff link is expired or already used. Return to Phantom for a fresh link.');
   if([...streams.values()].some(s=>s.wallet===h.wallet))return error(res,409,'This wallet already has an active stream');
   if(streams.size>=10)return error(res,429,'Maximum concurrent test streams reached');
   const id=randomUUID(),room='orbit-live-'+id,adminKey=randomBytes(32).toString('hex');
   const {service,url}=await clients();await service.createRoom({name:room,emptyTimeout:120,maxParticipants:120});
   const token=await tokenFor(room,'host-'+id,true);
   streams.set(id,{id,room,wallet:h.wallet,title:h.title,createdAt:new Date().toISOString(),lastSeen:0,secret:sha(adminKey)});
   res.setHeader('Cache-Control','no-store');
   return json(res,201,{stream:publicLive(streams.get(id)),url,token,adminKey});
  }
"""
    back=replace_one(back,"  if(p==='/api/live/start'&&req.method==='POST'){",endpoint+"  if(p==='/api/live/start'&&req.method==='POST'){",'server/live.mjs')
    # Frontend: wallet signs in Phantom, Safari gets a one-time link; Safari explicitly starts camera on tap.
    front=replace_one(front," const [busy,setBusy]=useState(false);\n useEffect(()=>{", " const [busy,setBusy]=useState(false);\n const [broadcasting,setBroadcasting]=useState(false);\n const heartbeatRef=useRef<ReturnType<typeof setInterval>|null>(null);\n useEffect(()=>{",'OrbitLive.tsx')
    front=replace_one(front,"  let disposed=false;let heartbeat:ReturnType<typeof setInterval>|undefined;", "  let disposed=false;",'OrbitLive.tsx')
    old="""    if(publish){
     if(!navigator.mediaDevices?.getUserMedia)throw new Error('This browser cannot use the camera or microphone. Open ORBIT in a compatible HTTPS browser.');
     await room.localParticipant.setCameraEnabled(true,{facingMode:'user'});
     await room.localParticipant.setMicrophoneEnabled(true);
     if(disposed)return;
     const localVideo=room.localParticipant.getTrackPublication(Track.Source.Camera)?.videoTrack;
     if(localVideo&&videoRef.current){const el=localVideo.attach();if(el instanceof HTMLVideoElement){el.muted=true;el.playsInline=true;el.autoplay=true}videoRef.current.appendChild(el)}
     const pulse=()=>postJson('/api/live/heartbeat',{id:session.stream.id,adminKey:session.adminKey}).catch(()=>setNotice('Server heartbeat failed — the stream may end.'));
     await pulse();heartbeat=setInterval(pulse,15000);
     setNotice('You are LIVE · Camera and microphone on');
    }else{"""
    front=replace_one(front,old,"""    if(publish){
     // Safari media permission must be requested from an explicit button tap.
     setNotice('Studio connected. Tap Start camera & microphone to go live.');
    }else{""",'OrbitLive.tsx')
    front=replace_one(front,"  return ()=>{disposed=true;if(heartbeat)clearInterval(heartbeat);room.disconnect();roomRef.current=null;clearElements();", "  return ()=>{disposed=true;if(heartbeatRef.current){clearInterval(heartbeatRef.current);heartbeatRef.current=null;}room.disconnect();roomRef.current=null;clearElements();",'OrbitLive.tsx')
    original=""" const toggleCam=async()=>{try{const v=!camera;await roomRef.current?.localParticipant.setCameraEnabled(v);setCamera(v)}catch(e){setNotice(reportError(e))}};"""
    replacement=""" const startCamera=async()=>{
  if(!roomRef.current||broadcasting||busy)return;
  if(!navigator.mediaDevices?.getUserMedia){setNotice('Camera and microphone require Safari on HTTPS. Open this link directly in Safari.');return;}
  setBusy(true);
  try{
   const room=roomRef.current;
   await room.localParticipant.setCameraEnabled(true,{facingMode:'user'});
   await room.localParticipant.setMicrophoneEnabled(true);
   const localVideo=room.localParticipant.getTrackPublication(Track.Source.Camera)?.videoTrack;
   if(localVideo&&videoRef.current){videoRef.current.replaceChildren();const el=localVideo.attach();if(el instanceof HTMLVideoElement){el.muted=true;el.playsInline=true;el.autoplay=true;}videoRef.current.appendChild(el);}
   await postJson('/api/live/heartbeat',{id:session.stream.id,adminKey:session.adminKey});
   const pulse=()=>postJson('/api/live/heartbeat',{id:session.stream.id,adminKey:session.adminKey}).catch(()=>setNotice('Heartbeat failed — broadcast may have ended.'));
   heartbeatRef.current=setInterval(pulse,15000);
   setCamera(true);setMic(true);setBroadcasting(true);setNotice('You are LIVE · Camera and microphone on');
  }catch(e){setNotice(reportError(e));try{await roomRef.current?.localParticipant.setCameraEnabled(false);await roomRef.current?.localParticipant.setMicrophoneEnabled(false);}catch{}}
  finally{setBusy(false)}
 };
 const toggleCam=async()=>{try{const v=!camera;await roomRef.current?.localParticipant.setCameraEnabled(v);setCamera(v)}catch(e){setNotice(reportError(e))}};"""
    front=replace_one(front,original,replacement,'OrbitLive.tsx')
    front=replace_one(front,'<span className="orbit-live-pill">● LIVE</span>{!connected&&', '<span className="orbit-live-pill" style={{display:(!connected||(publish&&!broadcasting))?\'none\':undefined}}>● LIVE</span>{!connected&&','OrbitLive.tsx')
    front=replace_one(front,"   {publish?<><button onClick={toggleCam} disabled={!connected}>","   {publish&&!broadcasting?<button className=\"orbit-live-start\" onClick={startCamera} disabled={!connected||busy}><Camera/> {busy?'Requesting permission…':'Start camera & microphone'}</button>:null}\n   {publish&&broadcasting?<><button onClick={toggleCam} disabled={!connected}>",'OrbitLive.tsx')
    front=replace_one(front,"{mic?'Mic on':'Mic off'}</button></>:<button onClick={enableSound}","{mic?'Mic on':'Mic off'}</button></>:!publish?<button onClick={enableSound}",'OrbitLive.tsx')
    front=replace_one(front,"{sound?'Sound enabled':'Enable sound'}</button>}","{sound?'Sound enabled':'Enable sound'}</button>:null}",'OrbitLive.tsx')
    front=replace_one(front," const [session,setSession]=useState<Session|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState('');", " // "+TAG+"\n const [session,setSession]=useState<Session|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState('');\n const [handoff,setHandoff]=useState<{url:string;expiresAt:string}|null>(null);\n const redeemed=useRef(false);\n const [copyNotice,setCopyNotice]=useState('');",'OrbitLive.tsx')
    front=replace_one(front," useEffect(()=>{if(directRoom&&!session&&!busy)void join(directRoom)},[directRoom,session,join]);", """ useEffect(()=>{if(directRoom&&!directRoom.startsWith('host/')&&!session&&!busy)void join(directRoom)},[directRoom,session,join]);
 const hostCode=directRoom.startsWith('host/')?directRoom.slice(5):'';
 const redeem=async()=>{
  if(!/^[a-f0-9]{64}$/.test(hostCode)||redeemed.current)return;
  redeemed.current=true;setBusy(true);setError('');
  try{
   const result=await postJson<Session>('/api/live/redeem',{code:hostCode});
   // Remove the bearer code from the Safari address bar immediately after redemption.
   history.replaceState(null,'',location.pathname+location.search+'#/live');
   setSession(result);
  }catch(e){setError(reportError(e));history.replaceState(null,'',location.pathname+location.search+'#/live');}
  finally{setBusy(false)}
 };
 const copyHandoff=async()=>{if(!handoff)return;try{await navigator.clipboard.writeText(handoff.url);setCopyNotice('Copied. Paste the link into Safari’s address bar.');}catch{setCopyNotice('Copy the link shown below, then paste it into Safari.')}};
""",'OrbitLive.tsx')
    front=replace_one(front,"  if(!navigator.mediaDevices?.getUserMedia){setError('Camera/microphone unavailable in this browser.');return}\n",'', 'OrbitLive.tsx')
    front=replace_one(front,"   const result=await postJson<Session>('/api/live/start',{wallet:address,nonce:challenge.nonce,signature,title});\n   setSession(result);", """   const result=await postJson<{code:string;expiresAt:string}>('/api/live/prepare',{wallet:address,nonce:challenge.nonce,signature,title});
   const url=new URL(location.href);url.hash=`#/live/host/${result.code}`;
   setHandoff({url:url.toString(),expiresAt:result.expiresAt});""",'OrbitLive.tsx')
    front=replace_one(front," const leave=()=>{setSession(null);location.hash='#/live';load()};", " const leave=()=>{setSession(null);setHandoff(null);redeemed.current=false;location.hash='#/live';load()};",'OrbitLive.tsx')
    front=replace_one(front,"  {session?<LivePlayer key={session.stream.id} session={session} onLeave={leave}/>:", """  {session?<LivePlayer key={session.stream.id} session={session} onLeave={leave}/>:
  hostCode?<div className="orbit-live-form"><h3><Camera/> Safari broadcast studio</h3><p>Your Phantom wallet has already authorized this session. Tap below to redeem your one-time link, then allow Safari to use your camera and microphone.</p><button className="orbit-live-start" disabled={busy||redeemed.current||!/^[a-f0-9]{64}$/.test(hostCode)} onClick={redeem}>{busy?'Opening studio…':'Open studio in Safari'}</button><p className="orbit-live-note">If the link has expired, return to ORBIT in Phantom and authorize a fresh one.</p></div>:
  handoff?<div className="orbit-live-form"><h3><Camera/> Continue in Safari</h3><p>Phantom wallet authorization succeeded. Your stream has not started yet.</p><p>Copy this temporary, one-time link. Switch to the Safari app and paste it into the address bar. Then tap Open studio and Start camera & microphone.</p><button className="orbit-live-start" onClick={copyHandoff}><Copy/> Copy Safari link</button><p className="orbit-live-handoff-url">{handoff.url}</p>{copyNotice&&<p className="orbit-live-note" role="status">{copyNotice}</p>}<p className="orbit-live-note">Expires at {new Date(handoff.expiresAt).toLocaleTimeString()}. Anyone with this link can start your stream until it is used. Do not share it.</p></div>:""", 'OrbitLive.tsx')
    # Camera starts only after Safari user action; no navigator.share or cross-app camera attempts.
    styles += "\n/* "+TAG+" */\n.orbit-live-handoff-url{overflow-wrap:anywhere;user-select:all;padding:12px;border:1px solid #303438;border-radius:8px;font-size:12px;color:#aeb4c0}\n.orbit-live-secondary{border:1px solid #3a4045;border-radius:8px;padding:10px 16px;color:#d4d7dc;background:#191b1e;margin-top:12px}\n"
    # Avoid file mutations until every anchor validates.
    contents = [(SERVER,back),(LIVE,front),(CSS,styles),(TEST,(HERE/'live-safari.test.mjs').read_text())]
    for f,_ in contents:
        if f.exists():
            bak=f.with_name(f.name+'.before-stage23')
            if not bak.exists():shutil.copy2(f,bak)
    for f,body in contents:
        f.parent.mkdir(parents=True,exist_ok=True)
        tmp=f.with_name(f.name+'.stage23.tmp')
        tmp.write_text(body)
        os.replace(tmp,f)
    print('STAGE 23 INSTALLED: Phantom signature -> one-time Safari handoff -> user-gesture camera/mic -> LiveKit')
    print('NO restart, push, republish or real-wallet transaction performed.')
    print('NEXT: pnpm --filter @workspace/orbit-launchpad run test && pnpm --filter @workspace/orbit-launchpad run check:syntax && pnpm --filter @workspace/orbit-launchpad run typecheck && pnpm --filter @workspace/orbit-launchpad run build')

if __name__ == '__main__':
    try:main()
    except Exception as e: print(str(e),file=sys.stderr);sys.exit(1)
