ORBIT Stage 19 — Devnet Raydium curve trade LEGACY mode

Why: The creation route was repaired in Stage 18 by using LEGACY, but the existing buy/sell curveTrade code still builds V0 transactions. The Phantom screenshot shows Unexpected error during V0 trade wallet approval.

This patch is intentionally narrow: changes only the curveTrade function in web/src/chain.ts to require Devnet and use LEGACY for both buy and sell. It does not change Raydium SDK execute/sendAndConfirm behavior. It is NOT a guarantee the wallet will sign or the trade will confirm; the SDK might still have another incompatibility.

Install into existing Replit Workspace via Shell:
 cd /home/runner/workspace
 unzip -o orbit_stage19_trade_legacy.zip -d .
 python3 orbit-stage19/apply.py && python3 orbit-stage19/verify.py && pnpm --filter @workspace/orbit-launchpad run test && pnpm --filter @workspace/orbit-launchpad run check:syntax && pnpm --filter @workspace/orbit-launchpad run typecheck && pnpm --filter @workspace/orbit-launchpad run build

Reopen the Development site in Phantom browser. Do not Republish. Do not bypass Phantom warnings. Use only separate Devnet wallet. Start with a small test buy, e.g. 0.01 Devnet SOL. Check transaction confirmation and token balance before retrying; don't retry blindly on an uncertain confirmation.

No automatic restart/kill, Git push, Republish, or blockchain submission by installer.
