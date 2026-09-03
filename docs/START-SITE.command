#!/bin/sh
cd "$(dirname "$0")"
open "http://127.0.0.1:8000/" 2>/dev/null || true
python3 -m http.server 8000
