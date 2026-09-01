from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "dist" / "client"
NESTED_ASSETS = CLIENT / "pku-lectures" / "_next"
ROOT_ASSETS = CLIENT / "_next"

if not (CLIENT / "index.html").exists():
    raise SystemExit("dist/client/index.html is missing; run the GitHub Pages build first")
if not NESTED_ASSETS.exists():
    raise SystemExit("prefixed static assets are missing")
if ROOT_ASSETS.exists():
    shutil.rmtree(ROOT_ASSETS)
shutil.move(str(NESTED_ASSETS), str(ROOT_ASSETS))
shutil.rmtree(CLIENT / "pku-lectures")
(CLIENT / ".nojekyll").touch()
print("Prepared dist/client for the /pku-lectures GitHub Pages mount point.")
