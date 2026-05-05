#!/usr/bin/env sh
set -eu

python -m compileall backend
node --check electron/main.js
node --check electron/preload.js
node --check renderer/scripts/app.js
