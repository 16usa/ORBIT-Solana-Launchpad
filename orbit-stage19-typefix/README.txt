ORBIT Stage 19 typefix: TS2367 at web/src/chain.ts, line ~843.
The Stage 19 Devnet-only guard narrows config.network to 'devnet'. Checking
config.network==='mainnet-beta' again inside this function cannot be true.
The patch removes ONLY the unreachable check within curveTrade. The earlier
Devnet-only guard is required and retained. Existing buy/sell transaction
construction is unchanged. A timestamped backup is created.

Install in existing Replit Shell after Stage 19:
cd /home/runner/workspace
unzip -o orbit_stage19_typefix.zip -d . && python3 orbit-stage19-typefix/apply.py && python3 orbit-stage19-typefix/verify.py && pnpm --filter @workspace/orbit-launchpad run test && pnpm --filter @workspace/orbit-launchpad run check:syntax && pnpm --filter @workspace/orbit-launchpad run typecheck && pnpm --filter @workspace/orbit-launchpad run build

No auto restart, no Git push, no Republish.
After compilation, Devnet buy/sell must still be verified safely with a
separate test wallet; signature approval/settlement not yet proven.
