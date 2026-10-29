ORBIT Stage 15: explain LEGACY signature message mutation, WITHOUT broadcasting.

The Stage14 test returned Wallet altered the transaction message. Stage15
reports whether the wallet/adapter changed the recent blockhash, fee payer,
program instructions, and whether its signature verifies against the returned
message. It does NOT treat any changed message as safe. No on-chain action.

Install: from /home/runner/workspace, unzip -o orbit_stage15.zip -d .
python3 orbit-stage15/apply_stage15.py
python3 orbit-stage15/verify_stage15.py
Then run normal test/typecheck/build checks in Replit.

Use separate test-only wallet. Never override Phantom warnings.
No Replit restart, GitHub push, or Republish.
