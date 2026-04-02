"""
Explanation Module — Provides human-readable reasoning traces.

Builds a structured explanation of how the system reached its conclusion:
- Facts used
- Rules evaluated
- Why the final rule was selected (or why no rule matched)
- Step-by-step reasoning history
"""

import logging
from engine.rules_loader import check_rule_conditions

logger = logging.getLogger(__name__)


def build_explanation(state, diagnosis_result):
    """
    Build a comprehensive explanation of the diagnosis process.

    Args:
        state: StateManager instance (with facts, history, candidates)
        diagnosis_result: dict from InferenceService.run_diagnosis()

    Returns:
        dict with structured explanation:
        {
            'summary': str,
            'facts_used': list,
            'matched_rules': list,
            'rejected_rules': list,
            'reasoning_steps': list,
            'decision_source': str
        }
    """
    facts = state.facts
    rule_id = diagnosis_result.get('rule_id')

    # === Facts Summary ===
    facts_used = [
        {'code': code, 'value': value, 'label': 'Có' if value else 'Không'}
        for code, value in sorted(facts.items())
    ]

    # === Matched Rules ===
    matched_rules = []
    all_matches = diagnosis_result.get('all_matches', [])
    for rule in all_matches:
        matched_rules.append({
            'rule_id': rule['rule_id'],
            'cause': rule['cause'],
            'priority': rule['priority'],
            'is_selected': rule['rule_id'] == rule_id
        })

    # === Rejected Rules (from evaluated) ===
    rejected_rules = []
    for eval_info in diagnosis_result.get('evaluated_rules', []):
        if not eval_info.get('matched', False):
            failed_conds = []
            for d in eval_info.get('conditions_detail', []):
                if d.get('status') != 'match':
                    failed_conds.append({
                        'code': d['code'],
                        'expected': d['expected'],
                        'actual': d['actual'],
                        'reason': d['status']
                    })
            rejected_rules.append({
                'rule_id': eval_info['rule_id'],
                'priority': eval_info['priority'],
                'failed_conditions': failed_conds,
                'conditions_met': len(eval_info.get('conditions_detail', [])) - len(failed_conds),
                'conditions_total': len(eval_info.get('conditions_detail', []))
            })

    # === Reasoning Steps ===
    reasoning_steps = []
    for entry in state.history:
        step_text = _format_history_entry(entry)
        if step_text:
            reasoning_steps.append(step_text)

    # === Summary ===
    if rule_id:
        summary = (
            f"Hệ thống đã xác định nguyên nhân qua luật {rule_id} "
            f"dựa trên {len(facts)} sự kiện thu thập được. "
            f"Tổng cộng {len(matched_rules)} luật khớp, "
            f"{len(rejected_rules)} luật bị loại."
        )
    else:
        summary = (
            f"Hệ thống không tìm thấy luật nào khớp hoàn toàn "
            f"với {len(facts)} sự kiện đã thu thập. "
            f"{len(rejected_rules)} luật đã được đánh giá nhưng không khớp."
        )

    return {
        'summary': summary,
        'facts_used': facts_used,
        'matched_rules': matched_rules,
        'rejected_rules': rejected_rules,
        'reasoning_steps': reasoning_steps,
        'decision_source': diagnosis_result.get('decision_source', 'unknown'),
        'total_rules_evaluated': len(matched_rules) + len(rejected_rules),
    }


def _format_history_entry(entry):
    """Format a single history entry to readable Vietnamese text."""
    action = entry.get('action', '')
    detail = entry.get('detail', '')
    step = entry.get('step', 0)
    ts = entry.get('timestamp', 0)

    if action == 'init':
        return f"Bước {step} ({ts}s): Khởi tạo — {detail}"
    elif action == 'add_fact':
        return f"Bước {step} ({ts}s): Thu thập sự kiện — {detail}"
    elif action == 'prune':
        return f"Bước {step} ({ts}s): Lọc luật — {detail}"
    elif action == 'nlp_parse':
        return f"Bước {step} ({ts}s): Phân tích NLP — {detail}"
    elif action == 'ask_question':
        return f"Bước {step} ({ts}s): Hỏi thêm — {detail}"
    elif action == 'forward_chain':
        return f"Bước {step} ({ts}s): Suy luận tiến — {detail}"
    else:
        return f"Bước {step} ({ts}s): {action} — {detail}"


def format_explanation_text(explanation):
    """
    Format the full explanation as plain text (for debug/logging).

    Args:
        explanation: dict from build_explanation()

    Returns:
        str with formatted explanation
    """
    lines = []
    lines.append("=" * 60)
    lines.append("  GIẢI THÍCH QUÁ TRÌNH SUY LUẬN")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"📝 {explanation['summary']}")
    lines.append("")

    lines.append("── Sự kiện đã thu thập ──")
    for f in explanation['facts_used']:
        lines.append(f"  • {f['code']}: {f['label']}")
    lines.append("")

    if explanation['matched_rules']:
        lines.append("── Luật khớp ──")
        for r in explanation['matched_rules']:
            marker = "🏆" if r['is_selected'] else "✅"
            lines.append(f"  {marker} {r['rule_id']} (P={r['priority']}): {r['cause']}")
        lines.append("")

    if explanation.get('reasoning_steps'):
        lines.append("── Quá trình suy luận ──")
        for step in explanation['reasoning_steps']:
            lines.append(f"  {step}")
        lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)
