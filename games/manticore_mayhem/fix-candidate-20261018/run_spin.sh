#!/bin/bash
# Math fix 2026-10-18: base / ante / super_ante at exactly 300,000 books each (5 processes x 3 batches x 20,000), nice 10.
cd /Users/corey/Projects/stake-engine/math-sdk
G=games/manticore_mayhem; F=$G/fix-candidate-20261018; LOG=$F/evidence/logs
for m in base ante super_ante; do
  echo "START $m $(date)" >> $LOG/timeline.log
  nice -n 10 env/bin/python $G/run.py --sims 300000 --modes $m --threads 5 --batch 20000 \
      --no-analysis --no-checks --out $F/games > $LOG/sim_$m.log 2>&1
  echo "END $m exit $? $(date)" >> $LOG/timeline.log
done
echo "SPIN-DONE $(date)" >> $LOG/timeline.log
