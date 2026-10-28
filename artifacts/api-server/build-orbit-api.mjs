import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const artifactDir = path.dirname(fileURLToPath(import.meta.url));
const sourceDir = path.resolve(
  artifactDir,
  '../orbit-launchpad/original/orbit-solana-launchpad/server',
);
const outputDir = path.resolve(artifactDir, 'dist/orbit-api');

await fs.access(path.join(sourceDir, 'app.mjs'));
await fs.rm(outputDir, { recursive: true, force: true });
await fs.mkdir(path.dirname(outputDir), { recursive: true });
await fs.cp(sourceDir, path.join(outputDir, 'server'), { recursive: true });

console.log(`Packaged ORBIT API server at ${outputDir}`);
