"""What-if runs: python whatif.py N name 'python-patch-code' ... ; patch code runs with R (ror_rules) in scope."""
import sys, random, json
from multiprocessing import Pool
import os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import ror_rules as R, ror_engine as E

def job(a):
    code, mode, seed, n = a
    exec(code, {'R': R}); E.build()
    eng = E.Engine(True); rng = random.Random(seed)
    tot = np.zeros(n); base = np.zeros(n); fs = np.zeros(n); kind = np.zeros(n, dtype=np.int8); cap = np.zeros(n, dtype=np.int8)
    for i in range(n):
        o = eng.round(rng, mode); tot[i] = o['total']; base[i] = o['base']; fs[i] = o['fs']; cap[i] = o['capped']
        kind[i] = 0 if o['kind'] is None else (1 if o['kind'] == 'freespins' else 2)
    return tot, base, fs, kind, cap

def run(code, mode, n, chunks=6):
    with Pool(6) as p:
        parts = p.map(job, [(code, mode, 777 + k, n // chunks) for k in range(chunks)])
    return [np.concatenate([q[i] for q in parts]) for i in range(5)]

if __name__ == '__main__':
    n = int(sys.argv[1]); modes = sys.argv[2].split(',')
    for name, code in zip(sys.argv[3::2], sys.argv[4::2]):
        line = [name]
        for m in modes:
            tot, base, fs, kind, cap = run(code, m, n)
            if m == 'base':
                line.append(f"base: spin {base.mean():.3f} total {tot.mean():.3f} hit {np.mean(tot>0):.3f}")
            else:
                f = fs
                fl = 30 if m == 'bonus' else 150
                k = f >= fl
                extra = f" | floor{fl}: redraw mean {f[k].mean():.1f} topup mean {np.maximum(f, fl).mean():.1f}"
                if m == 'super':
                    extra += f" floor20 topup {np.maximum(f, 20).mean():.1f}"
                line.append(f"{m}: mean {f.mean():.1f} p50 {np.median(f):.1f} <20 {np.mean(f<20):.3f} <30 {np.mean(f<30):.3f} <150 {np.mean(f<150):.3f} cap 1/{len(f)/max(cap.sum(),1):.0f} strikes?" + extra)
        print(' | '.join(line), flush=True)
