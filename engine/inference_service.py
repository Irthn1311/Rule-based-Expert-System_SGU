"""
Inference Service — Orchestrates the hybrid expert system pipeline.

Supports two modes:
1. GUIDED MODE (original): QuestionFlow + forward chaining
2. HYBRID MODE (new): NLP → State Manager → Forward/Backward chaining

Output schema (always guaranteed):
{
    "rule_id": str | None,
    "cause": str,
    "solution": str,
    "questions_asked": int,
    "diagnosis_time_ms": float,
    "decision_source": str,     # "rule_engine" | "fallback"
    "all_matches": list,
    "evaluated_rules": list,
    "debug_info": list
}
"""

import time
import logging
from engine.diagnosis_engine import ComputerDiagnosisEngine, NO_MATCH_RESULT
from engine.state_manager import StateManager
from engine.question_selector import select_next_question
from engine.explanation import build_explanation

logger = logging.getLogger(__name__)


class InferenceService:
    """
    Service that orchestrates the diagnosis process.
    Flask routes never touch the engine directly.
    """

    def __init__(self):
        self.engine = ComputerDiagnosisEngine()

    def _build_result(self, rule_id, cause, solution,
                      questions_asked, diagnosis_time_ms,
                      decision_source,
                      all_matches=None, evaluated_rules=None,
                      debug_info=None, matched_rule=None):
        """Build a standardised result dict."""
        return {
            'rule_id': rule_id,
            'cause': cause,
            'solution': solution,
            'questions_asked': questions_asked,
            'diagnosis_time_ms': round(diagnosis_time_ms, 2),
            'decision_source': decision_source,
            'matched_rule': matched_rule,
            'all_matches': all_matches or [],
            'evaluated_rules': evaluated_rules or [],
            'debug_info': debug_info or []
        }

    # ─── Original Guided Mode ───

    def run_diagnosis(self, answers, start_time=None):
        """Run forward chaining on collected answers."""
        t0 = time.time()
        result = self.engine.diagnose(answers)
        inference_ms = (time.time() - t0) * 1000

        decision_source = "rule_engine" if result['rule_id'] else "fallback"

        return self._build_result(
            rule_id=result['rule_id'],
            cause=result['cause'],
            solution=result['solution'],
            questions_asked=len(answers),
            diagnosis_time_ms=inference_ms,
            decision_source=decision_source,
            all_matches=result['all_matches'],
            evaluated_rules=result['evaluated_rules'],
            debug_info=result['debug_info'],
            matched_rule=result['matched_rule']
        )

    def run_quick_diagnosis(self, answers, rule_id=None, start_time=None):
        """Run diagnosis with optional flow hint (guided mode)."""
        result = self.run_diagnosis(answers)

        if rule_id and result['rule_id'] != rule_id:
            msg = (
                f"⚠️ Cây quyết định gợi ý luật {rule_id}, "
                f"nhưng engine chọn: {result['rule_id'] or '(không khớp)'}"
            )
            result['debug_info'].append(msg)
        elif rule_id and result['rule_id'] == rule_id:
            result['debug_info'].append(
                f"✅ Cây quyết định và engine đồng ý: {rule_id}"
            )

        return result

    # ─── Hybrid Mode (NEW) ───

    def run_hybrid_step(self, state):
        """
        Execute one step of the hybrid diagnosis loop.

        Algorithm:
        1. Run forward chaining on current facts
        2. IF rule matched → return result
        3. ELSE → use backward chaining to select next question
        4. Return question to ask

        Args:
            state: StateManager instance

        Returns:
            dict with either:
            - 'status': 'diagnosed' + full result + explanation
            - 'status': 'need_input' + next_question
            - 'status': 'no_more_questions' + fallback result
        """
        # Step 1: Try forward chaining
        t0 = time.time()
        result = self.engine.diagnose(state.facts)
        inference_ms = (time.time() - t0) * 1000

        if result['rule_id'] is not None:
            # Found a match!
            diagnosis = self._build_result(
                rule_id=result['rule_id'],
                cause=result['cause'],
                solution=result['solution'],
                questions_asked=len(state.asked),
                diagnosis_time_ms=inference_ms,
                decision_source='rule_engine',
                all_matches=result['all_matches'],
                evaluated_rules=result['evaluated_rules'],
                debug_info=result['debug_info'],
                matched_rule=result['matched_rule']
            )
            explanation = build_explanation(state, diagnosis)

            state.history.append({
                'step': len(state.history) + 1,
                'action': 'forward_chain',
                'detail': f'Luật {result["rule_id"]} khớp',
                'timestamp': round(time.time() - state.start_time, 3)
            })

            return {
                'status': 'diagnosed',
                'diagnosis': diagnosis,
                'explanation': explanation
            }

        # Step 2: No match yet — select next question via backward chaining
        next_q = select_next_question(state)

        if next_q:
            state.history.append({
                'step': len(state.history) + 1,
                'action': 'ask_question',
                'detail': f'Hỏi: {next_q["question_code"]} ({next_q["reason"]})',
                'timestamp': round(time.time() - state.start_time, 3)
            })

            return {
                'status': 'need_input',
                'question': next_q,
                'candidates_remaining': len(state.candidate_rules),
                'facts_count': len(state.facts)
            }

        # Step 3: No more questions to ask — return fallback
        diagnosis = self._build_result(
            rule_id=None,
            cause=NO_MATCH_RESULT['cause'],
            solution=NO_MATCH_RESULT['solution'],
            questions_asked=len(state.asked),
            diagnosis_time_ms=inference_ms,
            decision_source='fallback',
            evaluated_rules=result['evaluated_rules'],
            debug_info=result['debug_info'] + [
                "⚠️ Hết câu hỏi — không tìm thấy luật khớp"
            ]
        )
        explanation = build_explanation(state, diagnosis)

        return {
            'status': 'no_more_questions',
            'diagnosis': diagnosis,
            'explanation': explanation
        }
