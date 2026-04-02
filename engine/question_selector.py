"""
Question Selector — Smart dynamic question selection.

Replaces static QuestionFlow with intelligent question selection
based on backward chaining analysis. Selects the MOST INFORMATIVE
question to ask next.

Algorithm:
1. Get missing conditions from backward chaining
2. Score each condition by frequency across candidate rules
3. Select highest-score condition (most discriminating)
4. Map to symptom metadata (question_text, group)
"""

import logging
from engine.backward_module import suggest_backward_questions
from utils.mapper import build_symptom_map

logger = logging.getLogger(__name__)

# Cache symptom map
_symptom_map = None


def _get_symptom_map():
    global _symptom_map
    if _symptom_map is None:
        _symptom_map = build_symptom_map()
    return _symptom_map


def select_next_question(state):
    """
    Select the most informative question to ask next.

    Uses backward chaining to find which missing condition appears
    in the most candidate rules (highest discrimination power).

    Args:
        state: StateManager instance

    Returns:
        dict with question info, or None if nothing left to ask.
        {
            'question_code': str,
            'question_text': str,
            'group': str,
            'reason': str  # why this question was selected
        }
    """
    # Get suggestions from backward chaining
    suggestions = suggest_backward_questions(
        state.candidate_rules,
        state.facts,
        asked_codes=state.asked,
        max_count=10
    )

    if not suggestions:
        logger.info("Question selector: no more questions to ask")
        return None

    symptom_map = _get_symptom_map()

    # Find first suggestion with valid symptom metadata
    for code in suggestions:
        symptom = symptom_map.get(code)
        if symptom:
            # Count how many rules need this fact
            rule_count = sum(
                1 for r in state.candidate_rules
                for c in r.get('conditions', [])
                if c['code'] == code and code not in state.facts
            )

            question = {
                'question_code': code,
                'question_text': symptom['question_text'],
                'group': symptom.get('group', 'unknown'),
                'reason': f'Liên quan đến {rule_count} luật ứng viên'
            }

            logger.info(
                "Selected question: %s (covers %d rules)",
                code, rule_count
            )
            return question

    logger.info("Question selector: no valid symptom found for suggestions")
    return None


def get_question_stats(state):
    """
    Get statistics about the current question selection state.

    Returns:
        dict with stats for debug/explanation
    """
    from engine.backward_module import get_missing_frequency

    freq = get_missing_frequency(state.candidate_rules, state.facts)
    total_missing = len(freq)
    top_5 = freq.most_common(5)

    return {
        'total_missing_conditions': total_missing,
        'candidate_rules_count': len(state.candidate_rules),
        'facts_collected': len(state.facts),
        'questions_asked': len(state.asked),
        'top_conditions': [
            {'code': code, 'frequency': count}
            for code, count in top_5
        ]
    }
