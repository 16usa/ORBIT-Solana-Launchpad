# Orbit — Solana Launchpad Setup Guide (English)

This is the **English-language** initial implementation of an independent Solana token launchpad. The website interface, navigation, wallet messages, trading forms, input validation, browser metadata, and setup documentation are all in English.

> **Important:** This is an early technical foundation, **not** a fully functioning Pump.fun clone and **not** a production-ready financial application. The UI and integrations were implemented, but no live launch or trading transaction has been validated by a wallet on Solana. Do not accept mainnet funds until you complete devnet verification, integration testing, and an independent security review.

## Install in a new Replit project

1. Create a **new Node.js Replit**. Do not overwrite an existing Memflow project or deployed website.
2. Upload the ZIP, unzip it in the Replit Shell, and open the project directory.
3. Install dependencies and run the local checks:
   ```bash
   npm install
   npm test
   npm run check:syntax
   npm run build
   ```
4. Configure your Replit deployment as a **Node.js web service / Autoscale**, **not** a Static Deployment. For development, `npm run dev` runs Vite on port `5173` and the API on port `3000`. For a production-style build, run `npm run build`, then manually start `npm start`; the server listens on `process.env.PORT` (default: `3000`).
5. Add the required environment variables in Replit Secrets. Start with Solana **Devnet**:
   ```env
   SOLANA_CLUSTER=devnet
   RPC_URL=https://api.devnet.solana.com
   VITE_RPC_URL=https://api.devnet.solana.com
   PUBLIC_BASE_URL=https://YOUR-PUBLIC-REPLIT-URL
   PORT=3000
   ```
6. `PUBLIC_BASE_URL` must point to an externally reachable HTTPS website because launch metadata is published at this URL. Local/in-memory uploads are **not durable** and must be replaced before any real-money launch.
7. Use a compatible Solana wallet funded with test SOL. An appropriate Raydium LaunchLab configuration must exist on the selected network, otherwise the application should refuse to create the launch.

## Features in this version

- Original mobile and desktop UI with Explore (table and grid), Home, Search, Create Token, Token Details, Profile, Leaderboard, and Menu pages.
- Wallet connection through the Solana Wallet Adapter and Wallet Standard.
- Raydium LaunchLab SDK integration for building on-chain token launches and bonding-curve buy/sell transactions.
- Jupiter Swap API v2 route for post-migration swaps (optional server-side API key).
- Direct Solana RPC pool snapshots, without fabricated prices or coins.
- An API server for token metadata and image upload with transaction and on-chain account checks.

## Features not complete yet

A truly production-ready, independent Pump.fun-style platform also needs a secure and correctly configured fee model, an indexer for all Solana events, historical candles, order/fee previews, secure permanent metadata storage, a transactional database, real-time feeds, moderation and spam controls, creator rewards, a live-streaming stack, financial/legal review, and extensive integration and security testing.

Orbit currently uses an **existing Raydium on-chain bonding-curve program**, not its own custom smart contract. A fully independent protocol requires an audited Solana program (for example, written with Anchor), including bonding-curve math, buy/sell logic, migration, custody boundaries, fees, and authorization checks.

## Notes

- This project is not affiliated with Pump.fun.
- Do not enter wallet seed phrases in your website, Replit Secrets, or this chat.
- Do not turn on mainnet simply to bypass a Devnet configuration error.
- The website defaults to English (`<html lang="en">`); no Russian UI strings are included in this ZIP.
- Read `README.md` for details on limitations, security, and the architecture.
