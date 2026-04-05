"""
Rule Model — Mô hình luật IF-THEN và kết quả chẩn đoán.

Rule:  IF (conditions) AND NOT (not_conditions) THEN (adds_facts | triggers_diagnosis)
DiagnosisResult: kết quả chẩn đoán với Certainty Factor (mô hình MYCIN)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from .working_memory import WorkingMemory


@dataclass
class Rule:
    """
    Đại diện một luật IF-THEN trong Rule Base.

    Certainty Factor (CF): 0.0 → 1.0 (mô hình MYCIN)
    Priority (1–5): conflict resolution — priority cao hơn fire trước
    """
    id: str
    name: str
    group: str
    conditions: list[str]
    adds_facts: list[str] = field(default_factory=list)
    not_conditions: list[str] = field(default_factory=list)
    triggers_diagnosis: Optional[str] = None
    priority: int = 2
    cf: float = 0.8
    fired: bool = field(default=False, repr=False)

    @property
    def specificity(self) -> int:
        """Số lượng điều kiện — dùng cho conflict resolution."""
        return len(self.conditions) + len(self.not_conditions)

    def is_applicable(self, wm: WorkingMemory) -> bool:
        """
        Kiểm tra luật có thể kích hoạt không.
        Pattern matching: so sánh điều kiện với Working Memory.
        """
        if self.fired:
            return False
        return wm.has_all(self.conditions) and wm.has_none(self.not_conditions)

    def fire(self, wm: WorkingMemory) -> tuple[list[str], Optional[str]]:
        """
        Kích hoạt luật:
        - Thêm facts mới vào WM
        - Return (new_facts, diagnosis_id_or_None)
        """
        self.fired = True
        new_facts = wm.add_many(self.adds_facts, source=self.id)
        return new_facts, self.triggers_diagnosis

    def reset(self):
        """Reset trạng thái để dùng lại trong session mới."""
        self.fired = False

    @classmethod
    def from_dict(cls, d: dict) -> "Rule":
        return cls(
            id=d["id"],
            name=d.get("name", d["id"]),
            group=d.get("group", "unknown"),
            conditions=d.get("conditions", []),
            not_conditions=d.get("not_conditions", []),
            adds_facts=d.get("adds_facts", []),
            triggers_diagnosis=d.get("triggers_diagnosis"),
            priority=d.get("priority", 2),
            cf=d.get("cf", 0.8),
        )


@dataclass
class DiagnosisResult:
    """Một kết quả chẩn đoán được kích hoạt trong phiên làm việc."""
    diagnosis_id: str
    cf: float
    triggered_by_rule: Optional[str] = None
    triggered_by_question: Optional[str] = None
    combined_cf: Optional[float] = None

    @staticmethod
    def combine_cf(cf1: float, cf2: float) -> float:
        """
        Combine 2 CF theo công thức MYCIN:
          CF_combined = CF1 + CF2*(1-CF1)
        """
        return cf1 + cf2 * (1 - cf1)
