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
