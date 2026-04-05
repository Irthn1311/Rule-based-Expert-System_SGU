# PHẦN 8+9: Kiểm tra chất lượng + Dữ liệu triển khai (FINAL v2.0 — 50Q, 103R, 50D)


---

## PHẦN 8: KIỂM TRA CHẤT LƯỢNG

### 8.1 Kiểm tra luật trùng lặp

| Cặp luật nghi ngờ trùng | Phân tích | Kết quả |
|--------------------------|-----------|---------|
| R017 vs R018 (cả 2 từ display_hardware_issue) | R017: không có screen_lines; R018: có screen_lines — KHÁC NHAU | ✅ Không trùng |
| R030 vs R031 (cả 2 từ ram_related_bsod) | R030: NOT recent_driver; R031: HAS recent_driver — KHÁC NHAU | ✅ Không trùng |
| R052 vs R056 (cả 2 từ wifi_connected_no_internet) | R052: other_devices OK; R056: other_devices FAIL — KHÁC NHAU | ✅ Không trùng |
| R066 vs R067 vs R068 (cả 3 từ no_sound) | R066: audio_device_missing; R067: driver_yellow; R068: neither — KHÁC NHAU | ✅ Không trùng |
| R109 vs R110 (cả 2 liên quan file_corruption) | R109: file+CHKDSK→STR_04; R110: file+bad_sectors→STR_02 — khác diagnosis | ✅ Không trùng |

**→ Không phát hiện luật trùng lặp thực sự**

### 8.2 Phát hiện xung đột luật

| Tình huống xung đột | Cơ chế giải quyết |
|--------------------|--------------------|
| RAM BSOD (R030) vs Driver-caused RAM BSOD (R031) | R031 thêm điều kiện `recent_driver_update` → kích hoạt R031 trước (priority cao hơn) |
| Cáp màn hình (R017) vs Panel hỏng (R018) | Điều kiện mutually exclusive: NOT screen_lines vs HAS screen_lines |
| DNS lỗi (R053) vs IP conflict (R054) | Cần cả hai facts: dns_error_message vs ip_conflict — không thể cùng xảy ra |
| Thermal throttling (R092) vs RAM (R097) | R092 cần thermal_throttling fact; R097 cần NOT thermal_throttling |

**→ Không phát hiện xung đột luật nghiêm trọng**

### 8.3 Phát hiện vùng mù (Blind Spots)

| Vùng mù | Mô tả | Giải pháp đề xuất |
|---------|-------|------------------|
| **Laptop tắt đột ngột** | Không có câu hỏi/luật cho "máy tắt khi đang dùng" — có thể là quá nhiệt hoặc pin | Thêm option vào Q37 hoặc Q02 |
| **BIOS không nhận ổ đĩa** | Trường hợp BIOS không nhận drive chưa được cover rõ | Thêm câu hỏi về BIOS detection |
| **Display chỉ lỗi ở góc màn hình** | Chưa có luật cho partial screen display issues | Thêm option vào Q09 |
| **Lỗi update drivers cụ thể** | GPU/Audio/Network driver conflict chưa phân biệt rõ | Thêm câu hỏi "driver loại nào?" |
| **Multiple simultaneous issues** | Khi máy có cả lỗi mạng + âm thanh — chưa handle đồng thời | Cho phép restart từ Q01 sau mỗi diagnosis |
| **Laptop không nhận dock/USB-C hub** | Chưa có nhánh cho USB-C/Thunderbolt issues | Thêm vào peripherals branch |

### 8.4 Phát hiện nhánh quá yếu

| Nhánh yếu | Vấn đề | Cải thiện |
|-----------|--------|-----------|
| **Q07 (rút ngoại vi)** | Nếu trả lời A (máy bật được) → kết luận "peripheral_causing_issue" không đủ specific | Thêm câu hỏi "ngoại vi nào là thủ phạm?" |
| **DIAG_NET_06 (IP conflict)** | Chỉ 2 rules dẫn vào — coverage thấp | Thêm Q26 mandatory trong branch này |
| **Bluetooth (Q32-D)** | Chỉ 1 rule → DIAG_PER_04, không phân nhánh tiếp | Thêm phân biệt: driver lỗi, adapter, paired device |
| **Touchpad (Q32-F)** | Chỉ suggest_action, không có formal diagnosis | Thêm luật: Fn+hotkey fix vs driver fix |

### 8.5 Đề xuất cải thiện

1. **Thêm câu hỏi Q41**: "Máy có tắt đột ngột không?" → phân nhánh quá nhiệt / pin yếu / điện không ổn định
2. **Làm phong phú Bluetooth branch**: Thêm 2–3 câu hỏi → 3–4 diagnoses
3. **Thêm USB-C/Thunderbolt nhánh**: Ngày càng phổ biến trên laptop hiện đại
4. **Confidence Aggregation**: Khi nhiều rules cùng kích hoạt một diagnosis → cộng dồn CF
5. **Undo/Back navigation**: Cho phép user quay lại câu hỏi trước nếu trả lời sai

---

## PHẦN 9: DỮ LIỆU TRIỂN KHAI BACKEND

### 9.1 Inference Engine — Forward Chaining Python Implementation

```python
class WorkingMemory:
    """Bộ nhớ làm việc — lưu tất cả facts đã biết"""
    
    def __init__(self):
        self.facts: set[str] = set()
        self.session_data: dict = {}
    
    def add_fact(self, fact: str) -> None:
        self.facts.add(fact)
    
    def has_fact(self, fact: str) -> bool:
        return fact in self.facts
    
    def has_all_facts(self, facts: list[str]) -> bool:
        return all(f in self.facts for f in facts)
    
    def has_any_fact(self, facts: list[str]) -> bool:
        return any(f in self.facts for f in facts)
    
    def has_none_facts(self, facts: list[str]) -> bool:
        return not any(f in self.facts for f in facts)


class Rule:
    """Đại diện cho một luật IF-THEN"""
    
    def __init__(self, rule_data: dict):
        self.id = rule_data["id"]
        self.priority = rule_data.get("priority", 1)
        self.cf = rule_data.get("cf", 0.5)
        self.conditions = rule_data.get("conditions", [])
        self.not_conditions = rule_data.get("not_conditions", [])
        self.adds_facts = rule_data.get("adds_facts", [])
        self.triggers_diagnosis = rule_data.get("triggers_diagnosis", None)
        self.fired = False
    
    def is_applicable(self, wm: WorkingMemory) -> bool:
        """Kiểm tra xem luật có thể kích hoạt không"""
        if self.fired:
            return False
        conditions_met = wm.has_all_facts(self.conditions)
        not_conditions_met = wm.has_none_facts(self.not_conditions)
        return conditions_met and not_conditions_met
    
    def fire(self, wm: WorkingMemory) -> list[str]:
        """Kích hoạt luật — thêm facts mới vào working memory"""
        self.fired = True
        new_facts = []
        for fact in self.adds_facts:
            if not wm.has_fact(fact):
                wm.add_fact(fact)
                new_facts.append(fact)
        return new_facts


class ForwardChainingEngine:
    """Inference Engine theo chiến lược Forward Chaining"""
    
    def __init__(self, rules: list[Rule], diagnoses: dict):
        self.rules = sorted(rules, key=lambda r: r.priority, reverse=True)
        self.diagnoses = diagnoses
        self.wm = WorkingMemory()
    
    def add_facts_from_answer(self, question_id: str, option_value: str, questions_db: dict) -> None:
        """Thêm facts từ câu trả lời của người dùng"""
        question = questions_db.get(question_id)
        if not question:
            return
        
        for option in question.get("options", []):
            if option["value"] == option_value:
                for fact in option.get("adds_facts", []):
                    self.wm.add_fact(fact)
                
                # Trigger immediate diagnosis nếu có
                if "triggers_diagnosis" in option:
                    return option["triggers_diagnosis"]
                
                return option.get("next")
        return None
    
    def run_inference_cycle(self) -> tuple[list[str], list[str]]:
        """
        Chạy một chu kỳ suy diễn.
        Returns: (new_facts_added, diagnoses_triggered)
        """
        new_facts = []
        triggered_diagnoses = []
        agenda = []  # Conflict set
        
        # Bước 1: Match — tìm tất cả luật có thể kích hoạt
        for rule in self.rules:
            if rule.is_applicable(self.wm):
                agenda.append(rule)
        
        if not agenda:
            return new_facts, triggered_diagnoses
        
        # Bước 2: Conflict Resolution — chọn luật ưu tiên cao nhất
        # Đã sắp xếp theo priority trong __init__
        best_rule = agenda[0]
        
        # Bước 3: Fire the rule
        added = best_rule.fire(self.wm)
        new_facts.extend(added)
        
        if best_rule.triggers_diagnosis:
            triggered_diagnoses.append({
                "diagnosis_id": best_rule.triggers_diagnosis,
                "rule_id": best_rule.id,
                "cf": best_rule.cf,
                "diagnosis": self.diagnoses.get(best_rule.triggers_diagnosis)
            })
        
        return new_facts, triggered_diagnoses
    
    def run_until_stable(self) -> list[dict]:
        """
        Chạy forward chaining đến khi không còn luật nào kích hoạt được.
        Returns: Danh sách tất cả diagnoses tìm được
        """
        all_diagnoses = []
        max_iterations = 50  # Safety limit
        iteration = 0
        
        while iteration < max_iterations:
            new_facts, triggered = self.run_inference_cycle()
            all_diagnoses.extend(triggered)
            
            if not new_facts and not triggered:
                break  # Stable state — không có gì mới
            
            iteration += 1
        
        return all_diagnoses


class DiagnosticSession:
    """Quản lý một phiên chẩn đoán"""
    
    def __init__(self, questions_db: dict, rules_db: list, diagnoses_db: dict):
        self.questions_db = questions_db
        self.engine = ForwardChainingEngine(
            rules=[Rule(r) for r in rules_db],
            diagnoses=diagnoses_db
        )
        self.current_question = "Q01"
        self.history = []  # Lịch sử câu hỏi + câu trả lời
        self.final_diagnoses = []
    
    def get_current_question(self) -> dict:
        """Lấy câu hỏi hiện tại"""
        return self.questions_db.get(self.current_question)
    
    def answer_question(self, option_value: str) -> dict:
        """
        Xử lý câu trả lời và trả về:
        - next_question (nếu tiếp tục)
        - diagnoses (nếu đủ để kết luận)
        - intermediate_facts (để hiển thị reasoning)
        """
        self.history.append({
            "question": self.current_question,
            "answer": option_value
        })
        
        # Thêm facts từ câu trả lời
        immediate_diag = self.engine.add_facts_from_answer(
            self.current_question, option_value, self.questions_db
        )
        
        # Chạy inference cycle
        diagnoses = self.engine.run_until_stable()
        
        if diagnoses:
            self.final_diagnoses.extend(diagnoses)
        
        # Xác định câu hỏi tiếp theo
        if immediate_diag and immediate_diag.startswith("DIAG_"):
            # Đã có diagnosis trực tiếp
            if immediate_diag not in [d["diagnosis_id"] for d in self.final_diagnoses]:
                self.final_diagnoses.append({
                    "diagnosis_id": immediate_diag,
                    "cf": 0.85,
                    "via": "direct_question"
                })
            next_q = None
        else:
            next_q = immediate_diag
        
        self.current_question = next_q
        
        return {
            "next_question": next_q,
            "current_facts": list(self.engine.wm.facts),
            "triggered_diagnoses": self.final_diagnoses,
            "session_complete": next_q is None
        }
    
    def get_explanation(self) -> dict:
        """
        Tạo giải thích logic (Why/How path) cho người dùng
        """
        return {
            "question_path": self.history,
            "facts_collected": list(self.engine.wm.facts),
            "reasoning": self._build_reasoning_chain(),
            "final_diagnoses": self.final_diagnoses
        }
    
    def _build_reasoning_chain(self) -> list[dict]:
        """Xây dựng chuỗi lý luận dễ hiểu cho người dùng"""
        chain = []
        for step in self.history:
            q = self.questions_db.get(step["question"], {})
            for opt in q.get("options", []):
                if opt["value"] == step["answer"]:
                    chain.append({
                        "question": q.get("text", ""),
                        "answer": opt.get("label", ""),
                        "conclusion": f"→ Fact: {', '.join(opt.get('adds_facts', []))}"
                    })
                    break
        return chain
```

### 9.2 REST API Endpoints (FastAPI)

```python
from fastapi import FastAPI
from pydantic import BaseModel
import json, uuid

app = FastAPI()
sessions: dict = {}  # In production: use Redis

# Load knowledge base
with open("06_questions.json") as f:
    kb_data = json.load(f)
with open("07_rules_and_diagnoses.json") as f:
    rd_data = json.load(f)

questions_db = {q["id"]: q for q in kb_data["questions"]}
rules_db = rd_data["rules"]
diagnoses_db = {d["id"]: d for d in rd_data["diagnoses"]}

class AnswerRequest(BaseModel):
    session_id: str
    question_id: str
    answer: str

@app.post("/session/start")
async def start_session():
    """Bắt đầu phiên chẩn đoán mới"""
    session_id = str(uuid.uuid4())
    session = DiagnosticSession(questions_db, rules_db, diagnoses_db)
    sessions[session_id] = session
    first_question = session.get_current_question()
    return {
        "session_id": session_id,
        "question": first_question
    }

@app.post("/session/answer")
async def submit_answer(req: AnswerRequest):
    """Gửi câu trả lời và nhận câu hỏi tiếp theo hoặc kết luận"""
    session = sessions.get(req.session_id)
    if not session:
        return {"error": "Session not found"}
    
    result = session.answer_question(req.answer)
    
    if result["session_complete"]:
        return {
            "type": "diagnosis",
            "diagnoses": result["triggered_diagnoses"],
            "explanation": session.get_explanation()
        }
    else:
        next_q = questions_db.get(result["next_question"])
        return {
            "type": "question",
            "question": next_q,
            "facts_so_far": result["current_facts"]  # Cho debugging/transparency
        }

@app.get("/session/{session_id}/explain")
async def get_explanation(session_id: str):
    """Lấy giải thích logic của phiên chẩn đoán"""
    session = sessions.get(session_id)
    if not session:
        return {"error": "Session not found"}
    return session.get_explanation()

@app.get("/knowledge/questions")
async def get_questions():
    return kb_data["questions"]

@app.get("/knowledge/diagnoses")
async def get_diagnoses():
    return rd_data["diagnoses"]

@app.get("/knowledge/groups")
async def get_groups():
    return kb_data["groups"]
```

### 9.3 Test Cases mẫu

```python
TEST_CASES = [
    {
        "name": "TC001 — Adapter Laptop hỏng",
        "description": "Màn hoàn toàn không có phản ứng, laptop, đèn sạc không sáng",
        "answers": [
            ("Q01", "A"),  # Nguồn/Khởi động
            ("Q02", "A"),  # Hoàn toàn không phản ứng
            ("Q03", "A"),  # Laptop
            ("Q05", "A"),  # Đèn sạc không sáng
        ],
        "expected_diagnosis": "DIAG_PWR_01",
        "expected_cf_min": 0.85
    },
    {
      "name": "TC002 — Driver GPU lỗi sau Update",
      "description": "Màn hình nhấp nháy sau Windows Update",
      "answers": [
          ("Q01", "B"),  # Màn hình
          ("Q09", "B"),  # Nhấp nháy
          ("Q11", "B"),  # Sau Windows Update
      ],
      "expected_diagnosis": "DIAG_DSP_02",
      "expected_cf_min": 0.85
    },
    {
        "name": "TC003 — RAM gây BSOD",
        "description": "BSOD với mã memory error, ngẫu nhiên không theo pattern",
        "answers": [
            ("Q01", "C"),  # OS
            ("Q13", "A"),  # BSOD
            ("Q14", "A"),  # Memory error code
            ("Q19", "A"),  # Windows Memory Diagnostic báo lỗi
        ],
        "expected_diagnosis": "DIAG_OS_03",
        "expected_cf_min": 0.85
    },
    {
        "name": "TC004 — DNS Lỗi",
        "description": "Wi-Fi kết nối nhưng trình duyệt báo lỗi DNS",
        "answers": [
            ("Q01", "D"),  # Mạng
            ("Q20", "B"),  # Kết nối nhưng không Internet
            ("Q21", "C"),  # Không có cáp mạng
            ("Q22", "A"),  # Thiết bị khác OK
            ("Q23", "A"),  # Lỗi DNS
        ],
        "expected_diagnosis": "DIAG_NET_03",
        "expected_cf_min": 0.85
    },
    {
        "name": "TC005 — Thermal Throttling",
        "description": "Máy rất nóng, quạt ồn, CPU luôn 100%",
        "answers": [
            ("Q01", "G"),  # Hiệu năng
            ("Q37", "A"),  # Nóng + quạt ồn + chậm
            ("Q38", "A"),  # CPU 90-100%
            ("Q40", "D"),  # HWMonitor báo >90°C
        ],
        "expected_diagnosis": "DIAG_PERF_01",
        "expected_cf_min": 0.90
    },
    {
        "name": "TC006 — HDD Sắp Hỏng",
        "description": "Tiếng click lách cách từ HDD",
        "answers": [
            ("Q01", "H"),  # Lưu trữ
            ("Q36", "B"),  # Tiếng click HDD
        ],
        "expected_diagnosis": "DIAG_STR_02",
        "expected_cf_min": 0.90,
        "should_warn_urgent": True
    },
    {
        "name": "TC007 — Camera Privacy Locked",
        "description": "Camera không hoạt động do Privacy Settings",
        "answers": [
            ("Q01", "E"),  # Âm thanh/Camera
            ("Q27", "C"),  # Camera
            ("Q30", "A"),  # Privacy bị chặn
        ],
        "expected_diagnosis": "DIAG_CAM_01",
        "expected_cf_min": 0.95
    },
    {
        "name": "TC008 — USB Controller Driver Lỗi",
        "description": "Tất cả cổng USB đều không nhận thiết bị",
        "answers": [
            ("Q01", "F"),  # Ngoại vi
            ("Q32", "A"),  # USB device
            ("Q33", "C"),  # Tất cả cổng
        ],
        "expected_diagnosis": "DIAG_PER_02",
        "expected_cf_min": 0.85
    }
]

def run_test_case(tc: dict, session: DiagnosticSession) -> dict:
    """Chạy một test case và trả kết quả"""
    result = {"name": tc["name"], "passed": False, "details": {}}
    
    for q_id, answer in tc["answers"]:
        response = session.answer_question(answer)
        if response["session_complete"]:
            break
    
    # Kiểm tra kết quả
    final = session.final_diagnoses
    diagnosis_ids = [d.get("diagnosis_id") for d in final]
    
    result["found_diagnoses"] = diagnosis_ids
    result["expected"] = tc["expected_diagnosis"]
    result["passed"] = tc["expected_diagnosis"] in diagnosis_ids
    
    return result
```

### 9.4 Cấu trúc thư mục dự án đề xuất

```
project/
│
├── knowledge_base/           ← Thư mục này (knowledge base files)
│   ├── 01_strategy_and_design.md
│   ├── 02_fact_system.md
│   ├── 03_questions_40.md
│   ├── 04_rules_ifthen.md
│   ├── 05_diagnoses_table.md
│   ├── 06_questions.json           ← Dùng cho backend
│   ├── 07_rules_and_diagnoses.json ← Dùng cho backend
│   └── 08_inference_tree.md
│
├── backend/
│   ├── main.py                ← FastAPI app
│   ├── engine.py              ← Forward Chaining Inference Engine
│   ├── session.py             ← Session management
│   ├── models.py              ← Pydantic models
│   └── tests/
│       └── test_cases.py      ← 8 test cases mẫu
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js                 ← Web chatbot interface
│
└── docs/
    ├── presentation.pptx
    └── report.docx
```
