// ORBIT_STAGE25_PRIVY: login session only. Trading remains on the connected Solana wallet.
import React from 'react';
import { PrivyProvider, usePrivy } from '@privy-io/react-auth';
const appId = import.meta.env.VITE_PRIVY_APP_ID || '';
export function PrivyBoundary({children}:{children:React.ReactNode}) {
  if (!appId) return <>{children}</>;
  return <PrivyProvider appId={appId} config={{loginMethods:['email','wallet'], appearance:{theme:'dark'}}}>{children}</PrivyProvider>;
}
export function PrivyLogin() {
  const {ready,authenticated,login,logout,user}=usePrivy();
  if(!ready) return <button type="button" disabled className="wallet-adapter-button">Loading…</button>;
  if(authenticated) return <button type="button" className="wallet-adapter-button" title={user?.email?.address||'Privy account'} onClick={()=>void logout()}>Sign out</button>;
  return <button type="button" className="wallet-adapter-button" onClick={login}>Sign in</button>;
}
export function OptionalPrivyLogin(){return appId?<PrivyLogin/>:null;}

// ORBIT_STAGE27_PROFILE: Show authenticated account independently of Solana wallet adapter.
function PrivyAccount({network}:{network:string}) {
  const {ready,authenticated,user,login}=usePrivy();
  if(!ready)return <p className="subdued" role="status">Loading account…</p>;
  if(!authenticated)return <section className="panel" style={{marginTop:18}}><h3>Account</h3><p className="subdued">Sign in to access your Orbit account.</p><button type="button" className="button green-button" onClick={login}>Sign in</button></section>;
  const email=user?.email?.address;
  const address=user?.wallet?.address;
  return <section className="panel" style={{marginTop:18}}><div className="panel-label">ORBIT ACCOUNT</div><h3 style={{marginTop:12}}>Signed in</h3><div className="property"><span>Email</span><b style={{overflowWrap:'anywhere'}}>{email||'Not linked'}</b></div><div className="property"><span>Privy account</span><b style={{overflowWrap:'anywhere'}}>{user?.id||'—'}</b></div>{address&&<div className="property"><span>Privy linked wallet</span><b style={{overflowWrap:'anywhere'}}>{address}</b></div>}<p className="micro-note">Signing in does not automatically connect a Solana transaction-signing wallet. Network: {network}.</p></section>;
}
export function OptionalPrivyAccount({network}:{network:string}){return appId?<PrivyAccount network={network}/>:null;}
