"""Re-pay F + C boards with the SDK's own Lines.get_lines (run.py's check_lines, F + C rules).
Usage (from math-sdk/): PYTHONDONTWRITEBYTECODE=1 nice -n 19 env/bin/python <this file> [N per mode]"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, GAME)

from game_config import GameConfig  # noqa: E402
import variant_f  # noqa: E402
from gamestate_f import GameStateF  # noqa: E402
from run import check_lines, redirect_output  # noqa: E402

config = GameConfig()
variant_f.apply_working()
redirect_output(config, os.path.join(HERE, "scratch_sdk"))
gs = GameStateF(config)
check_lines(config, gs, n=int(sys.argv[1]) if len(sys.argv) > 1 else 3000)
