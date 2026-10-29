import BN from 'bn.js';
import {Keypair,PublicKey,VersionedTransaction,Transaction,TransactionMessage,SystemProgram} from '@solana/web3.js';
import {NATIVE_MINT,TOKEN_PROGRAM_ID} from '@solana/spl-token';
import {Raydium,TxVersion,LAUNCHPAD_PROGRAM,DEVNET_PROGRAM_ID,LaunchpadConfig,PlatformConfig,Curve,getPdaLaunchpadConfigId,getPdaLaunchpadPoolId} from '@raydium-io/raydium-sdk-v2';
import type {Connection} from '@solana/web3.js';
import type {WalletContextState} from '@solana/wallet-adapter-react';
import {callApi,postJson,amountBaseUnits,SOL} from './api';
import type {AppConfig,Launch} from './api';

export type PoolView={priceSol:number;raisedSol:number;targetSol:number;progress:number;status:number;poolId:string;decimals:number;updated:number};
const program=(config:AppConfig)=>config.network==='devnet'?DEVNET_PROGRAM_ID.LAUNCHPAD_PROGRAM:LAUNCHPAD_PROGRAM;
const cluster=(config:AppConfig)=>config.network==='devnet'?'devnet':'mainnet';
async function sdk(connection:Connection,config:AppConfig,wallet?:WalletContextState){
 const owner=wallet?.publicKey||Keypair.generate().publicKey;
 // ORBIT_STAGE7_MOBILE_SIGNING
 // Mobile wallet injection can support signTransaction without reliably
 // supporting signAllTransactions. Use one explicit signature request per
 // transaction on mobile; never retry a failed signing request automatically.
 const mobile=typeof navigator!=='undefined' && /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
 const signAll=mobile && wallet?.signTransaction
  ? async <T extends Transaction|VersionedTransaction>(txs:T[]):Promise<T[]>=>{
     const signed:T[]=[];
     for(const tx of txs){signed.push(await wallet.signTransaction!(tx));}
     return signed;
    }
  : wallet?.signAllTransactions?.bind(wallet);
 return Raydium.load({owner,connection,cluster:cluster(config) as any,signAllTransactions:signAll,disableFeatureCheck:true,disableLoadToken:true,blockhashCommitment:'confirmed'});
}
export async function getPool(connection:Connection,config:AppConfig,mint:string,programAddress?:string):Promise<PoolView>{
 const raydium=await sdk(connection,config);
 const id=new PublicKey(programAddress||program(config).toBase58());const mintA=new PublicKey(mint);
 const poolId=getPdaLaunchpadPoolId(id,mintA,NATIVE_MINT).publicKey;
 const p=await raydium.launchpad.getRpcPoolInfo({poolId});
 const status=Number(p.status); // 0 funding, 1 waiting for migration, 2 migrated.
 // A graduated token no longer has an executable curve price. Never present stale curve data as a live quote.
 const price=status===0 ? Number(Curve.getPrice({poolInfo:p,curveType:p.configInfo.curveType,decimalA:p.mintDecimalsA,decimalB:p.mintDecimalsB}).toString()) : 0;
 const raisedSol=Number(p.realB.toString())/1e9,targetSol=Number(p.totalFundRaisingB.toString())/1e9;
 return {priceSol:price,raisedSol,targetSol,progress:targetSol>0?Math.max(0,Math.min(100,raisedSol/targetSol*100)):0,status,poolId:poolId.toBase58(),decimals:p.mintDecimalsA,updated:Date.now()};
}
export async function verifyLaunchConfig(connection:Connection,config:AppConfig){
 if(!config.launchEnabled)throw new Error(config.launchBlockReason||'Token creation is disabled');
 const programId=program(config);
 const selected=import.meta.env.VITE_RAYDIUM_LAUNCH_CONFIG_ID;
 const configId=selected?new PublicKey(selected):getPdaLaunchpadConfigId(programId,NATIVE_MINT,0,0).publicKey;
 const cfg=await connection.getAccountInfo(configId,'confirmed');
 if(!cfg)throw new Error('LaunchLab config '+configId.toBase58()+' is unavailable on '+config.network+'. Set VITE_RAYDIUM_LAUNCH_CONFIG_ID to a verified SOL config.');
 if(!cfg.owner.equals(programId))throw new Error('The configured LaunchLab account is not owned by the expected Raydium program');
 const configInfo=LaunchpadConfig.decode(cfg.data);
 if(!configInfo.mintB.equals(NATIVE_MINT))throw new Error('This LaunchLab config does not use SOL. ORBIT currently supports SOL launches only.');
 return {configId,configInfo};
}
// ORBIT_STAGE4_PLATFORM_PREFLIGHT
// Raydium SDK defaults to the MAINNET platform unless platformId is supplied.
// On Devnet use the SDK's Devnet platform constant; allow an explicitly
// configured Devnet platform only when its on-chain account validates.
// This read-only check never creates accounts or sends transactions.
export async function requireLaunchPlatform(
 connection:Connection, config:AppConfig, walletKey:PublicKey|null|undefined
):Promise<PublicKey>{
 if(config.network!=='devnet')throw new Error('ORBIT token creation is restricted to Devnet; Mainnet launch remains disabled.');
 const programId=program(config);
 const override=String(import.meta.env.VITE_RAYDIUM_PLATFORM_ID||'').trim();
 let platformId:PublicKey;
 try{platformId=override?new PublicKey(override):DEVNET_PROGRAM_ID.LAUNCHPAD_PLATFORM}
 catch{throw new Error('Configured VITE_RAYDIUM_PLATFORM_ID is not a valid Solana address.');}
 const info=await connection.getAccountInfo(platformId,'confirmed');
 if(!info){
  const help=override?'Your configured VITE_RAYDIUM_PLATFORM_ID':'Raydium SDK Devnet LAUNCHPAD_PLATFORM';
  throw new Error(`${help} ${platformId.toBase58()} does not exist on Solana Devnet. Create/choose a verified Devnet PlatformConfig before launching; ORBIT will not fall back to the mainnet address.`);
 }
 if(!info.owner.equals(programId))throw new Error(`PlatformConfig ${platformId.toBase58()} is owned by ${info.owner.toBase58()}, not the Devnet LaunchLab program ${programId.toBase58()}.`);
 try{PlatformConfig.decode(info.data)}catch{throw new Error('The selected Devnet PlatformConfig could not be decoded by Raydium SDK.');}
 return platformId;
}

// A wallet-only diagnostic. An unsigned 0-lamport, self-directed transfer
// is created locally, but is NEVER broadcast. The wallet must still approve
// signing. This diagnostic cannot create a token or charge any network fee.
export async function checkWalletSigning(connection:Connection,config:AppConfig,wallet:WalletContextState):Promise<void>{
 if(config.network!=='devnet')throw new Error('The signature test is restricted to Devnet.');
 if(!wallet.publicKey||!wallet.signTransaction)throw new Error('The connected wallet does not support signing a single transaction.');
 const block=await connection.getLatestBlockhash('confirmed');
 const instruction=SystemProgram.transfer({fromPubkey:wallet.publicKey,toPubkey:wallet.publicKey,lamports:0});
 const message=new TransactionMessage({payerKey:wallet.publicKey,recentBlockhash:block.blockhash,instructions:[instruction]}).compileToV0Message();
 const tx=new VersionedTransaction(message);
 const signed=await wallet.signTransaction(tx);
 const sig=signed.signatures?.[0];
 if(!sig||!sig.some(v=>v!==0))throw new Error('Wallet returned a transaction without the fee-payer signature.');
 // Intentionally NO sendTransaction, sendRawTransaction, or execute() here.
}

export async function launchToken(connection:Connection,config:AppConfig,wallet:WalletContextState,input:{name:string;symbol:string;uri:string}){
 if(!wallet.publicKey||!wallet.signAllTransactions)throw new Error('Connect a wallet that supports transaction signing');
 if(!config.launchEnabled)throw new Error(config.launchBlockReason||'Token creation is currently disabled');
 const platformId=await requireLaunchPlatform(connection,config,wallet.publicKey);
 // ORBIT_STAGE6_SIGNING_PREFLIGHT: check wallet capability and test-SOL balance before constructing a transaction.
 const versionSupport=wallet.wallet?.adapter?.supportedTransactionVersions;
 if(versionSupport&&!versionSupport.has(0))throw new Error('The selected wallet cannot sign Solana version-0 transactions. Choose a wallet supporting version 0.');
 const balance=await connection.getBalance(wallet.publicKey,'confirmed');
 if(balance===0)throw new Error('This wallet has 0 SOL on Devnet. Fund it with test SOL, then retry. Do not use mainnet funds.');
 const raydium=await sdk(connection,config,wallet);
 const programId=program(config);const mint=Keypair.generate();
 const {configId,configInfo}=await verifyLaunchConfig(connection,config);
 const quoteInfo=await raydium.token.getTokenInfo(configInfo.mintB);
 const {execute,extInfo,transactions}=await raydium.launchpad.createLaunchpad({
  programId,mintA:mint.publicKey,name:input.name,symbol:input.symbol,uri:input.uri,
  decimals:6,migrateType:'cpmm',configId,configInfo,mintBDecimals:quoteInfo.decimals,
  createOnly:true,buyAmount:new BN(1000),slippage:new BN(100),extraSigners:[mint],txVersion:TxVersion.V0,
  platformId
 } as any);
 // Simulate the FIRST transaction only: later transactions may depend on it being confirmed.
 // Preflight simulation is not a wallet signature and never broadcasts a transaction.
 if(!Array.isArray(transactions)||transactions.length===0)throw new Error('Raydium did not build any launch transactions.');
 const first=transactions[0];
 if(first instanceof VersionedTransaction){
  const payer=first.message.staticAccountKeys[0];
  if(!payer?.equals(wallet.publicKey))throw new Error('Launch transaction fee payer differs from your connected wallet. Signing blocked.');
  let simulated;
  try{
   simulated=await connection.simulateTransaction(first,{sigVerify:false,replaceRecentBlockhash:true,commitment:'confirmed'});
  }catch(e){
   throw new Error(`Devnet transaction preflight RPC failed: ${e instanceof Error?e.message:String(e)}`,{cause:e});
  }
  if(simulated.value.err){
   const logs=(simulated.value.logs||[]).slice(-12).join(' | ');
   throw new Error(`Devnet launch simulation failed BEFORE wallet approval: ${JSON.stringify(simulated.value.err)}${logs?' | Program logs: '+logs:''}`);
  }
 }
 let txIds:string[];
 try{
  ({txIds}=await execute({sequentially:true}));
 }catch(e){
  const error=e as any;
  const name=String(error?.name||'');
  const message=String(error?.message||e);
  if(name.includes('WalletSign')||message==='Unexpected error'){
   const detail=String(error?.cause?.message||error?.reason||'');
   throw new Error(`Phantom or the wallet adapter could not sign the Devnet launch transaction (${name||'wallet error'}: ${message}). Check that Phantom Testnet Mode is enabled for Solana Devnet, that the wallet has Devnet SOL, and that no previous launch was confirmed. Do not keep retrying without checking transaction activity.${detail?' Details: '+detail:''}`,{cause:e});
  }
  throw e;
 }
 if(!Array.isArray(txIds)||!txIds.length)throw new Error('No confirmed creation transaction returned');
 return {mint:mint.publicKey.toBase58(),poolId:extInfo.address.poolId.toBase58(),programId:programId.toBase58(),txSignature:txIds.at(-1)!};
}
export async function curveTrade(connection:Connection,config:AppConfig,wallet:WalletContextState,item:Launch,side:'buy'|'sell',amount:string,slippageBps:number){
 if(!wallet.publicKey||!wallet.signAllTransactions)throw new Error('Connect wallet');
 if(config.network==='mainnet-beta'&&!config.mainnetTradingEnabled)throw new Error('Mainnet trading is disabled until reviewed');
 if(slippageBps<10||slippageBps>500)throw new Error('Allowed slippage: 0.1% to 5%');
 if(item.network!==config.network)throw new Error('Token network does not match the connected Solana network');
 const mintA=new PublicKey(item.mint),programId=new PublicKey(item.programId);
 if(!programId.equals(program(config)))throw new Error('This token belongs to a different launch program');
 const expectedPool=getPdaLaunchpadPoolId(programId,mintA,NATIVE_MINT).publicKey;
 if(!expectedPool.equals(new PublicKey(item.poolId)))throw new Error('Pool address does not match the canonical token PDA');
 const raydium=await sdk(connection,config,wallet);
 const p=await raydium.launchpad.getRpcPoolInfo({poolId:expectedPool});
 if(Number(p.status)!==0)throw new Error('Bonding curve is closed. Wait for migration or use a supported swap route.');
 if(!p.mintA.equals(mintA)||!p.mintB.equals(NATIVE_MINT))throw new Error('Live pool mints do not match the requested token/SOL pair');
 if(p.mintDecimalsB!==9)throw new Error('Unexpected SOL decimals in pool');
 const platformData=await connection.getAccountInfo(p.platformId,'confirmed');
 if(!platformData)throw new Error('Platform fee configuration not found');
 if(!platformData.owner.equals(programId))throw new Error('Platform config owner does not match the launch program');
 const platformInfo=PlatformConfig.decode(platformData.data);
 const mintInfo=await raydium.token.getTokenInfo(mintA);
 const mintBInfo=await raydium.token.getTokenInfo(p.mintB);
 if(side==='buy'){
  const {execute}=await raydium.launchpad.buyToken({programId,mintA,mintAProgram:new PublicKey(mintInfo.programId),mintB:p.mintB,mintBProgram:new PublicKey(mintBInfo.programId),poolInfo:p,configInfo:p.configInfo,platformFeeRate:platformInfo.feeRate,buyAmount:new BN(amountBaseUnits(amount,p.mintDecimalsB)),slippage:new BN(slippageBps),txVersion:TxVersion.V0} as any);
  return (await execute({sendAndConfirm:true})).txId;
 }
 const {execute}=await raydium.launchpad.sellToken({programId,mintA,mintAProgram:new PublicKey(mintInfo.programId),mintB:p.mintB,mintBProgram:new PublicKey(mintBInfo.programId),poolInfo:p,configInfo:p.configInfo,platformFeeRate:platformInfo.feeRate,sellAmount:new BN(amountBaseUnits(amount,p.mintDecimalsA)),slippage:new BN(slippageBps),txVersion:TxVersion.V0} as any);
 return (await execute({sendAndConfirm:true})).txId;
}
function b64(data:Uint8Array){let raw='';for(let i=0;i<data.length;i+=8192)raw+=String.fromCharCode(...data.slice(i,i+8192));return btoa(raw)}
function fromB64(data:string){return Uint8Array.from(atob(data),v=>v.charCodeAt(0))}
// Migrated pools: Jupiter V2 /order -> sign in wallet -> /execute. No private keys reach the server.
export async function migratedTrade(wallet:WalletContextState,item:Launch,side:'buy'|'sell',amount:string){
 if(!wallet.publicKey||!wallet.signTransaction)throw new Error('Your wallet must support signTransaction');
 const inp=side==='buy'?SOL:item.mint, out=side==='buy'?item.mint:SOL;
 const amt=amountBaseUnits(amount,side==='buy'?9:6);
 const order=await callApi<any>(`/api/swap/order?${new URLSearchParams({inputMint:inp,outputMint:out,amount:amt,taker:wallet.publicKey.toBase58()})}`);
 if(!order.transaction||!order.requestId)throw new Error(order.errorMessage||'No Jupiter route available');
 const tx=VersionedTransaction.deserialize(fromB64(order.transaction));
 const signed=await wallet.signTransaction(tx);
 const result=await postJson<any>('/api/swap/execute',{requestId:order.requestId,signedTransaction:b64(signed.serialize())});
 if(result.status!=='Success')throw new Error(result.error||result.errorMessage||'Swap failed');
 return result.signature as string;
}
