import React, {useCallback, useEffect, useRef, useState} from 'react';
import {useWallet} from '@solana/wallet-adapter-react';
import {Room, RoomEvent, Track, type RemoteTrack} from 'livekit-client';
import {Radio, Video, VideoOff, Mic, MicOff, Users, Play, X, Copy, Flag, RefreshCw, Camera, ShieldAlert} from 'lucide-react';
import {callApi,postJson,shorten} from './api';
import './orbit-live.css';

type Stream={id:string;title:string;creator:string;createdAt:string};
type LiveList={enabled:boolean;items:Stream[];message?:string};
type Session={stream:Stream;url:string;token:string;adminKey?:string};
function reportError(e:unknown){return e instanceof Error?e.message:String(e)}

function LivePlayer({session,onLeave}:{session:Session;onLeave:()=>void}){
 const publish=!!session.adminKey;
 const videoRef=useRef<HTMLDivElement>(null),audioRef=useRef<HTMLDivElement>(null),roomRef=useRef<Room|null>(null);
 const [connected,setConnected]=useState(false),[camera,setCamera]=useState(true),[mic,setMic]=useState(true),[notice,setNotice]=useState('Connecting to live stream…');
 const [sound,setSound]=useState(false),[reportOpen,setReportOpen]=useState(false),[reason,setReason]=useState(''),[reportSent,setReportSent]=useState(false);
 const [busy,setBusy]=useState(false);
 useEffect(()=>{
  let disposed=false;let heartbeat:ReturnType<typeof setInterval>|undefined;
  const room=new Room({adaptiveStream:true,dynacast:true});roomRef.current=room;
  const clearElements=()=>{for(const box of [videoRef.current,audioRef.current]){if(box)box.replaceChildren()}};
  const attach=(track:RemoteTrack)=>{
   const box=track.kind===Track.Kind.Video?videoRef.current:audioRef.current;if(!box)return;
   if(track.kind===Track.Kind.Video){for(const child of Array.from(box.children))child.remove()}
   const element=track.attach();element.autoplay=true;
   if(element instanceof HTMLVideoElement){element.playsInline=true;element.muted=true}
   box.appendChild(element);
  };
  room.on(RoomEvent.TrackSubscribed,(track)=>{if(!disposed)attach(track)});
  room.on(RoomEvent.TrackUnsubscribed,(track)=>{for(const el of track.detach())el.remove()});
  room.on(RoomEvent.Disconnected,()=>{if(!disposed){setConnected(false);setNotice('Disconnected from video server.')}});
  (async()=>{
   try{
    await room.connect(session.url,session.token,{autoSubscribe:true});
    if(disposed)return;
    if(publish){
     if(!navigator.mediaDevices?.getUserMedia)throw new Error('This browser cannot use the camera or microphone. Open ORBIT in a compatible HTTPS browser.');
     await room.localParticipant.setCameraEnabled(true,{facingMode:'user'});
     await room.localParticipant.setMicrophoneEnabled(true);
     if(disposed)return;
     const localVideo=room.localParticipant.getTrackPublication(Track.Source.Camera)?.videoTrack;
     if(localVideo&&videoRef.current){const el=localVideo.attach();if(el instanceof HTMLVideoElement){el.muted=true;el.playsInline=true;el.autoplay=true}videoRef.current.appendChild(el)}
     const pulse=()=>postJson('/api/live/heartbeat',{id:session.stream.id,adminKey:session.adminKey}).catch(()=>setNotice('Server heartbeat failed — the stream may end.'));
     await pulse();heartbeat=setInterval(pulse,15000);
     setNotice('You are LIVE · Camera and microphone on');
    }else{
     for(const remote of room.remoteParticipants.values())for(const pub of remote.trackPublications.values())if(pub.track)attach(pub.track as RemoteTrack);
     setNotice('Watching live · Tap Enable sound if needed');
    }
    setConnected(true);
   }catch(e){if(!disposed){setNotice(reportError(e));setConnected(false)}}
  })();
  return ()=>{disposed=true;if(heartbeat)clearInterval(heartbeat);room.disconnect();roomRef.current=null;clearElements();
   if(publish)postJson('/api/live/end',{id:session.stream.id,adminKey:session.adminKey}).catch(()=>{});
  };
 },[session,publish]);
 const toggleCam=async()=>{try{const v=!camera;await roomRef.current?.localParticipant.setCameraEnabled(v);setCamera(v)}catch(e){setNotice(reportError(e))}};
 const toggleMic=async()=>{try{const v=!mic;await roomRef.current?.localParticipant.setMicrophoneEnabled(v);setMic(v)}catch(e){setNotice(reportError(e))}};
 const enableSound=async()=>{try{await roomRef.current?.startAudio();setSound(true)}catch(e){setNotice(reportError(e))}};
 const sendReport=async()=>{try{await postJson('/api/live/report',{id:session.stream.id,reason});setReportSent(true);setReportOpen(false)}catch(e){setNotice(reportError(e))}};
 const share=()=>{const url=new URL(location.href);url.hash=`#/live/${session.stream.id}`;
  navigator.clipboard.writeText(url.toString()).then(()=>setNotice('Stream link copied')).catch(()=>setNotice('Copy link from browser address bar.'))};
 const stop=async()=>{if(busy)return;setBusy(true);try{if(publish)await postJson('/api/live/end',{id:session.stream.id,adminKey:session.adminKey});}catch(e){setNotice(reportError(e))}onLeave()};
 return <div className="orbit-live-view">
  <div className="orbit-live-header"><div><span className="orbit-live-eyebrow">{publish?'YOUR BROADCAST':'LIVE NOW'}</span><h2>{session.stream.title}</h2><small>By {shorten(session.stream.creator,7)} · {publish?'Broadcaster':'Viewer'}</small></div><button className="orbit-live-close" onClick={stop} aria-label="Leave live stream"><X/></button></div>
  <div className="orbit-live-stage"><div className="orbit-live-video" ref={videoRef}/><div className="orbit-live-audio" ref={audioRef}/><span className="orbit-live-pill">● LIVE</span>{!connected&&<div className="orbit-live-placeholder"><Video size={36}/><span>{notice}</span></div>}</div>
  <div className="orbit-live-status" role="status">{notice}</div>
  <div className="orbit-live-controls">
   {publish?<><button onClick={toggleCam} disabled={!connected}>{camera?<Camera/>:<VideoOff/>}{camera?'Camera on':'Camera off'}</button><button onClick={toggleMic} disabled={!connected}>{mic?<Mic/>:<MicOff/>}{mic?'Mic on':'Mic off'}</button></>:<button onClick={enableSound} disabled={!connected}>{sound?<Mic/>:<MicOff/>}{sound?'Sound enabled':'Enable sound'}</button>}
   <button onClick={share}><Copy/>Share link</button>
   <button className={publish?'orbit-live-danger':''} onClick={stop}>{publish?'End stream':'Leave'}</button>
  </div>
  {!publish&&<div className="orbit-live-report"><button disabled={reportSent} onClick={()=>setReportOpen(!reportOpen)}><Flag size={16}/>{reportSent?'Report received':'Report stream'}</button>{reportOpen&&<div className="orbit-live-report-form"><textarea maxLength={140} placeholder="Why are you reporting this stream?" value={reason} onChange={e=>setReason(e.target.value)}/><button disabled={reason.trim().length<6} onClick={sendReport}>Send report</button></div>}</div>}
  {publish&&<p className="orbit-live-tip"><ShieldAlert size={15}/> You are broadcasting live audio/video. Do not share private information. Closing this page ends your stream.</p>}
 </div>;
}

export default function OrbitLive({directRoom}:{directRoom:string}){
 const wallet=useWallet();const [list,setList]=useState<LiveList>({enabled:false,items:[]});const [title,setTitle]=useState('');
 const [session,setSession]=useState<Session|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const load=useCallback(async()=>{try{const data=await callApi<LiveList>('/api/live');setList(data)}catch(e){setError(reportError(e))}},[]);
 useEffect(()=>{load();const timer=setInterval(load,10000);return()=>clearInterval(timer)},[load]);
 const join=useCallback(async(id:string)=>{setBusy(true);setError('');try{const result=await postJson<Session>('/api/live/join',{id});setSession(result);if(location.hash!==`#/live/${id}`)location.hash=`#/live/${id}`;}catch(e){setError(reportError(e));if(location.hash.startsWith('#/live/'))location.hash='#/live'}finally{setBusy(false)}},[]);
 useEffect(()=>{if(directRoom&&!session&&!busy)void join(directRoom)},[directRoom,session,join]);
 const start=async()=>{
  if(!wallet.publicKey||!wallet.signMessage){setError('Connect a Solana wallet that supports signMessage to go live.');return}
  if(!navigator.mediaDevices?.getUserMedia){setError('Camera/microphone unavailable in this browser.');return}
  setBusy(true);setError('');
  try{
   const address=wallet.publicKey.toBase58();const challenge=await postJson<{nonce:string;message:string}>('/api/live/challenge',{wallet:address});
   const raw=await wallet.signMessage(new TextEncoder().encode(challenge.message));
   const signature=btoa(Array.from(raw,(v)=>String.fromCharCode(v)).join(''));
   const result=await postJson<Session>('/api/live/start',{wallet:address,nonce:challenge.nonce,signature,title});
   setSession(result);
  }catch(e){setError(reportError(e))}finally{setBusy(false)}
 };
 const leave=()=>{setSession(null);location.hash='#/live';load()};
 return <section className="orbit-live-page">
  <div className="page-heading"><small className="eyebrow">ORBIT / COMMUNITY</small><h1>Live streams</h1></div>
  {session?<LivePlayer key={session.stream.id} session={session} onLeave={leave}/>:
  <><div className="orbit-live-intro"><Radio size={21}/><span>Real-time video and audio. Anyone can watch; connected wallets can broadcast.</span></div>
  {!list.enabled?<div className="orbit-live-unavailable"><ShieldAlert size={24}/><h3>Live streaming needs a video server</h3><p>{list.message||'The server-side LiveKit connection is not configured.'}</p><p>Set LIVEKIT_URL, LIVEKIT_API_KEY and LIVEKIT_API_SECRET on the ORBIT API server. No simulated streams will be shown.</p></div>:
  <><div className="orbit-live-form"><h3><Video size={21}/> Start a live stream</h3><p>Broadcast from your camera and microphone. Phantom will ask for a message signature (not a transaction).</p><label htmlFor="orbit-live-title">Stream title</label><input id="orbit-live-title" type="text" maxLength={64} value={title} onChange={e=>setTitle(e.target.value)} placeholder="What are you streaming?"/>
   <button className="orbit-live-start" disabled={busy||title.trim().length<3||!wallet.publicKey||!wallet.signMessage} onClick={start}><Radio size={19}/>{busy?'Connecting…':'Go live'}</button>
   {!wallet.publicKey&&<span className="orbit-live-note">Connect Phantom using the button in the header to start broadcasting.</span>}
  </div>
  <div className="orbit-live-list-title"><h2>Live now <span>{list.items.length}</span></h2><button onClick={load} title="Refresh"><RefreshCw size={18}/></button></div>
  {list.items.length?<div className="orbit-live-list">{list.items.map(s=><button key={s.id} onClick={()=>join(s.id)} disabled={busy}><span className="orbit-live-broadcast-icon"><Radio/></span><span><b>{s.title}</b><small>By {shorten(s.creator,7)} · Started {new Date(s.createdAt).toLocaleTimeString()}</small></span><span className="orbit-live-join"><Play size={17}/> Watch</span></button>)}</div>:
  <div className="orbit-live-empty"><Users size={28}/><strong>No one is live yet</strong><span>Start a stream to be the first broadcaster.</span></div>}
  </>}
  </>}
  {error&&<p className="orbit-live-error" role="alert">{error}</p>}
 </section>;
}
