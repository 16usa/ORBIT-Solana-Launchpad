#!/usr/bin/env python3
"""Stage 20: install wallet avatar header and same wallet menu. No restarts or trades."""
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(os.environ.get('ORBIT_WORKSPACE', '/home/runner/workspace'))
SRC = ROOT / 'artifacts/orbit-launchpad/original/orbit-solana-launchpad/web/src'
BUTTON = SRC / 'OrbitWalletButton.tsx'
CSS = SRC / 'styles.css'
BUNDLE = Path(__file__).resolve().parent
MARKER = 'ORBIT_STAGE20_WALLET_AVATAR'


def atomic_write(path: Path, data: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix='.orbit-stage20-', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            stream.write(data)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def main():
    if not BUTTON.is_file() or not CSS.is_file():
        raise SystemExit('STAGE 20 STOPPED: ORBIT wallet component or styles.css not found. No changes.')
    original = BUTTON.read_text(encoding='utf-8')
    styles = CSS.read_text(encoding='utf-8')
    new_button = (BUNDLE / 'OrbitWalletButton.tsx').read_text(encoding='utf-8')
    new_css = (BUNDLE / 'avatar_styles.css').read_text(encoding='utf-8')
    if MARKER not in new_button or MARKER not in new_css:
        raise SystemExit('STAGE 20 STOPPED: invalid installer content.')
    if MARKER in original and MARKER in styles:
        print('STAGE 20 ALREADY INSTALLED. No changes.'); return
    if MARKER not in original:
        required = ('export default function OrbitWalletButton', 'WalletMultiButton', 'Open in Phantom')
        if not all(text in original for text in required):
            raise SystemExit('STAGE 20 STOPPED: unexpected wallet component version; no changes.')
    # Back up both files *before* modifying either one.
    backup = ROOT / '.orbit-backups' / ('stage20-wallet-avatar-' + datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f'))
    backup.mkdir(parents=True, exist_ok=False)
    shutil.copy2(BUTTON, backup / BUTTON.name)
    shutil.copy2(CSS, backup / CSS.name)
    if MARKER not in original:
        atomic_write(BUTTON, new_button)
    if MARKER not in styles:
        atomic_write(CSS, styles.rstrip() + '\n\n' + new_css.strip() + '\n')
    print('STAGE 20 INSTALLED')
    print('Backups:', backup)
    print('No restart, republish, GitHub push or blockchain transaction performed.')


if __name__ == '__main__':
    main()
