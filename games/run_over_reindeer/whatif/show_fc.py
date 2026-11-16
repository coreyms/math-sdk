import json, sys
for l in open(sys.argv[1]):
    d = json.loads(l); fb, sb = d['fs_bought'], d['su_bought']; g = d['whole_game']
    print(d['name'], d['n'])
    print('  FS bought %.2f±%.2f med %s u10 %s p99.9 %s caps %d | seen %s' % (fb['mean'], fb['se'], fb['median'], fb['under10'], fb['p99_9'], d['fs_cap_events'], d['fs_seen']))
    print('  SU bought %.2f±%.2f med %s u10 %s p99.9 %s caps %d | seen %s' % (sb['mean'], sb['se'], sb['median'], sb['under10'], sb['p99_9'], d['su_cap_events'], d['su_seen']))
    print('  natural %s / %s | 96.7 at FS 1/%s SU 1/%s | maxwin 1/%s ±%s%% | base %s share %s hit %s sd %s' % (d['fs_natural'], d['su_natural'], g['fs_1_in'], g['super_1_in'], d['maxwin_1_in'], round(100*d['maxwin_rel_error'],1), d['base_spin_rtp'], g['base_share'], g['hit'], g['sd']))
    print('  bands', g['bands'], 'base big', d['base_spin_big_wins'])
