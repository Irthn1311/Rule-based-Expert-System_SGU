"""
Question Controller
Manages the question navigation flow, tracking user progress through
the decision tree defined in question_flow.json.

CRITICAL: When the flow reaches a rule, this controller verifies that
all required conditions have been collected. If any are missing, it
generates additional questions BEFORE allowing the rule to activate.
This prevents the "rule shown but not actually matched" bug.
"""

import logging
from utils.json_loader import load_question_flow, load_rules
from utils.mapper import build_symptom_map

logger = logging.getLogger(__name__)


class QuestionController:
    """
    Controls the flow of questions during a diagnosis session.

    Navigates through the question_flow.json decision tree,
    determines the next question based on yes/no answers,
    and detects when a rule has been reached or flow has ended.

    When a rule is reached, verifies ALL conditions have facts collected.
    If not, asks the missing questions before activating the rule.
    """

    def __init__(self):
        self.flow_data = load_question_flow()
        self.symptom_map = build_symptom_map()
        # Build step lookup: step -> flow entry
        self.step_map = {str(entry['step']): entry for entry in self.flow_data}
        # Build rule lookup: rule_id -> rule dict
        rules = load_rules()
        self.rule_map = {r['rule_id']: r for r in rules}

    def get_first_step(self):
        """Get the first step identifier."""
        return "1"

    def get_step_data(self, step_id):
        """
        Get the flow data for a given step.

        Args:
            step_id: step identifier (string)

        Returns:
            dict with step data or None
        """
        return self.step_map.get(str(step_id))

    def get_question_for_step(self, step_id):
        """
        Get the question information for a given step.

        Args:
            step_id: step identifier

        Returns:
            dict with question_code, question_text, group, step
            or None if step not found
        """
        step_data = self.get_step_data(step_id)
        if not step_data:
            return None

        return {
            'step': step_data['step'],
            'question_code': step_data['question_code'],
            'question_text': step_data['question_text'],
            'group': step_data['group']
        }

    def _get_missing_conditions(self, rule_id, answers_dict):
        """
        Check which conditions of a rule are missing from collected answers.

        Args:
            rule_id: the rule ID (e.g. 'R01')
            answers_dict: current accumulated answers

        Returns:
            list of symptom_codes that are required but not yet collected.
        """
        rule = self.rule_map.get(rule_id)
        if not rule:
            return []

        missing = []
        for condition in rule.get('conditions', []):
            code = condition.get('code')
            if code and code not in answers_dict:
                missing.append(code)
        return missing

    def _make_question_for_symptom(self, symptom_code, rule_id):
        """
        Build a question dict for a symptom that needs to be asked
        to complete a rule's conditions.

        Args:
            symptom_code: the symptom code to ask about
            rule_id: the rule that needs this fact

        Returns:
            dict with question info, or None if symptom not found
        """
        symptom = self.symptom_map.get(symptom_code)
        if not symptom:
            logger.warning(
                "Symptom '%s' required by rule %s not found in symptoms_master",
                symptom_code, rule_id
            )
            return None

        return {
            'step': f'_补_{rule_id}_{symptom_code}',
            'question_code': symptom_code,
            'question_text': symptom['question_text'],
            'group': symptom.get('group', 'unknown')
        }

    def get_next_step(self, current_step, answer):
        """
        Determine the next step based on the current step and answer.

        Args:
            current_step: current step identifier (string)
            answer: boolean (True for Yes, False for No)

        Returns:
            dict with:
                - next_step: the next step ID
                - is_rule: True if the next step is a rule (starts with 'R')
                - is_end: True if the flow has ended
                - rule_id: the rule ID if is_rule is True
        """
        step_data = self.get_step_data(current_step)
        if not step_data:
            return {'next_step': None, 'is_rule': False, 'is_end': True, 'rule_id': None}

        if answer:
            next_val = str(step_data['yes_next'])
        else:
            next_val = str(step_data['no_next'])

        # Check if next step is a rule reference (starts with 'R')
        if next_val.startswith('R'):
            return {
                'next_step': next_val,
                'is_rule': True,
                'is_end': False,
                'rule_id': next_val
            }

        # Check if flow has ended
        if next_val == 'END':
            return {
                'next_step': 'END',
                'is_rule': False,
                'is_end': True,
                'rule_id': None
            }

        # Normal next step
        return {
            'next_step': next_val,
            'is_rule': False,
            'is_end': False,
            'rule_id': None
        }

    def process_answer(self, current_step, answer, answers_dict):
        """
        Process a user's answer and determine what happens next.

        CRITICAL LOGIC: When the flow reaches a rule, we check whether
        all of that rule's required conditions have been collected.
        If any are missing, we return the missing question instead of
        the rule — ensuring the rule engine can fully validate it later.

        Args:
            current_step: current step ID
            answer: boolean answer (True/False)
            answers_dict: current accumulated answers

        Returns:
            dict with:
                - question_code: the answered question's code
                - next_step: next step to go to
                - is_rule: whether the next step is a rule
                - is_end: whether the flow has ended
                - rule_id: rule ID if applicable
                - updated_answers: the answers dict with new answer added
                - pending_question: a question dict if we need to ask more
                                    before confirming a rule (None otherwise)
        """
        step_data = self.get_step_data(current_step)
        if not step_data:
            return None

        # Record the answer
        question_code = step_data['question_code']
        answers_dict[question_code] = answer

        # Get next step
        navigation = self.get_next_step(current_step, answer)

        # === KEY FIX: If next step is a rule, verify all conditions ===
        if navigation['is_rule']:
            rule_id = navigation['rule_id']
            missing = self._get_missing_conditions(rule_id, answers_dict)

            if missing:
                # We need to ask the first missing question
                missing_code = missing[0]
                pending_q = self._make_question_for_symptom(missing_code, rule_id)

                logger.info(
                    "Rule %s reached but missing %d facts: %s. "
                    "Asking '%s' first.",
                    rule_id, len(missing), missing, missing_code
                )

                # Return: NOT a rule yet, need to ask more questions
                return {
                    'question_code': question_code,
                    'next_step': current_step,  # stay on same logical step
                    'is_rule': False,
                    'is_end': False,
                    'rule_id': None,
                    'updated_answers': answers_dict,
                    'pending_question': pending_q,
                    'pending_rule_id': rule_id,
                    'pending_missing': missing
                }

        return {
            'question_code': question_code,
            'next_step': navigation['next_step'],
            'is_rule': navigation['is_rule'],
            'is_end': navigation['is_end'],
            'rule_id': navigation['rule_id'],
            'updated_answers': answers_dict,
            'pending_question': None,
            'pending_rule_id': None,
            'pending_missing': None
        }
