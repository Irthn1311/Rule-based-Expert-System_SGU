"""
State Manager — Centralized session state for the hybrid expert system.

Tracks all diagnosis state in one place:
- Known facts (symptom_code -> bool)
- Asked questions (codes already shown)
- Candidate rules (filtered by partial match)
- Reasoning history (log of each step)

Thread-safe for single-session Flask usage.
"""

import time
import logging
from engine.rules_loader import get_all_rules, check_rule_conditions

logger = logging.getLogger(__name__)


class StateManager:
    """
    Central state container for a single diagnosis session.

    Responsibilities:
    - Store and update known facts
    - Track which questions have been asked (avoid duplicates)
    - Maintain candidate rules (rules that could still match)
    - Record reasoning history for explanation
    """

    def __init__(self):
        self.facts = {}                # symptom_code -> bool
        self.asked = []                # list of symptom_codes already asked
        self.candidate_rules = []      # list of rule dicts still possible
        self.history = []              # list of {step, action, detail, timestamp}
        self.current_question = None   # symptom_code currently being asked
        self.start_time = time.time()
        self._init_candidates()

    def _init_candidates(self):
        """Load all rules as initial candidates."""
        self.candidate_rules = get_all_rules()
        self._log('init', f'Loaded {len(self.candidate_rules)} candidate rules')

    def _log(self, action, detail):
        """Append to reasoning history."""
        entry = {
            'step': len(self.history) + 1,
            'action': action,
            'detail': detail,
            'timestamp': round(time.time() - self.start_time, 3)
        }
        self.history.append(entry)
        logger.debug("State[%d] %s: %s", entry['step'], action, detail)

    # ── Fact Management ──

    def add_fact(self, code, value):
        """
        Add or update a single fact.
        Returns True if the fact is new or changed.
        """
        is_new = (code not in self.facts) or (self.facts[code] != value)
        self.facts[code] = bool(value)
        if is_new:
            self._log('add_fact', f'{code} = {value}')
            self._update_candidates()
        return is_new

    def add_facts(self, facts_dict):
        """
        Add multiple facts at once.
        Returns list of codes that were new/changed.
        """
        changed = []
        for code, value in facts_dict.items():
            if self.add_fact(code, value):
                changed.append(code)
        return changed

    def has_fact(self, code):
        """Check if a fact has been collected."""
        return code in self.facts

    def get_fact(self, code, default=None):
        """Get a fact value, or default if missing."""
        return self.facts.get(code, default)

    # ── Question Tracking ──

    def mark_asked(self, code):
        """Mark a symptom code as already asked."""
        if code not in self.asked:
            self.asked.append(code)

    def was_asked(self, code):
        """Check if this question was already asked."""
        return code in self.asked

    def set_current_question(self, code):
        """Set the currently active question being asked to the user."""
        self.current_question = code
        self._log('set_question', f'Active question: {code}')

    def clear_current_question(self):
        """Clear the current question after it's been answered."""
        self.current_question = None

    # ── Candidate Rules ──

    def _update_candidates(self):
        """
        Re-filter candidates: remove rules that are already impossible
        (a condition conflicts with a known fact).
        """
        still_possible = []
        for rule in self.candidate_rules:
            dominated = False
            for cond in rule.get('conditions', []):
                code = cond['code']
                expected = cond['value']
                if code in self.facts and self.facts[code] != expected:
                    dominated = True
                    break
            if not dominated:
                still_possible.append(rule)

        removed = len(self.candidate_rules) - len(still_possible)
        if removed > 0:
            self._log('prune', f'Removed {removed} impossible rules, {len(still_possible)} remaining')
        self.candidate_rules = still_possible

    def get_fully_matched_rules(self):
        """
        Return candidate rules where ALL conditions are satisfied.
        Sorted by priority descending.
        """
        matched = []
        for rule in self.candidate_rules:
            is_matched, _ = check_rule_conditions(rule, self.facts)
            if is_matched:
                matched.append(rule)
        return sorted(matched, key=lambda r: r.get('priority', 0), reverse=True)

    def get_candidate_count(self):
        """Number of rules still possible."""
        return len(self.candidate_rules)

    # ── Serialization (for Flask session) ──

    def to_dict(self):
        """Serialize state to a JSON-serializable dict."""
        return {
            'facts': dict(self.facts),
            'asked': list(self.asked),
            'candidate_rule_ids': [r['rule_id'] for r in self.candidate_rules],
            'history': list(self.history),
            'current_question': self.current_question,
            'start_time': self.start_time,
        }

    @classmethod
    def from_dict(cls, data):
        """Reconstruct state from a serialized dict."""
        state = cls.__new__(cls)
        state.facts = data.get('facts', {})
        state.asked = data.get('asked', [])
        state.history = data.get('history', [])
        state.current_question = data.get('current_question', None)
        state.start_time = data.get('start_time', time.time())

        # Reconstruct candidate rules from stored IDs
        all_rules = get_all_rules()
        rule_map = {r['rule_id']: r for r in all_rules}
        stored_ids = data.get('candidate_rule_ids', [])
        if stored_ids:
            state.candidate_rules = [rule_map[rid] for rid in stored_ids if rid in rule_map]
        else:
            state.candidate_rules = all_rules

        return state
