import React,{useEffect,useMemo,useState,useCallback} from 'react';
import {useWallet,useConnection} from '@solana/wallet-adapter-react';
import OrbitWalletButton from './OrbitWalletButton';
import {Rocket,Search,Plus,Home,Compass,UserRound,MoreHorizontal,ArrowUpRight,ChevronDown,Grid2X2,Rows3,SlidersHorizontal,Wallet,BarChart3,TrendingUp,Copy,CheckCircle2,AlertTriangle,X,Menu,Trophy,Radio,Coins,RefreshCw,LoaderCircle,ExternalLink,ShieldCheck,Info,ArrowLeft,Upload,Clock,Share2} from 'lucide-react';
import {AppConfig,Launch,NetworkStatus,callApi,postJson,shorten,ago} from './api';
import {PoolView,getPool,verifyLaunchConfig,launchToken,curveTrade,migratedTrade,requireLaunchPlatform,checkWalletSigning,inspectRaydiumLaunch} from './chain';
import WalletSetup from './WalletProvider';
import './styles.css';

type Page='discover'|'home'|'create'|'portfolio'|'menu'|'leaderboard'|'live'|'rewards'|'token';
function getInitialRoute():{page:Page;mint:string}{const h=location.hash.replace(/^#\/?/,'');if(h.startsWith('token/'))return {page:'token',mint:h.slice(6)};return {page:((['discover','home','create','portfolio','menu','leaderboard','live','rewards'].includes(h)?h:'discover') as Page),mint:''};}
function navigate(page:Page,mint=''){location.hash=page==='token'?`#/token/${mint}`:`#/${page}`;}
function Logo(){return <div className="logo" aria-label="Orbit"><span className="logo-ball"><span className="logo-dot"/></span><span>ORBIT<span className="logo-period">.</span></span></div>}
function Notice({network}:{network:string}){return <span className={'network-tag '+(network==='devnet'?'devnet':'mainnet')}><span className="live-dot"/> {network==='devnet'?'DEVNET — Test Network':'SOLANA MAINNET'}</span>}
function Toast({message,onClose}:{message:string;onClose:()=>void}){useEffect(()=>{const t=setTimeout(onClose,6500);return()=>clearTimeout(t)},[message,onClose]);return <aside className="toast" role="alert"><span>{message}</span><button onClick={onClose}><X size={15}/></button></aside>}
function Banner({children}:{children:React.ReactNode}){return <div className="banner"><Info size={16}/><span>{children}</span></div>}
function IconButton({children,onClick,title}:{children:React.ReactNode;onClick:()=>void;title:string}){return <button className="icon-btn" onClick={onClick} title={title}>{children}</button>}
function Empty({icon,heading,body,action}:{icon:React.ReactNode;heading:string;body:string;action?:React.ReactNode}){return <section className="empty"><div className="empty-icon">{icon}</div><h3>{heading}</h3><p>{body}</p>{action}</section>}
const allNav:{page:Page;title:string;icon:React.ReactNode}[]=[{page:'home',title:'Home',icon:<Home/>},{page:'discover',title:'Explore',icon:<Compass/>},{page:'create',title:'Create',icon:<Plus/>},{page:'portfolio',title:'Profile',icon:<UserRound/>},{page:'menu',title:'Menu',icon:<MoreHorizontal/>}];
function Nav({page}:{page:Page}){return <nav className="bottom-nav">{allNav.map(n=><button key={n.page} className={page===n.page?'active':''} onClick={()=>navigate(n.page)} title={n.title}>{n.icon}<span>{n.title}</span></button>)}</nav>}
function Header({config,openSearch}:{config:AppConfig;openSearch:()=>void}){return <header className="header"><button className="logo-action" onClick={()=>navigate('discover')}><Logo/></button><div className="header-right"><Notice network={config.network}/><IconButton onClick={openSearch} title="Search"><Search size={19}/></IconButton><OrbitWalletButton/></div></header>}
function MiniGraph({values}:{values:number[]}){if(values.length<2)return <div className="empty-graph">—</div>;const w=112,h=37,mn=Math.min(...values),mx=Math.max(...values);const span=mx-mn||1;const pts=values.map((v,i)=>`${(i/(values.length-1)*w).toFixed(1)},${(h-4-((v-mn)/span)*(h-8)).toFixed(1)}`).join(' ');return <svg className="mini-graph" viewBox="0 0 112 37" preserveAspectRatio="none" aria-label="Recent price history"><polyline points={pts} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>}
function CoinAvatar({l,size='small'}:{l:Launch;size?:'small'|'large'}){return <span className={'coin-avatar '+size}>{l.image?<img src={l.image} alt="" loading="lazy"/>:<Coins size={24}/>}<span className="sol-badge">≋</span></span>}
function PoolStamp({pool}:{pool?:PoolView}){if(!pool)return <span className="subdued">No data</span>;return <span className="price">{pool.priceSol>0?pool.priceSol.toExponential(3):'—'} <span>SOL</span></span>}
function ExplorerUrl({network,mint,children}:{network:string;mint:string;children:React.ReactNode}){return <a href={`https://solscan.io/token/${mint}${network==='devnet'?'?cluster=devnet':''}`} target="_blank" rel="noreferrer">{children}</a>}
function Cards({items,market,graph,mode,open}:{items:Launch[];market:Record<string,PoolView>;graph:Record<string,number[]>;mode:'grid'|'table';open:(mint:string)=>void}){
 if(mode==='table')return <div className="table-scroll"><table className="coin-table"><thead><tr><th>COIN</th><th>GRAPH</th><th>PRICE (SOL)</th><th>PROGRESS</th></tr></thead><tbody>{items.map((l,i)=><tr key={l.mint} onClick={()=>open(l.mint)}><td><span className="table-num">{i+1}</span><CoinAvatar l={l}/><span className="coin-label"><strong>{l.name}</strong><small>${l.symbol}</small></span></td><td><MiniGraph values={graph[l.mint]||[]}/></td><td><PoolStamp pool={market[l.mint]}/></td><td><div className="progress" style={{width:90}}><span style={{width:`${market[l.mint]?.progress||0}%`}}/></div></td></tr>)}</tbody></table></div>;
 return <div className="coin-grid">{items.map(l=><button key={l.mint} className="coin-card" onClick={()=>open(l.mint)}><div className="big-img">{l.image?<img src={l.image} alt="" loading="lazy"/>:<Coins/>}<span className="network-pill">SOL</span></div><div className="card-title">{l.name}</div><div className="subdued">${l.symbol}</div><div className="coin-price"><PoolStamp pool={market[l.mint]}/></div><div className="card-sub"><span>{shorten(l.creator,4)}</span><span className="green">● {ago(l.createdAt)}</span></div><p className="card-desc">{l.description||'Solana token launched on Orbit'}</p><div className="card-progress"><div className="progress"><span style={{width:`${market[l.mint]?.progress||0}%`}}/></div><small>{market[l.mint]?`${market[l.mint].progress.toFixed(0)}%`:'No data'}</small></div></button>)}</div>;
}
function Browse({title,tagline,config,items,market,graph,notify}:{title:string;tagline:string;config:AppConfig;items:Launch[];market:Record<string,PoolView>;graph:Record<string,number[]>;notify:(m:string)=>void}){
 const [mode,setMode]=useState<'grid'|'table'>('table');const [query,setQuery]=useState('');const [sort,setSort]=useState<'new'|'progress'>('new');const [filter,setFilter]=useState(false);
 const shown=useMemo(()=>items.filter(l=>(l.name+' '+l.symbol+' '+l.mint).toLowerCase().includes(query.toLowerCase())).sort((a,b)=>sort==='progress'?(market[b.mint]?.progress||0)-(market[a.mint]?.progress||0):new Date(b.createdAt).getTime()-new Date(a.createdAt).getTime()),[items,query,sort,market]);
 return <><div className="page-heading"><small className="eyebrow">{tagline}</small><h1>{title}</h1></div><div className="bar-line"><button className="pill primary" onClick={()=>setSort('progress')}><Rocket size={16}/> Trending</button><button className={'pill secondary '+(sort==='new'?'selected':'')} onClick={()=>setSort('new')}>New</button><span className="bar-spacer"/><span className="chain-chip">≋ <span>Solana</span></span><IconButton onClick={()=>setFilter(!filter)} title="Filter"><SlidersHorizontal size={18}/></IconButton></div>{filter&&<div className="filter-row"><label>Search tokens <input placeholder="Name, ticker, or address" value={query} onChange={e=>setQuery(e.target.value)}/></label><button onClick={()=>setMode(mode==='grid'?'table':'grid')} className="filter-switch">{mode==='grid'?<Rows3 size={17}/>:<Grid2X2 size={17}/>} {mode==='grid'?'Table':'Grid'}</button></div>}
 <div className="browse-toolbar"><span><span className="green">●</span> {shown.length} tokens launched on Orbit</span><div><IconButton title="Grid" onClick={()=>setMode('grid')}><Grid2X2 size={17} color={mode==='grid'?'#77f1af':undefined}/></IconButton><IconButton title="Table" onClick={()=>setMode('table')}><Rows3 size={17} color={mode==='table'?'#77f1af':undefined}/></IconButton></div></div>
 {shown.length?<Cards items={shown} market={market} graph={graph} mode={mode} open={mint=>navigate('token',mint)}/>:<Empty icon={<Compass size={28}/>} heading={query?'No matches found':'Tokens will appear here'} body={query?'Try a different search query.':'Only tokens actually created through this launchpad appear here. There are no demo prices or fabricated coins.'} action={<button className="button green-button" onClick={()=>navigate('create')}><Plus size={17}/> Create token</button>}/>}
 {config.network==='devnet'&&<Banner>You are on Devnet. It uses test SOL with no monetary value. A LaunchLab configuration must exist on this network.</Banner>}
 </>
}
function Creator({config,notify,onCreated}:{config:AppConfig;notify:(m:string)=>void;onCreated:()=>void}){
 const {connection}=useConnection(),wallet=useWallet();
 const [form,setForm]=useState({name:'',symbol:'',description:'',website:'',twitter:'',telegram:''});
 const [file,setFile]=useState<File|null>(null);const [imagePreview,setImagePreview]=useState('');const [busy,setBusy]=useState(false);const [receipt,setReceipt]=useState('');const [advanced,setAdvanced]=useState(false);
 const [rpcStatus,setRpcStatus]=useState<NetworkStatus|null>(null);const [checking,setChecking]=useState(false);
 async function checkRpc(){setChecking(true);try{
  const status=await callApi<NetworkStatus>('/api/network-status');
  if(!status.ready){setRpcStatus(status);return}
  try{const verified=await verifyLaunchConfig(connection,config);
   setRpcStatus({...status,reason:'SOL LaunchLab config verified: '+verified.configId.toBase58()});}
  catch(e){setRpcStatus({...status,ready:false,reason:(e as Error).message})}
 }catch(e){notify('RPC check failed: '+(e as Error).message)}finally{setChecking(false)}}
 // ORBIT_STAGE5_LAUNCH_DIAGNOSTICS
 const [launchError,setLaunchError]=useState('');
 const update=(k:string,v:string)=>setForm(p=>({...p,[k]:v}));
 const onFile=(f?:File)=>{if(!f)return;if(f.size>5_000_000){notify('Maximum image size is 5 MB');return}if(!['image/png','image/jpeg','image/gif','image/webp'].includes(f.type)){notify('Supported formats: PNG, JPG, GIF, and WebP');return}setFile(f);setImagePreview(URL.createObjectURL(f))};
 function uploadBase64(file:File):Promise<string>{return new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result).split(',')[1]);reader.onerror=reject;reader.readAsDataURL(file)})}
 // ORBIT_STAGE7_WALLET_TEST: no broadcast; requires a wallet approval.
 async function testWalletSignature(){
  if(busy)return;
  setBusy(true);
  setLaunchError('');
  try{
   await checkWalletSigning(connection,config,wallet);
   setLaunchError('Wallet signature test: PASSED. Phantom signed a Devnet version-0 transaction locally. Nothing was sent to Solana. A failing launch may involve transaction-specific instructions or the Raydium SDK.');
   notify('Wallet signature test passed. No transaction was sent.');
  }catch(err){
   const e=err as any;
   setLaunchError(`Wallet signature test: FAILED (no transaction sent).\n${String(e?.name||'Error')}: ${String(e?.message||err)}\nIf this failed in a Replit browser, open ORBIT inside the official Phantom in-app browser and verify Testnet Mode is set to Solana Devnet.`);
   notify('Wallet signature test failed. No transaction was sent.');
  }finally{setBusy(false)}
 }
 // ORBIT_STAGE12_READONLY_AUDIT
 // Inspect a Raydium launch WITHOUT asking Phantom to sign.
 async function inspectRaydium(){
  if(busy)return;
  setBusy(true);setLaunchError('');
  try{
   const report=await inspectRaydiumLaunch(connection,config,wallet);
   setLaunchError(report.slice(0,6500));
   notify('Read-only Raydium audit completed. No wallet prompt.');
  }catch(err){
   setLaunchError('Read-only Raydium audit failed. No transaction sent.\n'+String((err as Error)?.message||err));
   notify('Raydium audit failed; no transaction sent.');
  }finally{setBusy(false)}
 }
 async function create(e:React.FormEvent){e.preventDefault();if(!wallet.publicKey){notify('Connect your wallet first');return}if(!file){notify('Upload a token image');return}if(!config.launchEnabled){notify(config.launchBlockReason||'Token creation is currently disabled');return}
 setBusy(true);setReceipt('');setLaunchError('');let stage='Preparing launch';try{
  stage='Checking Solana Devnet';
  const network=await callApi<NetworkStatus>('/api/network-status');setRpcStatus(network);
  if(!network.ready)throw new Error(network.reason||'Devnet RPC or Raydium program is not ready');
  await verifyLaunchConfig(connection,config);
  // Fail before uploading metadata when the wallet has no Devnet platform config.
  stage='Verifying Raydium PlatformConfig';
  await requireLaunchPlatform(connection,config,wallet.publicKey);
  stage='Uploading token image';
  const uploaded=await postJson<{id:string}>('/api/media',{base64:await uploadBase64(file)});
  stage='Preparing token metadata';
  const meta=await postJson<{id:string;uri:string}>('/api/metadata',{...form,imageId:uploaded.id});
  stage='Building, signing or confirming Raydium launch';
  const tx=await launchToken(connection,config,wallet,{name:form.name.trim(),symbol:form.symbol.trim().toUpperCase(),uri:meta.uri});
  setReceipt(tx.mint);
  // A confirmed on-chain launch must not be lost if off-chain indexing fails.
  const pending={...tx,metadataId:meta.id,creator:wallet.publicKey.toBase58()};localStorage.setItem('orbit:pending-launch',JSON.stringify(pending));
  stage='Registering confirmed on-chain token';
  await postJson('/api/launches',pending);localStorage.removeItem('orbit:pending-launch');
  notify('Token created! The blockchain transaction is confirmed.');onCreated();navigate('token',tx.mint);
 }catch(err){
  const problem=err as any;
  const cause=problem?.cause;
  const logs=Array.isArray(problem?.logs)?problem.logs:[];
  const text=[
   `Step: ${stage}`,
   `Error: ${String(problem?.name||'Unknown')}`,
   `Message: ${String(problem?.message||err)}`,
   cause?`Cause: ${String(cause?.message||cause)}`:'',
   problem?.reason?`Reason: ${String(problem.reason)}`:'',
   problem?.signature?`Transaction signature: ${String(problem.signature)}`:'',
   logs.length?`Logs: ${logs.slice(0,20).join('\n')}`:'',
  ].filter(Boolean).join('\n');
  console.error('[ORBIT Devnet launch error]',stage,err);
  setLaunchError(text.slice(0,3500));
  notify(String(problem?.message||'Token creation failed'));
 }finally{setBusy(false)} }
 return <div className="create-wrap"><div className="create-header"><button className="back-link" onClick={()=>navigate('discover')}><ArrowLeft size={17}/> Back</button><h1>Create a new token</h1><p>The token and bonding curve are created on Solana through Raydium LaunchLab. You must approve each transaction in your wallet.</p></div>
 <form onSubmit={create} className="form-layout"><div className="form-main"><div className="panel"><div className="panel-label">Token details</div><p className="micro-note">The token name and ticker cannot be changed after creation.</p><label>Token name <input required maxLength={32} minLength={2} placeholder="Name your coin" value={form.name} onChange={e=>update('name',e.target.value)}/></label><label>Ticker <input required maxLength={10} minLength={2} pattern="[a-zA-Z0-9_]+" placeholder="e.g., ORB" value={form.symbol} onChange={e=>update('symbol',e.target.value)}/></label><label>Description (optional) <textarea maxLength={800} rows={4} placeholder="What is your project about?" value={form.description} onChange={e=>update('description',e.target.value)}/></label><button type="button" className="text-toggle" onClick={()=>setAdvanced(!advanced)}>Add social links <ChevronDown size={15} style={{transform:advanced?'rotate(180deg)':undefined}}/></button>{advanced&&<div className="socials">{(['website','twitter','telegram'] as const).map(k=><label key={k}>{k==='website'?'Website':k==='twitter'?'X / Twitter':'Telegram'} <input type="url" placeholder="https://..." value={form[k]} onChange={e=>update(k,e.target.value)}/></label>)}</div>}<hr/><div className="panel-label">Liquidity asset</div><div className="sol-choice">≋ <strong>SOL</strong> <span>Raydium LaunchLab</span></div><p className="micro-note">The initial quote asset is SOL. The token launches on a bonding curve and may migrate to a Raydium pool when the protocol requirements are met.</p></div>
 <div className="panel"><div className="panel-label">Coin image</div><label className="drop-zone"><input type="file" accept="image/png,image/jpeg,image/gif,image/webp" onChange={e=>onFile(e.target.files?.[0])} hidden/>{imagePreview?<img className="file-preview" src={imagePreview} alt="Token preview"/>:<Upload size={33}/>}<strong>{file?file.name:'Select an image'}</strong><small>PNG, JPG, GIF, WebP · up to 5 MB</small></label></div></div>
 <aside className="form-side"><div className="panel sticky-panel"><div className="panel-label">Launch settings</div><div className="property"><span>Network</span><b>{config.network==='devnet'?'Solana Devnet':'Solana Mainnet'}</b></div><div className="property"><span>Protocol</span><b>Raydium LaunchLab</b></div><div className="property"><span>Type</span><b>Bonding curve</b></div><div className="property"><span>Initial buy</span><b>None</b></div><div className="property"><span>Fee</span><b>Set by the protocol</b></div><div className="property"><span>RPC / Program</span><b>{rpcStatus?(rpcStatus.ready?'Ready for config check': 'Unavailable'):'Not checked'}</b></div><button className="button full" type="button" onClick={checkRpc} disabled={checking}>{checking?'Checking network…':'Check Devnet connection'}</button>{rpcStatus&&<p className={rpcStatus.ready?'micro-note':'warning-text'}>{rpcStatus.reason}{rpcStatus.slot!==null?` · Slot ${rpcStatus.slot}`:''}</p>}<Banner>All network fees and transactions must be approved in your wallet. Private keys are never sent to the app.</Banner>{receipt&&<p className="success-receipt">Created token address: <code>{receipt}</code></p>}{launchError&&<div role="alert" className="warning-text" style={{whiteSpace:'pre-wrap',overflowWrap:'anywhere',margin:'12px 0',fontSize:12}}><strong>Launch diagnostics</strong><br/>{launchError}<p style={{marginTop:10}}>If Phantom requested approval, check your Devnet transaction activity before attempting another launch.</p></div>}{!config.launchEnabled&&<p className="warning-text">{config.launchBlockReason}</p>}
 {wallet.publicKey&&config.network==='devnet'&&<button className="button full" type="button" disabled={busy} onClick={testWalletSignature}>Test wallet signature (no broadcast)</button>}{wallet.publicKey&&config.network==='devnet'&&<button className="button full" type="button" disabled={busy} onClick={inspectRaydium}>Inspect Raydium launch (read-only; no wallet prompt)</button>}{wallet.publicKey?<button className="button green-button full" type="submit" disabled={busy||!config.launchEnabled}>{busy?<><LoaderCircle className="spin" size={18}/> Approve in your wallet…</>:<><Rocket size={17}/> Create token on Solana</>}</button>:<div className="center-wallet"><OrbitWalletButton showHint/></div>}
 </div></aside></form></div>;
}
function TokenDetails({item,config,pool,graph,notify}:{item?:Launch;config:AppConfig;pool?:PoolView;graph:number[];notify:(m:string)=>void}){
 const {connection}=useConnection();const wallet=useWallet();const [side,setSide]=useState<'buy'|'sell'>('buy');const [amount,setAmount]=useState('0.1');const [slip,setSlip]=useState('1');const [busy,setBusy]=useState(false);const [sig,setSig]=useState('');
 const route=pool?.status===0?'curve':pool?.status===2?'jupiter':null;
 const routeEnabled=route==='curve' || (route==='jupiter' && config.network==='mainnet-beta' && config.mainnetTradingEnabled && config.tradeEnabled);
 const poolStatus=pool?.status===0?'Bonding curve active':pool?.status===1?'Waiting for migration':pool?.status===2?'Migrated to AMM':'Loading pool status';
 const display=useMemo(()=>item,[item]);if(!display)return <Empty icon={<Search/>} heading="Token not found" body="This address is not in the Orbit registry." action={<button className="button" onClick={()=>navigate('discover')}>Open catalog</button>}/>;
 const explorer=(sig:string)=>`https://solscan.io/tx/${sig}${config.network==='devnet'?'?cluster=devnet':''}`;
  async function trade(){if(!display){notify('Token not found');return}if(!wallet.publicKey){notify('Connect wallet');return}if(!route||!routeEnabled){notify(poolStatus+'. Trading is unavailable for this token on this network.');return}if(config.network==='mainnet-beta'&&!config.mainnetTradingEnabled){notify('Mainnet trading is disabled until reviewed');return}setBusy(true);setSig('');try{
  const tx=route==='jupiter'?await migratedTrade(wallet,display,side,amount):await curveTrade(connection,config,wallet,display,side,amount,Math.round(Number(slip)*100));
  setSig(tx);notify('Transaction submitted and confirmed');
 }catch(err){notify((err as Error).message)}finally{setBusy(false)} }
 return <div className="detail-wrap"><button className="back-link" onClick={()=>navigate('discover')}><ArrowLeft size={17}/> All tokens</button><div className="detail-title"><CoinAvatar l={display} size="large"/><div><h1>{display.name} <span>${display.symbol}</span></h1><div className="address-line"><span>{shorten(display.mint,7)}</span><IconButton title="Copy address" onClick={()=>{navigator.clipboard.writeText(display.mint);notify('Address copied')}}><Copy size={14}/></IconButton><ExplorerUrl network={config.network} mint={display.mint}><ExternalLink size={15}/></ExplorerUrl></div></div></div>
 <div className="detail-grid"><section className="detail-main"><div className="stats-grid"><div className="stat"><small>Token price</small><strong>{pool?(pool.status===0?`${pool.priceSol.toExponential(5)} SOL`:'Not on bonding curve'):'No data'}</strong></div><div className="stat"><small>Curve progress</small><strong>{pool?`${pool.progress.toFixed(2)}%`:'No data'}</strong></div><div className="stat"><small>SOL raised</small><strong>{pool?pool.raisedSol.toFixed(3):'—'}</strong></div><div className="stat"><small>SOL target</small><strong>{pool?pool.targetSol.toFixed(2):'—'}</strong></div></div><div className="chart-shell"><div className="chart-top"><b>Price history</b><span>Real RPC snapshots (this session only)</span></div>{graph.length>1?<div className="price-chart"><MiniGraph values={graph}/></div>:<div className="no-chart"><BarChart3 size={33}/><strong>No price history yet</strong><span>The chart will appear after a few price updates. Historical candles require a dedicated indexer.</span></div>}</div>
 <div className="panel"><h3>About the token</h3><p>{display.description||'No description provided'}</p><div className="property"><span>Creator</span><b>{shorten(display.creator,7)}</b></div><div className="property"><span>Mint</span><b><ExplorerUrl network={config.network} mint={display.mint}>{shorten(display.mint,9)} <ArrowUpRight size={13}/></ExplorerUrl></b></div><div className="property"><span>Pool</span><b>{shorten(display.poolId,8)}</b></div><div className="property"><span>Verification</span><b className="green">On-chain account</b></div></div></section>
 <aside className="trade-panel panel"><h3>Trade</h3><div className="side-tabs"><button className={side==='buy'?'on buy':''} onClick={()=>setSide('buy')}>Buy</button><button className={side==='sell'?'on sell':''} onClick={()=>setSide('sell')}>Sell</button></div><div className="property"><span>Pool status</span><b>{poolStatus}</b></div><div className="property"><span>Trading route</span><b>{route==='curve'?'Raydium bonding curve':route==='jupiter'?'Jupiter (post-migration)':'Unavailable'}</b></div>{pool?.status===1&&<Banner>Curve trading has ended. Migration is pending; no trades can be submitted here.</Banner>}{pool?.status===2&&!routeEnabled&&<Banner>This token graduated. A supported post-migration swap route is not available on this network.</Banner>}<label>Amount <div className="amount-wrap"><input type="text" inputMode="decimal" value={amount} onChange={e=>setAmount(e.target.value)}/><b>{side==='buy'?'SOL':display.symbol}</b></div></label>{route==='curve'&&<label>Max slippage (%) <input type="number" min="0.1" max="5" step="0.1" value={slip} onChange={e=>setSlip(e.target.value)}/></label>}
 <Banner>Prices can change quickly. Buys and sells submit real transactions. Fees, slippage and network costs depend on execution conditions.</Banner><button className={'button full '+(side==='buy'?'green-button':'red-button')} onClick={trade} disabled={busy||!wallet.publicKey||!routeEnabled||config.network==='mainnet-beta'&&!config.mainnetTradingEnabled}>{busy?<><LoaderCircle className="spin"/> Approve in wallet…</>:`${side==='buy'?'Buy':'Sell'} ${display.symbol}`}</button>{!wallet.publicKey&&<div className="center-wallet"><OrbitWalletButton showHint/></div>}{sig&&<a className="tx-link" href={explorer(sig)} rel="noreferrer" target="_blank"><CheckCircle2 size={15}/> View transaction <ExternalLink size={14}/></a>}</aside></div></div>;
}
function Profile({items,config,notify}:{items:Launch[];config:AppConfig;notify:(m:string)=>void}){const {publicKey}=useWallet();const wallet=publicKey?.toBase58();const myItems=items.filter(i=>i.creator===wallet);return <div><div className="page-heading"><small className="eyebrow">ACCOUNT</small><h1>My profile</h1></div>{wallet?<><div className="profile-banner"><Wallet size={24}/><div><b>{shorten(wallet,9)}</b><small>Connected wallet · {config.network}</small></div><IconButton title="Copy address" onClick={()=>{navigator.clipboard.writeText(wallet);notify('Address copied')}}><Copy size={17}/></IconButton></div><h2 className="section-heading">My launches <span>{myItems.length}</span></h2>{myItems.length?<div className="profile-list">{myItems.map(l=><button key={l.mint} className="profile-item" onClick={()=>navigate('token',l.mint)}><CoinAvatar l={l}/><span><strong>{l.name}</strong><small>${l.symbol} · {ago(l.createdAt)}</small></span><ArrowUpRight size={18}/></button>)}</div>:<Empty icon={<Rocket/>} heading="No tokens yet" body="Tokens launched by your wallet through this Orbit instance will appear here." action={<button className="button green-button" onClick={()=>navigate('create')}>Create token</button>}/>}</>:<Empty icon={<Wallet/>} heading="Connect wallet" body="Connect a wallet to see the tokens created by its public address." action={<OrbitWalletButton showHint/>}/>}</div>}
function MenuPage(){const nav=[{page:'discover' as Page,text:'Explore tokens',icon:<Compass/>},{page:'leaderboard' as Page,text:'Leaderboard',icon:<Trophy/>},{page:'live' as Page,text:'Live',icon:<Radio/>},{page:'rewards' as Page,text:'Rewards',icon:<Coins/>},{page:'create' as Page,text:'Create token',icon:<Plus/>}];return <div className="menu-page"><div className="page-heading"><small className="eyebrow">ORBIT</small><h1>Menu</h1></div><div className="menu-links">{nav.map(n=><button key={n.page} onClick={()=>navigate(n.page)}>{n.icon}{n.text}<ArrowUpRight size={16}/></button>)}</div></div>}
function Footer(){return <footer className="footer"><div><b>ORBIT</b><p>Independent interface · Solana launch infrastructure</p></div><div><span>RESOURCES</span><a href="https://solana.com/docs" target="_blank" rel="noreferrer">Solana documentation</a><a href="https://docs.raydium.io/" target="_blank" rel="noreferrer">Raydium LaunchLab</a><a href="https://developers.jup.ag/" target="_blank" rel="noreferrer">Jupiter API</a></div><div><span>INFORMATION</span><p>No returns are guaranteed. Independent security and legal reviews, plus durable metadata storage, are required before a mainnet launch.</p></div><small>© Orbit · Test build · Not affiliated with pump.fun</small></footer>}
function Shell({config}:{config:AppConfig}){
 const [route,setRoute]=useState(getInitialRoute());const [items,setItems]=useState<Launch[]>([]);const [market,setMarket]=useState<Record<string,PoolView>>({});const [history,setHistory]=useState<Record<string,number[]>>({});const [message,setMessage]=useState('');const [search,setSearch]=useState(false);const [query,setQuery]=useState('');
 const {connection}=useConnection();
 const notify=useCallback((m:string)=>setMessage(m),[]);
 const load=useCallback(async()=>{try{const r=await callApi<{items:Launch[]}>('/api/launches');setItems(r.items.filter(l=>l.network===config.network));}catch(e){notify((e as Error).message)}},[config.network,notify]);
 useEffect(()=>{const handler=()=>setRoute(getInitialRoute());window.addEventListener('hashchange',handler);return()=>window.removeEventListener('hashchange',handler)},[]);
 useEffect(()=>{load();const id=setInterval(load,15000);return()=>clearInterval(id)},[load]);
 useEffect(()=>{const saved=localStorage.getItem('orbit:pending-launch');if(saved){try{postJson('/api/launches',JSON.parse(saved)).then(()=>{localStorage.removeItem('orbit:pending-launch');load();notify('Launch restored from a confirmed transaction')}).catch(()=>{})}catch{}}},[load,notify]);
 useEffect(()=>{
  if(!items.length)return;let active=true;
  const update=async()=>{for(const l of (route.page==='token' && items.find(t=>t.mint===route.mint) ? [items.find(t=>t.mint===route.mint)!, ...items.filter(t=>t.mint!==route.mint).slice(0,14)] : items.slice(0,15))){
    if(!active)break;
    try{const p=await getPool(connection,config,l.mint,l.programId);if(active){setMarket(o=>({...o,[l.mint]:p}));setHistory(o=>{const old=o[l.mint]||[];return {...o,[l.mint]:p.status===0 && Number.isFinite(p.priceSol) ? [...old.slice(-60),p.priceSol] : old}});}}
    catch{ /* Missing/failed RPC data is never replaced by fictitious values. */ }
  }};
  update();const id=setInterval(update,20000);return()=>{active=false;clearInterval(id)};
 },[items,connection,config,route.page,route.mint]);
 const visible=useMemo(()=>items.filter(l=>(l.name+' '+l.symbol+' '+l.mint).toLowerCase().includes(query.toLowerCase())),[items,query]);
 const active=items.find(l=>l.mint===route.mint);
 return <><Header config={config} openSearch={()=>setSearch(true)}/><main className="main-container">
 {route.page==='discover'&&<Browse title="Explore coins" tagline="DISCOVER / SOLANA" config={config} items={items} market={market} graph={history} notify={notify}/>}
 {route.page==='home'&&<><div className="hero"><div><small className="eyebrow green">SOLANA · TOKEN LAUNCHPAD</small><h1>Create a token.<br/><em>Launch an idea.</em></h1><p>Launch tokens through Raydium on-chain programs. Transparent transactions, self-custodial wallets, and real on-chain data.</p><button className="button green-button" onClick={()=>navigate('create')}>Create token <ArrowUpRight size={17}/></button></div><div className="hero-planet"><span>O</span><i/></div></div><h2 className="section-heading">New launches <button onClick={()=>navigate('discover')}>View all <ArrowUpRight size={15}/></button></h2>{items.length?<Cards items={items.slice(0,6)} market={market} graph={history} mode="grid" open={m=>navigate('token',m)}/>:<Empty icon={<Rocket/>} heading="Waiting for the first launch" body="Real tokens will appear here once their transactions are confirmed and registered."/>}</>}
 {route.page==='create'&&<Creator config={config} notify={notify} onCreated={load}/>}
 {route.page==='portfolio'&&<Profile items={items} config={config} notify={notify}/>}
 {route.page==='menu'&&<MenuPage/>}
 {route.page==='leaderboard'&&<Browse title="Leaderboard" tagline="LEADERBOARD / BONDING CURVE" config={config} items={[...items].sort((a,b)=>(market[b.mint]?.progress||0)-(market[a.mint]?.progress||0))} market={market} graph={history} notify={notify}/>}
 {route.page==='live'&&<><div className="page-heading"><small className="eyebrow">LIVE</small><h1>Live streams</h1></div><Empty icon={<Radio size={28}/>} heading="Live streaming is not available yet" body="Actual live streams require WebRTC infrastructure, moderation, reports, and recording storage. This page does not simulate a live broadcast."/></>}
 {route.page==='rewards'&&<><div className="page-heading"><small className="eyebrow">REWARDS</small><h1>Rewards</h1></div><Empty icon={<Trophy size={28}/>} heading="Module not available yet" body="Rewards and payouts require a separately audited contract. No simulated balances or rewards are shown."/></>}
 {route.page==='token'&&<TokenDetails key={route.mint} item={active} config={config} pool={market[route.mint]} graph={history[route.mint]||[]} notify={notify}/>}
 </main><Footer/><Nav page={route.page}/>{search&&<div className="search-layer" role="dialog" aria-label="Search"><div className="search-box"><div className="search-head"><Search size={20}/><input autoFocus placeholder="Search by name, ticker, or mint" value={query} onChange={e=>setQuery(e.target.value)}/><IconButton title="Close" onClick={()=>{setSearch(false);setQuery('')}}><X size={19}/></IconButton></div><div className="search-results">{visible.slice(0,15).map(l=><button key={l.mint} onClick={()=>{setSearch(false);setQuery('');navigate('token',l.mint)}}><CoinAvatar l={l}/><span><b>{l.name}</b><small>${l.symbol} · {shorten(l.mint)}</small></span><ArrowUpRight size={16}/></button>)}{!visible.length&&<p>No results</p>}</div></div><button className="search-overlay" onClick={()=>setSearch(false)} aria-label="Close"/></div>}{message&&<Toast message={message} onClose={()=>setMessage('')}/>}</>;
}
export default function App(){const [config,setConfig]=useState<AppConfig|null>(null);const [error,setError]=useState('');useEffect(()=>{callApi<AppConfig>('/api/config').then(setConfig).catch(e=>setError(e.message))},[]);if(error)return <div className="app-loader"><AlertTriangle/><h2>API unavailable</h2><p>{error}</p><span>Start the server: npm run dev</span></div>;if(!config)return <div className="app-loader"><div className="logo-ball"><span className="logo-dot"/></div><p>Connecting to Orbit...</p></div>;return <WalletSetup rpc={config.rpc}><Shell config={config}/></WalletSetup>}
