"""
Conversation Test Runner
Simulates real user conversations by sending input to the Flask /chat/send endpoint.
Validates fact extraction, contextual answers, loop detection, and end-to-end diagnosis.
"""

import os
import sys
import json
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))


def load_test_cases():
    file_path = os.path.join(TESTS_DIR, 'conversation_test_cases.json')
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_results(report):
    file_path = os.path.join(TESTS_DIR, 'conversation_results.json')
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n  📄 Report saved to: {file_path}")


def check_nlp_facts(actual_facts, expected_facts):
    """Check if all expected facts are present and match in actual facts."""
    for key, value in expected_facts.items():
        if key not in actual_facts or actual_facts[key] != value:
            return False, f"Expected {key}={value}, but got {actual_facts.get(key, 'missing')}"
    return True, ""


def run_tests():
    test_cases = load_test_cases()
    results = []
    
    total = len(test_cases)
    passed = 0
    failed_cases = []
    total_questions = 0

    print("=" * 70)
    print("  CONVERSATION TEST SUITE")
    print("=" * 70)
    print()

    with app.test_client() as client:
        for tc in test_cases:
            test_id = tc['test_id']
            group = tc['group']
            description = tc['description']
            steps = tc['steps']
            
            # Reset session for new test
            client.get('/chat')
            
            active_question = None
            clarification_count = 0
            questions_asked = 0
            
            actual_facts = {}
            actual_rule = None
            test_pass = True
            fail_reason = ""
            
            for step in steps:
                payload = {'message': step['user']}
                if active_question:
                    payload['question_code'] = active_question
                    
                res = client.post('/chat/send', json=payload)
                data = res.get_json()
                
                # Check for loop / clarification
                debug = data.get('debug', {})
                input_source = debug.get('input_source', '')
                if 'clarification' in input_source:
                    clarification_count += 1
                
                actual_facts.update(debug.get('facts', {}))
                
                if data.get('status') == 'need_input':
                    active_question = data['question']['question_code']
                    questions_asked += 1
                elif data.get('status') == 'diagnosed':
                    actual_rule = data['diagnosis'].get('rule_id')
                    active_question = None
                else:
                    active_question = None
                    
            total_questions += questions_asked
                    
            # ── VALIDATION ──
            if 'expected_facts' in tc:
                ok, msg = check_nlp_facts(actual_facts, tc['expected_facts'])
                if not ok:
                    test_pass = False
                    fail_reason = f"NLP Mismatch: {msg}"
            
            if 'expected_rule' in tc and test_pass:
                if actual_rule != tc['expected_rule']:
                    test_pass = False
                    fail_reason = f"Rule Mismatch: Expected {tc['expected_rule']}, Got {actual_rule}"
                    
            if 'expected_clarification' in tc and test_pass:
                if clarification_count == 0:
                    test_pass = False
                    fail_reason = "Expected clarification message, but system missed it."

            if 'expected_progression' in tc and test_pass:
                if questions_asked == 0 and not actual_rule:
                    test_pass = False
                    fail_reason = "System stuck, completely failed to progress."

            status_symbol = "✅ PASS" if test_pass else "❌ FAIL"
            print(f"  {status_symbol}  [{group}] {test_id}: {description}")
            if not test_pass:
                print(f"         Reason: {fail_reason}")
                failed_cases.append({
                    'test_id': test_id,
                    'group': group,
                    'description': description,
                    'reason': fail_reason
                })
            
            if test_pass:
                passed += 1
                
            results.append({
                'test_id': test_id,
                'group': group,
                'passed': test_pass,
                'reason': fail_reason,
                'questions_asked': questions_asked,
                'final_rule': actual_rule
            })

    accuracy = (passed / total) * 100 if total > 0 else 0
    avg_questions = total_questions / total if total > 0 else 0

    print("\n=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    print(f"  Total tests:            {total}")
    print(f"  Passed:                 {passed}")
    print(f"  Failed:                 {total - passed}")
    print(f"  Accuracy:               {accuracy:.1f}%")
    print(f"  Avg questions asked:    {avg_questions:.1f}")
    print("=" * 70)

    if failed_cases:
        print("\n  TOP FAILED CASES:")
        print("  " + "-" * 50)
        for fc in failed_cases[:5]:
            print(f"  • {fc['test_id']} ({fc['group']})")
            print(f"    {fc['description']}")
            print(f"    => {fc['reason']}")
            
    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_tests': total,
            'passed': passed,
            'failed': total - passed,
            'accuracy': round(accuracy, 2),
            'avg_questions': round(avg_questions, 2)
        },
        'failed_cases': failed_cases,
        'results': results
    }
    
    save_results(report)


if __name__ == '__main__':
    run_tests()
