import React, { useEffect, useRef, useState } from 'react';
import { useWallet } from '@solana/wallet-adapter-react';
import { useWalletModal } from '@solana/wallet-adapter-react-ui';
import { WalletMultiButton } from '@solana/wallet-adapter-react-ui';
import { WalletReadyState } from '@solana/wallet-adapter-base';

// ORBIT_STAGE20_WALLET_AVATAR
// Phantom's private account avatar is not exposed by the Solana wallet adapter.
// This is a per-address LOCAL avatar. No image is sent to ORBIT or the network.
const avatarKey = (address: string) => `orbit:wallet-avatar:v1:${address}`;
function readAvatar(address: string): string | null {
  try {
    const value = localStorage.getItem(avatarKey(address));
    return value && /^data:image\/jpeg;base64,/.test(value) ? value : null;
  } catch {
    return null;
  }
}

async function imageToAvatar(file: File): Promise<string> {
  if (!['image/jpeg', 'image/png', 'image/webp', 'image/gif'].includes(file.type)) {
    throw new Error('Choose a JPG, PNG, WEBP or GIF image.');
  }
  if (file.size > 12 * 1024 * 1024) throw new Error('Image must be smaller than 12 MB.');
  return new Promise<string>((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    let finished = false;
    const clean = () => { if (!finished) { finished = true; URL.revokeObjectURL(url); } };
    img.onload = () => {
      try {
        const canvas = document.createElement('canvas');
        canvas.width = canvas.height = 160;
        const context = canvas.getContext('2d');
        if (!context) throw new Error('Image processing is unavailable.');
        const side = Math.min(img.naturalWidth, img.naturalHeight);
        if (!side) throw new Error('Invalid image.');
        context.drawImage(img, (img.naturalWidth - side) / 2, (img.naturalHeight - side) / 2, side, side, 0, 0, 160, 160);
        const data = canvas.toDataURL('image/jpeg', 0.82);
        clean();
        resolve(data);
      } catch (e) { clean(); reject(e); }
    };
    img.onerror = () => { clean(); reject(new Error('Could not open that image.')); };
    img.src = url;
  });
}

function ConnectedAvatarButton() {
  const { publicKey, wallet, disconnect } = useWallet();
  const { setVisible } = useWalletModal();
  const address = publicKey?.toBase58() ?? '';
  const [avatar, setAvatar] = useState<string | null>(() => readAvatar(address));
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState('');
  const root = useRef<HTMLDivElement>(null);
  const upload = useRef<HTMLInputElement>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    setAvatar(readAvatar(address));
    setOpen(false);
    setMessage('');
  }, [address]);

  useEffect(() => {
    if (!open) return;
    const outside = (e: PointerEvent) => {
      if (root.current && !root.current.contains(e.target as Node)) setOpen(false);
    };
    const escape = (e: KeyboardEvent) => { if (e.key === 'Escape') setOpen(false); };
    document.addEventListener('pointerdown', outside);
    document.addEventListener('keydown', escape);
    return () => { document.removeEventListener('pointerdown', outside); document.removeEventListener('keydown', escape); };
  }, [open]);

  useEffect(() => () => { if (timer.current) clearTimeout(timer.current); }, []);

  const notice = (text: string) => {
    setMessage(text);
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => setMessage(''), 2600);
  };

  const copyAddress = async () => {
    try {
      await navigator.clipboard.writeText(address);
      notice('Address copied');
    } catch {
      notice('Copy unavailable in this browser');
    }
  };

  const selectImage = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file || !address) return;
    try {
      const data = await imageToAvatar(file);
      // Ensure a wallet switch while processing cannot attach a photo to another account.
      if (publicKey?.toBase58() !== address) return;
      localStorage.setItem(avatarKey(address), data);
      setAvatar(data);
      setOpen(false);
      notice('Avatar saved on this device');
    } catch (e) {
      notice(e instanceof Error ? e.message : 'Could not save avatar');
    }
  };

  const clearAvatar = () => {
    try { localStorage.removeItem(avatarKey(address)); } catch { /* storage unavailable */ }
    setAvatar(null);
    setOpen(false);
    notice('Local avatar removed');
  };

  return <div className="orbit-account-menu" ref={root}>
    <button
      type="button"
      className="orbit-account-avatar-trigger"
      title={`Wallet ${address.slice(0, 5)}…${address.slice(-4)}`}
      aria-label={`Wallet options for ${address.slice(0, 5)}…${address.slice(-4)}`}
      aria-haspopup="menu"
      aria-expanded={open}
      onClick={() => setOpen(v => !v)}
    >
      {avatar
        ? <img src={avatar} alt="" className="orbit-account-avatar-image" />
        : wallet?.adapter.icon
          ? <img src={wallet.adapter.icon} alt="" className="orbit-account-wallet-icon" />
          : <span className="orbit-account-avatar-fallback" aria-hidden="true">●</span>}
    </button>
    {open && <div className="orbit-account-dropdown" role="menu" aria-label="Wallet options">
      <div className="orbit-account-dropdown-address" title={address}>{address.slice(0, 6)}…{address.slice(-5)}</div>
      <button type="button" role="menuitem" onClick={() => { void copyAddress(); setOpen(false); }}>Copy address</button>
      <button type="button" role="menuitem" onClick={() => { setOpen(false); setVisible(true); }}>Change wallet</button>
      <button type="button" role="menuitem" onClick={() => { setOpen(false); upload.current?.click(); }}>Set avatar</button>
      {avatar && <button type="button" role="menuitem" onClick={clearAvatar}>Remove avatar</button>}
      <button type="button" role="menuitem" onClick={() => { setOpen(false); void disconnect().catch(() => notice('Could not disconnect')); }}>Disconnect</button>
    </div>}
    <input
      className="orbit-account-avatar-upload"
      type="file"
      accept="image/png,image/jpeg,image/webp,image/gif"
      onChange={e => { void selectImage(e); }}
      ref={upload}
      aria-label="Choose wallet avatar"
      tabIndex={-1}
    />
    {message && <span className="orbit-account-avatar-notice" role="status">{message}</span>}
  </div>;
}

// Preserve the existing Phantom mobile browser link and wallet adapter picker.
export default function OrbitWalletButton({ showHint = false }: { showHint?: boolean }) {
  const { wallets, connected } = useWallet();
  const isMobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
  const availableWallet = wallets.some(({ readyState }) => readyState === WalletReadyState.Installed || readyState === WalletReadyState.Loadable);

  if (connected) return <ConnectedAvatarButton />;
  if (availableWallet) return <WalletMultiButton />;

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
