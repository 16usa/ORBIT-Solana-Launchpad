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

// ORBIT_STAGE8_RAYDIUM_NO_BROADCAST
// Constructs the actual Raydium CreateLaunchpad V0 transaction, preflights
// the first transaction, and requests a wallet signature. No transaction is
// submitted, no metadata is uploaded, and the generated test mint is discarded.
// The URI is deliberately inert: this must NEVER be used for a real launch.
export async function checkRaydiumLaunchSigning(
 connection:Connection,config:AppConfig,wallet:WalletContextState
):Promise<string>{
 if(config.network!=='devnet')throw new Error('Raydium signing diagnostic is Devnet-only.');
 if(!config.launchEnabled)throw new Error(config.launchBlockReason||'Devnet launch is unavailable.');
 if(!wallet.publicKey||!wallet.signTransaction)throw new Error('Connect a wallet with signTransaction support.');
 const platformId=await requireLaunchPlatform(connection,config,wallet.publicKey);
 const {configId,configInfo}=await verifyLaunchConfig(connection,config);
 const raydium=await sdk(connection,config,wallet);
 const mint=Keypair.generate();
 const quote=await raydium.token.getTokenInfo(configInfo.mintB);
 const built=await raydium.launchpad.createLaunchpad({
  programId:program(config),mintA:mint.publicKey,
  name:'ORBIT Diagnostic Only',symbol:'ORBDIAG',
  uri:'https://example.com/orbit-diagnostic-never-published.json',
  decimals:6,migrateType:'cpmm',configId,configInfo,
  mintBDecimals:quote.decimals,createOnly:true,
  buyAmount:new BN(1000),slippage:new BN(100),
  extraSigners:[mint],txVersion:TxVersion.V0,platformId
 } as any);
 if(!Array.isArray(built.transactions)||built.transactions.length===0)
  throw new Error('Raydium SDK returned no launch transactions.');
 // ORBIT_STAGE9_WALLET_FIRST_COSIGN
 // Some mobile wallets reject partially-signed multi-signer transactions.
 // Take ONLY the message from Raydium and start with zero signatures.
 // Let Phantom sign the wallet slot, then sign the ephemeral mint locally.
 // This is a diagnostic and is NEVER submitted to Solana.
 const sdkTx=built.transactions[0];
 if(!(sdkTx instanceof VersionedTransaction))
  throw new Error('Expected a V0 launch transaction; Raydium returned another format.');
 const sdkSignatures=sdkTx.signatures.filter(sig=>sig.some(b=>b!==0)).length;
 const tx=new VersionedTransaction(sdkTx.message);
 const n=tx.message.header.numRequiredSignatures;
 const signers=tx.message.staticAccountKeys.slice(0,n);
 const walletKey=wallet.publicKey;
 if(!signers[0]?.equals(walletKey))
  throw new Error('Raydium launch fee payer differs from the connected wallet.');
 if(!signers.some(k=>k.equals(walletKey)))
  throw new Error('Connected wallet is not listed as a required signer.');
 const unrecognized=signers.filter(k=>!k.equals(walletKey)&&!k.equals(mint.publicKey));
 if(unrecognized.length)
  throw new Error('Raydium requires an unexpected signer: '+unrecognized.map(k=>k.toBase58()).join(', '));
 // The new mint keypair is never sent to the wallet or server.
 // Unlike Stage 8, do NOT pre-sign before Phantom sees the transaction.
 const mintIndex=signers.findIndex(k=>k.equals(mint.publicKey));
 if(mintIndex<0)throw new Error('The Raydium transaction does not request the new mint signature.');
 const walletIndex=signers.findIndex(k=>k.equals(walletKey));
 if(walletIndex<0)throw new Error('The connected wallet is not a signer.');
 const bytes=tx.serialize().length;
 if(bytes>1232)throw new Error('Raydium transaction is oversized ('+bytes+' bytes).');
 const simulation=await connection.simulateTransaction(tx,{
  sigVerify:false,replaceRecentBlockhash:true,commitment:'confirmed'
 });
 if(simulation.value.err){
  const logs=(simulation.value.logs||[]).slice(-14).join(' | ');
  throw new Error('Raydium first transaction simulation failed: '+JSON.stringify(simulation.value.err)+(logs?' | '+logs:''));
 }
 const expectedMessage=tx.message.serialize();
 let signed:VersionedTransaction;
 try{signed=await wallet.signTransaction(tx) as VersionedTransaction;}
 catch(e){
  const err=e as any;
  throw new Error('Unsigned Raydium launch signing failed. Phantom may reject the launch instructions or multi-signer format (not just pre-signing). Required signers: '+n+'; transaction bytes: '+bytes+'; SDK supplied '+sdkSignatures+' signature(s). Wallet error: '+String(err?.name||'Error')+' — '+String(err?.message||e)+(err?.cause?.message?' | Cause: '+err.cause.message:''));
 }
 if(!(signed instanceof VersionedTransaction))
  throw new Error('Wallet returned a different transaction type.');
 const actualMessage=signed.message.serialize();
 if(actualMessage.length!==expectedMessage.length||actualMessage.some((v,i)=>v!==expectedMessage[i]))
  throw new Error('Wallet changed the Raydium message. The diagnostic refused to co-sign.');
 const walletSig=signed.signatures?.[walletIndex]?.slice();
 if(!walletSig||!walletSig.some(b=>b!==0))
  throw new Error('Wallet did not sign its required signer slot.');
 signed.sign([mint]); // Mint keypair co-signs AFTER wallet approval.
 const mintSig=signed.signatures?.[mintIndex];
 if(!mintSig||!mintSig.some(b=>b!==0))
  throw new Error('Local mint signature was not added.');
 if(signed.signatures[walletIndex].some((v,i)=>v!==walletSig[i]))
  throw new Error('Local mint co-signing modified the wallet signature.');
 // No execute, submit, send, registration, or metadata writes anywhere here.
 return 'Raydium V0 transaction: BUILT ('+bytes+' bytes, '+n+' signers; '+built.transactions.length+' SDK transaction(s); SDK originally had '+sdkSignatures+' signature(s)). Simulation: PASSED. Unsigned Raydium message accepted by Phantom: PASSED. Local mint co-signature added afterward: PASSED. No transaction sent and no token created.';
}


// ORBIT_STAGE12_READONLY_AUDIT
// Read-only LaunchLab transaction preflight. This diagnostic NEVER requests
// wallet signatures, signs with ephemeral keys, submits transactions, or
// uploads token metadata. A successful RPC simulation does NOT prove safety.
export async function inspectRaydiumLaunch(
 connection:Connection,config:AppConfig,wallet:WalletContextState
):Promise<string>{
 if(config.network!=='devnet'||!config.launchEnabled)
  throw new Error('Read-only launch audit is available on enabled Devnet only.');
 if(!wallet.publicKey)
  throw new Error('Connect a dedicated Devnet wallet to run this audit.');
 const payer=wallet.publicKey;
 const platformId=await requireLaunchPlatform(connection,config,payer);
 const {configId,configInfo}=await verifyLaunchConfig(connection,config);
 const raydium=await sdk(connection,config,wallet);
 const quote=await raydium.token.getTokenInfo(configInfo.mintB);
 const mint=Keypair.generate(); // Ephemeral only: never exported or broadcast.
 const built=await raydium.launchpad.createLaunchpad({
  programId:program(config),mintA:mint.publicKey,
  name:'ORBIT Readonly Check',symbol:'ORBAUDIT',
  uri:'https://example.com/orbit-readonly-check-not-for-launch.json',
  decimals:6,migrateType:'cpmm',configId,configInfo,
  mintBDecimals:quote.decimals,createOnly:true,
  buyAmount:new BN(1000),slippage:new BN(100),
  extraSigners:[mint],txVersion:TxVersion.V0,platformId
 } as any);
 if(!Array.isArray(built.transactions)||built.transactions.length!==1)
  throw new Error('Expected one create-only Raydium transaction, received '+String(built.transactions?.length??'none')+'. No wallet prompt.');
 const original=built.transactions[0];
 if(!(original instanceof VersionedTransaction)||original.message.version!==0)
  throw new Error('Raydium did not return a V0 transaction.');
 const message=original.message;
 const signerKeys=message.staticAccountKeys.slice(0,message.header.numRequiredSignatures);
 if(signerKeys.length!==2||!signerKeys[0].equals(payer)||!signerKeys[1].equals(mint.publicKey))
  throw new Error('Unexpected signer roles in Raydium launch. No wallet prompt.');
 const lookupTables=await Promise.all(message.addressTableLookups.map(async lookup=>{
  const response=await connection.getAddressLookupTable(lookup.accountKey,{commitment:'confirmed'});
  if(!response.value)throw new Error('Missing Devnet ALT '+lookup.accountKey.toBase58());
  return response.value;
 }));
 const allKeys=message.getAccountKeys({addressLookupTableAccounts:lookupTables});
 const instructions=message.compiledInstructions;
 const calledPrograms=instructions.map(ix=>{
  const id=allKeys.get(ix.programIdIndex);
  if(!id||ix.accountKeyIndexes.some(i=>!allKeys.get(i)))
   throw new Error('Unresolved account index in V0 transaction. No wallet prompt.');
  return id.toBase58();
 });
 const uniquePrograms=[...new Set(calledPrograms)];
 const allowed=new Set([
  program(config).toBase58(),SystemProgram.programId.toBase58(),
  TOKEN_PROGRAM_ID.toBase58(),
  'TokenzQdBNbLqP5VEhdkAS6EPFZ6LKruL4y3Yz9KP',
  'ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL',
  'ComputeBudget111111111111111111111111111111',
  'metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s',
  'MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr'
 ]);
 const unknown=uniquePrograms.filter(id=>!allowed.has(id));
 const bh=await connection.getLatestBlockhash('confirmed');
 const tx=new VersionedTransaction(message); // Fresh, zeroed signature slots.
 tx.message.recentBlockhash=bh.blockhash;
 const byteSize=tx.serialize().length;
 if(byteSize>1232)throw new Error('Raydium transaction exceeds 1232 bytes.');
 const [genesis,balance,fee,programAccounts,simulation]=await Promise.all([
  connection.getGenesisHash(),
  connection.getBalance(payer,'confirmed'),
  connection.getFeeForMessage(tx.message,'confirmed'),
  connection.getMultipleAccountsInfo(uniquePrograms.map(id=>new PublicKey(id)),'confirmed'),
  connection.simulateTransaction(tx,{
   sigVerify:false,replaceRecentBlockhash:false,commitment:'confirmed',
   accounts:{encoding:'base64',addresses:[payer.toBase58(),mint.publicKey.toBase58()]}
  })
 ]);
 const executable=uniquePrograms.map((id,i)=>
  id+' : '+(programAccounts[i]?.executable?'executable':programAccounts[i]?'not executable':'account missing')
 );
 const payerAfter=simulation.value.accounts?.[0]?.lamports;
 const spending=typeof payerAfter==='number'
  ?Math.max(0,(balance-payerAfter)/1e9).toFixed(9)+' SOL (estimated from simulation)'
  :'not available from RPC';
 const logs=(simulation.value.logs||[]).slice(-25).join('\n');
 const state=simulation.value.err?'FAILED '+JSON.stringify(simulation.value.err):'PASSED (unsigned preflight only)';
 const report=[
  'ORBIT Stage 12 - READ-ONLY Devnet launch audit',
  'No wallet signature requested. No transaction sent. No token created.',
  'This uses a temporary diagnostic mint/URI, not your actual token form.',
  'RPC genesis hash: '+genesis,
  'RPC simulation slot: '+simulation.context.slot,
  'Wallet Devnet balance: '+(balance/1e9).toFixed(6)+' SOL',
  'Simulated payer decrease: '+spending,
  'Signature fee estimate: '+(fee.value===null?'unavailable':(fee.value/1e9).toFixed(9)+' SOL'),
  'Transaction: '+byteSize+' bytes; '+instructions.length+' instructions; '+signerKeys.length+' signers; '+lookupTables.length+' lookup table(s)',
  'LaunchLab program: '+program(config).toBase58(),
  'Launch config: '+configId.toBase58(),
  'Platform config: '+platformId.toBase58(),
  'Program allowlist: '+(unknown.length?'UNREVIEWED '+unknown.join(', '):'all invoked programs recognized'),
  'Invoked program accounts:\n'+executable.join('\n'),
  'RPC simulation: '+state,
  'Units consumed: '+String(simulation.value.unitsConsumed??'unavailable'),
  'Last program logs:\n'+(logs||'(none)'),
  'IMPORTANT: sigVerify=false checks execution only; it does NOT prove that a wallet will sign or that Phantom safety warnings are wrong.'
 ];
 return report.join('\n');
}

// ORBIT_STAGE13_LEGACY_READONLY
// Build a Raydium LaunchLab *legacy* transaction to test whether a V0 ALT
// is the reason Phantom cannot inspect our Devnet creation transaction.
// Does not request any signature, broadcast, upload, or create a token.
export async function inspectRaydiumLegacy(
 connection:Connection,config:AppConfig,wallet:WalletContextState
):Promise<string>{
 if(config.network!=='devnet'||!config.launchEnabled)
  throw new Error('Legacy comparison is enabled for Solana Devnet only.');
 if(!wallet.publicKey)throw new Error('Connect a dedicated Devnet wallet to inspect the transaction.');
 const payer=wallet.publicKey;
 const platformId=await requireLaunchPlatform(connection,config,payer);
 const {configId,configInfo}=await verifyLaunchConfig(connection,config);
 const raydium=await sdk(connection,config,wallet);
 const mint=Keypair.generate();
 const quote=await raydium.token.getTokenInfo(configInfo.mintB);
 let built:any;
 try{
  built=await raydium.launchpad.createLaunchpad({
   programId:program(config),mintA:mint.publicKey,
   name:'ORBIT Legacy Audit',symbol:'ORBLEG',
   uri:'https://example.com/orbit-legacy-audit-never-published.json',
   decimals:6,migrateType:'cpmm',configId,configInfo,
   mintBDecimals:quote.decimals,createOnly:true,
   buyAmount:new BN(1000),slippage:new BN(100),
   extraSigners:[mint],txVersion:TxVersion.LEGACY,platformId
  } as any);
 }catch(e){
  return 'ORBIT Stage 13 - LEGACY read-only comparison\n'+
   'Legacy Raydium SDK build: FAILED. '+String((e as Error)?.message||e)+
   '\nNo transaction sent, no signature requested. Do not use Create Token.';
 }
 if(!Array.isArray(built.transactions)||built.transactions.length!==1)
  return 'ORBIT Stage 13 - LEGACY read-only comparison\n'+
   'Expected 1 legacy transaction, SDK built '+String(built.transactions?.length??'none')+
   '. This variant is not supported by the current one-transaction ORBIT launch. No signature or broadcast.';
 const original=built.transactions[0];
 if(!(original instanceof Transaction))
  throw new Error('Raydium returned a non-legacy transaction while LEGACY was requested.');
 if(original.feePayer&&!original.feePayer.equals(payer))
  throw new Error('Legacy builder fee payer differs from the connected Devnet wallet.');
 const bh=await connection.getLatestBlockhash('confirmed');
 // Reconstruct only the *instructions*; SDK signatures are intentionally discarded.
 const tx=new Transaction({feePayer:payer,recentBlockhash:bh.blockhash});
 tx.add(...original.instructions);
 const msg=tx.compileMessage();
 const signers=msg.accountKeys.slice(0,msg.header.numRequiredSignatures);
 if(signers.length!==2||!signers[0].equals(payer)||!signers[1].equals(mint.publicKey))
  throw new Error('Unexpected legacy transaction signers. Nothing was signed or submitted.');
 const called=[...new Set(tx.instructions.map(ix=>ix.programId.toBase58()))];
 const allowed=new Set([
  program(config).toBase58(),SystemProgram.programId.toBase58(),
  TOKEN_PROGRAM_ID.toBase58(),
  'TokenzQdBNbLqP5VEhdkAS6EPFZ6LKruL4y3Yz9KP',
  'ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL',
  'ComputeBudget111111111111111111111111111111',
  'metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s',
  'MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr'
 ]);
 const unknown=called.filter(id=>!allowed.has(id));
 if(unknown.length||!called.includes(program(config).toBase58()))
  throw new Error('Unknown/missing top-level program(s): '+unknown.join(', ')+'; no transaction submitted.');
 let bytes:number;
 try{bytes=tx.serialize({requireAllSignatures:false,verifySignatures:false}).length}
 catch(e){
  return 'ORBIT Stage 13 - LEGACY read-only comparison\n'+
   'Legacy transaction could not serialize: '+String((e as Error)?.message||e)+
   '\nNo wallet prompt or broadcast.';
 }
 if(bytes>1232)
  return 'ORBIT Stage 13 - LEGACY read-only comparison\n'+
   'Legacy transaction TOO LARGE: '+bytes+' bytes (max 1232). Do not switch the live launch to legacy. No wallet prompt or broadcast.';
 const fee=await connection.getFeeForMessage(msg,'confirmed');
 // Legacy web3.js overload: no second arg => unsigned simulation, no broadcast.
 const sim=await connection.simulateTransaction(tx);
 const status=sim.value.err?'FAILED '+JSON.stringify(sim.value.err):'PASSED (unsigned only)';
 return [
  'ORBIT Stage 13 - LEGACY read-only comparison',
  'No wallet signature requested. No transaction sent. No token created.',
  'Temporary mint and dummy metadata URI, not a production token.',
  'Format: LEGACY (no address lookup tables)',
  'Serialized bytes: '+bytes+' / 1232',
  'Instructions: '+tx.instructions.length+'; required signers: '+signers.length,
  'Fee: '+(fee.value===null?'unavailable':(fee.value/1e9).toFixed(9)+' SOL'),
  'Top-level programs: '+called.join(', '),
  'RPC simulation slot: '+sim.context.slot,
  'RPC simulation: '+status,
  'Units consumed: '+String(sim.value.unitsConsumed??'unavailable'),
  'Last logs:\n'+(sim.value.logs||[]).slice(-8).join('\n'),
  'This checks whether legacy formatting is feasible; it does NOT prove Phantom will approve a real launch.'
 ].join('\n');
}

// ORBIT_STAGE10_VERIFIED_DEVNET_LAUNCH
// Devnet only. No automatic retries or wallet-warning bypass.
export async function launchToken(
 connection:Connection,
 config:AppConfig,
 wallet:WalletContextState,
 input:{name:string;symbol:string;uri:string}
){
 if(config.network!=='devnet')
  throw new Error('Mainnet launches are disabled');

 if(!config.launchEnabled)
  throw new Error(config.launchBlockReason||'Launch unavailable');

 if(!wallet.publicKey||!wallet.signTransaction)
  throw new Error('Connect a V0-compatible Solana wallet');

 const payer=wallet.publicKey;
 const support=wallet.wallet?.adapter?.supportedTransactionVersions;

 if(support&&!support.has(0))
  throw new Error('Wallet does not support V0 transactions');

 if(await connection.getBalance(payer,'confirmed')===0)
  throw new Error('Wallet has no Devnet SOL');

 const programId=program(config);
 const platformId=await requireLaunchPlatform(
  connection,config,payer
 );

 const {configId,configInfo}=await verifyLaunchConfig(
  connection,config
 );

 const raydium=await sdk(connection,config,wallet);
 const mint=Keypair.generate();
 const quote=await raydium.token.getTokenInfo(configInfo.mintB);

 const built=await raydium.launchpad.createLaunchpad({
  programId,
  mintA:mint.publicKey,
  name:input.name,
  symbol:input.symbol,
  uri:input.uri,
  decimals:6,
  migrateType:'cpmm',
  configId,
  configInfo,
  mintBDecimals:quote.decimals,
  createOnly:true,
  buyAmount:new BN(1000),
  slippage:new BN(100),
  extraSigners:[mint],
  txVersion:TxVersion.V0,
  platformId
 } as any);

 if(!Array.isArray(built.transactions)||
    built.transactions.length!==1)
  throw new Error(
   'Expected one Raydium transaction. Signing blocked.'
  );

 const original=built.transactions[0];

 if(!(original instanceof VersionedTransaction)||
    original.message.version!==0)
  throw new Error('Unsupported Raydium transaction format');


 const message=original.message;
 // ORBIT_STAGE11_ALT_RESOLUTION
 // Solana V0 Address Lookup Tables are valid. Resolve every referenced table
 // on the same Devnet RPC, then validate programs using ALL resolved keys.
 // Missing tables or program IDs not on the existing allowlist fail closed.
 const lookupTables=await Promise.all(
  message.addressTableLookups.map(async lookup=>{
   const result=await connection.getAddressLookupTable(
    lookup.accountKey,{commitment:'confirmed'}
   );
   if(!result.value)
    throw new Error('Missing Devnet address lookup table: '+lookup.accountKey.toBase58());
   return result.value;
  })
 );
 const resolvedKeys=message.getAccountKeys({addressLookupTableAccounts:lookupTables});
 for(const ix of message.compiledInstructions){
  if(!resolvedKeys.get(ix.programIdIndex) ||
     ix.accountKeyIndexes.some(i=>!resolvedKeys.get(i)))
   throw new Error('Unresolved Devnet transaction account index; launch blocked');
 }

 const keys=message.staticAccountKeys;

 const signers=keys.slice(
  0,message.header.numRequiredSignatures
 );

 if(signers.length!==2||
    !signers[0].equals(payer)||
    !signers[1].equals(mint.publicKey))
  throw new Error('Unexpected transaction signers');

 const allowed=new Set([
  programId.toBase58(),
  SystemProgram.programId.toBase58(),
  TOKEN_PROGRAM_ID.toBase58(),
  'TokenzQdBNbLqP5VEhdkAS6EPFZ6LKruL4y3Yz9KP',
  'ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL',
  'ComputeBudget111111111111111111111111111111',
  'metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s',
  'MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr'
 ]);

 const programs=message.compiledInstructions.map(
  ix=>resolvedKeys.get(ix.programIdIndex)?.toBase58()
 );

 if(!programs.includes(programId.toBase58())||
    programs.some(id=>!id||!allowed.has(id)))
  throw new Error('Unreviewed program in launch transaction');

 const bh=await connection.getLatestBlockhash('confirmed');

 const tx=new VersionedTransaction(message);
 tx.message.recentBlockhash=bh.blockhash;

 tx.sign([mint]);

 if(tx.serialize().length>1232)
  throw new Error('Transaction exceeds Solana size limit');

 const sim=await connection.simulateTransaction(tx,{
  sigVerify:false,
  commitment:'confirmed'
 });

 if(sim.value.err)
  throw new Error(
   'Devnet simulation failed: '+
   JSON.stringify(sim.value.err)+' | '+
   (sim.value.logs||[]).slice(-15).join(' | ')
  );

 const expected=tx.message.serialize();
 let signed:VersionedTransaction;

 try {
  signed=await wallet.signTransaction(tx) as VersionedTransaction;
 } catch(e) {
  throw new Error(
   'Phantom rejected transaction. Do not bypass safety warnings. '+
   String((e as Error).message||e)
  );
 }

 if(!(signed instanceof VersionedTransaction))
  throw new Error('Invalid signed transaction type');

 const actual=signed.message.serialize();

 if(actual.length!==expected.length||
    actual.some((b,i)=>b!==expected[i]))
  throw new Error('Wallet changed transaction message');

 if(signed.signatures.length!==2||
    signed.signatures.some(sig=>!sig.some(b=>b!==0)))
  throw new Error('Required signature missing');

 const signature=await connection.sendRawTransaction(
  signed.serialize(),
  {
   skipPreflight:false,
   preflightCommitment:'confirmed',
   maxRetries:0
  }
 );

 let confirmation;

 try {
  confirmation=await connection.confirmTransaction(
   {signature,...bh},
   'confirmed'
  );
 } catch(e) {
  throw new Error(
   'Submission status uncertain. Check Devnet transaction '+
   signature+' before retrying. '+String(e)
  );
 }

 if(confirmation.value.err)
  throw new Error(
   'Transaction '+signature+' failed: '+
   JSON.stringify(confirmation.value.err)
  );

 return {
  mint:mint.publicKey.toBase58(),
  poolId:built.extInfo.address.poolId.toBase58(),
  programId:programId.toBase58(),
  txSignature:signature
 };
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
