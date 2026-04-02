"""
Diagnosis Engine
Implements the Experta-based knowledge engine for computer troubleshooting.
Uses forward chaining with dynamically loaded rules from JSON.
"""

import logging
from experta import KnowledgeEngine, Rule, DefFacts
from engine.facts import Symptom, DiagnosisResult
from engine.rules_loader import get_all_rules, check_rule_conditions

logger = logging.getLogger(__name__)

# Fallback result when no rule matches
NO_MATCH_RESULT = {
    'rule_id': None,
    'cause': 'Không xác định được lỗi',
    'solution': 'Vui lòng kiểm tra thêm hoặc cung cấp thêm thông tin'
}


class ComputerDiagnosisEngine(KnowledgeEngine):
    """
    Expert system engine for computer diagnosis.

    Uses a hybrid approach:
    - Experta Facts for symptom storage and forward chaining trigger
    - Manual condition checking against JSON-loaded rules

    This approach allows rules to be fully defined in JSON without
    hardcoding them as Python @Rule decorators.
    """

    def __init__(self):
        super().__init__()
        self.diagnosis_results = []
        self.evaluated_rules = []
        self.debug_info = []

    @DefFacts()
    def initial_facts(self):
        """Declare initial facts (none needed at start)."""
        yield Symptom(code="__init__", value=True)

    def declare_symptom(self, code, value):
        """
        Declare a symptom fact in the engine.

        Args:
            code: symptom code string
            value: boolean value
        """
        self.declare(Symptom(code=code, value=value))

    def _collect_facts_dict(self):
        """
        Collect all declared Symptom facts into a dictionary.

        Returns:
            dict mapping symptom_code -> bool value
        """
        facts_dict = {}
        for fact in self.facts.values():
            if isinstance(fact, Symptom):
                code = fact['code']
                if code not in ('__init__', '__run_inference__'):
                    facts_dict[code] = fact['value']
        return facts_dict

    @Rule(Symptom(code="__run_inference__", value=True))
    def run_inference(self):
        """
        Triggered rule that performs inference against all JSON rules.
        This is the core forward-chaining mechanism.
        """
        facts_dict = self._collect_facts_dict()
        all_rules = get_all_rules()

        self.debug_info = []
        self.evaluated_rules = []
        self.diagnosis_results = []

        for rule in all_rules:
            is_matched, detail = check_rule_conditions(rule, facts_dict)

            eval_info = {
                'rule_id': rule['rule_id'],
                'conditions': rule['conditions'],
                'conditions_detail': detail,
                'matched': is_matched,
                'priority': rule['priority']
            }
            self.evaluated_rules.append(eval_info)

            if is_matched:
                self.debug_info.append(
                    f"✅ Rule {rule['rule_id']} MATCHED (priority={rule['priority']})"
                )
                self.diagnosis_results.append(rule)
                self.declare(DiagnosisResult(
                    rule_id=rule['rule_id'],
                    cause=rule['cause'],
                    solution=rule['solution'],
                    priority=rule['priority']
                ))
            else:
                # Build per-condition failure summary
                failed = [d for d in detail if d['status'] != 'match']
                fail_summary = ', '.join(
                    f"{d['code']}={d['actual']}(expected {d['expected']})"
                    for d in failed
                )
                self.debug_info.append(
                    f"❌ Rule {rule['rule_id']} not matched [{fail_summary}]"
                )

        logger.debug(
            "Inference complete: %d rules evaluated, %d matched",
            len(all_rules), len(self.diagnosis_results)
        )

    def diagnose(self, facts_dict):
        """
        Run complete diagnosis given a dictionary of symptom facts.

        Args:
            facts_dict: dict mapping symptom_code -> bool value

        Returns:
            dict with keys: matched_rule, cause, solution, rule_id,
                            all_matches, evaluated_rules, debug_info
            Always returns valid output (never crashes, uses fallback).
        """
        try:
            self.reset()
            self.diagnosis_results = []
            self.evaluated_rules = []
            self.debug_info = []

            # Declare all symptom facts
            for code, value in facts_dict.items():
                bool_value = bool(value) if not isinstance(value, bool) else value
                self.declare(Symptom(code=code, value=bool_value))

            # Trigger inference
            self.declare(Symptom(code="__run_inference__", value=True))
            self.run()

            # Find best result (highest priority)
            best = None
            if self.diagnosis_results:
                best = sorted(
                    self.diagnosis_results,
                    key=lambda r: r.get('priority', 0),
                    reverse=True
                )[0]

            if best:
                return {
                    'matched_rule': best,
                    'cause': best['cause'],
                    'solution': best['solution'],
                    'rule_id': best['rule_id'],
                    'all_matches': self.diagnosis_results,
                    'evaluated_rules': self.evaluated_rules,
                    'debug_info': self.debug_info
                }
            else:
                return {
                    'matched_rule': None,
                    'cause': NO_MATCH_RESULT['cause'],
                    'solution': NO_MATCH_RESULT['solution'],
                    'rule_id': None,
                    'all_matches': [],
                    'evaluated_rules': self.evaluated_rules,
                    'debug_info': self.debug_info + [
                        "⚠️ Không tìm thấy luật nào khớp với triệu chứng"
                    ]
                }

        except Exception as e:
            logger.error("Diagnosis engine error: %s", str(e), exc_info=True)
            return {
                'matched_rule': None,
                'cause': NO_MATCH_RESULT['cause'],
                'solution': NO_MATCH_RESULT['solution'],
                'rule_id': None,
                'all_matches': [],
                'evaluated_rules': [],
                'debug_info': [f"🔥 Engine error: {str(e)}"]
            }
