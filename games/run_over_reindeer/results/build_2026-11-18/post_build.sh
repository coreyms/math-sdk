#!/bin/zsh
# After production.sh: full-book scan, the line-rule verifier, RTP before shaping, fixtures, tests.
# nice -n 10, at most 3 processes, one step at a time.
HERE=${0:A:h}
SDK=${HERE:h:h:h:h}
LIB=$HERE/production/games/run_over_reindeer/library
OLD=$HERE/../build_2026-11-15/production/games/run_over_reindeer/library/publish_files
py() { nice -n 10 $SDK/env/bin/python "$@" }
export PYTHONDONTWRITEBYTECODE=1
cd $HERE
date '+%H:%M:%S scan start'
py scan_production_books.py $LIB production_books_scan.json > production_books_scan.log 2>&1
date '+%H:%M:%S verify start'
py verify_line_readings.py $LIB/publish_files $OLD $HERE > verify_line_readings.log 2>&1
date '+%H:%M:%S rtp start'
py rtp_before_shaping.py $LIB/publish_files $OLD rtp_before_shaping.json > rtp_before_shaping.log 2>&1
cd $SDK
date '+%H:%M:%S fixtures start'
py games/run_over_reindeer/fixtures_make_2026_11_18.py --scratch $HERE/fixtures_scratch > $HERE/fixtures_make.log 2>&1
date '+%H:%M:%S pytest start'
py -m pytest games/run_over_reindeer/tests -q -p no:cacheprovider > $HERE/pytest_final.log 2>&1
date '+%H:%M:%S all done'
