export type AppConfig={network:'devnet'|'mainnet-beta';rpc:string;publicBase:string;tradeEnabled:boolean;mainnetTradingEnabled:boolean;launchEnabled:boolean;launchBlockReason:string;raydiumProgramAllowlisted:boolean};
export type NetworkStatus={network:string;rpcReachable:boolean;programDeployed:boolean;ready:boolean;slot:number|null;reason:string};
export type Launch={mint:string;poolId:string;creator:string;programId:string;txSignature:string;metadataId:string;network:string;name:string;symbol:string;image:string;description:string;createdAt:string;verified:boolean;confidence:string};
export const SOL='So11111111111111111111111111111111111111112';
export async function callApi<T=any>(path:string,options?:RequestInit):Promise<T>{
 const r=await fetch(path,{...options,headers: {...(options?.body?{'content-type':'application/json'}:{}),...options?.headers}});
 let data;try{data=await r.json()}catch{throw new Error(`HTTP ${r.status}`)}
 if(!r.ok)throw new Error(data?.error||data?.message||`HTTP ${r.status}`);
 return data as T;
}
export function postJson<T=any>(p:string, data:any){return callApi<T>(p,{method:'POST',body:JSON.stringify(data)});}
export function amountBaseUnits(input:string,decimals:number):string{
 const t=input.trim();if(!/^\d+(?:\.\d+)?$/.test(t))throw new Error('Enter a positive amount');
 const [whole,fraction='']=t.split('.');if(fraction.length>decimals)throw new Error(`Maximum ${decimals} decimal places`);
 const raw=BigInt(whole||'0')*10n**BigInt(decimals)+BigInt((fraction.padEnd(decimals,'0')||'0'));
 if(raw<=0n || raw>(2n**64n-1n))throw new Error('Amount is outside the allowed range');return raw.toString();
}
export const shorten=(v:string,n=5)=>v?`${v.slice(0,n)}…${v.slice(-4)}`:'—';
export function ago(date:string){const t=Math.max(0,Math.floor((Date.now()-new Date(date).getTime())/1000));return t<60?`${t}s`:t<3600?`${Math.floor(t/60)}m`:t<86400?`${Math.floor(t/3600)}h`:`${Math.floor(t/86400)}d`;}
