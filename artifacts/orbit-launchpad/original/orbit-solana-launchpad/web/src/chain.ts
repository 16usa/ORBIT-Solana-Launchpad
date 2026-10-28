import BN from 'bn.js';
import {Keypair,PublicKey,VersionedTransaction} from '@solana/web3.js';
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
 return Raydium.load({owner,connection,cluster:cluster(config) as any,signAllTransactions:wallet?.signAllTransactions?.bind(wallet),disableFeatureCheck:true,disableLoadToken:true,blockhashCommitment:'confirmed'});
}
export async function getPool(connection:Connection,config:AppConfig,mint:string,programAddress?:string):Promise<PoolView>{
 const raydium=await sdk(connection,config);
 const id=new PublicKey(programAddress||program(config).toBase58());const mintA=new PublicKey(mint);
 const poolId=getPdaLaunchpadPoolId(id,mintA,NATIVE_MINT).publicKey;
 const p=await raydium.launchpad.getRpcPoolInfo({poolId});
 const price=Curve.getPrice({poolInfo:p,curveType:p.configInfo.curveType,decimalA:p.mintDecimalsA,decimalB:p.mintDecimalsB});
 const raisedSol=Number(p.realB.toString())/1e9,targetSol=Number(p.totalFundRaisingB.toString())/1e9;
 return {priceSol:Number(price.toString()),raisedSol,targetSol,progress:targetSol>0?Math.max(0,Math.min(100,raisedSol/targetSol*100)):0,status:Number(p.status),poolId:poolId.toBase58(),decimals:p.mintDecimalsA,updated:Date.now()};
}
export async function launchToken(connection:Connection,config:AppConfig,wallet:WalletContextState,input:{name:string;symbol:string;uri:string}){
 if(!wallet.publicKey||!wallet.signAllTransactions)throw new Error('Connect a wallet that supports transaction signing');
 if(!config.launchEnabled)throw new Error(config.launchBlockReason||'Token creation is currently disabled');
 const raydium=await sdk(connection,config,wallet);
 const programId=program(config);const mint=Keypair.generate();
 const configId=getPdaLaunchpadConfigId(programId,NATIVE_MINT,0,0).publicKey;
 const cfg=await connection.getAccountInfo(configId,'confirmed');if(!cfg)throw new Error('Raydium LaunchLab configuration is unavailable on this network. Do not submit a transaction.');
 const configInfo=LaunchpadConfig.decode(cfg.data);
 const quoteInfo=await raydium.token.getTokenInfo(configInfo.mintB);
 const {execute,extInfo}=await raydium.launchpad.createLaunchpad({
  programId,mintA:mint.publicKey,name:input.name,symbol:input.symbol,uri:input.uri,
  decimals:6,migrateType:'cpmm',configId,configInfo,mintBDecimals:quoteInfo.decimals,
  createOnly:true,buyAmount:new BN(1000),slippage:new BN(100),extraSigners:[mint],txVersion:TxVersion.V0,
  ...(import.meta.env.VITE_RAYDIUM_PLATFORM_ID?{platformId:new PublicKey(import.meta.env.VITE_RAYDIUM_PLATFORM_ID)}:{})
 } as any);
 const {txIds}=await execute({sequentially:true});
 if(!Array.isArray(txIds)||!txIds.length)throw new Error('No confirmed creation transaction returned');
 return {mint:mint.publicKey.toBase58(),poolId:extInfo.address.poolId.toBase58(),programId:programId.toBase58(),txSignature:txIds.at(-1)!};
}
export async function curveTrade(connection:Connection,config:AppConfig,wallet:WalletContextState,item:Launch,side:'buy'|'sell',amount:string,slippageBps:number){
 if(!wallet.publicKey||!wallet.signAllTransactions)throw new Error('Connect wallet');
 if(config.network==='mainnet-beta'&&!config.mainnetTradingEnabled)throw new Error('Mainnet trading is disabled until reviewed');
 if(slippageBps<10||slippageBps>500)throw new Error('Allowed slippage: 0.1% to 5%');
 const raydium=await sdk(connection,config,wallet);const mintA=new PublicKey(item.mint),programId=new PublicKey(item.programId);
 const p=await raydium.launchpad.getRpcPoolInfo({poolId:new PublicKey(item.poolId)});
 const platformData=await connection.getAccountInfo(p.platformId,'confirmed');if(!platformData)throw new Error('Platform fee configuration not found');
 const platformInfo=PlatformConfig.decode(platformData.data);
 const mintInfo=await raydium.token.getTokenInfo(mintA);
 const mintBInfo=await raydium.token.getTokenInfo(p.mintB);
 if(side==='buy'){
  const {execute}=await raydium.launchpad.buyToken({programId,mintA,mintAProgram:new PublicKey(mintInfo.programId),mintB:p.mintB,mintBProgram:new PublicKey(mintBInfo.programId),poolInfo:p,configInfo:p.configInfo,platformFeeRate:platformInfo.feeRate,buyAmount:new BN(amountBaseUnits(amount,9)),slippage:new BN(slippageBps),txVersion:TxVersion.V0} as any);
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
