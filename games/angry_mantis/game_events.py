"""Angry Mantis specific book events. All amounts are integer cents of the bet; rows are padded (+1)."""

from src.events.events import *


def _row(gamestate, row: int) -> int:
    return row + 1 if gamestate.config.include_padding else row


def ante_lock_event(gamestate, reel: int, row: int) -> None:
    gamestate.book.add_event(
        {
            "index": len(gamestate.book.events),
            "type": "anteLock",
            "scatterPosition": {"reel": reel, "row": _row(gamestate, row)},
        }
    )


def bonus_start_event(gamestate) -> None:
    positions = [
        {"reel": p["reel"], "row": _row(gamestate, p["row"])} for p in gamestate.bonus_trigger_positions
    ]
    gamestate.book.add_event(
        {
            "index": len(gamestate.book.events),
            "type": "bonusStart",
            "mode": gamestate.bonus_mode,
            "host": gamestate.bonus_host,
            "totalFs": int(gamestate.tot_fs),
            "scatterPositions": positions,
        }
    )


def strike_event(gamestate, striker: str, trigger: str, strike_index: int, position=None) -> None:
    event = {
        "index": len(gamestate.book.events),
        "type": "strike",
        "striker": striker,
        "trigger": trigger,
        "strikeIndex": int(strike_index),
    }
    if position is not None:
        event["position"] = {"reel": position["reel"], "row": _row(gamestate, position["row"])}
    gamestate.book.add_event(event)


def eat_event(gamestate, striker: str, symbol_eaten, strike_index: int) -> None:
    gamestate.book.add_event(
        {
            "index": len(gamestate.book.events),
            "type": "eat",
            "striker": striker,
            "symbolEaten": symbol_eaten,
            "strikeIndex": int(strike_index),
            "remainingPool": list(gamestate.symbol_pool),
        }
    )


def remove_symbol_from_pool_event(gamestate, symbol: str) -> None:
    gamestate.book.add_event(
        {
            "index": len(gamestate.book.events),
            "type": "removeSymbolFromPool",
            "symbol": symbol,
            "remainingPool": list(gamestate.symbol_pool),
        }
    )


def retrigger_spins_event(gamestate, added: int, capped_from: int) -> None:
    positions = [
        {"reel": p["reel"], "row": _row(gamestate, p["row"])} for p in gamestate.special_syms_on_board["scatter"]
    ]
    gamestate.book.add_event(
        {
            "index": len(gamestate.book.events),
            "type": "retriggerSpins",
            "added": int(added),
            "newTotalFs": int(gamestate.tot_fs),
            "cappedFrom": int(capped_from),
            "positions": positions,
        }
    )


def max_win_cinematic_event(gamestate) -> None:
    gamestate.book.add_event(
        {
            "index": len(gamestate.book.events),
            "type": "maxWinCinematic",
            "payout": int(round(gamestate.config.wincap * 100)),
        }
    )


def bonus_end_event(gamestate) -> None:
    gamestate.book.add_event(
        {
            "index": len(gamestate.book.events),
            "type": "bonusEnd",
            "mode": gamestate.bonus_mode,
            "totalSessionWin": int(round(min(gamestate.win_manager.freegame_wins, gamestate.config.wincap) * 100)),
            "spinsPlayed": int(gamestate.fs),
            "symbolsEaten": len(gamestate.eaten_symbols),
            "eatenList": list(gamestate.eaten_symbols),
        }
    )
