"""
Rules Loader
Loads rules from JSON and provides utilities for rule matching.
Ensures strict boolean comparison and safe handling of missing facts.
"""

import logging
from utils.json_loader import load_rules

logger = logging.getLogger(__name__)


def get_all_rules():
    """
    Load all rules from the JSON knowledge base.
    Returns a list of rule dictionaries sorted by priority (descending).
    """
    rules = load_rules()
    return sorted(rules, key=lambda r: r.get('priority', 0), reverse=True)


def get_rules_by_group(group):
    """
    Get rules filtered by group name.

    Args:
        group: The group name (e.g., 'power', 'display', 'os', etc.)

    Returns:
        List of rule dictionaries for the specified group.
    """
    all_rules = get_all_rules()
    return [r for r in all_rules if r.get('group') == group]


def check_rule_conditions(rule, facts_dict):
    """
    Check if ALL conditions in a rule are satisfied by the given facts.
    Uses strict boolean comparison (identity check).

    Args:
        rule: A rule dictionary with 'conditions' list.
        facts_dict: A dictionary mapping symptom_code -> bool value.

    Returns:
        tuple: (is_matched: bool, detail: list[dict])
            detail contains per-condition match info for debugging.
    """
    conditions = rule.get('conditions', [])
    if not conditions:
        return False, []

    detail = []
    all_matched = True

    for condition in conditions:
        code = condition.get('code')
        expected_value = condition.get('value')

        if code is None or expected_value is None:
            detail.append({
                'code': code,
                'expected': expected_value,
                'actual': None,
                'status': 'invalid_condition'
            })
            all_matched = False
            continue

        # Missing fact → condition not met (safe, no crash)
        if code not in facts_dict:
            detail.append({
                'code': code,
                'expected': expected_value,
                'actual': '(missing)',
                'status': 'missing'
            })
            all_matched = False
            continue

        actual_value = facts_dict[code]

        # Strict boolean comparison
        if not isinstance(actual_value, bool):
            actual_value = bool(actual_value)
        if not isinstance(expected_value, bool):
            expected_value = bool(expected_value)

        matched = (actual_value is expected_value)
        detail.append({
            'code': code,
            'expected': expected_value,
            'actual': actual_value,
            'status': 'match' if matched else 'mismatch'
        })
        if not matched:
            all_matched = False

    return all_matched, detail


def find_matching_rules(facts_dict):
    """
    Find all rules whose conditions are fully satisfied.

    Args:
        facts_dict: A dictionary mapping symptom_code -> bool value.

    Returns:
        List of (rule, detail) tuples sorted by priority (highest first).
    """
    all_rules = get_all_rules()
    matched = []

    for rule in all_rules:
        is_matched, detail = check_rule_conditions(rule, facts_dict)
        if is_matched:
            matched.append((rule, detail))

    return matched


def find_best_matching_rule(facts_dict):
    """
    Find the highest-priority rule whose conditions are all met.

    Args:
        facts_dict: A dictionary mapping symptom_code -> bool value.

    Returns:
        The best matching rule dict, or None if no match.
    """
    matched = find_matching_rules(facts_dict)
    if matched:
        return matched[0][0]  # Already sorted by priority desc
    return None
