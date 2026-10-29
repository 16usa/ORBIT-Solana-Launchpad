ORBIT Stage 18 -- TypeScript typefix only

Fixes TS2740 in web/src/chain.ts around line 754:
  Uint8Array<ArrayBuffer> cannot be used as the Buffer expected by
  new TransactionInstruction({data}).

Fix:
  import { Buffer } from 'buffer';
  const data = Buffer.from(...existing byte values...);

This preserves the exact instruction bytes and does not relax any validation,
change any transaction logic, or send a transaction. It requires Stage 18.

Install from Replit Shell after uploading the ZIP to /home/runner/workspace:
  cd /home/runner/workspace
  unzip -o orbit_stage18_typefix.zip -d . && python3 orbit-stage18-typefix/apply.py && python3 orbit-stage18-typefix/verify.py && pnpm --filter @workspace/orbit-launchpad run test && pnpm --filter @workspace/orbit-launchpad run check:syntax && pnpm --filter @workspace/orbit-launchpad run typecheck && pnpm --filter @workspace/orbit-launchpad run build

No automatic restart, GitHub push, or Republish.

Do not attempt a real launch until the entire build passes. On any Phantom
security warning, cancel rather than override the warning. Use Devnet and a
dedicated test-only account.
