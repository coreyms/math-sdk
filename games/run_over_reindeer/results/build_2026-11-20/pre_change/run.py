"""Run Over Reindeer: books, configs and RGS format checks (math build 2026-11-18, F + C).

Usage (from math-sdk/):
  nice -n 19 env/bin/python games/run_over_reindeer/run.py --out DIR [--sims-base N] [--sims-bonus N]
        [--sims-super N] [--threads 3] [--batch B] [--no-sims] [--no-checks] [--check-lines] [--uncompressed]

Everything goes to DIR/run_over_reindeer/library (never inside the game folder). For the RGS
checks DIR must be named `games` (they write stats_summary.json to games/<id>/library relative
to the current folder; run.py steps into DIR's parent for them, as Manticore's run.py does).

The four base-type modes (base, ante_2, ante_4, ante_10) play the same rounds, so only `base` is
simulated and its books and lookup table are copied to the three antes; their weights come
from tools/shape_lut.py (game_optimization.py TARGETS), which writes the published lookup
tables. The SDK's Rust optimizer is not part of the flow (house convention since Angry
Mantis). Order: run.py (books) -> tools/shape_lut.py -> run.py --no-sims (configs + checks).

--check-lines re-pays engine boards with the SDK's own Lines.get_lines first. Since math 2026.11.18
every line must agree except one documented pattern (line_differences): a Wild-led line that the
game pays on the higher final win of its two readings, where the SDK compares them before
multipliers. A built-in self-check injects other differences and requires each to be caught.
The 2026-11-15 run.py is kept in results/build_2026-11-18/pre_change/.
The pre-2026-11-15 run.py (variant E smoke runs) is kept in results/build_2026-11-15/pre_change/.
"""

import argparse
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from game_config import ANTE_COSTS, MATH_VERSION, CONTRACT, GameConfig  # noqa: E402
from gamestate_f import GameStateF  # noqa: E402
from src.state.run_sims import create_books  # noqa: E402

ALL_MODES = ["base", "ante_2", "ante_4", "ante_10", "bonus", "super"]
SIM_MODES = ["base", "bonus", "super"]


def redirect_output(config, out_dir):
    """Point every output path at <out_dir>/<game_id>/library. Call BEFORE GameState(config)."""
    import src.config.output_filenames as output_filenames

    out_dir = os.path.abspath(out_dir)
    output_filenames.PATH_TO_GAMES = out_dir
    config.library_path = os.path.join(out_dir, config.game_id, "library")
    config.publish_path = os.path.join(config.library_path, "publish_files")
    return config.library_path


def line_differences(board, mult, engine_wins, sdk_wins):
    """Compare one board's line wins, ror_engine against the SDK's Lines.get_lines.

    Returns (excepted, unexplained): lists of (line index 0-11, engine win, SDK win).

    THE ONE DOCUMENTED EXCEPTION (math 2026.11.18, Corey 2026-11-18, M2 option b): the SDK
    compares a Wild-led line's two readings on paytable value BEFORE multipliers; the game pays
    the higher FINAL win. A line differs by design exactly when all of these hold, and only then
    is it excepted:
      * it starts with 3 or more Wilds (wm), followed by a paying symbol line of n > wm cells;
      * the Wilds-only pay (Grandma's car for wm) is above the symbol line's paytable value, so
        the SDK pays the Wilds-only reading: wm cells, its multipliers only;
      * the engine pays the symbol reading: n cells, symbol, its multipliers (base pay x the
        symbol cells' multiplier), and that win is above the SDK's, or EQUAL to it: an exact tie
        of final wins goes to the symbol line, so the amount is the same and only the reading
        recorded (kind, cells, multiplier) differs.
    Any other difference (another line, another amount, a line only one side pays, a lower
    engine win, a tie paid as the symbol line by one and not the other) is unexplained."""
    import ror_engine as E

    eng = {w[0]: w for w in engine_wins}
    sdk = {w["meta"]["lineIndex"] - 1: w for w in sdk_wins}
    excepted, unexplained = [], []
    for li in sorted(set(eng) | set(sdk)):
        e, s = eng.get(li), sdk.get(li)
        ew = e[3] if e else 0.0
        sw = s["win"] if s else 0.0
        if e and s and abs(ew - sw) < 1e-6 and e[2] == s["kind"]:
            continue
        cells = E.LINES[li]
        wm = 0
        while wm < 5 and E.IS_WILD[board[cells[wm]]]:
            wm += 1
        ok = False
        if e and s and 3 <= wm < 5:
            sym = board[cells[wm]]
            n = wm + 1
            while n < 5 and (board[cells[n]] == sym or E.IS_WILD[board[cells[n]]]):
                n += 1
            base, wild = E.PAY[sym][n], E.WILD_PAY[wm]
            m_sym = E._line_mult(mult, cells, n)
            ok = (wild > base > 0.0 and s["kind"] == wm and e[2] == n and e[1] == sym and e[4] == m_sym
                  and e[5] == list(cells[:n]) and abs(ew - round(base * m_sym, 2)) < 1e-6 and ew > sw - 1e-9
                  and abs(sw - round(wild * E._line_mult(mult, cells, wm), 2)) < 1e-6)
        (excepted if ok else unexplained).append((li, ew, sw))
    return excepted, unexplained


def _self_check_line_differences(samples):
    """--check-lines must still catch every other difference: perturb real engine wins in ways
    the exception does not cover and require each to be reported as unexplained."""
    faults = 0
    for board, mult, ewins, swins in samples:
        if not ewins:
            continue
        w = list(ewins[0])
        free = next(li for li in range(12) if li not in {x[0] for x in ewins})
        for bad in (
            [tuple(w[:3]) + (round(w[3] + 0.1, 2),) + tuple(w[4:])] + list(ewins[1:]),   # another amount
            list(ewins[1:]),                                                             # a line dropped
            list(ewins) + [(free, w[1], w[2], w[3], w[4], w[5])],                        # an extra line
        ):
            _, unexplained = line_differences(board, mult, bad, swins)
            assert unexplained, ("check-lines missed an injected difference", board, mult, bad)
            faults += 1
    return faults


def check_lines(config, gs, n=3000):
    """Pay random final boards (from the engine) with ror_engine and with SDK Lines. Every line
    must agree, except the documented 2026.11.18 pattern (line_differences)."""
    import random
    import ror_engine as E
    import ror_rules as R
    from src.calculations.lines import Lines

    rng = random.Random(99)
    eng = E.Engine()
    checked = excepted_lines = tie_lines = 0
    samples = []
    for mode in ("base", "bonus", "super"):
        for _ in range(n):
            rec = []
            eng.round(rng, mode, rec=rec)
            for s in rec:
                if "board" not in s:
                    continue
                board = []
                for reel in range(R.NUM_REELS):
                    col = []
                    for row in range(R.NUM_ROWS):
                        c = reel * R.NUM_ROWS + row
                        sym = gs.create_symbol(R.SYMBOLS[s["board"][c]])
                        if s["mult"][c]:
                            sym.assign_attribute({"multiplier": s["mult"][c]})
                        col.append(sym)
                    board.append(col)
                got = Lines.get_lines(board, config)
                ewins = s["wins"] or []
                excepted, unexplained = line_differences(s["board"], s["mult"], ewins, got["wins"])
                assert not unexplained, (mode, unexplained, s["board"], s["mult"])
                gap = sum(ew - sw for _, ew, sw in excepted)
                assert abs(got["totalWin"] + gap - s["win"]) < 1e-6, (mode, got["totalWin"], gap, s["win"])
                excepted_lines += len(excepted)
                tie_lines += sum(1 for _, ew, sw in excepted if abs(ew - sw) < 1e-6)
                if ewins and len(samples) < 200:
                    samples.append((s["board"], s["mult"], ewins, got["wins"]))
                checked += 1
    faults = _self_check_line_differences(samples)
    print(f"check-lines: {checked:,} boards; every line paid identically by ror_engine and SDK "
          f"Lines.get_lines except {excepted_lines:,} lines of the documented 2026.11.18 pattern "
          f"(Wild-led line paid on its higher final win; {tie_lines:,} of them exact ties, same amount, "
          f"recorded as the symbol line); self-check: {faults} injected differences "
          f"all caught")


def copy_base_to_antes(gs):
    """The antes play the base game's rounds: same books, same raw lookup table."""
    of = gs.output_files
    for ante in ANTE_COSTS:
        for src, dst in (
            (of.books["base"]["paths"]["books_compressed"], of.books[ante]["paths"]["books_compressed"]),
            (of.books["base"]["paths"]["books_uncompressed"], of.books[ante]["paths"]["books_uncompressed"]),
            (of.lookups["base"]["paths"]["base_lookup"], of.lookups[ante]["paths"]["base_lookup"]),
            (of.lookups["base"]["paths"]["segmented_id"], of.lookups[ante]["paths"]["segmented_id"]),
            (of.force["base"]["paths"]["force_record"], of.force[ante]["paths"]["force_record"]),
            (os.path.join(of.config_path, "books_base.verification.json"),
             os.path.join(of.config_path, f"books_{ante}.verification.json")),
            (os.path.join(of.config_path, "event_config_base.json"),
             os.path.join(of.config_path, f"event_config_{ante}.json")),
        ):
            if os.path.exists(src):
                shutil.copyfile(src, dst)
        print(f"copied the base books and lookup table to {ante}", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--sims-base", type=int, default=600_000)
    ap.add_argument("--sims-bonus", type=int, default=240_000)
    ap.add_argument("--sims-super", type=int, default=210_000)
    ap.add_argument("--modes", default="base,bonus,super",
                    help="which simulated modes to (re)make, so a long build can resume mode by mode")
    ap.add_argument("--threads", type=int, default=3)
    ap.add_argument("--batch", type=int, default=None)
    ap.add_argument("--no-sims", action="store_true")
    ap.add_argument("--no-checks", action="store_true")
    ap.add_argument("--check-lines", action="store_true")
    ap.add_argument("--uncompressed", action="store_true")
    a = ap.parse_args()
    assert a.threads <= 3, "at most 3 worker processes on this Mac"

    config = GameConfig()
    print(f"Run Over Reindeer math {MATH_VERSION}, contract {CONTRACT}", flush=True)
    lib = redirect_output(config, a.out)
    gs = GameStateF(config)
    from game_optimization import OptimizationSetup
    OptimizationSetup(config)
    if a.check_lines:
        check_lines(config, gs)

    if not a.no_sims:
        allsims = {"base": a.sims_base, "bonus": a.sims_bonus, "super": a.sims_super}
        sims = {m: allsims[m] for m in a.modes.split(",") if m}
        batch = a.batch or max(1, min(sims.values()) // a.threads)
        create_books(gs, config, sims, batch, a.threads, not a.uncompressed, False)
        if "base" in sims:
            copy_base_to_antes(gs)
        print("books written to", lib, flush=True)

    if a.no_sims:
        copy_base_to_antes(gs)   # idempotent: brings the antes' side files up to date
    published = [m for m in ALL_MODES if os.path.exists(gs.output_files.lookups[m]["paths"]["optimized_lookup"])]
    if len(published) == len(ALL_MODES):
        from src.write_data.write_configs import generate_configs
        generate_configs(gs)
        if not a.no_checks:
            out_dir = os.path.abspath(a.out)
            assert os.path.basename(out_dir) == "games", "the RGS checks need the --out folder to be named `games`"
            os.chdir(os.path.dirname(out_dir))
            from utils.rgs_verification import execute_all_tests
            execute_all_tests(config)
    else:
        print(f"shaped lookup tables missing for {sorted(set(ALL_MODES) - set(published))}: "
              "run tools/shape_lut.py, then run.py --no-sims for the configs and the RGS checks", flush=True)
