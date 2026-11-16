"""What-if 4, variant E: variant D with the top of the bonus tables trimmed so the 7,777x cap
comes about 1 in 2.5M base spins.
Usage: ../../../env/bin/python whatif4e.py NAME 'extra Free Spins patch' 'extra Super patch'
(the extra patches run after the bought-round tables of whatif4.py)."""
import json, sys
import numpy as np
import whatif4 as W

if __name__ == "__main__":
    name, extra, extra_su = sys.argv[1], sys.argv[2], sys.argv[3]
    rng = np.random.default_rng(44)
    Fd = W.run(W.L12 + "; " + W.FS.format(g0=0.80, g1=0.19) + "; " + extra, "bonus", 600000, 5000)
    Sd = W.run(W.L12 + "; " + W.SU.format(g0=0.66, g1=0.31) + "; " + extra_su, "super", 600000, 5010)
    B = W.run(W.L12 + "; " + W.BASE + "; " + W.SANTA.format(z=39) + "; " + W.TRIM_BASE, "base", 3000000, 7002)["base"]
    Fb, Sb = Fd["fs"], Sd["fs"]
    Ft, St = np.maximum(Fb, 10), np.maximum(Sb, 50)
    out = {"name": name, "extra": [extra, extra_su], "fs_bought": W.round_table(Fd, np.ones(len(Fb))),
           "su_bought": W.round_table(Sd, np.ones(len(Sb)))}
    nf, ns = 105.0, 315.0
    # natural = bought rounds + top-up + richer mix; Super target scales with the bought mean
    ns = round(float(St.mean()) * nf / float(Ft.mean()), 1) if Ft.mean() < 100 else ns
    wf, af = W.tilt(Ft, nf)
    ws, as_ = W.tilt(St, ns)
    out["fs_natural"] = dict(W.round_table(Fd, wf), tilt_a=round(af, 3), paid=nf)
    out["su_natural"] = dict(W.round_table(Sd, ws), tilt_a=round(as_, 3), paid=ns)
    EB = float(B.mean())
    pf, ps = W.solve_rates(EB, nf, ns)
    res = W.compose(B, Fb, wf, Sb, ws, pf, ps, 10, 50, rng)
    res["fs_1_in"], res["super_1_in"] = round(1 / pf), round(1 / ps)
    out["whole_game"] = res
    rows = {}
    for cost, fs_t, su_t in ((2, 80, 1000), (4, 43, 250), (10, None, 40)):
        need = 0.967 * cost - EB
        pf_free = (need - St.mean() / su_t) / Ft.mean()
        row = {"targets_fs_su": [fs_t, su_t], "fs_1_in_at_super_target": round(1 / pf_free) if pf_free > 0 else None}
        if fs_t:
            row["rtp_at_targets"] = round((EB + Ft.mean() / fs_t + St.mean() / su_t) / cost, 4)
        rows[str(cost)] = row
    out["antes"] = rows
    print(json.dumps(out))
