# 📘 Phân tích kỹ thuật: Hệ Chuyên Gia Chẩn Đoán Máy Tính (Rule-Based Expert System)

> **Môn học:** Công nghệ Tri thức  
> **Loại hệ thống:** Rule-Based Expert System — Forward Chaining  
> **Công nghệ:** Python 3.13 · Flask 3 · HTML/CSS/JS (Vanilla)  
> **Dữ liệu:** 50 câu hỏi · 103 luật · 50 chẩn đoán · ~166 facts

---

## I. Kiến Trúc Tổng Thể

```
┌─────────────────────────────────────────────────────────────┐
│                    NGƯỜI DÙNG (Trình duyệt)                  │
│              chat.html + style.css + chat.js                 │
└────────────────────────┬────────────────────────────────────┘
                         │  HTTP (fetch API)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    FLASK WEB SERVER (app.py)                 │
│  Routes: /start · /message · /select · /submit              │
│          /explanation · /reset · /status                     │
└──────┬──────────────────┬──────────────────┬────────────────┘
       │                  │                  │
       ▼                  ▼                  ▼
┌───────────┐    ┌───────────────┐   ┌─────────────────┐
│ NLU Layer │    │ Engine Layer  │   │ Services Layer  │
│ patterns  │    │ working_mem   │   │ session_store   │
│ intent_cl │    │ rule_model    │   └─────────────────┘
│ fact_extr │    │ forward_eng   │
└───────────┘    │ diag_session  │
                 │ question_sel  │
                 │ explainatn_bl │
                 └───────┬───────┘
                         │
                         ▼
              ┌─────────────────────┐
              │  KNOWLEDGE BASE     │
              │ 06_questions.json   │
              │ 07_rules_diag.json  │
              └─────────────────────┘
```

### Luồng dữ liệu tổng quát

```
User input
  → Flask route
    → NLU (text) hoặc direct option (button)
      → DiagnosticSession.answer()
        → QuestionFlowManager.process_answer()
          → ForwardChainingEngine.run_until_stable()
            → WorkingMemory ← Rule.fire()
          → DiagnosisResult
        → QuestionSelector.select() [dynamic Q]
      → ExplanationBuilder
  → JSON Response → chat.js render
```

---

## II. Tầng Engine (`engine/`)

### 2.1 `working_memory.py` — Bộ nhớ làm việc

**Vai trò:** Lưu trữ tất cả **facts** đã được xác lập trong phiên chẩn đoán. Đây là "vùng nhớ ngắn hạn" của hệ chuyên gia.

**Nguyên tắc thiết kế:** Monotonic reasoning — facts chỉ được **thêm vào**, không bao giờ bị xóa trong một phiên. Điều này đảm bảo tính nhất quán của suy luận.

#### Class `WorkingMemory`

| Thuộc tính | Kiểu | Vai trò |
|---|---|---|
| `_facts` | `set[str]` | Tập hợp facts hiện tại (không trùng lặp) |
| `_fact_history` | `list[tuple]` | Lịch sử (fact, nguồn gốc) để trace |

```python
class WorkingMemory:
    def __init__(self):
        self._facts: set[str] = set()
        self._fact_history: list[tuple[str, str]] = []
```

#### Phương thức chính

| Phương thức | Tham số | Trả về | Mục đích |
|---|---|---|---|
| `add(fact, source)` | `str, str` | `bool` | Thêm 1 fact. `True` nếu fact mới, `False` nếu đã có |
| `add_many(facts, source)` | `list, str` | `list[str]` | Thêm nhiều facts, trả list facts thực sự mới |
| `has(fact)` | `str` | `bool` | Kiểm tra 1 fact có tồn tại không |
| `has_all(facts)` | `list` | `bool` | Kiểm tra **tất cả** facts có tồn tại không |
| `has_none(facts)` | `list` | `bool` | Kiểm tra **không có** fact nào tồn tại |
| `snapshot()` | — | `frozenset` | Chụp trạng thái để phát hiện thay đổi |

**Ví dụ hoạt động:**
```python
wm = WorkingMemory()
wm.add("no_power", source="Q02:A")   # → True (fact mới)
wm.add("no_power", source="Q02:A")   # → False (đã có)
wm.has("no_power")                   # → True
wm.has_all(["no_power", "is_laptop"])# → False (thiếu is_laptop)
```

---

### 2.2 `rule_model.py` — Mô hình luật IF-THEN

**Vai trò:** Định nghĩa cấu trúc dữ liệu cho một luật suy diễn và kết quả chẩn đoán.

#### Class `Rule`

Mỗi `Rule` đại diện cho một luật dạng:
```
IF (conditions) AND NOT (not_conditions) THEN (adds_facts | triggers_diagnosis)
```

| Thuộc tính | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | `str` | Mã luật (VD: `R001_PWR`) |
| `name` | `str` | Tên mô tả luật |
| `group` | `str` | Nhóm lỗi (`power_startup`, `display`, ...) |
| `conditions` | `list[str]` | Danh sách facts PHẢI có trong WM |
| `not_conditions` | `list[str]` | Danh sách facts KHÔNG được có trong WM |
| `adds_facts` | `list[str]` | Facts sẽ thêm vào WM khi rule fire |
| `triggers_diagnosis` | `str \| None` | Mã chẩn đoán được kích hoạt |
| `priority` | `int` | Độ ưu tiên 1–5 (conflict resolution) |
| `cf` | `float` | Certainty Factor 0.0–1.0 (mô hình MYCIN) |
| `fired` | `bool` | Đánh dấu đã fire hay chưa |

```python
@dataclass
class Rule:
    id: str
    name: str
    conditions: list[str]
    not_conditions: list[str] = []
    adds_facts: list[str] = []
    triggers_diagnosis: Optional[str] = None
    priority: int = 2
    cf: float = 0.8
    fired: bool = False
```

#### Phương thức `is_applicable(wm)`

```python
def is_applicable(self, wm: WorkingMemory) -> bool:
    if self.fired:
        return False
    return wm.has_all(self.conditions) and wm.has_none(self.not_conditions)
```

> **Ý nghĩa:** Rule chỉ applicable khi chưa fire, tất cả conditions đều có trong WM, và không có not_condition nào trong WM.

#### Phương thức `fire(wm)`

```python
def fire(self, wm: WorkingMemory) -> tuple[list[str], Optional[str]]:
    self.fired = True
    new_facts = wm.add_many(self.adds_facts, source=self.id)
    return new_facts, self.triggers_diagnosis
```

> **Ý nghĩa:** Đánh dấu rule đã fire, thêm facts mới vào WM, trả về (facts_mới, diagnosis_id).

#### Class `DiagnosisResult`

Lưu kết quả một lần chẩn đoán được kích hoạt.

```python
@dataclass
class DiagnosisResult:
    diagnosis_id: str
    cf: float                          # CF của rule kích hoạt
    triggered_by_rule: Optional[str]
    triggered_by_question: Optional[str]
    combined_cf: Optional[float]       # CF tổng hợp (nếu nhiều rule cùng → 1 diagnosis)

    @staticmethod
    def combine_cf(cf1: float, cf2: float) -> float:
        return cf1 + cf2 * (1 - cf1)  # Công thức MYCIN
```

**Công thức MYCIN để kết hợp CF:**
```
CF_combined = CF1 + CF2 × (1 - CF1)

Ví dụ: CF1=0.85, CF2=0.70
  → 0.85 + 0.70 × (1-0.85)
  → 0.85 + 0.70 × 0.15
  → 0.85 + 0.105 = 0.955
```

---

### 2.3 `forward_engine.py` — Forward Chaining Inference Engine

**Vai trò:** Triển khai thuật toán forward chaining theo vòng lặp MATCH → SELECT → FIRE.

**Nguyên lý:** Xuất phát từ facts đã biết, áp dụng các luật để suy ra facts mới, tiếp tục cho đến khi không còn luật nào có thể kích hoạt (điểm cố định — fixed point).

#### Class `ForwardChainingEngine`

```python
class ForwardChainingEngine:
    def __init__(self, rules: list[Rule], diagnoses_db: dict):
        self.rules = rules
        self.diagnoses_db = diagnoses_db
        self.wm = WorkingMemory()
        self._diagnosis_cf_map: dict[str, float] = {}
        self._fired_rules_log: list[dict] = []
```

#### Thuật toán chính: `run_until_stable()`

```
WHILE iteration < MAX_ITERATIONS:
    conflict_set = [r for r in rules if r.is_applicable(wm)]
    IF conflict_set is empty:
        BREAK  ← Đạt điểm cố định
    best_rule = max(conflict_set, key=(priority, specificity, CF))
    new_facts, diag = best_rule.fire(wm)
    IF diag:
        update diagnosis_cf_map(diag, MYCIN)
    iteration++
```

#### Phương thức `_build_conflict_set()`

```python
def _build_conflict_set(self) -> list[Rule]:
    conflict_set = [r for r in self.rules if r.is_applicable(self.wm)]
    conflict_set.sort(
        key=lambda r: (r.priority, r.specificity, r.cf),
        reverse=True
    )
    return conflict_set
```

> **Conflict Resolution Strategy:** Khi nhiều rules cùng applicable (Conflict Set), engine chọn rule tốt nhất theo thứ tự ưu tiên:
> 1. `priority` (5 > 4 > ... > 1)
> 2. `specificity` = `len(conditions) + len(not_conditions)` — rule phức tạp hơn ưu tiên hơn
> 3. `cf` — rule có độ tin cậy cao hơn ưu tiên hơn

#### Phương thức `get_near_fire_rules(max_missing)`

```python
def get_near_fire_rules(self, max_missing: int = 3) -> list[dict]:
    near_fire = []
    for rule in self.rules:
        if rule.fired: continue
        missing = [f for f in rule.conditions if not self.wm.has(f)]
        blocked = any(self.wm.has(f) for f in rule.not_conditions)
        if blocked: continue
        if 0 < len(missing) <= max_missing:
            near_fire.append({
                "rule": rule,
                "missing_facts": missing,
                "missing_count": len(missing),
            })
    return near_fire  # Sorted: ít missing nhất trước
```

> **Mục đích:** Tìm các rules "gần được fire" (thiếu ≤ 3 facts). Kết quả này được dùng cho **Dynamic Questioning** — chọn câu hỏi tiếp theo giúp fire được rule nhanh nhất.

#### Phương thức `get_top_diagnoses(n)`

Trả về top N chẩn đoán có CF cao nhất, đã format đầy đủ thông tin để hiển thị cho người dùng.

---

### 2.4 `diagnostic_session.py` — Phiên chẩn đoán

**Vai trò:** Quản lý toàn bộ một phiên chẩn đoán từ câu hỏi đầu đến kết quả cuối. Đây là "controller" điều phối mọi thứ.

#### Class `QuestionFlowManager`

Quản lý luồng câu hỏi theo cấu trúc JSON.

```python
class QuestionFlowManager:
    def __init__(self, questions_data: list[dict]):
        self._questions: dict[str, dict] = {q["id"]: q for q in questions_data}
```

#### Phương thức `process_answer(question_id, selected_values, engine)`

**Đây là hàm quan trọng nhất trong flow.** Xử lý câu trả lời của người dùng:

```
INPUT: question_id, selected_values (list), engine

FOR EACH selected_value:
    option = get_option(question, value)
    
    1. Thêm option.adds_facts → engine.add_facts()
    2. Nếu option.triggers_diagnosis → add CF vào diagnosis_map
    3. Lưu option.next → next_question_id
    4. Lưu option.suggest_action nếu có

engine.run_until_stable()  ← Chạy forward chaining

RETURN {
    new_facts, diagnoses_triggered,
    next_question_id, is_terminal,
    current_wm
}
```

**Quan trọng:** Hàm xác định `is_terminal = True` khi:
- Đã có chẩn đoán VÀ không có `next_question_id`
- Hoặc option trực tiếp triggers diagnosis mà không có next Q

#### Class `DiagnosticSession`

Quản lý state đầy đủ của một session web:

```python
class DiagnosticSession:
    ROOT_QUESTION = "Q01"

    def __init__(self, questions, rules, diagnoses):
        self.engine = ForwardChainingEngine(...)
        self.flow = QuestionFlowManager(...)
        
        # State tracking
        self.current_question_id = "Q01"
        self.history: list[dict] = []
        self.final_diagnoses: list[dict] = []
        self.is_complete: bool = False
        
        # Extended fields for web chat
        self.expected_input_mode: str = "single_choice"
        self.asked_question_ids: set[str] = set()
        self.current_group: Optional[str] = None
```

#### Phương thức `answer(selected_values)`

Xử lý một câu trả lời hoàn chỉnh:

```
1. Ghi vào history (Q&A log)
2. Gọi flow.process_answer() → result
3. Cập nhật final_diagnoses (dedup + sort by CF)
4. Nếu is_terminal → self.is_complete = True
5. Else → self.current_question_id = result.next_question_id
6. Trả về result + next_question + top_diagnoses
```

#### Phương thức `get_explanation()`

Tập hợp toàn bộ trace của phiên để tạo explanation:
- `question_path`: Danh sách Q&A theo thứ tự
- `working_memory_final`: Tất cả facts trong WM
- `rules_fired`: Log tất cả rules đã fire
- `near_fire_rules`: Rules gần fire nhưng chưa được

#### Class `KnowledgeBaseLoader`

```python
class KnowledgeBaseLoader:
    def __init__(self, questions_path, rules_path):
        # Load JSON
        self.questions = q_data["questions"]   # 50 câu hỏi
        self.rules = r_data["rules"]           # 103 luật
        self.diagnoses = r_data["diagnoses"]   # 50 chẩn đoán
    
    def create_session(self) -> DiagnosticSession:
        return DiagnosticSession(self.questions, self.rules, self.diagnoses)
```

> **Singleton pattern:** Chỉ load KB một lần khi Flask khởi động. Mỗi request tạo session mới từ KB đã load.

---

### 2.5 `question_selector.py` — Dynamic Questioning

**Vai trò:** Chọn câu hỏi tiếp theo thông minh dựa trên trạng thái hiện tại, thay vì chỉ đi theo thứ tự cố định trong JSON.

**Triết lý thiết kế:** Dynamic Questioning là **bổ sung**, không thay thế flow JSON. Nếu câu hỏi "mặc định" từ JSON cũng tốt thì ưu tiên giữ nguyên flow để không làm gãy logic gốc.

#### Pre-computation (tính toán trước khi query)

```python
def __init__(self, questions_data, diagnoses_data):
    # Pre-build maps để query nhanh O(1)
    self._fact_to_questions = self._build_fact_question_map()
    # fact_id → [question_id, ...]
    
    self._question_to_facts = self._build_question_fact_map()
    # question_id → {fact_id, ...}
    
    self._diag_to_facts = self._build_diag_fact_map()
    # diagnosis_id → {fact_id, ...}
```

#### Thuật toán `select(near_fire_rules, asked_qids, current_group, fallback_qid)`

```
Bước 1: Gom candidate_facts từ near_fire_rules
  candidate_facts = ⋃ {nf.missing_facts for nf in near_fire_rules}

Bước 2: Tìm candidate questions
  candidate_qids = {q | q covers ≥1 candidate_fact} - asked_qids

Bước 3: Score từng candidate
  FOR EACH qid IN candidate_qids:
    score = coverage_score(qid)     × 2.0
          + discrimination_score(qid) × 1.5
          + group_bonus(qid)          × 0.5
          + proximity_score(qid)

Bước 4: So sánh với fallback
  IF fallback_qid not asked AND fallback_score > 0:
    return fallback_qid  ← ưu tiên JSON flow
  ELSE:
    return best scoring candidate
```

#### Công thức Scoring chi tiết

| Thành phần | Công thức | Ý nghĩa |
|---|---|---|
| `coverage_score` | `\|q_facts ∩ candidate_facts\| × 2.0` | Câu hỏi cover nhiều missing facts |
| `discrimination_score` | `(diagnoses_covered / total_diag) × 1.5` | Phân biệt được nhiều diagnoses |
| `group_bonus` | `+0.5 nếu same group` | Tránh nhảy group bừa |
| `proximity_score` | `Σ overlap/missing_count` | Câu hỏi giúp fire rules gần nhất |

---

### 2.6 `explanation_builder.py` — Giải thích suy luận

**Vai trò:** Tạo giải thích dạng ngôn ngữ tự nhiên (tiếng Việt) về quá trình suy luận của hệ thống.

**Ý nghĩa học thuật:** Đây là **Explanation Facility** — một thành phần bắt buộc trong hệ chuyên gia chuẩn. Giúp hệ thống có tính **explainable AI** (XAI).

#### Hàm `build_short_explanation(question, near_fire_rules, current_group)`

Tạo 1 câu ngắn hiển thị **inline** dưới câu hỏi:

```python
def build_short_explanation(question, near_fire_rules, current_group):
    # Ưu tiên 1: dùng field "purpose" trong JSON
    purpose = question.get("purpose", "")
    if purpose:
        return f"💡 {purpose}"
    
    # Fallback: tạo từ near-fire rules
    rule_names = [nf["rule"].name for nf in near_fire_rules[:2]]
    return f"💡 Câu hỏi này giúp kiểm tra: {' và '.join(rule_names)}"
```

#### Hàm `build_full_explanation(session)`

Tạo explanation đầy đủ cho modal "Giải thích chi tiết":

```python
def build_full_explanation(session) -> dict:
    return {
        "question_path":  [...],   # Q&A history
        "facts_collected": [...],  # Tất cả facts trong WM
        "fact_history":   [...],   # Từng fact + nguồn gốc
        "rules_fired":    [...],   # Log rules đã fire + CF
        "top_diagnoses":  [...],   # Top N kết quả
        "narration":      [...],   # Giải thích bằng tiếng Việt tự nhiên
        "summary": {
            "questions_asked": N,
            "facts_collected": N,
            "rules_fired": N,
            "diagnoses_found": N,
        }
    }
```

#### Hàm `_build_narration(question_path, rules_fired, top_diagnoses)`

Tạo danh sách câu văn tiếng Việt mô tả từng bước suy luận. Ví dụ output:
```
📋 Quá trình chẩn đoán:
  1. Máy tính của bạn là laptop hay máy bàn? → Laptop
  2. Tình trạng pin và sạc? → Đèn sạc sáng nhưng pin không tăng

🔍 Luật đã kích hoạt:
  • R015_LAPTOP_NO_CHARGE: thêm facts `no_charge, probable_battery`
  • R023_BATTERY_ISSUE: → DIAG_PWR_02 (CF=85%)

✅ Kết quả chẩn đoán:
  🥇 Pin laptop chai hoặc hỏng — Độ tin cậy: 87%
     Mức độ: 🟠 Cao
```

---

## III. Tầng NLU (`nlu/`)

**Vai trò:** Hiểu text tự nhiên từ người dùng, chuyển thành facts và ý định (intent). Đây là **Rule-Based NLU**, không dùng AI/ML.

### 3.1 `patterns.py` — Bảng ánh xạ từ khóa

**Vai trò:** Kho dữ liệu trung tâm cho toàn bộ NLU layer. Được thiết kế như "thư viện" — các module khác đều import từ đây.

#### `INTENT_KEYWORDS: dict[str, list[str]]`

Ánh xạ **nhóm lỗi → danh sách từ khóa nhận dạng**:

```python
INTENT_KEYWORDS = {
    "power_startup": [
        "không bật", "không lên nguồn", "không khởi động",
        "sạc không vào", "pin chai", "adapter hỏng",
        "tắt đột ngột", "beep", ...
    ],
    "display": [
        "màn hình", "màn đen", "nhấp nháy", "sọc",
        "màu sai", "backlight", "gpu", ...
    ],
    "network": [...],
    "os_boot": [...],
    "audio_camera": [...],
    "peripherals": [...],
    "performance": [...],
    "storage": [...],
}
```

> **Có 8 nhóm ý định**, tương ứng 8 nhóm câu hỏi trong knowledge base.

#### `KEYWORD_FACT_MAP: list[tuple[str, list[str]]]`

**Ordered list** ánh xạ **pattern text → danh sách facts**:

```python
KEYWORD_FACT_MAP = [
    # More specific first (order matters!)
    ("không sạc được",              ["no_charge"]),
    ("đèn sạc không sáng",          ["no_charge", "battery_indicator_red"]),
    ("chỉ chạy khi cắm điện",       ["laptop_only_on_adapter"]),
    ("không lên nguồn",             ["no_power"]),
    ("bsod",                        ["bsod_appears"]),
    ("màn hình xanh",               ["bsod_appears"]),
    ("memory management",           ["bsod_appears", "bsod_memory_error"]),
    ("wifi có nhưng không có internet", ["wifi_connected_no_internet"]),
    # ~80 patterns tổng cộng
]
```

> **Thứ tự quan trọng:** Pattern dài/cụ thể hơn đặt trước, pattern ngắn đặt sau. Một text có thể match nhiều patterns → thu thập tất cả facts.

#### `UNDERSTOOD_TEMPLATES / UNCERTAIN_MESSAGE`

Các mẫu câu bot trả lời khi hiểu/không hiểu intent:
```python
UNDERSTOOD_TEMPLATES = {
    "power_startup": "Tôi hiểu máy bạn đang gặp vấn đề về nguồn điện...",
    "network":       "Tôi hiểu máy bạn đang gặp vấn đề về mạng...",
    ...
}
UNCERTAIN_MESSAGE = "Tôi chưa xác định rõ vấn đề. Hãy chọn từ danh sách..."
```

---

### 3.2 `intent_classifier.py` — Phân loại ý định

**Vai trò:** Từ text người dùng, xác định họ đang hỏi về nhóm lỗi nào.

#### Class `IntentClassifier`

#### Phương thức `classify(text)`

```python
def classify(self, text: str) -> dict:
    normalized = _normalize(text)   # lowercase + clean
    
    scores = {}
    for intent, keywords in INTENT_KEYWORDS.items():
        score = 0.0
        for kw in keywords:
            if kw in normalized:
                # Keyword dài hơn = cụ thể hơn = trọng số cao hơn
                weight = 1.0 + len(kw.split()) * 0.3
                score += weight
        if score > 0:
            scores[intent] = score
    
    # Normalize → [0, 1]
    total = sum(scores.values())
    normalized_scores = {k: v/total for k, v in scores.items()}
    
    top_intent = max(normalized_scores, key=...)
    top_conf = normalized_scores[top_intent]
    
    return {
        "intent":     top_intent if top_conf >= MIN_CONFIDENCE else None,
        "confidence": top_conf,
        "is_certain": top_conf >= HIGH_CONFIDENCE,  # ≥ 0.6
        "scores":     normalized_scores,
    }
```

**Ví dụ:**
```
Input:  "wifi có nhưng không vào được internet"
Scores: {network: 3.5, os_boot: 0.3}
Normalized: {network: 0.92, os_boot: 0.08}
Output: {intent: "network", confidence: 0.92, is_certain: True}
```

#### Hàm `_normalize(text)`

```python
def _normalize(text: str) -> str:
    text = text.lower().strip()
    # Giữ tiếng Việt có dấu, xóa ký tự đặc biệt
    text = re.sub(r"[^\w\s\u00C0-\u024F\u1E00-\u1EFF]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text
```

> **Quan trọng:** Unicode range `\u1E00-\u1EFF` bao gồm toàn bộ ký tự tiếng Việt có dấu. Giữ nguyên dấu để không mất thông tin ngữ nghĩa.

---

### 3.3 `fact_extractor.py` — Trích xuất facts

**Vai trò:** Từ text người dùng, trích xuất danh sách facts cụ thể để thêm vào Working Memory.

#### Class `FactExtractor`

#### Phương thức `extract(text)`

```python
def extract(self, text: str) -> dict:
    normalized = _normalize(text)
    extracted_facts = []
    matched_patterns = []
    
    for pattern, facts in KEYWORD_FACT_MAP:
        if pattern in normalized:
            for fact in facts:
                if fact not in extracted_facts:
                    extracted_facts.append(fact)  # Giữ thứ tự + không lặp
            matched_patterns.append(pattern)
    
    return {
        "facts":            extracted_facts,
        "matched_patterns": matched_patterns,
        "has_facts":        len(extracted_facts) > 0,
        "understood_message": FACTS_UNDERSTOOD_PREFIX + facts_display,
    }
```

#### Phương thức `extract_and_classify(text, intent_result)`

Kết hợp fact extraction + intent classification thành một output thống nhất:

```python
def extract_and_classify(self, text, intent_result) -> dict:
    fact_result = self.extract(text)
    intent = intent_result.get("intent")
    intent_certain = intent_result.get("is_certain", False)
    
    has_facts = fact_result["has_facts"]
    is_certain = has_facts          # Certainty = có facts cụ thể
    
    # Nếu intent rõ + chưa có facts → gợi ý skip đến nhóm đó
    skip_to_group = None
    if intent_certain and not has_facts and intent:
        skip_to_group = IntentClassifier().get_group_question_start(intent)
    
    return {
        "facts":             fact_result["facts"],
        "intent":            intent,
        "is_certain":        is_certain,
        "uncertain":         not is_certain and not intent_certain,
        "understood_message": fact_result["understood_message"],
        "skip_to_group":     skip_to_group,  # QID để skip vào nhóm
    }
```

**Ba kịch bản đầu ra:**

| Trường hợp | `is_certain` | `skip_to_group` | Hành động |
|---|---|---|---|
| Text có facts cụ thể | `True` | có thể có | Add facts, advance Q |
| Intent rõ, không có facts | `False` | có | Skip đến Q đầu nhóm |
| Không rõ gì | `False` | None | Hiển thị clarification |

---

## IV. Tầng Services (`services/`)

### 4.1 `session_store.py` — Quản lý phiên

**Vai trò:** Lưu trữ và quản lý lifecycle của tất cả DiagnosticSessions đang active.

#### Class `ExtendedSession`

Wrapper bao quanh `DiagnosticSession` với metadata web:

```python
class ExtendedSession:
    def __init__(self, session_id: str, diagnostic_session: DiagnosticSession):
        self.session_id = session_id
        self.ds = diagnostic_session
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
    
    def touch(self):
        """Cập nhật thời gian hoạt động → reset TTL countdown."""
        self.last_activity = datetime.now()
    
    def is_expired(self, ttl_minutes=30) -> bool:
        return (datetime.now() - self.last_activity) > timedelta(minutes=ttl_minutes)
```

#### Class `SessionStore`

```python
class SessionStore:
    def __init__(self, kb: KnowledgeBaseLoader, ttl_minutes=30):
        self._sessions: dict[str, ExtendedSession] = {}
        self._lock = threading.Lock()  # Thread-safe
        
        # Background cleanup thread
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop, daemon=True
        )
        self._cleanup_thread.start()
```

| Phương thức | Vai trò |
|---|---|
| `create()` | Tạo session mới (UUID key) → `ExtendedSession` |
| `get(session_id)` | Lấy session + touch() + kiểm tra TTL |
| `delete(session_id)` | Xóa session thủ công (/reset route) |
| `_cleanup_loop()` | Background thread: dọn session hết hạn mỗi 5 phút |
| `stats()` | Thống kê: active / completed / in_progress |

**Thread safety:** Mọi thao tác trên `_sessions` dict đều dùng `threading.Lock()` để tránh race condition khi nhiều người dùng đồng thời.

---

## V. Tầng Web (`app.py`)

**Vai trò:** Flask application — điểm kết nối giữa tất cả các layer.

### 5.1 Khởi tạo (`init_app()`)

```python
def init_app():
    global kb, store, question_selector, intent_clf, fact_extractor
    
    kb = KnowledgeBaseLoader(QUESTIONS_PATH, RULES_PATH)  # Load JSON 1 lần
    store = SessionStore(kb)                               # Session manager
    question_selector = QuestionSelector(kb.questions, kb.diagnoses)  # Pre-compute
    intent_clf = IntentClassifier()
    fact_extractor = FactExtractor()
```

> **Singleton globals:** Tất cả services chỉ khởi tạo 1 lần. Sessions riêng lẻ mới được tạo mỗi request.

### 5.2 Routes và flow

#### `POST /start`
```
Tạo session mới → trả Q01 + session_id
```

#### `POST /message` — **Route phức tạp nhất**
```
text → NLU (intent + facts)
  → _match_text_to_option():
      Chiến lược 1: fact_overlap (score +10/fact)
      Chiến lược 2: label_word_match (score +2/word)
      Chiến lược 3: letter_match A/B/C... (score +5)
      
  IF match found (score ≥ 2):
    ds.answer([matched_value])  ← advance question
    
  ELSE IF facts extracted:
    engine.add_facts(facts)     ← enriche WM, keep Q
    engine.run_until_stable()
    
  ELSE IF intent clear:
    skip to group start Q       ← jump đến nhóm
    
  ELSE:
    clarification message       ← xin mô tả lại
```

#### `POST /select`
```
{session_id, question_id, value}
→ validate question_id match
→ ds.answer([value])
→ response
```

#### `POST /submit`
```
{session_id, question_id, values: list}
→ ds.answer(values + ["SUBMIT"])
→ response
```

#### `GET /explanation`
```
→ build_full_explanation(session)
→ JSON với Q&A path, facts, rules, narration
```

#### `POST /reset`
```
→ store.delete(old_session_id)
→ store.create() → new session
→ trả Q01 mới
```

### 5.3 Helper: `_match_text_to_option(text, question, extracted_facts)`

**Giải quyết vấn đề:** User gõ text dạng tự nhiên, map về option cụ thể của câu hỏi hiện tại.

```python
def _match_text_to_option(text, question, extracted_facts) -> str | None:
    text_lower = text.lower().strip()
    best_match, best_score = None, 0
    
    for opt in question["options"]:
        score = 0
        
        # Tier 1: fact match (strongest signal)
        opt_facts = set(opt.get("adds_facts", []))
        if opt_facts & set(extracted_facts):
            score += len(opt_facts & set(extracted_facts)) * 10
        
        # Tier 2: label word match
        label_words = [w for w in opt["label"].lower().split() if len(w) > 2]
        hits = sum(1 for w in label_words if w in text_lower)
        score += hits * 2
        
        # Tier 3: single letter (A/B/C)
        if re.fullmatch(r'[a-zA-Z]', text.strip()):
            if text.strip().upper() == opt["value"]:
                score += 5
        
        if score > best_score:
            best_score, best_match = score, opt["value"]
    
    return best_match if best_score >= 2 else None
```

---

## VI. Tầng Frontend

### 6.1 `templates/chat.html` — Cấu trúc HTML

Template Jinja2 với các vùng chức năng:

| ID / Component | Vai trò |
|---|---|
| `#chat-messages` | Vùng hiển thị messages (scroll) |
| `#quick-replies` | Container quick-reply buttons |
| `#multi-select-area` | Checkbox area cho multi_choice |
| `#text-input-row` | Text input + Send button |
| `#side-panel` | Panel "Quá trình suy luận" bên phải |
| `#facts-list` | Hiển thị facts tags |
| `#candidate-list` | Hiển thị candidate diagnoses |
| `#diagnosis-modal` | Modal kết quả cuối |
| `#explanation-modal` | Modal giải thích chi tiết |
| `#typing-template` | HTML template của typing indicator |

### 6.2 `static/css/style.css` — Hệ thống Design

**Thiết kế theo CSS Custom Properties (variables):**

```css
:root {
  --primary:       #2563eb;   /* Blue chính */
  --primary-light: #dbeafe;   /* Blue nhạt (backgrounds) */
  --bot-bg:        #f0f7ff;   /* Nền bubble bot */
  --user-bg:       #2563eb;   /* Nền bubble user */
  --surface:       #ffffff;   /* Nền card */
  --border:        #e2e8f0;   /* Màu viền */
  --radius:        12px;      /* Bo góc */
}
```

**Các component chính:**

| Class | Mô tả |
|---|---|
| `.app-header` | Header cố định 60px |
| `.chat-container` | Chat window (flex column) |
| `.message.bot-message` | Row message bot (avatar trái) |
| `.message.user-message` | Row message user (avatar phải) |
| `.bubble` | Nội dung message với border-radius |
| `.quick-reply-btn` | Pill button cho single_choice |
| `.multi-option` | Checkbox item cho multi_choice |
| `.side-panel` | Panel suy luận 300px bên phải |
| `.candidate-item` | Card chẩn đoán tạm + CF bar |
| `.diagnosis-modal` | Modal kết quả cuối (centered) |
| `.cf-fill` | Progress bar CF với gradient |

**Animation `fadeUp`:**
```css
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
/* Áp dụng cho mọi .message → smooth entrance */
```

### 6.3 `static/js/chat.js` — Frontend Logic

**State management:**

```javascript
const state = {
  sessionId: null,        // UUID từ server
  currentQuestion: null,  // Question đang hiển thị
  inputMode: 'single_choice', // text | single_choice | multi_choice
  isWaiting: false,       // True khi đang chờ server
  lastDiagnoses: [],      // Lưu cached diagnoses cho modal
};
```

#### Luồng khởi động

```
DOMContentLoaded
  → startSession()
    → POST /start
      → applyResponse(res)
        → state.sessionId = res.session_id
        → renderQuickReplies(res.question)
        → addBotMessage(res.bot_message)
```

#### Hàm `applyResponse(res)` — **Trung tâm của frontend**

```javascript
function applyResponse(res) {
    // 1. Cập nhật state
    state.sessionId = res.session_id;
    state.inputMode = res.input_mode;
    state.currentQuestion = res.question;
    
    // 2. Cập nhật side panel
    updateSidePanel(res.top_diagnoses, []);
    wmCount.textContent = res.wm_size;
    appendFactTags(res.facts_added);
    
    // 3. Hiển thị bot message
    addBotMessage(res.bot_message);
    
    // 4. Nếu session complete → show diagnosis
    if (res.session_complete) {
        showDiagnosisModal(res.diagnoses);
        return;
    }
    
    // 5. Render input theo type
    if (res.question.type === 'multi_choice') {
        renderMultiChoice(res.question);
    } else {
        renderQuickReplies(res.question);
    }
}
```

#### Ba loại input rendering

**Single Choice:**
```javascript
function renderQuickReplies(question) {
    question.options.forEach(opt => {
        const btn = document.createElement('button');
        btn.className = 'quick-reply-btn';
        btn.onclick = () => sendSelect(question.id, opt.value, opt.label);
        quickReplies.appendChild(btn);
    });
}
```

**Multi Choice:**
```javascript
function renderMultiChoice(question) {
    question.options.forEach(opt => {
        // Tạo checkbox label
        const cb = document.createElement('input');
        cb.type = 'checkbox';
        cb.value = opt.value;
        // User check → submit → POST /submit với array values
    });
}
```

**Text Input:** Luôn hiện, nhưng disabled khi đang waiting.

#### Hàm `formatMarkdown(text)`

Chuyển markdown đơn giản thành HTML để render bot message:

```javascript
function formatMarkdown(text) {
    return escHtml(text)
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')  // Bold
        .replace(/\*(.*?)\*/g, '<em>$1</em>')              // Italic
        .replace(/`(.*?)`/g, '<code>$1</code>')            // Code
        .replace(/^• (.+)$/gm, '<div>• $1</div>')         // Bullets
        .replace(/\n\n/g, '</p><p>')                       // Paragraphs
        .replace(/\n/g, '<br>');                           // Newlines
}
```

#### Hàm `showDiagnosisModal(diagnoses)` — Hiển thị kết quả

Render Diagnosis Card với:
- Primary diagnosis: CF meter, severity badge, solution steps
- Alt diagnoses: Danh sách alternative với CF pill
- Actions: "Xem giải thích" + "Bắt đầu lại"

---

## VII. Knowledge Base (JSON)

### 7.1 `06_questions.json` — Cấu trúc câu hỏi

```json
{
  "metadata": { "version": "2.0", "total_questions": 50 },
  "groups": [
    { "id": "power_startup", "name": "Nguồn / Khởi động", "root_question": "Q02" },
    ...
  ],
  "questions": [
    {
      "id": "Q01",
      "text": "Vấn đề chính của máy bạn là gì?",
      "type": "single_choice",
      "group": "root",
      "purpose": "Phân loại nhóm lỗi",
      "options": [
        {
          "value": "A",
          "label": "Máy không bật / không có điện",
          "adds_facts": ["user_reports_power_issue"],
          "sets_group": "power_startup",
          "next": "Q02"
        },
        ...
      ]
    }
  ]
}
```

**Các loại question type:**
- `single_choice`: Radio — chỉ 1 lựa chọn
- `yes_no`: Dạng đặc biệt của single_choice (2 options)
- `multi_choice`: Checkbox — nhiều lựa chọn + SUBMIT

### 7.2 `07_rules_and_diagnoses.json` — Luật và chẩn đoán

**Cấu trúc Rule:**
```json
{
  "id": "R015_LAPTOP_BATTERY",
  "name": "Laptop + no_power + no_charge → battery issue",
  "group": "power_startup",
  "conditions": ["no_power", "is_laptop", "no_charge"],
  "not_conditions": ["adapter_confirmed_faulty"],
  "adds_facts": ["probable_battery_issue"],
  "triggers_diagnosis": "DIAG_PWR_02",
  "priority": 3,
  "cf": 0.85
}
```

**Cấu trúc Diagnosis:**
```json
{
  "id": "DIAG_PWR_02",
  "name": "Pin laptop chai hoặc hỏng",
  "severity": "MEDIUM",
  "user_fixable": true,
  "needs_technician": false,
  "default_cf": 0.82,
  "solution_steps": [
    "Kiểm tra đèn sạc khi cắm adapter",
    "Thử calibrate pin (xả hết rồi sạc đầy)",
    "Nếu pin vẫn không sạc → thay pin mới"
  ],
  "warning": "Không dùng pin trong môi trường nóng ẩm",
  "symptoms": ["no_power", "is_laptop", "no_charge", "laptop_only_on_adapter"]
}
```

---

## VIII. Luồng End-to-End — Ví dụ Thực Tế

### Scenario: "Laptop không lên nguồn, không sạc được"

```
[1] User mở http://localhost:5000
    → GET / → render chat.html
    → JS: startSession() → POST /start
    → Flask: store.create() → DiagnosticSession(Q01)
    → Response: {session_id: "abc...", question: Q01, bot_message: greeting}
    → JS: renderQuickReplies(Q01) → 8 buttons hiện ra

[2] User click "Máy không bật / không có điện"
    → POST /select {session_id, question_id: "Q01", value: "A"}
    → Flask: ds.answer(["A"])
      → flow.process_answer("Q01", ["A"], engine)
        → option A: adds_facts=["user_reports_power_issue"]
        → engine.add_facts(["user_reports_power_issue"])
        → engine.run_until_stable() ← chưa rule nào fire
        → next_question_id = "Q02"
    → Response: {question: Q02, bot_message: "Khi bạn nhấn nút nguồn..."}

[3] User gõ "hoàn toàn không có phản ứng gì" (text input)
    → POST /message {..., text: "hoàn toàn không có phản ứng gì"}
    → Flask:
      intent_clf.classify() → {intent: "power_startup", confidence: 0.91}
      fact_extractor.extract() → {facts: ["no_power", "fan_not_spinning"]}
      
      _match_text_to_option(text, Q02, ["no_power", "fan_not_spinning"]):
        Option A adds_facts=["no_power","fan_not_spinning"]:
          overlap = {"no_power","fan_not_spinning"} → score = 2×10 = 20
        MATCH! value = "A"
      
      ds.answer(["A"])
        → engine.add_facts(["no_power", "fan_not_spinning"])
        → WM: {user_reports_power_issue, no_power, fan_not_spinning}
        → engine.run_until_stable()
          → R001 (conditions: no_power): NOT applicable (missing is_laptop)
          → R002 (conditions: no_power, is_desktop): NOT applicable
          → No rules fire yet
        → next_question = "Q03"
    → Response: {question: Q03, facts_added: ["no_power","fan_not_spinning"]}
    → JS: side panel cập nhật fact tags

[4] User gõ "laptop" (text input)
    → POST /message {..., text: "laptop"}
    → _match_text_to_option("laptop", Q03, ["is_laptop"]):
        Option A: adds_facts=["is_laptop"], overlap={"is_laptop"}: score=10
        Option B: adds_facts=["is_desktop"]: score=0
        MATCH! value = "A"
    → ds.answer(["A"])
      → engine.add_facts(["is_laptop"])
      → WM: {user_reports_power_issue, no_power, fan_not_spinning, is_laptop}
      → engine.run_until_stable()
        → MATCH: R012 (conditions: no_power, is_laptop)
          FIRE R012 → adds_facts: ["probable_power_issue_laptop"]
          WM + "probable_power_issue_laptop"
        → MATCH: R013 (conditions: probable_power_issue_laptop)
          FIRE R013 → adds_facts: ["check_adapter_and_battery"]
          → No more rules
      → next_question = "Q05"
    → Response: {question: Q05, facts: ["is_laptop"]}

[5] User click "Đèn sạc sáng nhưng pin không tăng"
    → POST /select {question_id: "Q05", value: "B"}
    → option B: adds_facts=["no_charge"]
    → ds.answer(["B"])
      → engine.add_facts(["no_charge"])
      → WM + "no_charge"
      → run_until_stable():
        → MATCH R015 (no_power, is_laptop, no_charge)
          FIRE → triggers_diagnosis: "DIAG_PWR_02" (CF=0.85)
        → diagnosis_cf_map: {DIAG_PWR_02: 0.85}
      → is_terminal = True (option B: no next)
    → Response: {session_complete: True, diagnoses: [...]}
    → JS: showDiagnosisModal() → hiển thị kết quả

[6] User click "Xem giải thích chi tiết"
    → GET /explanation?session_id=abc...
    → build_full_explanation(session):
      question_path: [Q01→A, Q02→A, Q03→A, Q05→B]
      facts: [user_reports_power_issue, no_power, fan_not_spinning,
              is_laptop, probable_power_issue_laptop,
              check_adapter_and_battery, no_charge]
      rules_fired: [R012, R013, R015]
      diagnoses: [{id: DIAG_PWR_02, name: "Pin laptop chai...", cf: 0.85}]
    → JS: renderExplanation() → hiển thị modal
```

---

## IX. Tổng Kết Kỹ Thuật

### Kiến trúc theo tầng (Layered Architecture)

| Tầng | Module | Không phụ thuộc vào |
|---|---|---|
| Knowledge Base | JSON files | — |
| Engine Core | `working_memory`, `rule_model` | — |
| Inference | `forward_engine` | Engine core |
| Session | `diagnostic_session`, `question_selector`, `explanation_builder` | Inference |
| NLU | `patterns`, `intent_classifier`, `fact_extractor` | — (độc lập) |
| Services | `session_store` | Session |
| Web API | `app.py` | Tất cả layers trên |
| Frontend | HTML/CSS/JS | Flask API |

### Điểm mạnh của thiết kế

| Điểm | Giải thích |
|---|---|
| **Separation of Concerns** | Mỗi module có 1 trách nhiệm rõ ràng |
| **Knowledge Independence** | Engine không hardcode rule — đọc từ JSON |
| **Explainability** | Explanation Facility trace từng bước suy luận |
| **Extensibility** | Thêm rule/question chỉ cần sửa JSON |
| **Testability** | 43 unit tests, không phụ thuộc browser |
| **Thread Safety** | SessionStore dùng Lock cho multi-user |
| **Graceful Fallback** | Mọi layer đều có fallback khi không xác định được |

### Giới hạn của hệ thống

| Giới hạn | Lý do |
|---|---|
| NLU keyword-based | Không xử lý được câu phức tạp, ngữ nghĩa ẩn |
| In-memory sessions | Mất data khi restart Flask |
| Single-language (Vi) | Patterns chỉ tiếng Việt |
| Sequential questions | Multi-modal diagnosis chưa hoàn thiện |

---

*Tài liệu được tạo tự động từ source code — PC Expert v1.0.0*
