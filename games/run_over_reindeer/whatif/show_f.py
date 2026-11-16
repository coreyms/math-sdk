import json, sys
for l in open(sys.argv[1]):
    d = json.loads(l); fb, sb = d['fs_bought'], d['su_bought']; g = d['whole_game']; fr, sr = d['fs_rounds'], d['su_rounds']
    print(d['name'])
    print('  FS bought %.2f±%.2f (n %d) med %s u10 %s p99.9 %s ge5000 %s caps %d | strikes %s cols %s 2+ %s topcol %s gw %s' % (fb['mean'], fb['se'], fb['n'], fb['median'], fb['under10'], fb['p99_9'], fb['ge5000'], fb['cap_events'], fr['strikes'], fr['columns'], fr['two_plus_columns'], fr['top_column_p50_p90'], fr['top_grandma_p50_p90']))
    print('  SU bought %.2f±%.2f (n %d) med %s u10 %s p99.9 %s ge5000 %s caps %d | strikes %s cols %s 2+ %s topcol %s gw %s' % (sb['mean'], sb['se'], sb['n'], sb['median'], sb['under10'], sb['p99_9'], sb['ge5000'], sb['cap_events'], sr['strikes'], sr['columns'], sr['two_plus_columns'], sr['top_column_p50_p90'], sr['top_grandma_p50_p90']))
    print('  natural %s / %s | 96.7 at FS 1/%s SU 1/%s | maxwin 1/%s ±%s%% | base %s share %s hit %s sd %s' % (d['fs_natural'], d['su_natural'], g['fs_1_in'], g['super_1_in'], d['maxwin_1_in_from_bonus'], round(100 * d['maxwin_rel_error']) if d['maxwin_rel_error'] else None, d['base_spin_rtp'], g['base_share'], g['hit'], g['sd']))
    print('  bands', g['bands'], ' base big', d['base_spin_big_wins'])
