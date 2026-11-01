import React, {useEffect, useRef, useState} from 'react';
import {PrivyProvider, usePrivy} from '@privy-io/react-auth';

const appId = import.meta.env.VITE_PRIVY_APP_ID || '';
export function PrivyBoundary({children}:{children:React.ReactNode}) {
  if (!appId) return <>{children}</>;
  return <PrivyProvider appId={appId} config={{loginMethods:['email','wallet'], appearance:{theme:'dark'}}}>{children}</PrivyProvider>;
}
function AccountMenu() {
  const {ready, authenticated, login, logout, user} = usePrivy();
  const [open,setOpen] = useState(false);
  const root = useRef<HTMLDivElement>(null);
  useEffect(()=>{
    if(!open)return;
    const outside=(e:PointerEvent)=>{if(root.current&&!root.current.contains(e.target as Node))setOpen(false)};
    const escape=(e:KeyboardEvent)=>{if(e.key==='Escape')setOpen(false)};
    const route=()=>setOpen(false);
    document.addEventListener('pointerdown',outside);
    document.addEventListener('keydown',escape);
    window.addEventListener('hashchange',route);
    return ()=>{document.removeEventListener('pointerdown',outside);document.removeEventListener('keydown',escape);window.removeEventListener('hashchange',route)};
  },[open]);
  if(!ready)return <button type="button" disabled className="wallet-adapter-button">Loading…</button>;
  if(!authenticated)return <button type="button" className="wallet-adapter-button" onClick={login}>Sign In</button>;
  const label=user?.email?.address || user?.wallet?.address || 'Orbit account';
  const initial=(user?.email?.address?.[0]||'O').toUpperCase();
  return <div className="orbit-privy-menu" ref={root}>
    <button type="button" className="orbit-privy-trigger" aria-label="Account menu" aria-expanded={open} aria-haspopup="menu" onClick={()=>setOpen(v=>!v)}>{initial}</button>
    {open&&<div className="orbit-privy-dropdown" role="menu" aria-label="Orbit account">
      <div className="orbit-privy-identity" title={label}>{label}</div>
      <button type="button" role="menuitem" onClick={()=>{setOpen(false);window.location.hash='#/portfolio'}}>My Profile</button>
      <button type="button" role="menuitem" onClick={()=>{setOpen(false);void logout()}}>Sign Out</button>
    </div>}
  </div>;
}
export function OptionalPrivyLogin(){return appId?<AccountMenu/>:null;}
function PrivyAccount({network}:{network:string}) {
  const {ready,authenticated,user,login,logout}=usePrivy();
  if(!ready)return <p className="subdued" role="status">Loading account…</p>;
  if(!authenticated)return <section className="panel orbit-profile-account"><div className="panel-label">ORBIT ACCOUNT</div><h3>Sign in to Orbit</h3><p className="subdued">Sign in with email or a supported wallet. Trading requires a separate connected Solana wallet.</p><button type="button" className="button green-button" onClick={login}>Sign In</button></section>;
  const email=user?.email?.address;
  const address=user?.wallet?.address;
  return <section className="panel orbit-profile-account"><div className="panel-label">ORBIT ACCOUNT</div><h3>My Account</h3><div className="property"><span>Status</span><b className="green">Signed in</b></div><div className="property"><span>Email</span><b>{email||'Not linked'}</b></div>{address&&<div className="property"><span>Privy linked wallet</span><b>{address}</b></div>}<p className="micro-note">Your Orbit sign-in and the wallet used to sign Solana transactions are separate. Network: {network}.</p><button type="button" className="button" onClick={()=>void logout()}>Sign Out</button></section>;
}
export function OptionalPrivyAccount({network}:{network:string}){return appId?<PrivyAccount network={network}/>:<section className="panel orbit-profile-account"><div className="panel-label">ORBIT ACCOUNT</div><p className="subdued">Email sign-in is not configured for this deployment. Connect Phantom to use wallet features.</p></section>;}
