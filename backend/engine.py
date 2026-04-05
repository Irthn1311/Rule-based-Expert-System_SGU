"""
FORWARD CHAINING INFERENCE ENGINE — CHUẨN HÓA
Expert System: PC/Laptop Diagnostic
Môn: Công Nghệ Tri Thức — SGU

Architecture:
  - Working Memory: set of facts (strings)
  - Rule Base: list of Rule objects  
  - Inference Engine: Rete-inspired forward chaining
  - Session: manages Q&A flow + inference cycles
  - Explanation Facility: traces fired rules + reasoning path
"""

from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


# ─────────────────────────────────────────────────────────────
# 1. WORKING MEMORY
# ─────────────────────────────────────────────────────────────

class WorkingMemory:
    """
    Bộ nhớ làm việc (Working Memory / Fact Base).
    Lưu tất cả facts đã được xác lập trong phiên chẩn đoán.
    
    Trong hệ Forward Chaining chuẩn:
      - Facts là các symbols/strings (e.g. "no_power", "is_laptop")
      - Facts chỉ được ADD vào, không xóa (monotonic reasoning)
      - Các rule sẽ match facts trong WM để quyết định có fire không
    """

    def __init__(self):
        self._facts: set[str] = set()
        self._fact_history: list[tuple[str, str]] = []  # (fact, source_rule_or_question)

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


# ─────────────────────────────────────────────────────────────
# 2. RULE MODEL
# ─────────────────────────────────────────────────────────────

@dataclass
class Rule:
    """
    Đại diện một luật IF-THEN trong Rule Base.

    Cấu trúc:
      IF (all conditions) AND NOT (any not_conditions)
      THEN (add adds_facts to WM) AND/OR (trigger diagnosis)

    Certainty Factor (CF):
      - 0.0 → 1.0
      - Mô hình tương tự MYCIN CF
      - Khi nhiều rules dẫn đến cùng diagnosis:
          CF_combined = CF1 + CF2*(1-CF1)

    Priority (1–5):
      - Conflict Resolution: rule priority cao hơn được fire trước
      - Specificity: rule nhiều điều kiện hơn được ưu tiên (tự động tính)
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
        - Thêm facts mới vào WM (THEN phần thêm fact)
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


# ─────────────────────────────────────────────────────────────
# 3. DIAGNOSIS RESULT
# ─────────────────────────────────────────────────────────────

@dataclass
class DiagnosisResult:
    """Một kết quả chẩn đoán được kích hoạt trong phiên làm việc."""
    diagnosis_id: str
    cf: float
    triggered_by_rule: Optional[str] = None  # rule ID đã fire
    triggered_by_question: Optional[str] = None  # question ID nếu direct trigger
    combined_cf: Optional[float] = None  # CF sau khi combine

    @staticmethod
    def combine_cf(cf1: float, cf2: float) -> float:
        """
        Combine 2 CF theo công thức MYCIN:
          CF_combined = CF1 + CF2*(1-CF1)
        """
        return cf1 + cf2 * (1 - cf1)


# ─────────────────────────────────────────────────────────────
# 4. INFERENCE ENGINE — FORWARD CHAINING
# ─────────────────────────────────────────────────────────────

class ForwardChainingEngine:
    """
    Inference Engine theo chiến lược Forward Chaining.

    Thuật toán:
      1. MATCH: Tìm tất cả rules có thể kích hoạt (Conflict Set)
      2. SELECT: Chọn rule tốt nhất theo Conflict Resolution Strategy
      3. FIRE: Kích hoạt rule → thêm facts + trigger diagnosis
      4. Lặp lại đến khi Conflict Set rỗng (fixed point)

    Conflict Resolution Strategy:
      Priority 1: rule.priority cao hơn
      Priority 2: rule.specificity cao hơn (nhiều điều kiện hơn = specific hơn)
      Priority 3: rule.cf cao hơn
      Priority 4: thứ tự định nghĩa trong rule base (recency)
    """

    def __init__(self, rules: list[Rule], diagnoses_db: dict):
        self.rules = rules
        self.diagnoses_db = diagnoses_db  # {id: diagnosis_dict}
        self.wm = WorkingMemory()
        self._diagnosis_cf_map: dict[str, float] = {}  # track combined CF per diagnosis
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

        # Sort: primary=priority DESC, secondary=specificity DESC, tertiary=cf DESC
        conflict_set.sort(
            key=lambda r: (r.priority, r.specificity, r.cf),
            reverse=True
        )
        return conflict_set

    def _fire_rule(self, rule: Rule) -> list[DiagnosisResult]:
        """
        FIRE phase: kích hoạt một rule.
        Return list DiagnosisResult (thường 0 hoặc 1 phần tử).
        """
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
            # Combine CF nếu diagnosis này đã được trigger trước đó
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

        # SELECT: chọn rule đầu tiên (đã sort theo priority)
        best_rule = conflict_set[0]
        diagnoses = self._fire_rule(best_rule)

        return True, diagnoses

    def run_until_stable(self) -> list[DiagnosisResult]:
        """
        Chạy forward chaining đến điểm cố định (fixed point).
        
        Fixed point: khi không còn rule nào có thể kích hoạt trong WM hiện tại.
        Đây là điều kiện kết thúc chuẩn của forward chaining.

        Safety: giới hạn MAX_ITERATIONS để tránh infinite loop.
        """
        all_diagnoses: list[DiagnosisResult] = []
        MAX_ITERATIONS = 100
        iteration = 0

        while iteration < MAX_ITERATIONS:
            fired, new_diags = self.run_one_cycle()
            all_diagnoses.extend(new_diags)

            if not fired:
                break  # Fixed point reached

            iteration += 1

        return all_diagnoses

    @property
    def fired_rules_trace(self) -> list[dict]:
        """Trace của tất cả rules đã fire — dùng cho Explanation Facility."""
        return list(self._fired_rules_log)

    def get_diagnosis_details(self, diag_id: str) -> Optional[dict]:
        return self.diagnoses_db.get(diag_id)

    def reset(self):
        """Reset engine cho session mới."""
        self.wm = WorkingMemory()
        self._diagnosis_cf_map = {}
        self._fired_rules_log = []
        for rule in self.rules:
            rule.reset()


# ─────────────────────────────────────────────────────────────
# 5. QUESTION FLOW MANAGER
# ─────────────────────────────────────────────────────────────

class QuestionFlowManager:
    """
    Quản lý luồng câu hỏi trong phiên chẩn đoán.

    Trách nhiệm:
    - Load questions từ JSON
    - Xác định câu hỏi tiếp theo dựa trên câu trả lời + WM
    - Xử lý các loại câu hỏi: single_choice, yes_no, multi_choice
    - Phát hiện dead-ends và infinite loops (an toàn)
    """

    def __init__(self, questions_data: list[dict]):
        self._questions: dict[str, dict] = {q["id"]: q for q in questions_data}
        self._question_visit_count: dict[str, int] = {}
        self.MAX_VISIT_PER_QUESTION = 3  # Chống loop

    def get_question(self, qid: str) -> Optional[dict]:
        return self._questions.get(qid)

    def get_option(self, question: dict, value: str) -> Optional[dict]:
        for opt in question.get("options", []):
            if opt["value"] == value:
                return opt
        return None

    def process_answer(
        self,
        question_id: str,
        selected_values: list[str],  # list để support multi_choice
        engine: ForwardChainingEngine
    ) -> dict:
        """
        Xử lý câu trả lời của người dùng.

        Returns dict:
        {
          "new_facts": [...],
          "diagnoses_triggered": [...],   # list DiagnosisResult
          "next_question_id": str | None,
          "suggest_action": str | None,
          "is_terminal": bool             # True = phiên kết thúc
        }
        """
        question = self.get_question(question_id)
        if not question:
            return self._error_result(f"Question {question_id} not found")

        # Track visits để phát hiện loop
        self._question_visit_count[question_id] = \
            self._question_visit_count.get(question_id, 0) + 1

        if self._question_visit_count[question_id] > self.MAX_VISIT_PER_QUESTION:
            return self._fallback_result("Phiên chẩn đoán gặp lỗi vòng lặp. Vui lòng bắt đầu lại.")

        # Tổng hợp facts + diagnoses từ tất cả options được chọn
        all_new_facts = []
        all_direct_diags = []
        suggest_action = None
        next_question_id = None

        for val in selected_values:
            opt = self.get_option(question, val)
            if not opt:
                continue

            # Thêm facts
            facts = opt.get("adds_facts", [])
            if facts:
                new = engine.add_facts(facts, source=f"{question_id}:{val}")
                all_new_facts.extend(new)

            # Direct diagnosis trigger
            if "triggers_diagnosis" in opt:
                diag_id = opt["triggers_diagnosis"]
                diag = engine.get_diagnosis_details(diag_id)
                if diag:
                    cf = diag.get("default_cf", 0.85)
                    all_direct_diags.append(DiagnosisResult(
                        diagnosis_id=diag_id,
                        cf=cf,
                        triggered_by_question=f"{question_id}:{val}"
                    ))

            # Suggest action
            if "suggest_action" in opt:
                suggest_action = opt["suggest_action"]

            # Next question (lấy từ option cuối cùng có next)
            if "next" in opt:
                next_question_id = opt["next"]

        # Run inference engine để tìm thêm diagnoses từ rules
        rule_diagnoses = engine.run_until_stable()

        # Merge diagnoses
        all_diagnoses = all_direct_diags + rule_diagnoses

        # Xác định terminal state
        is_terminal = bool(all_diagnoses) and next_question_id is None

        # Nếu có diagnoses nhưng cũng có next → vẫn tiếp tục hỏi (confirmatory)
        # Trừ khi đây là direct terminal trigger
        if all_direct_diags and next_question_id is None:
            is_terminal = True

        return {
            "new_facts": all_new_facts,
            "diagnoses_triggered": [self._format_diag(d, engine) for d in all_diagnoses],
            "next_question_id": next_question_id,
            "suggest_action": suggest_action,
            "is_terminal": is_terminal,
            "current_wm": list(engine.wm.facts)
        }

    def _format_diag(self, diag_result: DiagnosisResult, engine: ForwardChainingEngine) -> dict:
        """Format diagnosis result với đầy đủ thông tin."""
        details = engine.get_diagnosis_details(diag_result.diagnosis_id) or {}
        return {
            "id": diag_result.diagnosis_id,
            "name": details.get("name", diag_result.diagnosis_id),
            "cf": round(diag_result.combined_cf or diag_result.cf, 3),
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
                "severity": "UNKNOWN",
                "solution_steps": ["Mang máy đến kỹ thuật viên để kiểm tra trực tiếp"],
                "needs_technician": True,
                "message": msg
            }]
        }


# ─────────────────────────────────────────────────────────────
# 6. SESSION MANAGER
# ─────────────────────────────────────────────────────────────

class DiagnosticSession:
    """
    Quản lý một phiên chẩn đoán từ đầu đến cuối.

    Luồng:
    1. Bắt đầu từ Q01 (root question)
    2. Nhận câu trả lời → xử lý → quyết định Q tiếp theo
    3. Kết thúc khi: có diagnosis mà không có nextQ
    4. Trả về explanation (trace) để giải thích cho người dùng
    """

    ROOT_QUESTION = "Q01"

    def __init__(self, questions_data: list[dict], rules_data: list[dict], diagnoses_data: list[dict]):
        # Build rules from data
        rules = [Rule.from_dict(r) for r in rules_data]

        # Build diagnoses lookup
        diagnoses_db = {d["id"]: d for d in diagnoses_data}

        self.engine = ForwardChainingEngine(rules, diagnoses_db)
        self.flow = QuestionFlowManager(questions_data)

        self.current_question_id: str = self.ROOT_QUESTION
        self.history: list[dict] = []  # Lịch sử Q&A
        self.final_diagnoses: list[dict] = []
        self.is_complete: bool = False

    def get_current_question(self) -> Optional[dict]:
        """Lấy câu hỏi hiện tại để hiển thị cho người dùng."""
        return self.flow.get_question(self.current_question_id)

    def answer(self, selected_values: list[str] | str) -> dict:
        """
        Xử lý câu trả lời của người dùng.
        
        Args:
            selected_values: Có thể là string (single) hoặc list (multi_choice)
        
        Returns: Dict với thông tin về session state
        """
        if isinstance(selected_values, str):
            selected_values = [selected_values]

        # Lưu vào history
        self.history.append({
            "question_id": self.current_question_id,
            "question_text": self.get_current_question().get("text", ""),
            "answers": selected_values
        })

        # Xử lý câu trả lời
        result = self.flow.process_answer(
            self.current_question_id,
            selected_values,
            self.engine
        )

        # Cập nhật trạng thái session
        if result.get("diagnoses_triggered"):
            self.final_diagnoses.extend(result["diagnoses_triggered"])

        if result.get("is_terminal") or not result.get("next_question_id"):
            self.is_complete = True
            self.current_question_id = None
        else:
            self.current_question_id = result["next_question_id"]

        return {
            **result,
            "session_complete": self.is_complete,
            "next_question": self.get_current_question() if not self.is_complete else None
        }

    def get_explanation(self) -> dict:
        """
        Explanation Facility: giải thích logic chẩn đoán cho người dùng.

        Quan trọng cho học thuật — thể hiện hệ chuyên gia có khả năng
        giải thích "tại sao" đưa ra kết luận đó.
        """
        # Build reasoning chain từ Q&A history
        reasoning_steps = []
        for step in self.history:
            q = self.flow.get_question(step["question_id"]) or {}
            answers_detail = []
            for val in step["answers"]:
                for opt in q.get("options", []):
                    if opt["value"] == val:
                        answers_detail.append({
                            "value": val,
                            "label": opt.get("label", val),
                            "facts_added": opt.get("adds_facts", [])
                        })
            reasoning_steps.append({
                "question": step["question_text"],
                "answers": answers_detail
            })

        # Build rule trace
        rule_trace = []
        for log in self.engine.fired_rules_trace:
            rule_trace.append({
                "rule": log["rule_id"],
                "rule_name": log["rule_name"],
                "added_facts": log["new_facts"],
                "triggered_diagnosis": log["triggers_diagnosis"],
                "certainty": log["cf"]
            })

        # Tổng hợp
        return {
            "question_path": reasoning_steps,
            "working_memory_final": sorted(self.engine.wm.facts),
            "rules_fired": rule_trace,
            "diagnoses": self.final_diagnoses,
            "explanation_text": self._build_natural_language_explanation()
        }

    def _build_natural_language_explanation(self) -> list[str]:
        """Giải thích bằng ngôn ngữ tự nhiên (tiếng Việt)."""
        lines = []
        lines.append("📋 QUÁ TRÌNH CHẨN ĐOÁN:")
        lines.append("")

        for i, step in enumerate(self.history, 1):
            q = self.flow.get_question(step["question_id"]) or {}
            q_text = q.get("text", step["question_id"])
            answers = []
            for val in step["answers"]:
                for opt in q.get("options", []):
                    if opt["value"] == val:
                        answers.append(opt.get("label", val))
            lines.append(f"  {i}. Hỏi: {q_text}")
            lines.append(f"     → Trả lời: {', '.join(answers)}")

        lines.append("")
        lines.append("🔍 CÁC LUẬT ĐÃ ĐƯỢC KÍCH HOẠT:")
        for log in self.engine.fired_rules_trace:
            if log["new_facts"]:
                lines.append(f"  - {log['rule_name']}: thêm facts {log['new_facts']}")
            if log["triggers_diagnosis"]:
                lines.append(f"  - {log['rule_name']}: → KẾT LUẬN: {log['triggers_diagnosis']} (CF={log['cf']})")

        lines.append("")
        lines.append("✅ KẾT QUẢ CHẨN ĐOÁN:")
        for diag in self.final_diagnoses:
            lines.append(f"  🔴 {diag.get('name', diag['id'])} (Độ tin cậy: {diag['cf']*100:.0f}%)")
            lines.append(f"     Mức độ: {diag.get('severity', 'UNKNOWN')}")
            if diag.get("solution_steps"):
                lines.append(f"     Hướng xử lý:")
                for step in diag["solution_steps"]:
                    lines.append(f"       • {step}")

        return lines


# ─────────────────────────────────────────────────────────────
# 7. KNOWLEDGE BASE LOADER
# ─────────────────────────────────────────────────────────────

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

    def create_session(self) -> DiagnosticSession:
        return DiagnosticSession(self.questions, self.rules, self.diagnoses)


# ─────────────────────────────────────────────────────────────
# 8. FastAPI REST BACKEND
# ─────────────────────────────────────────────────────────────

"""
Installation: pip install fastapi uvicorn python-multipart

Run: uvicorn engine:app --reload --port 8000

Endpoints:
  POST /api/session/start        → bắt đầu phiên mới
  POST /api/session/{id}/answer  → gửi câu trả lời
  GET  /api/session/{id}/explain → lấy explanation
  GET  /api/knowledge/questions  → danh sách câu hỏi
  GET  /api/knowledge/diagnoses  → danh sách diagnoses
"""

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uuid

    app = FastAPI(
        title="PC Diagnostic Expert System",
        description="Rule-based Expert System cho chẩn đoán lỗi máy tính Windows/PC/Laptop",
        version="1.1.0"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global KB loader và sessions store
    kb: Optional[KnowledgeBaseLoader] = None
    active_sessions: dict[str, DiagnosticSession] = {}

    @app.on_event("startup")
    async def startup():
        global kb
        kb = KnowledgeBaseLoader(
            questions_path="knowledge_base/06_questions.json",
            rules_path="knowledge_base/07_rules_and_diagnoses.json"
        )
        print(f"✅ Knowledge Base loaded: {len(kb.questions)} questions, {len(kb.rules)} rules, {len(kb.diagnoses)} diagnoses")

    # ── Request/Response Models ──

    class StartSessionResponse(BaseModel):
        session_id: str
        first_question: dict

    class AnswerRequest(BaseModel):
        answers: list[str]  # list để hỗ trợ multi_choice

    class AnswerResponse(BaseModel):
        session_id: str
        session_complete: bool
        next_question: Optional[dict]
        new_facts: list[str]
        diagnoses_triggered: list[dict]
        suggest_action: Optional[str]
        current_wm: list[str]

    # ── Endpoints ──

    @app.post("/api/session/start", response_model=StartSessionResponse)
    async def start_session():
        """Bắt đầu một phiên chẩn đoán mới."""
        if not kb:
            raise HTTPException(500, "Knowledge Base not loaded")

        session_id = str(uuid.uuid4())
        session = kb.create_session()
        active_sessions[session_id] = session

        first_q = session.get_current_question()
        if not first_q:
            raise HTTPException(500, "Could not load root question")

        return StartSessionResponse(
            session_id=session_id,
            first_question=first_q
        )

    @app.post("/api/session/{session_id}/answer", response_model=AnswerResponse)
    async def submit_answer(session_id: str, req: AnswerRequest):
        """Gửi câu trả lời cho câu hỏi hiện tại."""
        session = active_sessions.get(session_id)
        if not session:
            raise HTTPException(404, f"Session {session_id} not found")
        if session.is_complete:
            raise HTTPException(400, "Session already complete")

        result = session.answer(req.answers)

        return AnswerResponse(
            session_id=session_id,
            session_complete=result["session_complete"],
            next_question=result.get("next_question"),
            new_facts=result.get("new_facts", []),
            diagnoses_triggered=result.get("diagnoses_triggered", []),
            suggest_action=result.get("suggest_action"),
            current_wm=result.get("current_wm", [])
        )

    @app.get("/api/session/{session_id}/explain")
    async def get_explanation(session_id: str):
        """Lấy giải thích đầy đủ của phiên chẩn đoán."""
        session = active_sessions.get(session_id)
        if not session:
            raise HTTPException(404, f"Session {session_id} not found")
        return session.get_explanation()

    @app.get("/api/knowledge/questions")
    async def get_questions():
        if not kb:
            raise HTTPException(500, "KB not loaded")
        return {"questions": kb.questions, "count": len(kb.questions)}

    @app.get("/api/knowledge/diagnoses")
    async def get_diagnoses():
        if not kb:
            raise HTTPException(500, "KB not loaded")
        return {"diagnoses": kb.diagnoses, "count": len(kb.diagnoses)}

    @app.get("/api/knowledge/groups")
    async def get_groups():
        if not kb:
            raise HTTPException(500, "KB not loaded")
        return {"groups": kb.groups}

    @app.get("/api/health")
    async def health():
        if not kb:
            return {"status": "degraded", "reason": "KB not loaded"}
        return {
            "status": "ok",
            "questions": len(kb.questions),
            "rules": len(kb.rules),
            "diagnoses": len(kb.diagnoses),
            "active_sessions": len(active_sessions)
        }

except ImportError:
    # FastAPI không được cài — chỉ dùng engine core
    app = None


# ─────────────────────────────────────────────────────────────
# 9. TEST RUNNER
# ─────────────────────────────────────────────────────────────

def run_test_case(tc: dict, kb: KnowledgeBaseLoader) -> dict:
    """
    Chạy một test case.
    
    tc format:
    {
      "name": "TC001",
      "answer_path": [("Q01","A"), ("Q02","A"), ("Q03","A"), ("Q05","A")],
      "expected_diagnosis": "DIAG_PWR_01",
      "expected_cf_min": 0.80
    }
    """
    session = kb.create_session()
    result = {"name": tc["name"], "passed": False, "details": {}}

    for question_id, answer_value in tc["answer_path"]:
        if session.is_complete:
            break

        current_q = session.get_current_question()
        if not current_q:
            result["details"]["error"] = "Session ended prematurely"
            return result

        if current_q["id"] != question_id:
            result["details"]["error"] = (
                f"Expected question {question_id}, got {current_q['id']}"
            )
            return result

        session.answer([answer_value])

    # Kiểm tra kết quả
    found_ids = [d["id"] for d in session.final_diagnoses]
    expected = tc["expected_diagnosis"]

    result["found_diagnoses"] = found_ids
    result["expected"] = expected
    result["passed"] = expected in found_ids

    if result["passed"] and "expected_cf_min" in tc:
        for d in session.final_diagnoses:
            if d["id"] == expected:
                result["actual_cf"] = d["cf"]
                result["cf_ok"] = d["cf"] >= tc["expected_cf_min"]
                if not result["cf_ok"]:
                    result["passed"] = False
                break

    if not result["passed"]:
        result["explanation"] = session.get_explanation()

    return result


TEST_CASES = [
    {
        "name": "TC01 — Adapter Laptop hỏng",
        "description": "Laptop không bật, đèn sạc không sáng",
        "answer_path": [("Q01","A"),("Q02","A"),("Q03","A"),("Q05","A")],
        "expected_diagnosis": "DIAG_PWR_01",
        "expected_cf_min": 0.85
    },
    {
        "name": "TC02 — Pin laptop chai",
        "description": "Chỉ chạy khi cắm điện",
        "answer_path": [("Q01","A"),("Q02","A"),("Q03","A"),("Q05","C")],
        "expected_diagnosis": "DIAG_PWR_02",
        "expected_cf_min": 0.80
    },
    {
        "name": "TC03 — RAM gây POST fail (beep nhiều)",
        "description": "Nhiều tiếng beep + không lên màn hình",
        "answer_path": [("Q01","A"),("Q02","B"),("Q04","C"),("Q05","A")],
        "expected_diagnosis": "DIAG_PWR_05",
        "expected_cf_min": 0.80
    },
    {
        "name": "TC04 — Cáp màn hình lỏng",
        "description": "Màn đen + màn ngoài OK + không sọc",
        "answer_path": [("Q01","B"),("Q09","A"),("Q10","A"),("Q12","B")],
        "expected_diagnosis": "DIAG_DSP_03",
        "expected_cf_min": 0.75
    },
    {
        "name": "TC05 — Driver GPU lỗi sau Update",
        "description": "Màn hình nhấp nháy sau khi cập nhật driver",
        "answer_path": [("Q01","B"),("Q09","B"),("Q11","A")],
        "expected_diagnosis": "DIAG_DSP_02",
        "expected_cf_min": 0.85
    },
    {
        "name": "TC06 — Màn hình vỡ LCD sau va đập",
        "description": "Sọc ngang + máy bị rơi",
        "answer_path": [("Q01","B"),("Q09","C"),("Q11","C")],
        "expected_diagnosis": "DIAG_DSP_03",
        "expected_cf_min": 0.90
    },
    {
        "name": "TC07 — Backlight hỏng",
        "description": "Nhìn nghiêng thấy hình mờ",
        "answer_path": [("Q01","B"),("Q09","A"),("Q10","C"),("Q11","D"),("Q12","B")],
        "expected_diagnosis": "DIAG_DSP_03",
        "expected_cf_min": 0.80
    },
    {
        "name": "TC08 — BSOD Memory code → RAM lỗi",
        "description": "BSOD với MEMORY_MANAGEMENT, MemTest fail",
        "answer_path": [("Q01","C"),("Q13","A"),("Q14","A"),("Q19","A")],
        "expected_diagnosis": "DIAG_OS_03",
        "expected_cf_min": 0.85
    },
    {
        "name": "TC09 — BSOD Driver code → Software conflict",
        "description": "BSOD driver error, vừa cài phần mềm",
        "answer_path": [("Q01","C"),("Q13","A"),("Q14","B"),("Q17","A")],
        "expected_diagnosis": "DIAG_OS_02",
        "expected_cf_min": 0.85
    },
    {
        "name": "TC10 — Boot loop sau Windows Update",
        "description": "Khởi động lặp lại sau update",
        "answer_path": [("Q01","C"),("Q13","B"),("Q17","B")],
        "expected_diagnosis": "DIAG_OS_05",
        "expected_cf_min": 0.85
    },
    {
        "name": "TC11 — Dừng logo, Safe Mode OK → Driver",
        "description": "Stuck at logo, vào Safe Mode được",
        "answer_path": [("Q01","C"),("Q13","C"),("Q16","A"),("Q17","A")],
        "expected_diagnosis": "DIAG_OS_02",
        "expected_cf_min": 0.80
    },
    {
        "name": "TC12 — Dừng logo, Safe Mode fail → OS corrupt",
        "description": "Stuck at logo, Safe Mode cũng lỗi",
        "answer_path": [("Q01","C"),("Q13","C"),("Q16","B")],
        "expected_diagnosis": "DIAG_OS_01",
        "expected_cf_min": 0.80
    },
    {
        "name": "TC13 — BSOD disk + CHKDSK → HDD BSOD",
        "description": "BSOD NTFS + CHKDSK bad sectors",
        "answer_path": [("Q01","C"),("Q13","A"),("Q14","C"),("Q19","B")],
        "expected_diagnosis": "DIAG_STR_02",
        "expected_cf_min": 0.85
    },
    {
        "name": "TC14 — MBR hỏng",
        "description": "Windows không load, Safe Mode fail, không thay đổi gần đây",
        "answer_path": [("Q01","C"),("Q13","E"),("Q16","B")],
        "expected_diagnosis": "DIAG_OS_06",
        "expected_cf_min": 0.80
    },
    {
        "name": "TC15 — Wi-Fi adapter hardware hỏng",
        "description": "Không thấy Wi-Fi, adapter không trong DM",
        "answer_path": [("Q01","D"),("Q20","A"),("Q25","A")],
        "expected_diagnosis": "DIAG_NET_02",
        "expected_cf_min": 0.85
    },
    {
        "name": "TC16 — Driver Wi-Fi lỗi",
        "description": "Không thấy Wi-Fi, adapter OK nhưng chấm than",
        "answer_path": [("Q01","D"),("Q20","A"),("Q25","B")],
        "expected_diagnosis": "DIAG_NET_01",
        "expected_cf_min": 0.80
    },
    {
        "name": "TC17 — Router/ISP lỗi",
        "description": "Tất cả thiết bị không vào được Internet",
        "answer_path": [("Q01","D"),("Q20","B"),("Q21","B"),("Q22","B")],
        "expected_diagnosis": "DIAG_NET_04",
        "expected_cf_min": 0.85
    },
    {
        "name": "TC18 — DNS lỗi",
        "description": "Kết nối OK nhưng DNS_PROBE_FINISHED",
        "answer_path": [("Q01","D"),("Q20","B"),("Q22","A"),("Q23","A")],
        "expected_diagnosis": "DIAG_NET_03",
        "expected_cf_min": 0.85
    },
    {
        "name": "TC19 — IP Conflict",
        "description": "ERR_NETWORK_CHANGED",
        "answer_path": [("Q01","D"),("Q20","B"),("Q22","A"),("Q23","C")],
        "expected_diagnosis": "DIAG_NET_06",
        "expected_cf_min": 0.85
    },
    {
        "name": "TC20 — Network Stack TCP/IP hỏng",
        "description": "Cả WiFi lẫn LAN đều không có Internet, máy lệnh không lấy được IP",
        "answer_path": [("Q01","D"),("Q20","B"),("Q21","B"),("Q22","A"),("Q26","B")],
        "expected_diagnosis": "DIAG_NET_05",
        "expected_cf_min": 0.85
    },
    {
        "name": "TC21 — Driver âm thanh lỗi",
        "description": "Không âm thanh, driver chấm than",
        "answer_path": [("Q01","E"),("Q27","A"),("Q28","B")],
        "expected_diagnosis": "DIAG_AUD_01",
        "expected_cf_min": 0.85
    },
    {
        "name": "TC22 — Âm thanh bị muted",
        "description": "Không âm thanh, volume ở 0",
        "answer_path": [("Q01","E"),("Q27","A"),("Q28","C")],
        "expected_diagnosis": "DIAG_AUD_02",
        "expected_cf_min": 0.80
    },
    {
        "name": "TC23 — Camera Privacy bị chặn",
        "description": "Camera bị chặn trong privacy settings",
        "answer_path": [("Q01","E"),("Q27","C"),("Q30","A")],
        "expected_diagnosis": "DIAG_CAM_01",
        "expected_cf_min": 0.90
    },
    {
        "name": "TC24 — Cổng USB vật lý hỏng",
        "description": "1 cổng lỗi, thiết bị OK ở máy khác",
        "answer_path": [("Q01","F"),("Q32","A"),("Q33","A"),("Q34","A")],
        "expected_diagnosis": "DIAG_PER_01",
        "expected_cf_min": 0.85
    },
    {
        "name": "TC25 — USB Controller hỏng",
        "description": "Tất cả cổng USB đều không nhận",
        "answer_path": [("Q01","F"),("Q32","A"),("Q33","C")],
        "expected_diagnosis": "DIAG_PER_02",
        "expected_cf_min": 0.80
    },
    {
        "name": "TC26 — Thiết bị USB hỏng",
        "description": "USB lỗi cả ở máy khác",
        "answer_path": [("Q01","F"),("Q32","A"),("Q33","A"),("Q34","B")],
        "expected_diagnosis": "DIAG_PER_03",
        "expected_cf_min": 0.85
    },
    {
        "name": "TC27 — Thermal Throttling",
        "description": "Nóng, quạt ồn, HWMonitor >90°C",
        "answer_path": [("Q01","G"),("Q37","A"),("Q38","A"),("Q40","D")],
        "expected_diagnosis": "DIAG_PERF_01",
        "expected_cf_min": 0.85
    },
    {
        "name": "TC28 — Malware gây chậm",
        "description": "CPU cao, phần mềm diệt virus phát hiện mối đe dọa",
        "answer_path": [("Q01","G"),("Q37","A"),("Q38","A"),("Q39","C")],
        "expected_diagnosis": "DIAG_PERF_02",
        "expected_cf_min": 0.80
    },
    {
        "name": "TC29 — HDD cơ học hỏng (urgent)",
        "description": "Tiếng click lách cách từ HDD",
        "answer_path": [("Q01","H"),("Q36","B")],
        "expected_diagnosis": "DIAG_STR_02",
        "expected_cf_min": 0.85
    },
    {
        "name": "TC30 — Ổ đĩa C đầy",
        "description": "Ổ C gần đầy, máy chạy chậm",
        "answer_path": [("Q01","H"),("Q36","A")],
        "expected_diagnosis": "DIAG_STR_01",
        "expected_cf_min": 0.85
    }
]


if __name__ == "__main__":
    import os

    kb_path_q = os.path.join("knowledge_base", "06_questions.json")
    kb_path_r = os.path.join("knowledge_base", "07_rules_and_diagnoses.json")

    if not os.path.exists(kb_path_q):
        print(f"❌ File not found: {kb_path_q}")
        print("Chạy từ thư mục project/")
        exit(1)

    kb = KnowledgeBaseLoader(kb_path_q, kb_path_r)
    print(f"✅ Loaded KB: {len(kb.questions)} Q, {len(kb.rules)} rules, {len(kb.diagnoses)} D")
    print()

    # Chạy test cases
    passed = 0
    failed = 0

    for tc in TEST_CASES:
        result = run_test_case(tc, kb)
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        print(f"{status} | {tc['name']}")

        if not result["passed"]:
            failed += 1
            print(f"       Expected: {result.get('expected')}")
            print(f"       Found:    {result.get('found_diagnoses', [])}")
        else:
            passed += 1
            if "actual_cf" in result:
                print(f"       CF: {result['actual_cf']:.2f} ({'✅' if result.get('cf_ok') else '⚠️ LOW'})")

    print()
    print(f"═══ KẾT QUẢ: {passed}/{len(TEST_CASES)} passed ({'%.0f' % (passed/len(TEST_CASES)*100)}% accuracy) ═══")
