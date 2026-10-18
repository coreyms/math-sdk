"""Copied 2026-10-17 (math fix 2026.10.18) from the harsh review's summarise.py, unchanged: run it in the
folder that holds the walk_<mode>.json files tools/phantom_walk.py wrote."""
"""READ-ONLY. One table of the walk results (walk_<mode>.json) for the report."""
import json
MODES = ["base", "ante", "super_ante", "bonus", "super", "epic", "mystery"]
D = {m: json.load(open(f"walk_{m}.json")) for m in MODES}
print("books walked:", sum(D[m]["books"] for m in MODES), {m: D[m]["books"] for m in MODES})
print("missing LUT rows:", {m: D[m]["missing_lut_rows"] for m in MODES})
print("violations:")
for m in MODES: print(f"  {m:10s} {D[m]['violations']}")
print("\nfeature rates (weighted, per round):")
for m in MODES:
    w = D[m]["weighted"]
    fr = {k: w[k] for k in ("feat_bonus", "feat_super", "feat_epic") if k in w}
    print(f"  {m:10s} " + "  ".join(f"{k[5:]} {v*100:.4f}% (1 in {1/v:,.1f})" for k, v in fr.items()),
          "  on8:", {k: f"1 in {1/v:,.0f}" for k, v in w.items() if k.endswith("_on_8")},
          "  scatter-sting rounds:", f"{w.get('scatter_sting_round',0)*100:.4f}%")
b = D["base"]["weighted"]; a = D["ante"]["weighted"]; s = D["super_ante"]["weighted"]
print("\nAnte vs base, per tier:", {t: round(a[f"feat_{t}"] / b[f"feat_{t}"], 2) for t in ("bonus", "super", "epic")})
print("Super Ante vs base: super", round(s["feat_super"] / b["feat_super"], 1), " epic", round(s["feat_epic"] / b["feat_epic"], 1))
print("Super Ante regular Free Spins:", s.get("feat_bonus", 0))
print("\nbase-game spin numbers:")
for m in ("base", "ante", "super_ante"):
    w = D[m]["weighted"]
    print(f"  {m:10s} hit {w['hit']*100:.2f}%  wins under 1x / all wins {w['win_under_1x']/w['hit']*100:.1f}%  3+ cascade steps 1 in {1/w['b_3plus_steps']:.0f}"
          f"  swipe spins {w['b_swipe_spin']*100:.2f}%  sting runs {w['b_sting_run']*100:.2f}%")
print("\nfree spins (per free spin, weighted):")
for m in ("base", "ante", "super_ante", "bonus", "super", "epic", "mystery"):
    w = D[m]["weighted"]
    for ft in ("bonus", "super", "epic"):
        k = f"f_{ft}_spins"
        if k not in w or w[k] == 0: continue
        n = w[k]
        rescue = w.get(f"f_{ft}_deadpre_swipe", 0) / w[f"f_{ft}_deadpre"]
        paid = w.get(f"f_{ft}_paidpre_swipe", 0) / w[f"f_{ft}_paidpre"]
        print(f"  {m:10s} {ft:5s} dead {w.get(f'f_{ft}_dead',0)/n*100:5.1f}%  super sting {w.get(f'f_{ft}_super_sting',0)/n*100:5.2f}%"
              f"  big sting {w.get(f'f_{ft}_big_sting',0)/n*100:5.2f}%  roar {w.get(f'f_{ft}_roar',0)/n*100:5.2f}%"
              f"  swipe if dead so far {rescue*100:5.1f}% vs if paid {paid*100:5.1f}%  sting run {w.get(f'f_{ft}_sting_run',0)/n*100:5.1f}%")
print("\nupgrades in the buys (share of rounds):")
for m in ("bonus", "super"):
    w = D[m]["weighted"]
    print(f"  {m}: " + ", ".join(f"{k[5:]} {v*100:.4f}% (1 in {1/v:,.1f})" for k, v in w.items() if k.startswith("feat_") and "_on_" not in k))
print("\nfloors (lowest free spins total / round total on an uncapped round, x the base bet):")
for m in MODES: print(f"  {m:10s} {D[m]['mins']}")
print("\nsting runs: last sting in a paying cluster always (0 violations); share where the cluster already paid without it:")
for m in MODES:
    c = D[m]["counts"]
    for k in [k for k in c if k.endswith("_sting_runs")]:
        pre = k[:-len("_sting_runs")]
        ext = c.get(pre + "_sting_only_extended_existing", 0)
        print(f"  {m:10s} {pre:8s} runs {c[k]:7d}  only extended an already paying cluster {ext:6d} ({ext/c[k]*100:.1f}%)")
print("\nswipes walked:", {m: sum(v for k, v in D[m]["counts"].items() if k.endswith("_swipes")) for m in MODES})
print("scatter sting placeholder mismatches:")
for m in MODES:
    c = D[m]["counts"]; w = D[m]["weighted"]
    if c.get("scatter_sting_reveals"):
        print(f"  {m:10s} scatter-sting reveals {c['scatter_sting_reveals']}, visible S max {c.get('scatter_sting_visible_S_max')}, "
              f"phantom {c.get('ss_mismatch_phantom',0)} larger {c.get('ss_mismatch_larger',0)}; weighted share of all rounds: phantom {w.get('ss_mismatch_phantom',0)*100:.4f}% larger {w.get('ss_mismatch_larger',0)*100:.4f}%")
print("\ncap books, capping step listing more than paid:", {m: (D[m]["counts"].get("cap_books"), D[m]["counts"].get("capping_step_lists_more_than_paid"), D[m]["counts"].get("cap_with_unplayed_spins")) for m in MODES})
print("mystery: nothing that pays 0, share of all Mysteries:", D["mystery"]["weighted"]["mys_nothing_zero"], " split", {k: D["mystery"]["weighted"][k] for k in ("mys_nothing", "mys_super", "mys_epic")})
