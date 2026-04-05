import json, sys

files = {
    'questions': r'd:\SGU\CNTT\CongNgheTriThuc\project\knowledge_base\06_questions.json',
    'rules_diag': r'd:\SGU\CNTT\CongNgheTriThuc\project\knowledge_base\07_rules_and_diagnoses.json'
}

all_ok = True
for name, path in files.items():
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        if name == 'questions':
            q_count = len(data['questions'])
            print(f'[OK] {name}: {q_count} questions loaded')
            dead_ends = []
            for q in data['questions']:
                is_multi = q.get('type') == 'multi_choice'
                for opt in q.get('options', []):
                    has_next = 'next' in opt
                    has_diag = 'triggers_diagnosis' in opt
                    has_suggest = 'suggest_action' in opt
                    has_facts_only = is_multi and bool(opt.get('adds_facts'))
                    if not (has_next or has_diag or has_suggest or has_facts_only):
                        dead_ends.append(f"{q['id']} opt={opt['value']}")
            if dead_ends:
                print(f'  [WARN] Dead-end options (no continuation): {dead_ends[:10]}')
            else:
                print(f'  [OK] No dead-end options found')
        elif name == 'rules_diag':
            r_count = len(data['rules'])
            d_count = len(data['diagnoses'])
            print(f'[OK] {name}: {r_count} rules, {d_count} diagnoses loaded')
            diag_ids = {d['id'] for d in data['diagnoses']}
            broken_refs = []
            for r in data['rules']:
                td = r.get('triggers_diagnosis')
                if td and td not in diag_ids:
                    broken_refs.append(f"{r['id']} -> {td}")
            if broken_refs:
                print(f'  [WARN] Broken diagnosis refs in rules: {broken_refs}')
            else:
                print(f'  [OK] All rule->diagnosis refs valid ({len(diag_ids)} diagnoses total)')
    except json.JSONDecodeError as e:
        print(f'[ERROR] JSON parse error in {name}: {e}')
        all_ok = False
    except Exception as e:
        print(f'[ERROR] {name}: {e}')
        all_ok = False

sys.exit(0 if all_ok else 1)
