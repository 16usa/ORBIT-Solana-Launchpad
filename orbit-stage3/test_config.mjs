// Safe self-contained smoke test: an ephemeral test API on localhost only.
// No real Solana requests, no wallet signing, no live process changes.
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { resolve, join } from 'node:path';
import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';

const temp = mkdtempSync(join(tmpdir(), 'orbit-stage3-'));
process.env.DATA_DIR = temp;
process.env.SOLANA_CLUSTER = 'devnet';
process.env.RPC_URL = 'https://api.devnet.solana.com';
process.env.VITE_RPC_URL = 'https://api.devnet.solana.com';
process.env.PUBLIC_BASE_URL = 'https://orbit-solana-launchpad.replit.app';
process.env.RAYDIUM_PROGRAM_ID = 'DRay6fNdQ5J82H7xV6uq2aV3mNrUZ1J4PgSKsWgptcm6';
process.env.ENABLE_MAINNET_TRADING = 'false';
const modulePath = resolve('artifacts/orbit-launchpad/original/orbit-solana-launchpad/server/app.mjs');
let server;
try {
  const { makeServer } = await import(pathToFileURL(modulePath).href);
  server = makeServer();
  await new Promise((ok, fail) => server.listen(0, '127.0.0.1', ok).once('error', fail));
  const url = `http://127.0.0.1:${server.address().port}`;
  const response = await fetch(url + '/api/config');
  assert.equal(response.status, 200);
  const config = await response.json();
  assert.equal(config.network, 'devnet');
  assert.equal(config.publicBase, 'https://orbit-solana-launchpad.replit.app');
  assert.equal(config.launchEnabled, true);
  assert.equal(config.raydiumProgramAllowlisted, true);
  assert.equal(config.mainnetTradingEnabled, false);
  console.log('ORBIT Stage 3 isolated API config smoke test: PASS');
} finally {
  if (server) await new Promise(ok => server.close(ok));
  rmSync(temp, { recursive: true, force: true });
}
