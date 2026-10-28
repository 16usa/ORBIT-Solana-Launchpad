import React,{useMemo} from 'react';
import {ConnectionProvider,WalletProvider} from '@solana/wallet-adapter-react';
import {WalletModalProvider} from '@solana/wallet-adapter-react-ui';
import '@solana/wallet-adapter-react-ui/styles.css';
export default function WalletSetup({rpc,children}:{rpc:string;children:React.ReactNode}){
 const wallets=useMemo(()=>[],[]);
 return <ConnectionProvider endpoint={rpc}><WalletProvider wallets={wallets} autoConnect={false}><WalletModalProvider>{children}</WalletModalProvider></WalletProvider></ConnectionProvider>;
}
