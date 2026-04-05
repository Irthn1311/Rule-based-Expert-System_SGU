"""
Forward Chaining Inference Engine.

Thuật toán:
  1. MATCH: Tìm tất cả rules có thể kích hoạt (Conflict Set)
  2. SELECT: Chọn rule tốt nhất theo Conflict Resolution Strategy
  3. FIRE: Kích hoạt rule → thêm facts + trigger diagnosis
  4. Lặp lại đến khi Conflict Set rỗng (fixed point)

Conflict Resolution Strategy:
  Priority 1: rule.priority cao hơn
  Priority 2: rule.specificity cao hơn (nhiều điều kiện hơn)
  Priority 3: rule.cf cao hơn
"""

from __future__ import annotations
from typing import Optional

from .working_memory import WorkingMemory
from .rule_model import Rule, DiagnosisResult


class ForwardChainingEngine:
    """
    Inference Engine theo chiến lược Forward Chaining (Rete-inspired).
    """

    def __init__(self, rules: list[Rule], diagnoses_db: dict):
        self.rules = rules
        self.diagnoses_db = diagnoses_db  # {id: diagnosis_dict}
        self.wm = WorkingMemory()
        self._diagnosis_cf_map: dict[str, float] = {}
        self._fired_rules_log: list[dict] = []

    def add_facts(self, facts: list[str], source: str = "question") -> list[str]:
        """Thêm facts từ câu trả lời của người dùng vào WM."""
        return self.wm.add_many(facts, source=source)

    def _build_conflict_set(self) -> list[Rule]:
        """
        MATCH phase: tìm tất cả rules applicable.
        Return sorted conflict set (theo priority, specificity, CF).
        """
        conflict_set = [r for r in self.rules if r.is_applicable(self.wm)]
        conflict_set.sort(
            key=lambda r: (r.priority, r.specificity, r.cf),
            reverse=True
        )
        return conflict_set

    def _fire_rule(self, rule: Rule) -> list[DiagnosisResult]:
        """FIRE phase: kích hoạt một rule."""
        new_facts, diag_id = rule.fire(self.wm)

        self._fired_rules_log.append({
            "rule_id": rule.id,
            "rule_name": rule.name,
            "new_facts": new_facts,
            "triggers_diagnosis": diag_id,
            "cf": rule.cf
        })

        results = []
        if diag_id:
            existing_cf = self._diagnosis_cf_map.get(diag_id, 0.0)
            if existing_cf > 0:
                combined = DiagnosisResult.combine_cf(existing_cf, rule.cf)
                self._diagnosis_cf_map[diag_id] = combined
            else:
                self._diagnosis_cf_map[diag_id] = rule.cf

            results.append(DiagnosisResult(
                diagnosis_id=diag_id,
                cf=rule.cf,
                triggered_by_rule=rule.id,
                combined_cf=self._diagnosis_cf_map[diag_id]
            ))

        return results

    def run_one_cycle(self) -> tuple[bool, list[DiagnosisResult]]:
        """
        Chạy một chu kỳ: MATCH → SELECT → FIRE.
        Return: (any_rule_fired, new_diagnoses)
        """
        conflict_set = self._build_conflict_set()
        if not conflict_set:
            return False, []
        best_rule = conflict_set[0]
        diagnoses = self._fire_rule(best_rule)
        return True, diagnoses

    def run_until_stable(self) -> list[DiagnosisResult]:
        """
        Chạy forward chaining đến điểm cố định (fixed point).
        Fixed point: không còn rule nào có thể kích hoạt.
        Safety: giới hạn MAX_ITERATIONS = 100.
        """
        all_diagnoses: list[DiagnosisResult] = []
        MAX_ITERATIONS = 100
        iteration = 0

        while iteration < MAX_ITERATIONS:
            fired, new_diags = self.run_one_cycle()
            all_diagnoses.extend(new_diags)
            if not fired:
                break
            iteration += 1

        return all_diagnoses

    def get_near_fire_rules(self, max_missing: int = 3) -> list[dict]:
        """
        Tìm rules gần thỏa điều kiện (missing ≤ max_missing facts).
        Dùng cho Dynamic Questioning để chọn câu hỏi thông minh.
        
        Return: [{"rule": Rule, "missing_facts": [...], "missing_count": N}]
        """
        near_fire = []
        for rule in self.rules:
            if rule.fired:
                continue
            missing = [f for f in rule.conditions if not self.wm.has(f)]
            # Check not_conditions không phá vỡ
            blocked = any(self.wm.has(f) for f in rule.not_conditions)
            if blocked:
                continue
            if 0 < len(missing) <= max_missing:
                near_fire.append({
                    "rule": rule,
                    "missing_facts": missing,
                    "missing_count": len(missing),
                })
        # Sort: ít missing facts nhất trước (gần fire nhất)
        near_fire.sort(key=lambda x: (x["missing_count"], -x["rule"].priority))
        return near_fire

    @property
    def fired_rules_trace(self) -> list[dict]:
        """Trace của tất cả rules đã fire — dùng cho Explanation Facility."""
        return list(self._fired_rules_log)

    def get_diagnosis_details(self, diag_id: str) -> Optional[dict]:
        return self.diagnoses_db.get(diag_id)

    def get_top_diagnoses(self, n: int = 3) -> list[dict]:
        """
        Lấy top N diagnoses theo combined CF.
        Dùng cho Diagnosis Card trong UI.
        """
        sorted_diags = sorted(
            self._diagnosis_cf_map.items(),
            key=lambda x: x[1],
            reverse=True
        )
        result = []
        for diag_id, cf in sorted_diags[:n]:
            details = self.diagnoses_db.get(diag_id, {})
            result.append({
                "id": diag_id,
                "name": details.get("name", diag_id),
                "cf": round(cf, 3),
                "cf_percent": round(cf * 100),
                "severity": details.get("severity", "UNKNOWN"),
                "user_fixable": details.get("user_fixable", True),
                "solution_steps": details.get("solution_steps", []),
                "needs_technician": details.get("needs_technician", False),
                "warning": details.get("warning"),
            })
        return result

    def reset(self):
        """Reset engine cho session mới."""
        self.wm = WorkingMemory()
        self._diagnosis_cf_map = {}
        self._fired_rules_log = []
        for rule in self.rules:
            rule.reset()
