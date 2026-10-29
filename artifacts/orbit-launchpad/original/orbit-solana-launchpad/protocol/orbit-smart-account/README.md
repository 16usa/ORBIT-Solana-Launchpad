# ORBIT Smart Account — Stage 28 (Devnet prototype)

This is an **isolated, unverified prototype**, not a production-ready trading vault. It is NOT integrated with the ORBIT frontend and is NOT deployed. The existing Raydium LaunchLab flow remains unchanged.

## Implemented
- One PDA vault per wallet (`[b"vault", owner]`), initialized only by the wallet owner.
- Owner-signed deposit and owner-signed withdrawal of SOL, preserving rent-exempt balance.
- Owner-signed session authorization with expiry <= 24h, max-trade amount and total budget.
- Owner-signed immediate revocation of session metadata.
- No admin withdrawal instruction.

## NOT implemented (important)
- **Session keys CANNOT trade or withdraw.** No trade instruction exists yet.
- No bonding curve, swap, token vault, fee logic, price validation, MEV protection, migration, automated trading, or linked-wallet detection.
- No Privy wallet delegation, frontend, backend executor, tests on local validator, or security audit.
- No on-chain enforced spend accounting yet: `remaining_budget_lamports` is configuration data only until a trading instruction implements decrementing it.

## Why this order?
The owner must retain the ability to withdraw. A session key must never be permitted to withdraw or transfer to arbitrary accounts. Before adding trades, define allowlisted protocols, asset ownership, min-out/slippage, instruction account validation, per-trade budget accounting, expiration and revocation checks, and security tests.

## Local prerequisites and validation
Install Rust and Anchor CLI 0.31.x in a supported development environment. Set a unique program ID in `declare_id!` before any deployment, then run:

```sh
cd artifacts/orbit-launchpad/original/orbit-solana-launchpad/protocol/orbit-smart-account
cargo check
anchor build
```

No deployment or transfer of funds is performed by this patch. Do not fund this prototype on Mainnet. Review all code before using even on Devnet.
