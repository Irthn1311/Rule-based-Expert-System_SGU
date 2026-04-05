import json

with open('knowledge_base/06_questions.json', encoding='utf-8') as f:
    qdata = json.load(f)
with open('knowledge_base/07_rules_and_diagnoses.json', encoding='utf-8') as f:
    rdata = json.load(f)

q_count = len(qdata['questions'])
r_count = len(rdata['rules'])
d_count = len(rdata['diagnoses'])

print('=== GROUND TRUTH FROM JSON ===')
print(f'Questions actual  : {q_count}')
print(f'Questions metadata: {qdata["metadata"]["total_questions"]}')
print(f'Rules actual      : {r_count}')
print(f'Diagnoses actual  : {d_count}')
print(f'Rules metadata    : {qdata["metadata"]["total_rules"]}')
print(f'Diagnoses metadata: {qdata["metadata"]["total_diagnoses"]}')
print()
print('=== QUESTION IDs ===')
for q in qdata['questions']:
    print(f'  {q["id"]}', end='')
print()
print()
print('=== DIAGNOSIS IDs ===')
for d in rdata['diagnoses']:
    print(f'  {d["id"]}', end='')
print()
print()

# Count facts per question
all_facts = set()
for q in qdata['questions']:
    for opt in q.get('options', []):
        for f in opt.get('adds_facts', []):
            all_facts.add(f)

# Count facts from rules adds_facts
for r in rdata['rules']:
    for f in r.get('adds_facts', []):
        all_facts.add(f)

print(f'=== FACTS PRODUCIBLE: {len(all_facts)} ===')

# Check groups coverage
groups_in_q = set()
for q in qdata['questions']:
    groups_in_q.add(q.get('group', q.get('id')))

diag_groups = {}
for d in rdata['diagnoses']:
    g = d.get('group', 'none')
    diag_groups[g] = diag_groups.get(g, 0) + 1

print('=== DIAGNOSES BY GROUP ===')
for g, cnt in sorted(diag_groups.items()):
    print(f'  {g}: {cnt}')
