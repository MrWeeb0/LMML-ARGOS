COLIȚA Puișor:
import sys
import json

def agent(observation, memory):
"""
Primește starea curentă a jocului (observation) și memoria persistentă (memory).
Trebuie să returneze un dicționar reprezentând acțiunea legală aleasă.
"""
legal_actions = observation.get('legal_actions', [])
if not legal_actions:
return {}

# Strategie de bază: alege prima acțiune legală disponibilă
return legal_actions[0]

def serve():
memory = {}
for line in sys.stdin:
if not line.strip():
continue
try:
data = json.loads(line)
# Unele motoare trimit {"observation": ...}
obs = data.get('observation', data)

action = agent(obs, memory)

print(json.dumps(action))
sys.stdout.flush()
except Exception as e:
print(f"Eroare în agent: {e}", file=sys.stderr)
print(json.dumps({}))
sys.stdout.flush()

if name == 'main':

COLIȚA Puișor:
import sys
import json

def agent(observation, memory):
legal_actions = observation.get('legal_actions', [])
if not legal_actions:
return {}

# 1. Dacă există acțiuni de livrare de contracte profitabile, execută-le prioritar
delivery_actions = [a for a in legal_actions if a.get('type') == 'deliver']
if delivery_actions:
# Alege contractul cu valoarea cea mai mare (fabricate > materii prime)
delivery_actions.sort(key=lambda x: x.get('value', 0), reverse=True)
return delivery_actions[0]

# 2. Dacă poți prelua un contract bun și ai loc în barcă
claim_actions = [a for a in legal_actions if a.get('type') == 'claim']
if claim_actions and observation.get('round', 0) < 60:
claim_actions.sort(key=lambda x: x.get('value', 0), reverse=True)
return claim_actions[0]

# 3. Construire de ateliere sau pornire producție dacă ai resurse
production_actions = [a for a in legal_actions if a.get('type') in ['buil
