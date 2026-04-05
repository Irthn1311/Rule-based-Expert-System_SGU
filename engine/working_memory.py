"""
Working Memory — Bộ nhớ làm việc của hệ chuyên gia.

Trong hệ Forward Chaining chuẩn:
  - Facts là các symbols/strings (e.g. "no_power", "is_laptop")
  - Facts chỉ được ADD vào, không xóa (monotonic reasoning)
  - Các rule sẽ match facts trong WM để quyết định có fire không
"""

from __future__ import annotations


class WorkingMemory:
    """
    Bộ nhớ làm việc (Working Memory / Fact Base).
    Lưu tất cả facts đã được xác lập trong phiên chẩn đoán.
    """

    def __init__(self):
        self._facts: set[str] = set()
        self._fact_history: list[tuple[str, str]] = []  # (fact, source)

    def add(self, fact: str, source: str = "user") -> bool:
        """Thêm fact vào WM. Return True nếu fact mới (chưa có)."""
        if fact not in self._facts:
            self._facts.add(fact)
            self._fact_history.append((fact, source))
            return True
        return False

    def add_many(self, facts: list[str], source: str = "user") -> list[str]:
        """Thêm nhiều facts, return danh sách facts thực sự mới."""
        new_facts = []
        for f in facts:
            if self.add(f, source):
                new_facts.append(f)
        return new_facts

    def has(self, fact: str) -> bool:
        return fact in self._facts

    def has_all(self, facts: list[str]) -> bool:
        return all(f in self._facts for f in facts)

    def has_any(self, facts: list[str]) -> bool:
        return any(f in self._facts for f in facts)

    def has_none(self, facts: list[str]) -> bool:
        return not any(f in self._facts for f in facts)

    @property
    def facts(self) -> frozenset[str]:
        return frozenset(self._facts)

    @property
    def history(self) -> list[tuple[str, str]]:
        return list(self._fact_history)

    def snapshot(self) -> frozenset[str]:
        """Chụp trạng thái hiện tại để phát hiện thay đổi."""
        return frozenset(self._facts)

    def __repr__(self):
        return f"WorkingMemory({sorted(self._facts)})"
