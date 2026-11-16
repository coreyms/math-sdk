"""Variant F (study only, 2026-11-10): variant E with the bonus-round crossing REMOVED.

Corey 2026-11-10: "I don't think the column wilds should ever multiply from their original
set value." A held column keeps the multiplier it landed with for the whole round.
Nothing settled is changed: this module applies variant_e.apply() and then patches the copy
in memory. NO_CROSSING_STUDY.md reports what it does.

apply(cap=50, column_tables=None, extra=None)
  cap            the bonus-round column cap (50 = as settled; 100 = removed, the global 100x)
  column_tables  None = the settled bonus tables; "base" = the base game's column tables
                 in both bonus rounds; or a dict {"freespins": {...}, "super": {...}}
  extra          optional dict {"freespins": {key: value}, "super": {...}} of FEATURE
                 overrides (the restoring adjustments tested in the study)
"""

import ror_engine as E
import ror_rules as R
import variant_e


def apply(cap=50, column_tables=None, extra=None):
    variant_e.apply()
    for mode in ("freespins", "super"):
        f = R.FEATURE[mode]
        f["column_crossing"] = False
        f["column_cap"] = cap
        if column_tables == "base":
            f["column_mult"] = {t: dict(v) for t, v in variant_e.BASE["column_mult"].items()}
        elif isinstance(column_tables, dict) and mode in column_tables:
            f["column_mult"] = column_tables[mode]
        if extra and mode in extra:
            f.update(extra[mode])
    R.VARIANT = "F"
    E.build()
