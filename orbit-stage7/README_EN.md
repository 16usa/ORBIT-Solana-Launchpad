# ORBIT Stage 7 — mobile Phantom transaction-signing compatibility

## Diagnosis

The launch progressed past Devnet RPC, Raydium program, PlatformConfig, wallet connectivity, and the zero-balance check. It now fails at the wallet approval boundary as `WalletSignTransactionError: Unexpected error`. This does **not** prove Phantom itself is at fault: a wallet can reject an invalid or unsupported launch transaction, or a mobile webview may not support the SDK's multi-transaction signing path.

## What this patch changes

1. On **mobile only**, Raydium SDK's `signAllTransactions` interface is backed by `wallet.signTransaction` invoked once per transaction, sequentially. It never automatically retries an approval that failed. Desktop behavior is unchanged.
2. Adds a **Test wallet signature (no broadcast)** button on the Devnet Create Token page. It builds a Solana version-0 transaction that transfers **0 lamports to the same wallet**, asks the connected wallet to sign, checks the returned signature, and **never submits that transaction**. Approval may still be requested by the wallet.
3. Preserves the existing Stage 6 preflight and diagnostics. **No attempt to bypass user approval.** No token is created by the diagnostic.

If the test **fails**, try the same Dev preview URL inside the **official Phantom mobile in-app browser** (not the Replit app browser) with Phantom Testnet Mode set to Solana Devnet. If it **passes**, the wallet can sign a simple V0 transaction; the failing launch could still be transaction-specific or SDK-related. The patch does not guarantee a mint will succeed.

## Install — Replit Shell only

Upload `orbit_stage7.zip` to the existing ORBIT Replit workspace, then:

```sh
cd /home/runner/workspace
unzip -o orbit_stage7.zip -d .
python3 orbit-stage7/apply_stage7.py
python3 orbit-stage7/verify_stage7.py
pnpm --filter @workspace/orbit-launchpad run test
pnpm --filter @workspace/orbit-launchpad run check:syntax
pnpm --filter @workspace/orbit-launchpad run typecheck
pnpm --filter @workspace/orbit-launchpad run build
```

If any command fails, do **not** publish; examine the error. The installer checks the Stage 6 markers and takes backups at `.orbit-backups/stage7-*`.

## After install

Refresh the **development** site, or manually restart its Dev Workflow if necessary. Before making another token creation attempt, review the Phantom Devnet activity to rule out a previously submitted mint. Press **Test wallet signature (no broadcast)** and inspect its result. This does not cost SOL, send a network transaction, or create a mint.

## Guardrails and limitations

- No automatic process restarts, no dependency installation, no Git push, no Republish, no Mainnet enablement.
- Backend and uploaded metadata still use ephemeral storage. Production token launches require durable metadata and an independent security review.
- Static syntax + server tests do not prove Phantom compatibility; the wallet test needs a real connected wallet and user consent.
