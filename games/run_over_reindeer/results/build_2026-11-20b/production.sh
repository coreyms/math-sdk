#!/bin/zsh
# Run Over Reindeer production build 2026-11-20b (math 2026.11.20: minimums redrawn, option B shaping, and no fifth
# scatter: a Super trigger is exactly 4). Books, then the shaper (option B), configs and Stake's checks, analyze_luts.
# The 2026-11-18 script with the label, nice -n 19 and the books step only: the shaping step waits
# for Corey's choice (REDRAW_2026-11-20.md), because the 2026-11-18 shaper targets cannot all be
# met on the redrawn books. Resumable: a mode whose books and raw lookup table exist is skipped.
# 3 worker processes. Logs: production_<step>.log beside this script.
set -e
HERE=${0:A:h}
SDK=${HERE:h:h:h:h}
OUT=$HERE/production/games
LIB=$OUT/run_over_reindeer/library
py() { nice -n 19 env/bin/python "$@" }
export PYTHONDONTWRITEBYTECODE=1
cd $SDK
mkdir -p $OUT
for m in base bonus super; do
  if [[ -f $LIB/publish_files/books_$m.jsonl.zst && -f $LIB/lookup_tables/lookUpTable_$m.csv ]]; then
    echo "$(date '+%H:%M:%S') $m: books exist, skipped" | tee -a $HERE/production_progress.log
    continue
  fi
  echo "$(date '+%H:%M:%S') $m: books start" | tee -a $HERE/production_progress.log
  py games/run_over_reindeer/run.py --out $OUT --modes $m --threads 3 --batch 10000 \
      --sims-base 600000 --sims-bonus 240000 --sims-super 210000 --no-checks > $HERE/production_books_$m.log 2>&1
  echo "$(date '+%H:%M:%S') $m: books done" | tee -a $HERE/production_progress.log
done
echo "$(date '+%H:%M:%S') books all done" | tee -a $HERE/production_progress.log
mkdir -p $HERE/raw_sdk_luts && cp -n $LIB/publish_files/lookUpTable_*_0.csv $HERE/raw_sdk_luts/
echo "$(date '+%H:%M:%S') shaper start" | tee -a $HERE/production_progress.log
py games/run_over_reindeer/tools/shape_lut.py $LIB --report $HERE/production_shape.json > $HERE/production_shape.log 2>&1
echo "$(date '+%H:%M:%S') configs and Stake checks start" | tee -a $HERE/production_progress.log
py games/run_over_reindeer/run.py --out $OUT --no-sims > $HERE/production_checks.log 2>&1 || echo "CHECKS FAILED" | tee -a $HERE/production_progress.log
echo "$(date '+%H:%M:%S') analysis start" | tee -a $HERE/production_progress.log
py $HERE/analyze_luts.py $LIB $HERE/production_luts.json > $HERE/production_luts.log 2>&1
(cd $LIB/publish_files && shasum -a 256 *) > $HERE/SHA256SUMS
echo "$(date '+%H:%M:%S') all done" | tee -a $HERE/production_progress.log
