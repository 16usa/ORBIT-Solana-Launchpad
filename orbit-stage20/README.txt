ORBIT Stage 20 — Circular wallet avatar header

Behavior:
- Connected wallet's large green button is replaced with a compact circular avatar.
- Tap the avatar to show: Copy address, Change wallet, Set avatar, Disconnect.
- Select JPG, PNG, WEBP, or GIF: picture is cropped to a 160px JPEG and saved
  locally in this browser, under the connected wallet's PUBLIC address.
- 'Remove avatar' is available after setting a local picture.
- Phantom's private per-account avatar is NOT exposed by Solana wallet adapters.
  Automatic syncing of the exact Phantom account avatar is not available.
- When no local avatar is set, the wallet icon appears in a round button.
- Connecting a wallet and the previous Phantom in-app browser link remain intact.
- No server/database changes, no private keys, no trades, no auto-restarts.

Installation — put orbit_stage20_wallet_avatar.zip into /home/runner/workspace

  cd /home/runner/workspace
  unzip -o orbit_stage20_wallet_avatar.zip -d . && \
  python3 orbit-stage20/apply.py && \
  python3 orbit-stage20/verify.py && \
  pnpm --filter @workspace/orbit-launchpad run test && \
  pnpm --filter @workspace/orbit-launchpad run check:syntax && \
  pnpm --filter @workspace/orbit-launchpad run typecheck && \
  pnpm --filter @workspace/orbit-launchpad run build

Only Development updates are intended. No Republish.
