#!/bin/zsh
cd "$(dirname "$0")"
/usr/bin/python3 tooling/preview-server.py --port 4173 --open
