import csv
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


root = Path(__file__).resolve().parent
answers = {}
with (root / 'train-answers.csv').open(newline='', encoding='utf-8-sig') as f:
    answers = {row['request_id']: row for row in csv.DictReader(f)}

with tempfile.TemporaryDirectory() as directory:
    working = Path(directory)
    shutil.copyfile(root / 'train-input.csv', working / 'test-input.csv')
    subprocess.run([sys.executable, str(root / 'main.py')], cwd=working, check=True)
    with (working / 'routing_log.csv').open(newline='', encoding='utf-8-sig') as f:
        decisions = list(csv.DictReader(f))

with (root / 'train-input.csv').open(newline='', encoding='utf-8-sig') as f:
    requests = list(csv.DictReader(f))

assert len(decisions) == len(requests)
assert [row['request_id'] for row in decisions] == [row['request_id'] for row in requests]
assert all(row['model'] in ('cheap', 'expensive') for row in decisions)

correct = 0
cost = 0
for row in decisions:
    guide = row['model']
    response = answers[row['request_id']][guide + '_answer']
    expected = answers[row['request_id']]['reference_answer']
    correct += response.strip().casefold() == expected.strip().casefold()
    cost += 1 if guide == 'cheap' else 25

total = len(decisions)
quality = correct / total
budget = 20 * total
print(f'Quality: {quality:.2%} ({correct}/{total})')
print(f'Cost: {cost}/{budget} dirham')
print(f'Cheap: {sum(r["model"] == "cheap" for r in decisions)}')
print(f'Expensive: {sum(r["model"] == "expensive" for r in decisions)}')
print('PASS' if quality >= .80 and cost <= budget else 'FAIL')
