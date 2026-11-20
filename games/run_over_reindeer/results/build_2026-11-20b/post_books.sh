#!/bin/zsh
# After production.sh (2026-11-20b): full-book scan, book-by-book comparison with 2026-11-20, per-round extraction (new
# and the 2026-11-20 tables' books), the option B distribution check, the game's tests. nice -n 19, one step at a time.
HERE=${0:A:h}
SDK=${HERE:h:h:h:h}
LIB=$HERE/production/games/run_over_reindeer/library
OLD=$HERE/../build_2026-11-20/production/games/run_over_reindeer/library/publish_files
py() { nice -n 19 $SDK/env/bin/python "$@" }
export PYTHONDONTWRITEBYTECODE=1
cd $HERE
date '+%H:%M:%S scan start'
py scan_production_books.py $LIB production_books_scan.json > production_books_scan.log 2>&1
date '+%H:%M:%S compare start'
py compare_books.py $LIB/publish_files $OLD compare_books.json > compare_books.log 2>&1
date '+%H:%M:%S extract start'
py extract_rounds.py $LIB/publish_files analysis/new_2026-11-20b > extract_rounds.log 2>&1
[[ -d analysis/old_2026-11-20 ]] || cp -R ../build_2026-11-20/analysis/new_2026-11-20 analysis/old_2026-11-20
date '+%H:%M:%S distribution start'
py check_b_distribution.py check_b_distribution.json > check_b_distribution.md 2> check_b_distribution.log
cd $SDK
date '+%H:%M:%S pytest start'
py -m pytest games/run_over_reindeer/tests -q -p no:cacheprovider -rs > $HERE/pytest_final.log 2>&1
date '+%H:%M:%S all done'
