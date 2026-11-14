import json,random
from pathlib import Path
from main import read,recover,consensus

def main():
 observations,register=map(read,['observations.csv','ring_register.csv'])
 result,rows=recover(observations,register)
 ring=result['ring']
 years=sorted({r['date'][:4] for r in rows})
 observers=sorted({v for r in rows for v in r['observers'].split('|')})
 checks={}
 checks['leave_one_reading_out']=[consensus(rows[:i]+rows[i+1:])[0] for i in range(len(rows))]
 checks['leave_one_year_out']={y:consensus([r for r in rows if not r['date'].startswith(y)])[0] for y in years}
 checks['leave_one_observer_out']=[consensus([r for r in rows if o not in r['observers'].split('|')])[0] for o in observers]
 checks['radius_localities']={str(d):[r['locality_id'] for r in result['ranked_localities'] if r['nearest_registered_stork_km']>d] for d in [5,10,20,50]}
 assert all(v==ring for v in checks['leave_one_reading_out'])
 assert all(v==ring for v in checks['leave_one_year_out'].values())
 assert all(v==ring for v in checks['leave_one_observer_out'])
 assert all(v==[result['locality_id']] for v in checks['radius_localities'].values())
 shuffled=observations.copy();random.Random(0).shuffle(shuffled)
 assert recover(shuffled,register)[0]['ring']==ring
 checks['row_order_invariant']=True
 checks['ring_absent_from_entire_register']=ring not in {r['ring'] for r in register}
 assert checks['ring_absent_from_entire_register']
 Path('verification.json').write_text(json.dumps(checks,indent=2)+'\n',encoding='utf-8')
 print('All stability checks passed')

if __name__=='__main__':main()
