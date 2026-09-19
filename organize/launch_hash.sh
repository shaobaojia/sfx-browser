#!/bin/bash
cd /volume1/主目录/Hermes/read/Projects/sfx-browser/organize
mkdir -p hash3_20260919
setsid nohup python3 hash_all.py > hash3_20260919/run.log 2>&1 < /dev/null &
echo "launched pid $!"
