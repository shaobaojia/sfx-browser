#!/bin/bash
cd /volume1/主目录/Hermes/read/Projects/sfx-browser/organize
setsid nohup python3 rar_audit.py > rar_audit_run.log 2>&1 < /dev/null &
