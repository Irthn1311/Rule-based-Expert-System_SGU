"""
Mapper Utility
Maps between symptom codes and their metadata (question_text, group, etc.).
"""

from utils.json_loader import load_symptoms, load_rules


def build_symptom_map():
    """
    Build a dictionary mapping symptom_code -> symptom metadata.
    Returns: dict[str, dict]
    """
    symptoms = load_symptoms()
    return {s['symptom_code']: s for s in symptoms}


def build_rule_map():
    """
    Build a dictionary mapping rule_id -> rule metadata.
    Returns: dict[str, dict]
    """
    rules = load_rules()
    return {r['rule_id']: r for r in rules}


def get_question_text(symptom_code):
    """Get the question text for a given symptom code."""
    symptom_map = build_symptom_map()
    symptom = symptom_map.get(symptom_code)
    if symptom:
        return symptom['question_text']
    return None


def get_rule_by_id(rule_id):
    """Get a rule by its ID."""
    rule_map = build_rule_map()
    return rule_map.get(rule_id)
