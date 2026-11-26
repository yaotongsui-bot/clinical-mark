"""Print the records of one judge request that match a pattern: show.py <key> <regex> [<key> <regex> ...]"""
import json, re, sys
R = {r['key']: r for r in json.load(open('reference/judge_requests.json', encoding='utf-8'))}
a = sys.argv[1:]
for key, rx in zip(a[::2], a[1::2]):
    p = json.loads(R[key]['user'])
    recs = p.get('records_in_time_order') or p.get('recorded_actions')
    print('@', key, '| T', p.get('decision_time', '')[:16], '|', p.get('ai_statement') or p.get('ai_action', {}).get('text'))
    for x in recs:
        if re.search(rx, x.get('text', ''), re.I):
            print(f"  {x['id']} {x.get('date','')[5:]} {x.get('time','')} {x.get('type','')}{' ONGOING' if x.get('ongoing_at_decision') else ''}: {x.get('text','').strip()[:130]}")
