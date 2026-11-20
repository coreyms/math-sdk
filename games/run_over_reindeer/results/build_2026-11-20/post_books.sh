#!/bin/zsh
# After production.sh (books only): full-book scan, book-by-book comparison with 2026.11.18,
# per-round extraction, the shaping options, and the game's tests (book tests skip the lookup
# check until a shaping option is chosen). nice -n 19, at most 3 processes, one step at a time.
HERE=${0:A:h}
SDK=${HERE:h:h:h:h}
LIB=$HERE/production/games/run_over_reindeer/library
OLD=$HERE/../build_2026-11-18/production/games/run_over_reindeer/library/publish_files
py() { nice -n 19 $SDK/env/bin/python "$@" }
export PYTHONDONTWRITEBYTECODE=1
cd $HERE
date '+%H:%M:%S scan start'
py scan_production_books.py $LIB production_books_scan.json > production_books_scan.log 2>&1
date '+%H:%M:%S compare start'
py compare_books.py $LIB/publish_files $OLD compare_books.json > compare_books.log 2>&1
date '+%H:%M:%S extract start'
py extract_rounds.py $LIB/publish_files analysis/new_2026-11-20 > extract_rounds.log 2>&1
date '+%H:%M:%S options start'
py options.py analysis/new_2026-11-20 options.json --old analysis/old_2026-11-18 > options.log 2>&1
cd $SDK
date '+%H:%M:%S pytest start'
py -m pytest games/run_over_reindeer/tests -q -p no:cacheprovider > $HERE/pytest_books.log 2>&1
date '+%H:%M:%S all done'
