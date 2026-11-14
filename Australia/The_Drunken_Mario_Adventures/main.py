import json,sys
from pathlib import Path

root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).with_name('evidence')
sites=json.loads((root/'observer-installed.json').read_text())['coin_sites']
rows=[json.loads(line) for line in (root/'behavior.jsonl').read_text().splitlines() if line.strip()]

def pattern(row):
 taken={coin[0] for coin in row['episode']['collected']}
 return ''.join(str(int(site in taken)) for site in sites)

wins=[row for row in rows if row['state']['won']]
if not wins:raise ValueError('No completed winning episode')
best=max(wins,key=lambda row:row['score'])
bits=pattern(best)
tail=rows[-20:]
if len(tail)<20 or any(not row['state']['won'] or pattern(row)!=bits for row in tail):raise ValueError('Coin pattern has not stabilized')
if len(bits)%5:raise ValueError('Invalid bit count')
values=[int(bits[i:i+5],2) for i in range(0,len(bits),5)]
if any(value<1 or value>26 for value in values):raise ValueError('Invalid letter code')
print('SIGMOID_'+''.join(chr(value+64) for value in values))
