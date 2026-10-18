#!/bin/bash
# Math fix 2026-10-18: Mystery re-dealt, 393,000 books (5 processes x 3 batches x 26,200), nice 10.
cd /Users/corey/Projects/stake-engine/math-sdk
G=games/manticore_mayhem; F=$G/fix-candidate-20261018; LOG=$F/evidence/logs
echo "START mystery $(date)" >> $LOG/timeline.log
/usr/bin/time -p nice -n 10 env/bin/python $G/run.py --sims 393000 --modes mystery --threads 5 --batch 26200 \
    --no-analysis --no-checks --out $F/games > $LOG/sim_mystery.log 2> $LOG/sim_mystery.time
echo "END mystery exit $? $(date)" >> $LOG/timeline.log
