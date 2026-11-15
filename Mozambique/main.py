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
