"""
Full audit script: phát hiện TẤT CẢ lỗi logic trong knowledge base
"""
import json, sys

Q_PATH = r'd:\SGU\CNTT\CongNgheTriThuc\project\knowledge_base\06_questions.json'
R_PATH = r'd:\SGU\CNTT\CongNgheTriThuc\project\knowledge_base\07_rules_and_diagnoses.json'

with open(Q_PATH, encoding='utf-8') as f: qdata = json.load(f)
with open(R_PATH, encoding='utf-8') as f: rdata = json.load(f)

questions   = {q['id']: q for q in qdata['questions']}
rules       = rdata['rules']
diagnoses   = {d['id']: d for d in rdata['diagnoses']}
diag_ids    = set(diagnoses.keys())
q_ids       = set(questions.keys())

issues = []

# ── 1. Dead-end options ──────────────────────────────────
for qid, q in questions.items():
    is_multi = q.get('type') == 'multi_choice'
    for opt in q.get('options', []):
        has_next  = 'next' in opt
        has_diag  = 'triggers_diagnosis' in opt
        has_act   = 'suggest_action' in opt
        has_facts = bool(opt.get('adds_facts'))
        # multi_choice: facts-only options are ok (engine runs inference after)
        if is_multi and has_facts:
            continue
        if not (has_next or has_diag or has_act):
            issues.append(('DEAD_END', 'CRITICAL', qid, opt['value'], 'No next / triggers_diagnosis / suggest_action'))

# ── 2. Broken next references ────────────────────────────
for qid, q in questions.items():
    for opt in q.get('options', []):
        nxt = opt.get('next')
        if nxt and nxt not in q_ids:
            issues.append(('BROKEN_NEXT', 'CRITICAL', qid, opt['value'], f'next="{nxt}" does not exist'))

# ── 3. Broken diagnosis references (questions) ───────────
for qid, q in questions.items():
    for opt in q.get('options', []):
        td = opt.get('triggers_diagnosis')
        if td and td not in diag_ids:
            issues.append(('BROKEN_DIAG_Q', 'CRITICAL', qid, opt['value'], f'triggers_diagnosis="{td}" not in diagnoses'))

# ── 4. Broken diagnosis references (rules) ───────────────
for r in rules:
    td = r.get('triggers_diagnosis')
    if td and td not in diag_ids:
        issues.append(('BROKEN_DIAG_R', 'CRITICAL', r['id'], '-', f'triggers_diagnosis="{td}" not in diagnoses'))

# ── 5. Dead rules (conditions never produced) ─────────────
# Collect all facts that CAN be produced
produced_facts = set()
# From questions
for q in qdata['questions']:
    for opt in q.get('options', []):
        produced_facts.update(opt.get('adds_facts', []))
        if opt.get('sets_group'):
            produced_facts.add(f"group:{opt['sets_group']}")

# From rules (adds_facts)
changed = True
while changed:
    changed = False
    for r in rules:
        conditions = r.get('conditions', [])
        not_conds  = r.get('not_conditions', [])
        adds       = r.get('adds_facts', [])
        if adds and all(c in produced_facts for c in conditions):
            for f in adds:
                if f not in produced_facts:
                    produced_facts.add(f)
                    changed = True

# Now check each rule's conditions
for r in rules:
    dead_conds = [c for c in r.get('conditions', []) if c not in produced_facts]
    if dead_conds:
        issues.append(('DEAD_RULE', 'HIGH', r['id'], '-', f'Conditions never produced: {dead_conds}'))

# ── 6. Self-loop detection ────────────────────────────────
for qid, q in questions.items():
    for opt in q.get('options', []):
        nxt = opt.get('next')
        if nxt == qid:
            issues.append(('SELF_LOOP', 'CRITICAL', qid, opt['value'], f'next loops back to self'))

# ── 7. Q17 multi_choice - check for SUBMIT pattern ──────
for qid, q in questions.items():
    if q.get('type') != 'multi_choice':
        continue
    # SUBMIT pattern: a question is valid if it has a SUBMIT option with next
    has_submit = any(o.get('value') == 'SUBMIT' and 'next' in o for o in q.get('options', []))
    if has_submit:
        continue  # valid pattern: options add facts, SUBMIT continues flow
    # Old-style multi_choice: check each non-fact option
    for opt in q.get('options', []):
        v = opt['value']
        if not opt.get('adds_facts') and not opt.get('triggers_diagnosis') and 'next' not in opt:
            issues.append(('MULTI_DEAD', 'HIGH', qid, v,
                           'multi_choice option has no facts/next/diagnosis'))

# ── 8. Q08, Q38, Q39 multi_choice same issue ─────────────
for qid in ('Q08', 'Q38', 'Q39'):
    q = questions.get(qid, {})
    if q.get('type') == 'multi_choice':
        # Check if there's any option with explicit next or triggers_diagnosis
        has_terminator = any('next' in o or 'triggers_diagnosis' in o for o in q.get('options',[]))
        if not has_terminator:
            issues.append(('MULTI_NO_EXIT', 'HIGH', qid, '-', 
                           'multi_choice has no option with next/diagnosis → session hangs'))

# ── 9. Q26-D dead-end ─────────────────────────────────────
# already handled by check 1

# ── Print report ──────────────────────────────────────────
print(f"\n{'='*70}")
print(f"FULL AUDIT REPORT — {len(issues)} issues found")
print(f"{'='*70}\n")

severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
issues.sort(key=lambda x: severity_order.get(x[1], 9))

for kind, sev, loc, opt, desc in issues:
    icon = '🔴' if sev == 'CRITICAL' else '🟠' if sev == 'HIGH' else '🟡'
    print(f"{icon} [{sev}] {kind}")
    print(f"   Location : {loc}  option={opt}")
    print(f"   Problem  : {desc}")
    print()

# Summary
from collections import Counter
by_sev = Counter(i[1] for i in issues)
print(f"\nSUMMARY: CRITICAL={by_sev.get('CRITICAL',0)}, HIGH={by_sev.get('HIGH',0)}, MEDIUM={by_sev.get('MEDIUM',0)}")
print(f"TOTAL diagnosed facts producible: {len(produced_facts)}")
