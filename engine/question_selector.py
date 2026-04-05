"""
Dynamic Question Selector — Chọn câu hỏi thông minh tiếp theo.

Thuật toán scoring:
  1. Tìm rules gần thỏa (near-fire: missing ≤ 3 facts)
  2. Lấy missing facts từ các rules đó
  3. Map missing facts → candidate questions
  4. Score mỗi candidate question:
     - coverage_score: số missing facts được hỏi
     - discrimination_score: số diagnoses phân biệt
     - group_bonus: cùng group → +bonus
     - asked_penalty: đã hỏi rồi → loại
  5. Return câu hỏi có score cao nhất
  6. Fallback: câu hỏi tiếp theo theo flow JSON gốc
"""

from __future__ import annotations
from typing import Optional


class QuestionSelector:
    """
    Chọn câu hỏi tiếp theo một cách thông minh dựa trên trạng thái hiện tại.

    Dynamic Questioning Strategy:
    - Ưu tiên câu hỏi giúp fire rules gần nhất
    - Ưu tiên câu hỏi phân biệt được nhiều diagnoses
    - Không hỏi lại câu đã hỏi
    - Không nhảy group bừa (group_bonus)
    """

    # Thông số scoring
    COVERAGE_WEIGHT = 2.0      # Hệ số cho số facts covered
    DISCRIM_WEIGHT = 1.5       # Hệ số cho khả năng phân biệt diagnosis
    GROUP_BONUS = 0.5          # Bonus cùng group
    MAX_MISSING = 3            # Số missing facts tối đa để xét "near-fire"

    def __init__(self, questions_data: list[dict], diagnoses_data: list[dict]):
        self._questions: dict[str, dict] = {q["id"]: q for q in questions_data}
        self._diagnoses: list[dict] = diagnoses_data

        # Pre-build: fact → list of question IDs có thể cung cấp fact này
        self._fact_to_questions: dict[str, list[str]] = self._build_fact_question_map()

        # Pre-build: question → set of facts nó có thể add
        self._question_to_facts: dict[str, set[str]] = self._build_question_fact_map()

        # Pre-build: diagnosis → set of facts liên quan
        self._diag_to_facts: dict[str, set[str]] = self._build_diag_fact_map()

    def _build_fact_question_map(self) -> dict[str, list[str]]:
        """Mỗi fact liên kết đến các câu hỏi có thể cung cấp fact đó."""
        result: dict[str, list[str]] = {}
        for qid, q in self._questions.items():
            for opt in q.get("options", []):
                for fact in opt.get("adds_facts", []):
                    result.setdefault(fact, [])
                    if qid not in result[fact]:
                        result[fact].append(qid)
        return result

    def _build_question_fact_map(self) -> dict[str, set[str]]:
        """Mỗi câu hỏi có thể cung cấp những facts nào."""
        result: dict[str, set[str]] = {}
        for qid, q in self._questions.items():
            facts = set()
            for opt in q.get("options", []):
                facts.update(opt.get("adds_facts", []))
            result[qid] = facts
        return result

    def _build_diag_fact_map(self) -> dict[str, set[str]]:
        """Mỗi diagnosis liên quan đến những facts nào."""
        result: dict[str, set[str]] = {}
        for d in self._diagnoses:
            result[d["id"]] = set(d.get("symptoms", []))
        return result

    def select(
        self,
        near_fire_rules: list[dict],
        asked_qids: set[str],
        current_group: Optional[str],
        fallback_qid: Optional[str] = None,
        wm_facts: Optional[set[str]] = None,
    ) -> Optional[str]:
        """
        Chọn câu hỏi tốt nhất tiếp theo.

        Args:
            near_fire_rules: Output từ engine.get_near_fire_rules()
            asked_qids: Set các QID đã hỏi
            current_group: Nhóm lỗi đang chẩn đoán
            fallback_qid: Câu hỏi mặc định từ JSON flow
            wm_facts: Facts hiện có trong WM

        Returns:
            QID của câu hỏi được chọn, hoặc None
        """
        if not near_fire_rules:
            return fallback_qid

        # Step 1: Gom tất cả missing facts từ near-fire rules
        candidate_facts: set[str] = set()
        for nf in near_fire_rules:
            candidate_facts.update(nf["missing_facts"])

        # Step 2: Tìm candidate questions (có thể cung cấp ít nhất 1 missing fact)
        candidate_qids: set[str] = set()
        for fact in candidate_facts:
            for qid in self._fact_to_questions.get(fact, []):
                if qid not in asked_qids:
                    candidate_qids.add(qid)

        # Loại bỏ câu đã hỏi
        candidate_qids -= asked_qids

        if not candidate_qids:
            return fallback_qid

        # Step 3: Score từng candidate
        scored = []
        for qid in candidate_qids:
            score = self._score_question(
                qid, candidate_facts, near_fire_rules, current_group
            )
            scored.append((qid, score))

        if not scored:
            return fallback_qid

        # Chọn câu có score cao nhất
        scored.sort(key=lambda x: x[1], reverse=True)
        best_qid = scored[0][0]

        # Nếu fallback tốt hơn hoặc bằng best → ưu tiên fallback (JSON flow)
        # Điều này đảm bảo dynamic questioning chỉ "bổ sung" chứ không phá vỡ flow
        if fallback_qid and fallback_qid not in asked_qids:
            fallback_score = self._score_question(
                fallback_qid, candidate_facts, near_fire_rules, current_group
            )
            # Fallback ưu tiên trừ khi candidate score cao hơn đáng kể (>1.5x)
            if fallback_score > 0 or scored[0][1] < 1.5:
                return fallback_qid

        return best_qid

    def _score_question(
        self,
        qid: str,
        candidate_facts: set[str],
        near_fire_rules: list[dict],
        current_group: Optional[str],
    ) -> float:
        """Tính score cho một câu hỏi."""
        question = self._questions.get(qid)
        if not question:
            return 0.0

        q_facts = self._question_to_facts.get(qid, set())

        # 1. Coverage: số missing facts mà câu hỏi này có thể hỏi
        covered = q_facts & candidate_facts
        coverage_score = len(covered) * self.COVERAGE_WEIGHT

        # 2. Discrimination: câu hỏi này giúp phân biệt bao nhiêu diagnoses
        diag_count = 0
        for diag_id, diag_facts in self._diag_to_facts.items():
            if q_facts & diag_facts:
                diag_count += 1
        discrim_score = min(diag_count / max(len(self._diagnoses), 1), 1.0) * self.DISCRIM_WEIGHT

        # 3. Group bonus: cùng group với chẩn đoán đang chạy
        group_score = 0.0
        if current_group and question.get("group") == current_group:
            group_score = self.GROUP_BONUS

        # 4. Proximity bonus: câu hỏi sắp fire rules gần nhất
        proximity_score = 0.0
        for nf in near_fire_rules[:3]:  # Top 3 rules gần nhất
            missing = set(nf["missing_facts"])
            overlap = len(q_facts & missing)
            if overlap > 0:
                # Rule có ít missing facts hơn → ưu tiên hơn
                proximity_score += overlap / nf["missing_count"]

        total = coverage_score + discrim_score + group_score + proximity_score
        return round(total, 3)

    def build_question_context(
        self,
        qid: str,
        near_fire_rules: list[dict],
        current_group: Optional[str],
    ) -> str:
        """
        Tạo context explanation ngắn để bot giải thích tại sao hỏi câu này.
        Dùng cho "short_explanation" trong bot message.
        """
        q = self._questions.get(qid)
        if not q:
            return ""

        purpose = q.get("purpose", "")
        if purpose:
            return purpose

        # Fallback: tạo từ near-fire rules
        if near_fire_rules:
            rule_names = [nf["rule"].name for nf in near_fire_rules[:2]]
            if rule_names:
                return f"Câu hỏi này giúp kiểm tra: {', '.join(rule_names)}"

        return ""

    def get_group_first_question(self, group_id: str) -> Optional[str]:
        """Tìm câu hỏi đầu tiên của một nhóm (dùng khi user chọn group từ NLU)."""
        group_to_root = {
            "power_startup": "Q02",
            "display": "Q09",
            "os_boot": "Q13",
            "network": "Q20",
            "audio_camera": "Q27",
            "peripherals": "Q32",
            "performance": "Q37",
            "storage": "Q36",
        }
        return group_to_root.get(group_id)
