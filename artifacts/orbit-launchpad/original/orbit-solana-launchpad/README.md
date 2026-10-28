# ORBIT — Solana Launchpad (first implementation)

**A real codebase, not a screen mockup.** An independent interface inspired by the category of token-launch sites. The first implementation uses an existing on-chain Raydium **LaunchLab bonding-curve program**; it does *not* call Pump.fun contracts or use a Pump.fun wallet. The website name, branding and design are original.

## What works in this source

- Responsive English-language dark-mode website: Explore (table/grid), token details, create token form, portfolio of coins created here, home, search, leader board, footer and navigation.
- Wallet Standard-compatible Solana wallet connection (Phantom and other compatible installed wallets via Solana wallet adapter).
- User-submitted token image and on-chain metadata JSON served from the launchpad site.
- Launch transaction builder based on **Raydium SDK 0.2.64-alpha** using the creator's connected wallet and a new local mint keypair. No signing keys are sent to the server. **On-chain token creation must be tested in an actual devnet environment before mainnet.**
- On-chain bonding-curve account reads and SDK buy/sell builders with exact numeric base units and slippage settings. The wallet signs every trade.
- Optional Jupiter Swap API v2 integration for **mainnet migrated pools**; the browser signs the routed transaction.
- Server verifies a transaction exists and is confirmed, the recorded creator is a signer, mint and pool accounts exist and have expected program owners. It then records created tokens in a local JSON registry.
- Zero seeded coins, no simulated prices. In the initial implementation live price snapshots only appear while a user's session is open; **these are not historical candles**.

## What's NOT implemented / not proven

- Pump.fun feature parity (creator revenue programs, realtime global discovery, X live feeds, bounty markets, browser-wide OHLCV history, user profile social graph, content moderation, analytics, full metadata permanence, automatic indexing, custom platform fee program).
- Independent proprietary Solana smart contract. This version is a separate site and brand **using Raydium's on-chain program**, not a separate bespoke bonding-curve program. A custom audited Anchor program is necessary for complete control of curve math and fees.
- Production-grade horizontally scaled backend. `launches.json` is a single-writer prototype store; for production, move to Postgres plus a realtime indexer and durable object storage/IPFS/Arweave for images and metadata.
- No real wallet transactions have been signed during the creation of this code bundle. The launch, trading, and migration integrations **must be verified on devnet and reviewed by a Solana engineer**. Migration is performed by the protocol's authorized migrator, not this site.
- There is no fee or revenue collection to a wallet controlled by Orbit by default. To receive partner fees, configure a legitimate Raydium PlatformConfig with proper on-chain authority and accounting.

See **[INSTALLATION_EN.md](INSTALLATION_EN.md)** for the complete English-language setup guide.

## Start on Replit / local machine

Requirement: Node.js 20.18+ and a browser with a supported Solana wallet.

1. Extract the ZIP into a **new** Replit Node.js workspace. Do not overwrite any existing Memflow workspace.
2. Open Replit Shell and run `npm install`.
3. Copy `.env.example` to `.env` and fill in the values. Replit must expose port `3000` for `npm run start`, or port `5173` for `npm run dev`.
4. Configure the environment in Replit Secrets as needed, including `SOLANA_CLUSTER=devnet`, `RPC_URL`, `VITE_RPC_URL`, `PUBLIC_BASE_URL` set to your **actual public HTTPS URL**. For local UI-only tests, you can leave `PUBLIC_BASE_URL` empty, but on-chain launches will be disabled because the token metadata would not have a publicly reachable URL.
5. Run `npm run dev` for development (two servers) and open the web preview for port `5173`.
6. For production: run `npm run build`, then **manually** start `npm start` (single Node server on `PORT`, default 3000). There is no automatic process restart, kill or redeployment script.
7. `npm test` and `npm run check:syntax` run without connecting wallets. `npx tsc --noEmit` and `npm run build` require installed dependencies.

**Important:** The browser build receives its RPC endpoint and optional platform ID from public `VITE_*` variables. Avoid using API-key-protected URLs in `VITE_RPC_URL` if you need to keep their key private. `PUBLIC_BASE_URL` must remain stable, or the token's permanent on-chain metadata URI may break. This prototype's uploads are local to the server and can be lost if a host resets its filesystem.

The default launch config attempts `getPdaLaunchpadConfigId(programId, NATIVE_MINT, 0, 0)` and chooses `migrateType:'cpmm'`. The chosen Raydium program **must have this config available on the network** and its migration parameters must match the intended economics. If the config doesn't exist, launching fails closed. Do not switch to mainnet just to make the error disappear.

For mainnet swap routing of already migrated coins, add `JUPITER_API_KEY` **only as a server secret**. See https://dev.jup.ag/docs/ultra/ and current Jupiter Swap API v2 docs; their access requirements and schemas can change.

### Example `.env` (replace the public URL)

```
SOLANA_CLUSTER=devnet
RPC_URL=https://api.devnet.solana.com
VITE_RPC_URL=https://api.devnet.solana.com
PUBLIC_BASE_URL=https://your-project.replit.app
PORT=3000
```

### Useful links

- Raydium official launch demos: https://github.com/raydium-io/raydium-docs-v1/blob/main/products/launchlab/code-demos.mdx
- Raydium LaunchLab protocol: https://docs.raydium.io/
- Solana wallet integration: https://solana.com/docs/frontend

### Security / operations checklist before launch

- Verify Raydium deployed program addresses and set `RAYDIUM_PROGRAM_ID` to the correct network's LaunchLab program address for server allowlisting. Verify the platform config ID and fee distributions on-chain.
- Replace local JSON token registry with a transactional database and store image/metadata content on immutable decentralized storage before real users mint tokens.
- Add a blockchain indexer so registration, trades and migrated pool status are recovered after disconnection; validate canonical pool PDA, on-chain token metadata and metadata ownership before exposing a launch as verified.
- Add access controls and quota for media and metadata uploads, address-based anti-abuse controls, upload malware checks, image moderation, alerting, error monitoring and independent security review.
- Add quotes/fee previews and post-confirmation transaction reconciliation on each trading route. Only offer routes supported by on-chain pool status.
- Verify all swaps/fees in devnet, include RPC retries, transaction simulation, mainnet rate limiting and auditing before accepting real funds. Never enter seed phrases in the site or environment.

### Current dev status

Tests cover Node.js server input validation, upload type detection, file storage and API health only. Browser SDK or on-chain integration tests are not run here because this build environment does not have network access for `npm install` or a Solana RPC endpoint. Therefore calling this **production ready** would be misleading.
