import json

with open('knowledge_base/06_questions.json', encoding='utf-8') as f:
    qdata = json.load(f)

with open('knowledge_base/07_rules_and_diagnoses.json', encoding='utf-8') as f:
    rdata = json.load(f)

qs = qdata['questions']
rules = rdata['rules']
diags = rdata['diagnoses']

print("=== ACTUAL COUNT FROM JSON ===")
print(f"Total Questions: {len(qs)}")
print(f"Total Rules: {len(rules)}")
print(f"Total Diagnoses: {len(diags)}")

print("\n--- Question IDs ---")
for q in qs:
    print(f"  {q['id']}")

mc = [q for q in qs if q.get('type') == 'multi_choice']
print(f"\n--- Multi-choice questions: {len(mc)} ---")
for q in mc:
    has_submit = any(o.get('value') == 'SUBMIT' for o in q.get('options', []))
    print(f"  {q['id']}: has_SUBMIT={has_submit}")

print("\n--- Metadata in 06_questions.json ---")
meta = qdata.get('metadata', {})
print(f"  metadata total_questions: {meta.get('total_questions')}")
print(f"  metadata total_rules: {meta.get('total_rules')}")
print(f"  metadata total_diagnoses: {meta.get('total_diagnoses')}")

print("\n--- Diagnosis IDs ---")
for d in diags:
    print(f"  {d['id']}")

rule_diag_refs = set()
for r in rules:
    if r.get('triggers_diagnosis'):
        rule_diag_refs.add(r['triggers_diagnosis'])

q_diag_refs = set()
for q in qs:
    for opt in q.get('options', []):
        if opt.get('triggers_diagnosis'):
            q_diag_refs.add(opt['triggers_diagnosis'])

all_refs = rule_diag_refs | q_diag_refs
diag_ids = {d['id'] for d in diags}

print("\n=== BROKEN REFS ===")
broken = all_refs - diag_ids
if broken:
    for b in sorted(broken):
        print(f"  BROKEN: {b}")
else:
    print("  None - all refs valid!")

print("\n=== DEAD-END OPTIONS ===")
dead_ends = []
for q in qs:
    for opt in q.get('options', []):
        if opt.get('value') == 'SUBMIT':
            continue
        has_next = 'next' in opt
        has_diag = 'triggers_diagnosis' in opt
        if not has_next and not has_diag:
            dead_ends.append(f"{q['id']}:{opt['value']}")
if dead_ends:
    for d in dead_ends:
        print(f"  DEAD-END: {d}")
else:
    print("  None!")

print("\n=== RULE IDs ===")
for r in rules:
    print(f"  {r['id']}")
