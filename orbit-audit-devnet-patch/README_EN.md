# ORBIT — Devnet hardening patch (October 2026)

Target repository: `16usa/ORBIT-Solana-Launchpad`.
This **is a patch for the existing Replit workspace**, not a new application.

## Apply safely

1. Upload `ORBIT-devnet-hardening-patch.zip` to the **existing ORBIT** Replit workspace and extract it to the workspace root (do not import the ZIP as a brand-new app).
2. From the ORBIT repository root, run:

   ```bash
   python3 orbit-audit-devnet-patch/apply_orbit_patch.py
   pnpm --filter @workspace/orbit-launchpad run test
   pnpm --filter @workspace/orbit-launchpad run check:syntax
   pnpm --filter @workspace/orbit-launchpad run typecheck
   pnpm --filter @workspace/orbit-launchpad run build
   ```

3. Confirm `GET /api/config` returns `launchEnabled`, `launchBlockReason` and `mainnetTradingEnabled` without revealing secrets.
4. Review `git diff` and then commit/push the changed files from Replit, **only if the tests pass**.
5. Replit must pick up code changes through its normal workflow. This patch **does not restart, kill, deploy or push anything automatically**.

The Python script checks for exact source anchors **before** writing any file, stores backups under `artifacts/orbit-launchpad/original/orbit-solana-launchpad/.orbit-backups/<timestamp>/`, and updates only seven known files. Do not run twice; repeated application intentionally stops instead of applying twice.

## Changes included

- Fix local development requests to `/api`, `/media` and `/metadata` by proxying to the actual Replit API service on port 8080 (`API_PORT` overridable). Production routing remains unchanged.
- Expose explicit **Devnet launch readiness** from `/api/config`, so the Create page explains missing public metadata URL or program allowlist instead of offering a broken launch button.
- **Disable mainnet token creation** while the original implementation relies on ephemeral filesystem uploads. No real-money minting before durable metadata and review.
- Require an allowlisted Raydium program and a successful direct top-level instruction invocation before the server registers a token. This improves checks but does **not** replace canonical PDA/metadata verification.
- Require `ENABLE_MAINNET_TRADING=true` plus a Jupiter API key before enabling existing mainnet swap proxy routes. The frontend blocks mainnet curve trading while this switch is off.
- Reject public metadata base URLs with embedded paths, credentials, queries or fragments.
- Add tests for URL validation and launch gating response fields.

## Verification performed for this patch

- Ran all 18 native Node server tests: **18 passed**.
- Ran `node --check` on both Node server modules: passed.
- Checked that the edit anchors are present in the current GitHub version (including the Replit-specific Vite configuration).

**Not verified:** full PNPM dependency installation/build, wallet interaction, Raydium Devnet config existence, actual token minting or buy/sell confirmation, deployed preview accessibility. These must be tested in Replit and Devnet. Do not describe the product as production-ready.

## Critical remaining launchpad work

1. Replace ephemeral JSON catalog and media files with a transaction-safe database plus permanent object/IPFS/Arweave metadata storage.
2. Integrate a Solana event indexer and reliable token discovery beyond launches made on this single instance.
3. Verify Raydium configuration IDs and Devnet create/buy/sell/migrate flows using real test wallets.
4. Validate canonical pool PDAs, on-chain metadata URI and authentic launch instruction semantics before displaying a token as independently verified.
5. Add historical OHLCV price data, real-time transaction feeds and portfolio accounting.
6. Audit financial permissions, fees, rate limits, wallet signing, RPC resilience and moderation before mainnet.

All user-facing UI remains English. No simulated transactions or fake market data are added.
