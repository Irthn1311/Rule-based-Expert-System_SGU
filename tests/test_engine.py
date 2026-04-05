"""
test_engine.py — Test forward chaining engine core.

Chạy: pytest tests/test_engine.py -v
"""

import sys
import os
import pytest

# Ensure project root in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from engine.working_memory import WorkingMemory
from engine.rule_model import Rule, DiagnosisResult
from engine.forward_engine import ForwardChainingEngine
from engine.diagnostic_session import KnowledgeBaseLoader, DiagnosticSession


# ── Fixtures ──────────────────────────────────────────────────

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
QUESTIONS_PATH = os.path.join(DATA_DIR, '06_questions.json')
RULES_PATH = os.path.join(DATA_DIR, '07_rules_and_diagnoses.json')


@pytest.fixture(scope='session')
def kb():
    return KnowledgeBaseLoader(QUESTIONS_PATH, RULES_PATH)


@pytest.fixture
def session(kb):
    return kb.create_session()


# ── Working Memory Tests ──────────────────────────────────────

class TestWorkingMemory:

    def test_add_fact(self):
        wm = WorkingMemory()
        assert wm.add('no_power') is True
        assert wm.has('no_power') is True

    def test_add_duplicate_returns_false(self):
        wm = WorkingMemory()
        wm.add('is_laptop')
        assert wm.add('is_laptop') is False

    def test_has_all(self):
        wm = WorkingMemory()
        wm.add('no_power')
        wm.add('is_laptop')
        assert wm.has_all(['no_power', 'is_laptop']) is True
        assert wm.has_all(['no_power', 'no_charge']) is False

    def test_has_none(self):
        wm = WorkingMemory()
        wm.add('power_led_on')
        assert wm.has_none(['no_power']) is True
        assert wm.has_none(['power_led_on']) is False

    def test_history(self):
        wm = WorkingMemory()
        wm.add('no_power', source='Q01')
        assert len(wm.history) == 1
        assert wm.history[0] == ('no_power', 'Q01')


# ── Rule Model Tests ──────────────────────────────────────────

class TestRule:

    def test_rule_applicable(self):
        rule = Rule(
            id='R_TEST', name='Test', group='test',
            conditions=['no_power', 'is_laptop'],
        )
        wm = WorkingMemory()
        wm.add('no_power')
        assert rule.is_applicable(wm) is False  # missing is_laptop
        wm.add('is_laptop')
        assert rule.is_applicable(wm) is True

    def test_not_conditions_block_rule(self):
        rule = Rule(
            id='R_TEST', name='Test', group='test',
            conditions=['no_power'],
            not_conditions=['power_led_on']
        )
        wm = WorkingMemory()
        wm.add('no_power')
        wm.add('power_led_on')
        assert rule.is_applicable(wm) is False

    def test_rule_fires_and_adds_facts(self):
        rule = Rule(
            id='R_TEST', name='Test', group='test',
            conditions=['no_power'],
            adds_facts=['probable_power_issue'],
        )
        wm = WorkingMemory()
        wm.add('no_power')
        new_facts, diag = rule.fire(wm)
        assert 'probable_power_issue' in new_facts
        assert diag is None
        assert wm.has('probable_power_issue')

    def test_cf_combine(self):
        combined = DiagnosisResult.combine_cf(0.85, 0.90)
        assert 0.98 < combined < 1.0

    def test_rule_reset(self):
        rule = Rule(id='R', name='R', group='g', conditions=['f'])
        wm = WorkingMemory()
        wm.add('f')
        rule.fire(wm)
        assert rule.fired is True
        rule.reset()
        assert rule.fired is False


# ── Forward Engine Tests ──────────────────────────────────────

class TestForwardEngine:

    def test_engine_fires_rule(self):
        rules = [Rule.from_dict({
            'id': 'R001',
            'name': 'Test rule',
            'group': 'test',
            'conditions': ['no_power', 'is_laptop'],
            'triggers_diagnosis': 'DIAG_TEST',
            'cf': 0.9
        })]
        diagnoses = [{'id': 'DIAG_TEST', 'name': 'Test Diag', 'severity': 'HIGH'}]
        db = {d['id']: d for d in diagnoses}

        engine = ForwardChainingEngine(rules, db)
        engine.add_facts(['no_power', 'is_laptop'])
        results = engine.run_until_stable()

        assert len(results) == 1
        assert results[0].diagnosis_id == 'DIAG_TEST'
        assert results[0].cf == 0.9

    def test_engine_chain_rules(self):
        """Test chaining: R1 fires → adds fact → R2 fires."""
        rules = [
            Rule.from_dict({
                'id': 'R1', 'name': 'Chain R1', 'group': 'test',
                'conditions': ['fact_a'],
                'adds_facts': ['fact_b'],
                'cf': 0.8
            }),
            Rule.from_dict({
                'id': 'R2', 'name': 'Chain R2', 'group': 'test',
                'conditions': ['fact_b'],
                'triggers_diagnosis': 'DIAG_CHAIN',
                'cf': 0.85
            }),
        ]
        db = {'DIAG_CHAIN': {'id': 'DIAG_CHAIN', 'name': 'Chain Diag'}}
        engine = ForwardChainingEngine(rules, db)
        engine.add_facts(['fact_a'])
        results = engine.run_until_stable()
        assert any(r.diagnosis_id == 'DIAG_CHAIN' for r in results)

    def test_near_fire_rules(self):
        rules = [Rule.from_dict({
            'id': 'R001', 'name': 'Near fire test', 'group': 'test',
            'conditions': ['fact_a', 'fact_b'],
            'cf': 0.9
        })]
        engine = ForwardChainingEngine(rules, {})
        engine.add_facts(['fact_a'])  # missing: fact_b
        near = engine.get_near_fire_rules(max_missing=2)
        assert len(near) == 1
        assert 'fact_b' in near[0]['missing_facts']


# ── End-to-End Test Cases ─────────────────────────────────────

class TestE2E:
    """Test các test cases gốc từ engine.py — 30 TCs."""

    TEST_CASES = [
        {
            "name": "TC01 — Adapter hỏng",
            "path": [("Q01","A"),("Q02","A"),("Q03","A"),("Q05","A")],
            "expected": "DIAG_PWR_01",
        },
        {
            "name": "TC02 — Pin chai",
            "path": [("Q01","A"),("Q02","A"),("Q03","A"),("Q05","C")],
            "expected": "DIAG_PWR_02",
        },
        {
            "name": "TC05 — Driver GPU lỗi",
            "path": [("Q01","B"),("Q09","B"),("Q11","A")],
            "expected": "DIAG_DSP_02",
        },
        {
            "name": "TC08 — RAM BSOD",
            "path": [("Q01","C"),("Q13","A"),("Q14","A"),("Q19","A")],
            "expected": "DIAG_OS_03",
        },
        {
            "name": "TC15 — WiFi adapter hỏng",
            "path": [("Q01","D"),("Q20","A"),("Q25","A")],
            "expected": "DIAG_NET_02",
        },
        {
            "name": "TC21 — Driver âm thanh",
            "path": [("Q01","E"),("Q27","A"),("Q28","B")],
            "expected": "DIAG_AUD_01",
        },
        {
            "name": "TC24 — USB cổng hỏng",
            "path": [("Q01","F"),("Q32","A"),("Q33","A"),("Q34","A")],
            "expected": "DIAG_PER_01",
        },
        {
            "name": "TC29 — HDD hỏng",
            "path": [("Q01","H"),("Q36","B")],
            "expected": "DIAG_STR_02",
        },
    ]

    def _run(self, session, path, expected):
        for qid, val in path:
            if session.is_complete:
                break
            q = session.get_current_question()
            if not q:
                return False
            session.answer([val])
        found_ids = [d['id'] for d in session.final_diagnoses]
        return expected in found_ids

    @pytest.mark.parametrize("tc", TEST_CASES, ids=[t["name"] for t in TEST_CASES])
    def test_case(self, kb, tc):
        session = kb.create_session()
        result = self._run(session, tc["path"], tc["expected"])
        assert result, (
            f"Expected {tc['expected']} not found in "
            f"{[d['id'] for d in session.final_diagnoses]}"
        )
