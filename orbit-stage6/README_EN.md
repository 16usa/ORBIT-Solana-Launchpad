# ORBIT Stage 6 — Devnet Wallet Signing Preflight

The previous `WalletSignTransactionError / Unexpected error` happens while Phantom signs a Raydium LaunchLab creation transaction. **It does not by itself prove a wallet defect**: the transaction payload, wallet network mode or signer requirements might be the cause.

## Changes

- Before requesting Phantom approval, check that the connected wallet supports V0 transactions and has a nonzero **Devnet** SOL balance.
- Ask Solana Devnet RPC to **simulate the first Raydium launch transaction without signature verification**. If the simulation fails, show the error and program logs before prompting Phantom.
- If simulation succeeds but Phantom still rejects the signature, show a more actionable error including its original adapter error and safe next steps.
- Uses the existing Stage 5 diagnostics display. No new permissions, private keys, or changes to signing methods.

**Limitations:** A successful RPC simulation does not guarantee Phantom will sign or that the eventual transaction will succeed. Later dependent transactions are not simulated. Phantom Testnet Mode must match Solana Devnet. This patch does **not** fix underlying wallet provider bugs. Do not repeatedly submit launches without checking Devnet history for previously successful transactions.

## Install with Replit Shell (no Agent)

Upload `orbit_stage6.zip` to the ORBIT workspace Files and run:

```sh
cd /home/runner/workspace
unzip -o orbit_stage6.zip -d .
python3 orbit-stage6/apply_stage6.py
python3 orbit-stage6/verify_stage6.py
pnpm --filter @workspace/orbit-launchpad run check:syntax
pnpm --filter @workspace/orbit-launchpad run typecheck
pnpm --filter @workspace/orbit-launchpad run build
```

The script changes only `web/src/chain.ts` and creates a timestamped backup. It does not restart services or publish to `.replit.app`. To see it in `.replit.dev`, refresh Dev Preview after the developer workflow picks up the source change. If necessary restart the Dev workflow **manually**. **Do not Republish.**

## Interpreting results

- `Devnet launch simulation failed` -> review program logs. This is a blockchain preparation or program error, before the wallet is asked to sign.
- `Phantom or wallet adapter could not sign` -> request reached wallet signing; check Phantom's **Testnet Mode**, connected address, Devnet SOL balance, and wallet rejection UI. The SDK may also pass an unsupported payload; report the full error (but never seed phrases or private keys).
- `No confirmed creation transaction returned` -> signature/submission confirmation was not returned. Check chain history before another attempt.

Production remains unpublished. Mainnet launch protection stays in place.
