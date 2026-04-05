"""
Diagnostic Session và Question Flow Manager.

DiagnosticSession: Quản lý một phiên chẩn đoán từ đầu đến cuối.
QuestionFlowManager: Xử lý luồng câu hỏi và câu trả lời.
KnowledgeBaseLoader: Load JSON knowledge base.
"""

from __future__ import annotations
import json
from typing import Optional

from .working_memory import WorkingMemory
from .rule_model import Rule, DiagnosisResult
from .forward_engine import ForwardChainingEngine


class QuestionFlowManager:
    """
    Quản lý luồng câu hỏi trong phiên chẩn đoán.

    Trách nhiệm:
    - Load questions từ JSON
    - Xác định câu hỏi tiếp theo dựa trên câu trả lời + WM
    - Xử lý các loại: single_choice, yes_no, multi_choice
    - Phát hiện dead-ends và infinite loops
    """

    def __init__(self, questions_data: list[dict]):
        self._questions: dict[str, dict] = {q["id"]: q for q in questions_data}
        self._question_visit_count: dict[str, int] = {}
        self.MAX_VISIT_PER_QUESTION = 3

    def get_question(self, qid: str) -> Optional[dict]:
        return self._questions.get(qid)

    def get_all_questions(self) -> dict[str, dict]:
        return self._questions

    def get_option(self, question: dict, value: str) -> Optional[dict]:
        for opt in question.get("options", []):
            if opt["value"] == value:
                return opt
        return None

    def process_answer(
        self,
        question_id: str,
        selected_values: list[str],
        engine: ForwardChainingEngine
    ) -> dict:
        """
        Xử lý câu trả lời của người dùng.

        Returns dict:
        {
          "new_facts": [...],
          "diagnoses_triggered": [...],
          "next_question_id": str | None,
          "suggest_action": str | None,
          "is_terminal": bool
        }
        """
        question = self.get_question(question_id)
        if not question:
            return self._error_result(f"Question {question_id} not found")

        self._question_visit_count[question_id] = \
            self._question_visit_count.get(question_id, 0) + 1

        if self._question_visit_count[question_id] > self.MAX_VISIT_PER_QUESTION:
            return self._fallback_result("Phiên chẩn đoán gặp lỗi. Vui lòng bắt đầu lại.")

        all_new_facts = []
        all_direct_diags = []
        suggest_action = None
        next_question_id = None

        for val in selected_values:
            opt = self.get_option(question, val)
            if not opt:
                continue

            facts = opt.get("adds_facts", [])
            if facts:
                new = engine.add_facts(facts, source=f"{question_id}:{val}")
                all_new_facts.extend(new)

            if "triggers_diagnosis" in opt:
                diag_id = opt["triggers_diagnosis"]
                diag = engine.get_diagnosis_details(diag_id)
                if diag:
                    cf = diag.get("default_cf", 0.85)
                    existing = engine._diagnosis_cf_map.get(diag_id, 0.0)
                    if existing > 0:
                        combined = DiagnosisResult.combine_cf(existing, cf)
                        engine._diagnosis_cf_map[diag_id] = combined
                    else:
                        engine._diagnosis_cf_map[diag_id] = cf

                    all_direct_diags.append(DiagnosisResult(
                        diagnosis_id=diag_id,
                        cf=cf,
                        triggered_by_question=f"{question_id}:{val}",
                        combined_cf=engine._diagnosis_cf_map[diag_id]
                    ))

            if "suggest_action" in opt:
                suggest_action = opt["suggest_action"]

            if "next" in opt:
                next_question_id = opt["next"]

        # Run forward chaining với facts mới
        rule_diagnoses = engine.run_until_stable()

        all_diagnoses = all_direct_diags + rule_diagnoses

        is_terminal = bool(all_diagnoses) and next_question_id is None
        if all_direct_diags and next_question_id is None:
            is_terminal = True

        return {
            "new_facts": all_new_facts,
            "diagnoses_triggered": [self._format_diag(d, engine) for d in all_diagnoses],
            "direct_diagnoses": [self._format_diag(d, engine) for d in all_direct_diags],
            "next_question_id": next_question_id,
            "suggest_action": suggest_action,
            "is_terminal": is_terminal,
            "current_wm": list(engine.wm.facts)
        }

    def _format_diag(self, diag_result: DiagnosisResult, engine: ForwardChainingEngine) -> dict:
        details = engine.get_diagnosis_details(diag_result.diagnosis_id) or {}
        return {
            "id": diag_result.diagnosis_id,
            "name": details.get("name", diag_result.diagnosis_id),
            "cf": round(diag_result.combined_cf or diag_result.cf, 3),
            "cf_percent": round((diag_result.combined_cf or diag_result.cf) * 100),
            "severity": details.get("severity", "UNKNOWN"),
            "user_fixable": details.get("user_fixable", True),
            "solution_steps": details.get("solution_steps", []),
            "needs_technician": details.get("needs_technician", False),
            "warning": details.get("warning"),
            "triggered_by": diag_result.triggered_by_rule or diag_result.triggered_by_question
        }

    def _error_result(self, msg: str) -> dict:
        return {"error": msg, "is_terminal": True}

    def _fallback_result(self, msg: str) -> dict:
        return {
            "is_terminal": True,
            "diagnoses_triggered": [{
                "id": "DIAG_FALLBACK",
                "name": "Không xác định được lỗi",
                "cf": 0.5,
                "cf_percent": 50,
                "severity": "UNKNOWN",
                "solution_steps": ["Mang máy đến kỹ thuật viên để kiểm tra trực tiếp"],
                "needs_technician": True,
                "message": msg
            }]
        }


class DiagnosticSession:
    """
    Quản lý một phiên chẩn đoán từ đầu đến cuối.

    Thêm các field mở rộng cho web chat:
    - expected_input_mode: text | single_choice | multi_choice
    - asked_question_ids: set các Q đã hỏi
    - current_group: nhóm lỗi đang chẩn đoán
    """

    ROOT_QUESTION = "Q01"

    def __init__(self, questions_data: list[dict], rules_data: list[dict], diagnoses_data: list[dict]):
        rules = [Rule.from_dict(r) for r in rules_data]
        diagnoses_db = {d["id"]: d for d in diagnoses_data}

        self.engine = ForwardChainingEngine(rules, diagnoses_db)
        self.flow = QuestionFlowManager(questions_data)

        self.current_question_id: str = self.ROOT_QUESTION
        self.history: list[dict] = []
        self.final_diagnoses: list[dict] = []
        self.is_complete: bool = False

        # Extended fields for web chat
        self.expected_input_mode: str = "single_choice"  # text | single_choice | multi_choice
        self.asked_question_ids: set[str] = set()
        self.current_group: Optional[str] = None
        self.pending_multi_facts: list[str] = []  # facts tạm trong multi_choice

    def get_current_question(self) -> Optional[dict]:
        """Lấy câu hỏi hiện tại đã enrich với input_mode."""
        q = self.flow.get_question(self.current_question_id)
        if q:
            self._set_input_mode(q)
        return q

    def _set_input_mode(self, question: dict):
        q_type = question.get("type", "single_choice")
        if q_type == "multi_choice":
            self.expected_input_mode = "multi_choice"
        elif q_type == "yes_no":
            self.expected_input_mode = "single_choice"
        else:
            self.expected_input_mode = "single_choice"

    def answer(self, selected_values: list[str] | str) -> dict:
        """
        Xử lý câu trả lời của người dùng.
        Hỗ trợ cả string đơn lẻ và list (multi_choice).
        """
        if isinstance(selected_values, str):
            selected_values = [selected_values]

        current_q = self.get_current_question()
        if not current_q:
            return {"error": "No active question", "session_complete": True}

        self.asked_question_ids.add(self.current_question_id)

        self.history.append({
            "question_id": self.current_question_id,
            "question_text": current_q.get("text", ""),
            "question_type": current_q.get("type", "single_choice"),
            "answers": selected_values,
            "answer_labels": self._get_answer_labels(current_q, selected_values)
        })

        result = self.flow.process_answer(
            self.current_question_id,
            selected_values,
            self.engine
        )

        if result.get("diagnoses_triggered"):
            self.final_diagnoses.extend(result["diagnoses_triggered"])

        # Dedup diagnoses
        self.final_diagnoses = self._dedup_diagnoses(self.final_diagnoses)

        if result.get("is_terminal") or not result.get("next_question_id"):
            self.is_complete = True
            self.current_question_id = None
        else:
            self.current_question_id = result["next_question_id"]

        # Update group from question
        if self.current_question_id:
            next_q = self.flow.get_question(self.current_question_id)
            if next_q and next_q.get("sets_group") is None:
                pass  # group stays
            group = self._detect_group_from_options(current_q, selected_values)
            if group:
                self.current_group = group

        next_question = self.get_current_question() if not self.is_complete else None

        return {
            **result,
            "session_complete": self.is_complete,
            "next_question": next_question,
            "input_mode": self.expected_input_mode if not self.is_complete else None,
            "current_group": self.current_group,
            "top_diagnoses": self.engine.get_top_diagnoses(3),
        }

    def _get_answer_labels(self, question: dict, values: list[str]) -> list[str]:
        labels = []
        for val in values:
            for opt in question.get("options", []):
                if opt["value"] == val:
                    labels.append(opt.get("label", val))
        return labels

    def _detect_group_from_options(self, question: dict, selected_values: list[str]) -> Optional[str]:
        for val in selected_values:
            for opt in question.get("options", []):
                if opt["value"] == val and "sets_group" in opt:
                    return opt["sets_group"]
        return None

    def _dedup_diagnoses(self, diags: list[dict]) -> list[dict]:
        """Giữ diagnoses với CF cao nhất cho mỗi ID."""
        seen: dict[str, dict] = {}
        for d in diags:
            did = d["id"]
            if did not in seen or d["cf"] > seen[did]["cf"]:
                seen[did] = d
        return sorted(seen.values(), key=lambda x: x["cf"], reverse=True)

    def get_explanation(self) -> dict:
        """Explanation Facility: giải thích toàn bộ quá trình suy luận."""
        reasoning_steps = []
        for step in self.history:
            q = self.flow.get_question(step["question_id"]) or {}
            reasoning_steps.append({
                "question_id": step["question_id"],
                "question": step["question_text"],
                "answers": step.get("answer_labels", step["answers"])
            })

        rule_trace = []
        for log in self.engine.fired_rules_trace:
            rule_trace.append({
                "rule": log["rule_id"],
                "rule_name": log["rule_name"],
                "added_facts": log["new_facts"],
                "triggered_diagnosis": log["triggers_diagnosis"],
                "certainty": log["cf"],
                "certainty_percent": round(log["cf"] * 100),
            })

        return {
            "question_path": reasoning_steps,
            "working_memory_final": sorted(self.engine.wm.facts),
            "rules_fired": rule_trace,
            "diagnoses": self.final_diagnoses,
            "top_diagnoses": self.engine.get_top_diagnoses(3),
            "near_fire_rules": [
                {
                    "rule_id": nf["rule"]["id"] if isinstance(nf["rule"], dict) else nf["rule"].id,
                    "missing_facts": nf["missing_facts"]
                }
                for nf in self.engine.get_near_fire_rules(5)[:5]
            ],
        }


class KnowledgeBaseLoader:
    """Load knowledge base từ JSON files."""

    def __init__(self, questions_path: str, rules_path: str):
        with open(questions_path, encoding="utf-8") as f:
            q_data = json.load(f)
        with open(rules_path, encoding="utf-8") as f:
            r_data = json.load(f)

        self.questions: list[dict] = q_data["questions"]
        self.groups: list[dict] = q_data.get("groups", [])
        self.rules: list[dict] = r_data["rules"]
        self.diagnoses: list[dict] = r_data["diagnoses"]
        self.metadata: dict = q_data.get("metadata", {})

    def create_session(self) -> DiagnosticSession:
        return DiagnosticSession(self.questions, self.rules, self.diagnoses)

    @property
    def stats(self) -> dict:
        return {
            "questions": len(self.questions),
            "rules": len(self.rules),
            "diagnoses": len(self.diagnoses),
            "groups": len(self.groups),
        }
