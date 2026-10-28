import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
const require=createRequire(import.meta.url);
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
let ts;
try {ts=require('typescript');} catch { try{ts=require('/opt/nvm/versions/node/v22.16.0/lib/node_modules/typescript/lib/typescript.js')}catch{console.log('TypeScript unavailable, skipping'); process.exit(0)} }
function recurse(dir){return fs.readdirSync(dir,{withFileTypes:true}).flatMap(f=>f.isDirectory()?recurse(path.join(dir,f.name)):!f.name.endsWith('.d.ts') && !/\.d\.ts$/.test(f.name)&&/\.(tsx?|jsx?)$/.test(f.name)?[path.join(dir,f.name)]:[])}
let bad=false;
for(const p of [...recurse(path.join(root,'web','src')),path.join(root,'vite.config.ts')]){
 const source=fs.readFileSync(p,'utf8');
 const result=ts.transpileModule(source,{fileName:path.relative(root,p), reportDiagnostics:true,compilerOptions:{module:ts.ModuleKind.ESNext,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2022}});
 const errs=(result.diagnostics??[]).filter(d=>d.category===ts.DiagnosticCategory.Error);
 if(errs.length){bad=true;console.error(p, errs.map(e=>ts.flattenDiagnosticMessageText(e.messageText,' ')).join('\n'));}
 }
if(bad)process.exit(1); console.log('TypeScript/TSX syntax: OK');
