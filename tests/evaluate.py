"""
Evaluation Module
Tests the expert system against predefined test cases.
Computes accuracy, average diagnosis time, and average number of questions.
Saves results to tests/results.json.

Evaluation compares by rule_id ONLY — no string matching on cause.
"""

import os
import sys
import json
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.inference_service import InferenceService

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))


def load_test_cases():
    """Load test cases from JSON file."""
    test_file = os.path.join(TESTS_DIR, 'test_cases.json')
    with open(test_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_results(report):
    """Save evaluation results to tests/results.json."""
    results_file = os.path.join(TESTS_DIR, 'results.json')
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n  📄 Results saved to: {results_file}")


def run_evaluation():
    """
    Run all test cases and compute evaluation metrics.

    Comparison logic: rule_id ONLY (no cause string matching).
    Handles expected_rule=null for edge cases.

    Returns:
        dict with accuracy, avg_time, avg_questions, and detailed results
    """
    test_cases = load_test_cases()
    service = InferenceService()

    results = []
    correct = 0
    total = len(test_cases)
    total_time = 0.0
    total_questions = 0
    failed_cases = []

    print("=" * 70)
    print("  EVALUATION — Computer Expert System")
    print("=" * 70)
    print()

    for tc in test_cases:
        test_id = tc['test_id']
        description = tc['description']
        answers = tc['answers']
        expected_rule = tc['expected_rule']  # str or None

        # Simulate diagnosis
        start_time = time.time()
        diagnosis = service.run_diagnosis(answers, start_time=start_time)
        elapsed_ms = (time.time() - start_time) * 1000

        actual_rule = diagnosis.get('rule_id')
        actual_cause = diagnosis.get('cause', '')

        # Compare by rule_id ONLY
        is_correct = (actual_rule == expected_rule)

        if is_correct:
            correct += 1

        total_time += elapsed_ms
        total_questions += len(answers)

        status = "✅ PASS" if is_correct else "❌ FAIL"
        print(f"  {status}  {test_id}: {description}")
        if not is_correct:
            print(f"         Expected rule: {expected_rule}")
            print(f"         Got rule:      {actual_rule} ({actual_cause})")
            failed_cases.append({
                'test_id': test_id,
                'description': description,
                'expected_rule': expected_rule,
                'actual_rule': actual_rule,
                'actual_cause': actual_cause
            })
        print()

        results.append({
            'test_id': test_id,
            'description': description,
            'expected_rule': expected_rule,
            'actual_rule': actual_rule,
            'actual_cause': actual_cause,
            'correct': is_correct,
            'diagnosis_time_ms': round(elapsed_ms, 2),
            'questions_asked': len(answers)
        })

    # Compute metrics
    accuracy = (correct / total) * 100 if total > 0 else 0
    avg_time_ms = total_time / total if total > 0 else 0
    avg_questions = total_questions / total if total > 0 else 0

    print("=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    print(f"  Total test cases:       {total}")
    print(f"  Passed:                 {correct}")
    print(f"  Failed:                 {total - correct}")
    print(f"  Accuracy:               {accuracy:.1f}%")
    print(f"  Avg diagnosis time:     {avg_time_ms:.2f}ms")
    print(f"  Avg questions per case: {avg_questions:.1f}")
    print("=" * 70)

    # Print top 5 failed cases
    if failed_cases:
        print()
        print("  TOP FAILED CASES:")
        print("  " + "-" * 50)
        for fc in failed_cases[:5]:
            print(f"  • {fc['test_id']}: {fc['description']}")
            print(f"    Expected: {fc['expected_rule']}  Got: {fc['actual_rule']}")
        print()

    # Build report
    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total': total,
            'correct': correct,
            'failed': total - correct,
            'accuracy': round(accuracy, 2),
            'avg_diagnosis_time_ms': round(avg_time_ms, 2),
            'avg_questions': round(avg_questions, 1)
        },
        'failed_cases': failed_cases,
        'results': results
    }

    # Save to JSON
    save_results(report)

    return report


if __name__ == '__main__':
    run_evaluation()
