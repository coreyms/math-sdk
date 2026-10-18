#!/bin/bash
# phantom walk (tools/phantom_walk.py = the harsh review's walk.py) over the candidate, nice 10
cd /Users/corey/Projects/stake-engine/math-sdk/games/manticore_mayhem/fix-candidate-20261018/evidence/walk
export MANTICORE_LIB=/Users/corey/Projects/stake-engine/math-sdk/games/manticore_mayhem/fix-candidate-20261018/games/manticore_mayhem/library WALK_OUT=/Users/corey/Projects/stake-engine/math-sdk/games/manticore_mayhem/fix-candidate-20261018/evidence/walk
PY=/Users/corey/Projects/stake-engine/math-sdk/env/bin/python
for m in "$@"; do nice -n 10 $PY /Users/corey/Projects/stake-engine/math-sdk/games/manticore_mayhem/tools/phantom_walk.py $m > log_$m.txt 2>&1; echo "walk $m exit $?" >> walk_done.txt; done
