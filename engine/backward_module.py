"""
Backward Chaining Module — Determines what facts are still needed.

For each candidate rule, find conditions NOT yet in known facts.
Returns the set of missing conditions that would help confirm or reject rules.
"""

import logging
from collections import Counter

logger = logging.getLogger(__name__)


def find_missing_conditions(candidate_rules, known_facts):
    """
    For each candidate rule, identify conditions not yet collected.

    Args:
        candidate_rules: list of rule dicts (from state_manager.candidate_rules)
        known_facts: dict mapping symptom_code -> bool

    Returns:
        dict mapping rule_id -> list of missing condition codes
    """
    missing_by_rule = {}

    for rule in candidate_rules:
        rule_id = rule['rule_id']
        missing = []
        for cond in rule.get('conditions', []):
            code = cond['code']
            if code not in known_facts:
                missing.append(code)
        if missing:
            missing_by_rule[rule_id] = missing

    return missing_by_rule


def get_all_missing_conditions(candidate_rules, known_facts):
    """
    Collect ALL unique missing condition codes across all candidate rules.

    Args:
        candidate_rules: list of rule dicts
        known_facts: dict

    Returns:
        set of symptom_codes that are still needed
    """
    missing = set()
    for rule in candidate_rules:
        for cond in rule.get('conditions', []):
            code = cond['code']
            if code not in known_facts:
                missing.add(code)
    return missing


def get_missing_frequency(candidate_rules, known_facts):
    """
    Count how many candidate rules need each missing condition.
    Higher frequency = more discriminating = should ask first.

    Args:
        candidate_rules: list of rule dicts
        known_facts: dict

    Returns:
        Counter mapping symptom_code -> frequency count
    """
    counter = Counter()
    for rule in candidate_rules:
        for cond in rule.get('conditions', []):
            code = cond['code']
            if code not in known_facts:
                counter[code] += 1
    return counter


def suggest_backward_questions(candidate_rules, known_facts, asked_codes=None, max_count=5):
    """
    Suggest which questions to ask next using backward chaining logic.

    Algorithm:
    1. Find all missing conditions across candidate rules
    2. Count frequency of each missing condition
    3. Exclude already-asked questions
    4. Return top-N most informative questions

    Args:
        candidate_rules: list of rule dicts
        known_facts: dict
        asked_codes: set/list of codes already asked (to skip)
        max_count: max number of suggestions

    Returns:
        list of symptom_codes sorted by information gain (desc)
    """
    asked_set = set(asked_codes or [])
    freq = get_missing_frequency(candidate_rules, known_facts)

    # Remove already-asked codes
    suggestions = [
        (code, count) for code, count in freq.most_common()
        if code not in asked_set and code not in known_facts
    ]

    result = [code for code, _ in suggestions[:max_count]]

    logger.debug(
        "Backward chaining: %d candidates, %d missing conditions, top suggestion: %s",
        len(candidate_rules), len(freq), result[0] if result else '(none)'
    )

    return result
