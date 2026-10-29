#!/usr/bin/env python3
"""ORBIT Stage 21: turn bottom-right three dots into a compact accessible popover.

UI-only: never touches chain, wallets, API, transactions, process state or Git.
"""
from __future__ import annotations

import os
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(os.environ.get('ORBIT_WORKSPACE', '/home/runner/workspace'))
SRC = ROOT / 'artifacts/orbit-launchpad/original/orbit-solana-launchpad/web/src'
APP, STYLE = SRC / 'App.tsx', SRC / 'styles.css'
BASE = Path(__file__).resolve().parent
MARKER = 'ORBIT_STAGE21_MENU_POPUP'


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError('STAGE 21 STOPPED: ' + message + '. No changes.')


def atomic_write(path: Path, contents: str) -> None:
    fd, temporary = tempfile.mkstemp(dir=str(path.parent), prefix='.orbit-stage21-', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            stream.write(contents)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main() -> None:
    require(APP.is_file() and STYLE.is_file(), 'App.tsx or styles.css missing')
    app, css = APP.read_text(encoding='utf-8'), STYLE.read_text(encoding='utf-8')
    if MARKER in app and MARKER in css:
        print('STAGE 21 ALREADY INSTALLED — nothing changed.')
        return
    require(MARKER not in app and MARKER not in css, 'partial installation; restore from backup first')
    pattern = re.compile(r'(?ms)^function Nav\(\{page\}.*?(?=^function Header\()')
    nav_blocks = list(pattern.finditer(app))
    require(len(nav_blocks) == 1, 'expected bottom navigation component not found uniquely')
    old_nav = nav_blocks[0].group(0)
    require('allNav.map' in old_nav and 'navigate(n.page)' in old_nav and "className=\"bottom-nav\"" in old_nav,
            'unexpected navigation component; refusing to replace')
    require(re.findall(r'^function\s+\w+', old_nav, re.M) == ['function Nav'], 'unexpected helper inside Nav block')
    require('function getInitialRoute()' in app and "const h=location.hash.replace(/^#\\/?/,'');" in app,
            'unexpected route parser')
    require(app.count('function MenuPage()') == 1 and app.count("{route.page==='menu'&&<MenuPage/>}") == 1,
            'expected old Menu page not found uniquely')
    require(len(re.findall(r'(?m)^function MenuPage\(\).*$', app)) == 1,
            'MenuPage unexpectedly reformatted; declining automatic patch')

    replacement_nav = (BASE / 'nav_component.tsx.txt').read_text(encoding='utf-8')
    new_styles = (BASE / 'menu_styles.css').read_text(encoding='utf-8')
    require(replacement_nav.count(MARKER) == 1 and new_styles.count(MARKER) == 1, 'incomplete patch')
    require('role="menu"' in replacement_nav and 'setOpen(false)' in replacement_nav, 'unsafe menu template')

    # Match and validate before writing either file (fail-closed).
    updated_app = app[:nav_blocks[0].start()] + replacement_nav + '\n' + app[nav_blocks[0].end():]
    updated_app = updated_app.replace(
        "const h=location.hash.replace(/^#\\/?/,'');",
        "const h=location.hash.replace(/^#\\/?/,'');if(h==='menu')return {page:'discover',mint:''};",
        1,
    )
    updated_app = re.sub(r'(?m)^function MenuPage\(\).*\n', '', updated_app, count=1)
    updated_app = updated_app.replace("{route.page==='menu'&&<MenuPage/>}", '', 1)
    updated_css = css.rstrip() + '\n\n' + new_styles.strip() + '\n'
    require(updated_app.count(MARKER) == 1 and updated_css.count(MARKER) == 1, 'transformation validation failed')
    require("{route.page==='menu'&&<MenuPage/>}" not in updated_app, 'legacy menu page still rendered')

    backup_dir = ROOT / '.orbit-backups' / ('stage21-popup-menu-' + datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f'))
    backup_dir.mkdir(parents=True, exist_ok=False)
    shutil.copy2(APP, backup_dir / 'App.tsx')
    shutil.copy2(STYLE, backup_dir / 'styles.css')
    try:
        atomic_write(APP, updated_app)
        atomic_write(STYLE, updated_css)
    except Exception:
        atomic_write(APP, app)
        atomic_write(STYLE, css)
        raise
    print('STAGE 21 INSTALLED: bottom-right menu now opens a floating popover.')
    print('Backup:', backup_dir)
    print('UI only. No server restart, publishing, GitHub push, or Solana transaction.')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError) as exc:
        raise SystemExit(str(exc)) from exc
