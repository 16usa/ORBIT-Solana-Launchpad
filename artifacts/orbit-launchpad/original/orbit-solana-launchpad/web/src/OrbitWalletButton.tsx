import React from 'react';
import { useWallet } from '@solana/wallet-adapter-react';
import { WalletMultiButton } from '@solana/wallet-adapter-react-ui';
import { WalletReadyState } from '@solana/wallet-adapter-base';

// Phantom on iOS requires its in-app browser; an empty wallet picker in Safari
// is not a connection method. Keep Wallet Standard autodetection untouched.
export default function OrbitWalletButton({ showHint = false }: { showHint?: boolean }) {
  const { wallets, connected } = useWallet();
  const isMobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
  const availableWallet = wallets.some(({ readyState }) => readyState === WalletReadyState.Installed || readyState === WalletReadyState.Loadable);

  if (connected || availableWallet) return <WalletMultiButton />;

  // The browse link opens the current page inside Phantom; it does NOT grant
  // account access or sign transactions, which still require wallet approval.
  if (isMobile) {
    const currentUrl = window.location.href;
    const ref = window.location.origin;
    const url = `https://phantom.com/ul/browse/${encodeURIComponent(currentUrl)}?ref=${encodeURIComponent(ref)}`;
    return <div className="orbit-wallet-action">
      <a className="wallet-adapter-button orbit-phantom-link" href={url} rel="noreferrer" aria-label="Open ORBIT in Phantom wallet browser">Open in Phantom</a>
      {showHint && <p className="orbit-wallet-hint">On iPhone, open this site inside Phantom's browser to connect. If the button doesn't open Phantom, open the Phantom app and paste this site's address into its search bar.</p>}
    </div>;
  }

  return <div className="orbit-wallet-action">
    <a className="wallet-adapter-button orbit-phantom-link" href="https://phantom.com/download" target="_blank" rel="noreferrer">Get Phantom</a>
    {showHint && <p className="orbit-wallet-hint">Install a Solana wallet extension, then reload ORBIT and choose your wallet. Never share a recovery phrase.</p>}
  </div>;
}
