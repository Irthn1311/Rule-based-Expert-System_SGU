# Báo Cáo Học Thuật: Hệ Thống Chuyên Gia Chẩn Đoán Lỗi Máy Tính

> **Môn học:** Công Nghệ Tri Thức  
> **Cơ sở:** Trường Đại học Sài Gòn (SGU)

---

## 1. Biểu Diễn Tri Thức (Knowledge Representation)

### 1.1. Facts — Biểu Diễn Tri Thức Dạng Tình Trạng

Hệ thống áp dụng mô hình **biểu diễn sự kiện dạng ký hiệu nguyên tử (atomic symbolic facts)**. Mỗi fact là một chuỗi định danh định nghĩa trước (tiếng Anh, dạng `snake_case`) đại diện cho một tình trạng quan sát được của máy tính. Tập hợp tất cả facts đang hoạt động trong một phiên làm việc được lưu trữ trong cấu trúc **Working Memory** — hay còn gọi là *Fact Base*.

**Đặc điểm của tập Facts:**

- **Monotonic** (đơn điệu): Facts chỉ được **thêm vào** (assert), không bao giờ bị thu hồi (retract) trong suốt một phiên chẩn đoán. Đây là quyết định thiết kế có chủ ý, đảm bảo tính nhất quán của quá trình suy luận theo mô hình closed-world assumption.
- **Symbolic**: Mỗi fact là một token biểu tượng, không mang giá trị số. Ví dụ: `no_power`, `battery_indicator_red`, `is_laptop`, `screen_black`, `bsod_appears`, v.v.
- **Nguồn gốc được truy vết**: Mỗi fact được ghi nhận cùng nguồn gốc (source) — hoặc từ câu trả lời của người dùng (`question_id:option_value`), hoặc do một luật suy luận tạo ra (phần thân hậu kiện của luật).

**Phân loại theo nguồn gốc:**

| Loại | Ví dụ | Nguồn |
|------|-------|-------|
| Facts quan sát trực tiếp | `no_power`, `screen_black`, `bsod_appears` | Câu trả lời người dùng |
| Facts phân loại thiết bị | `is_laptop`, `is_desktop` | Câu trả lời người dùng |
| Facts trung gian (derived facts) | `probable_adapter_issue`, `thermal_throttling`, `ram_related_bsod` | Kích hoạt bởi luật trung gian |
| Facts bối cảnh | `recent_change_caused_issue`, `malware_suspected`, `psu_tested_ok` | Câu trả lời người dùng |

Tính đến phiên bản hiện tại, tri thức cơ sở (knowledge base) sử dụng trên **120 ký hiệu facts** phân bố trên 8 nhóm chủ đề: nguồn điện, màn hình, hệ điều hành, mạng, âm thanh/camera, ngoại vi, hiệu năng và lưu trữ.

---

### 1.2. Rules — Biểu Diễn Tri Thức Dạng Luật IF-THEN

Hệ thống tổ chức tri thức chẩn đoán dưới dạng **103 luật IF-THEN** được lưu trữ trong tập tin JSON (`07_rules_and_diagnoses.json`). Cấu trúc hình thức của một luật được định nghĩa như sau:

```
RULE_id:
  IF   conditions = {f₁, f₂, ..., fₙ}
  AND  NOT not_conditions = {g₁, g₂, ..., gₘ}
  THEN [adds_facts = {h₁, h₂, ...}]
       [triggers_diagnosis = DIAG_id]
  WITH priority ∈ {1,2,3,4,5},  cf ∈ [0.0, 1.0]
```

**Hậu kiện (consequent) của một luật có thể thực hiện hai tác vụ:**

1. **Thêm facts trung gian** vào Working Memory — tạo ra bước suy luận nhiều tầng (multi-step chaining). Ví dụ: R001 khẳng định `probable_adapter_issue` rồi R002 đọc fact đó để kích hoạt chẩn đoán cuối cùng.

2. **Kích hoạt một chẩn đoán** trực tiếp (`triggers_diagnosis`) — kết thúc chuỗi suy luận cho một nhánh nhất định.

**Thuộc tính siêu dữ liệu của mỗi luật:**

| Trường | Kiểu | Ý nghĩa |
|--------|------|---------|
| `id` | String | Định danh duy nhất (R001, R_BT01, ...) |
| `group` | Enum | Nhóm triệu chứng (power_startup, display, ...) |
| `priority` | Int [1–5] | Độ ưu tiên cho conflict resolution |
| `cf` | Float [0–1] | Certainty Factor theo mô hình MYCIN |
| `conditions` | List[String] | Mệnh đề tiền kiện (AND logic) |
| `not_conditions` | List[String] | Phủ định tiền kiện (NOT logic) |
| `adds_facts` | List[String] | Hậu kiện — thêm facts mới |
| `triggers_diagnosis` | String? | Hậu kiện — kích hoạt chẩn đoán |

**Ví dụ minh họa — chuỗi suy luận 2 bước:**

```
R001: IF {no_power, battery_indicator_red, is_laptop}
      THEN adds_facts: [probable_adapter_issue]     (CF=0.85, priority=3)

R002: IF {probable_adapter_issue, no_charge}
      THEN triggers_diagnosis: DIAG_PWR_01           (CF=0.90, priority=4)
```

**Ví dụ minh họa — luật có điều kiện phủ định:**

```
R003: IF {power_led_on, laptop_only_on_adapter, is_laptop}
      AND NOT {no_charge}
      THEN triggers_diagnosis: DIAG_PWR_02           (CF=0.85, priority=3)
```

Điều kiện phủ định (`not_conditions`) đóng vai trò **ngăn chặn kích hoạt sai** khi ngữ cảnh mâu thuẫn — đây là cơ chế phân biệt các trường hợp biên quan trọng trong chẩn đoán kỹ thuật.

---

### 1.3. Diagnoses — Biểu Diễn Tri Thức Dạng Kết Luận

Hệ thống định nghĩa **50 chẩn đoán** (`DIAG_*`) được cấu trúc như các đối tượng tri thức giàu ngữ nghĩa. Mỗi chẩn đoán không chỉ là một nhãn (label) mà còn mang theo toàn bộ thông tin hành động cần thiết cho người dùng.

**Cấu trúc một đối tượng chẩn đoán:**

| Trường | Ý nghĩa |
|--------|---------|
| `id` | Định danh (VD: `DIAG_PWR_01`) |
| `code` | Mã kỹ thuật (VD: `faulty_adapter`) |
| `name` | Tên mô tả bằng tiếng Việt |
| `group` | Nhóm chủ đề |
| `severity` | Mức độ nghiêm trọng: CRITICAL / HIGH / MEDIUM / LOW |
| `user_fixable` | Người dùng tự khắc phục được không |
| `symptoms` | Danh sách facts triệu chứng liên quan |
| `solution_steps` | Các bước khắc phục tuần tự |
| `needs_technician` | Có cần kỹ thuật viên không |
| `warning` | Cảnh báo đặc biệt (nếu có) |
| `default_cf` | CF mặc định khi kích hoạt trực tiếp qua question |

**Phân bố theo nhóm và mức độ nghiêm trọng:**

| Nhóm | Tổng chẩn đoán | CRITICAL | HIGH | MEDIUM | LOW |
|------|---------------|----------|------|--------|-----|
| power_startup | 8 | 1 | 5 | 2 | 0 |
| display | 5 | 0 | 2 | 2 | 1 |
| os_boot | 6 | 1 | 4 | 0 | 1 |
| network | 6 | 0 | 2 | 2 | 2 |
| audio_camera | 5 | 0 | 1 | 2 | 2 |
| peripherals | 9 | 0 | 3 | 4 | 2 |
| performance | 4 | 0 | 2 | 1 | 1 |
| storage | 4 | 1 | 2 | 1 | 0 |
| general | 1 | 0 | 1 | 0 | 0 |

---

## 2. Cơ Chế Suy Luận (Inference Mechanism)

### 2.1. Quá Trình Forward Chaining

Hệ thống áp dụng chiến lược **Forward Chaining** (Suy luận Tiến) — xuất phát từ dữ liệu quan sát (facts) và suy luận về phía kết luận (diagnoses), trái ngược với Backward Chaining vốn bắt đầu từ giả thuyết và kiểm chứng ngược lại.

Chu trình suy luận cơ bản tuân theo vòng lặp **MATCH → SELECT → FIRE** kinh điển (lấy cảm hứng từ kiến trúc Rete), được thực thi bởi lớp `ForwardChainingEngine`:

```
REPEAT {
    Conflict_Set ← MATCH(Rules, Working_Memory)
    IF Conflict_Set = ∅ THEN STOP   ← Fixed Point
    best_rule ← SELECT(Conflict_Set)
    FIRE(best_rule) → update(Working_Memory)
} UNTIL Fixed_Point OR MAX_ITERATIONS = 100
```

**Giai đoạn MATCH (Pattern Matching):**

Với mỗi luật `R` trong tập luật, hệ thống kiểm tra điều kiện kích hoạt:

```
applicable(R, WM) ≡
    ∀f ∈ R.conditions : f ∈ WM
    ∧ ∀g ∈ R.not_conditions : g ∉ WM
    ∧ ¬R.fired
```

Luật chỉ được xét nếu: (1) toàn bộ điều kiện tiền kiện đều có mặt trong Working Memory, (2) không có bất kỳ điều kiện phủ định nào bị vi phạm, và (3) luật chưa từng được kích hoạt trong phiên hiện tại (cơ chế **no-loop** tự nhiên).

**Giai đoạn FIRE (Activation):**

Khi một luật được kích hoạt:
- Đánh dấu `fired = True` để ngăn kích hoạt lại.
- Thêm tất cả `adds_facts` vào Working Memory (nếu chúng chưa tồn tại).
- Nếu có `triggers_diagnosis`: tính toán và ghi nhận Certainty Factor vào bảng kết quả chẩn đoán.

**Đặc tính Fixed Point:**

Quá trình dừng lại tại *điểm cố định* (fixed point) — trạng thái mà trong đó không còn luật nào khả dụng. Để phòng ngừa vòng lặp vô hạn trong các trường hợp tri thức bất nhất, hệ thống giới hạn cứng tối đa **100 vòng lặp** (MAX_ITERATIONS = 100) — giải pháp bảo vệ an toàn tiêu chuẩn trong thiết kế production expert systems.

---

### 2.2. Conflict Resolution — Giải Quyết Xung Đột

Khi nhiều luật đồng thời thỏa mãn điều kiện kích hoạt (tức Conflict Set có kích thước > 1), hệ thống áp dụng chiến lược **ưu tiên đa tiêu chí (multi-criteria priority)** để lựa chọn luật tốt nhất:

```
score(R) = (R.priority, R.specificity, R.cf)
```

Các tiêu chí được sắp xếp theo thứ tự ưu tiên giảm dần:

| Tiêu chí | Định nghĩa | Lý cớ học thuật |
|----------|-----------|-----------------|
| **Priority** (1–5) | Giá trị ưu tiên được chỉ định thủ công bởi knowledge engineer | Phản ánh tầm quan trọng chuyên môn của luật trong ngữ cảnh chẩn đoán |
| **Specificity** | `len(conditions) + len(not_conditions)` | Luật có nhiều điều kiện hơn = cụ thể hơn = phù hợp chính xác hơn với tình huống (tránh over-generalization) |
| **Certainty Factor** | Giá trị CF ∈ [0.0, 1.0] | Luật có độ tin cậy cao hơn được ưu tiên |

Tiêu chí **Specificity** được lấy cảm hứng từ nguyên lý *Most Specific Rule First* — nguyên tắc phổ biến trong thiết kế rule-based systems, tương tự cơ chế conflict resolution của CLIPS và OPS5.

**Ví dụ minh họa:**

Giả sử có R_Q08_MOBO (priority=5, 4 điều kiện) và R005 (priority=3, 1 điều kiện) cùng khả dụng trong một tình huống. Hệ thống sẽ ưu tiên kích hoạt R_Q08_MOBO trước vì có priority cao hơn và specificity cao hơn — dẫn đến chẩn đoán chính xác hơn (bo mạch chủ hỏng) thay vì kết luận chung (PSU hỏng).

---

### 2.3. Kết Hợp Certainty Factor — Mô Hình MYCIN

Hệ thống áp dụng **công thức kết hợp Certainty Factor của MYCIN** khi cùng một chẩn đoán được kích hoạt bởi nhiều luật độc lập:

```
CF_combined = CF₁ + CF₂ × (1 − CF₁)
```

Công thức này có tính chất:
- **Monotone tăng**: Mỗi bằng chứng mới chỉ làm tăng hoặc duy trì mức độ tin cậy, không bao giờ giảm.
- **Bão hòa về 1**: Giới hạn trên là 1.0 nhưng không bao giờ đạt được qua phép tính hữu hạn.
- **Đối xứng**: `combine(CF₁, CF₂) = combine(CF₂, CF₁)`.

Cơ chế này cho phép hệ thống hỗ trợ **lập luận từ nhiều nguồn bằng chứng khác nhau** — một tính năng quan trọng để chẩn đoán các tình huống phức tạp mà chỉ một luật duy nhất không đủ sức kết luận.

---

## 3. Kiến Trúc Hệ Thống (System Architecture)

Hệ thống được tổ chức theo kiến trúc phân tầng gồm **4 tầng chức năng** tách biệt, tuân theo nguyên lý Separation of Concerns:

```
┌─────────────────────────────────────────────────────────┐
│                  PRESENTATION LAYER                     │
│           Web Chat UI  ·  Decision Tree Viz             │
├─────────────────────────────────────────────────────────┤
│                  APPLICATION LAYER                      │
│     DiagnosticSession  ·  QuestionFlowManager          │
│     NLU (IntentClassifier · FactExtractor)             │
├─────────────────────────────────────────────────────────┤
│                   INFERENCE LAYER                       │
│   ForwardChainingEngine  ·  WorkingMemory              │
│   QuestionSelector (Dynamic Q)  ·  ExplanationBuilder  │
├─────────────────────────────────────────────────────────┤
│                  KNOWLEDGE BASE LAYER                   │
│      06_questions.json  ·  07_rules_and_diagnoses.json │
│  (50 Questions · 103 Rules · 50 Diagnoses · 8 Groups)  │
└─────────────────────────────────────────────────────────┘
```

**Mô tả các tầng:**

**Tầng Tri Thức (Knowledge Base Layer):** Tách biệt hoàn toàn nội dung tri thức khỏi cơ chế suy luận — thể hiện nguyên lý tách biệt *knowledge* và *engine* trong xây dựng hệ chuyên gia. Toàn bộ tri thức được lưu trữ dưới dạng JSON có cấu trúc chuẩn, có thể cập nhật mà không cần sửa code.

**Tầng Suy Luận (Inference Layer):** Chứa `ForwardChainingEngine` và `WorkingMemory` — nhân lõi của hệ thống. Tầng này hoàn toàn không biết về giao diện người dùng hay cách thức thu thập dữ liệu. Nó chỉ nhận facts và trả về kết quả suy luận.

**Tầng Ứng Dụng (Application Layer):** Điều phối toàn bộ luồng phiên chẩn đoán, quản lý trạng thái, xử lý câu hỏi/câu trả lời và phân tích ngữ nghĩa văn bản đầu vào (NLU module).

**Tầng Giao Diện (Presentation Layer):** Giao diện chat web với khả năng hiển thị cây quyết định động — cung cấp trải nghiệm tương tác cho người dùng cuối.

**Luồng dữ liệu trong một phiên chẩn đoán:**

```
User Input (Text hoặc Option Selection)
    │
    ▼
[NLU Layer] → Intent Classification → Skip Q01 nếu intent rõ ràng
    │
    ▼
[DiagnosticSession] → xử lý câu trả lời, ghi nhận lịch sử
    │
    ▼
[QuestionFlowManager] → thêm facts vào Working Memory
    │
    ▼
[ForwardChainingEngine] → run_until_stable() → MATCH/SELECT/FIRE
    │
    ▼
[DiagnósisResult + CF] → ghi nhận kết luận, cập nhật CF_map
    │
    ▼
[QuestionSelector] → chọn câu hỏi tiếp theo thông minh
    │
    ▼
[ExplanationBuilder] → tạo giải thích lý luận
    │
    ▼
Presentation Layer → hiển thị kết quả cho người dùng
```

---

## 4. Explanation Facility — Cơ Chế Giải Thích

**Explanation Facility** (Cơ sở giải thích) là một trong những đặc trưng phân biệt hệ chuyên gia với các hệ thống phân loại thông thường. Nó cho phép hệ thống trả lời hai câu hỏi căn bản: **"Tại sao bạn hỏi điều này?"** và **"Tại sao bạn đưa ra kết luận đó?"**

### 4.1. Giải Thích Inline (Short Explanation)

Trong quá trình hỏi đáp, mỗi câu hỏi được kèm theo một giải thích ngắn (1–2 câu) hiển thị ngay bên dưới trong giao diện chat. Giải thích này được tạo ra theo thứ tự ưu tiên:

1. **Trường `purpose` của câu hỏi** (được định nghĩa sẵn trong knowledge base): Ví dụ, câu hỏi Q04 có purpose *"Số tiếng beep là mã lỗi BIOS — phân biệt POST thành công hay thất bại"*.
2. **Các luật gần kích hoạt nhất** (near-fire rules): Nếu không có purpose, hệ thống tổng hợp từ tên của 2 luật đang gần thỏa mãn nhất.
3. **Giải thích mặc định dự phòng**: Câu tổng quát về mục đích thu hẹp nguyên nhân.

### 4.2. Giải Thích Toàn Diện (Full Explanation)

Sau khi hoàn thành chẩn đoán, `ExplanationBuilder.build_full_explanation()` tổng hợp một báo cáo lý luận đầy đủ bao gồm:

**a) Đường Dẫn Câu Hỏi (Question Path):** Danh sách có thứ tự tất cả các câu hỏi đã được hỏi, câu trả lời người dùng chọn, được thể hiện bằng nhãn ngôn ngữ tự nhiên thay vì mã kỹ thuật.

**b) Lịch Sử Facts (Fact History):** Toàn bộ facts trong Working Memory cùng nguồn gốc của từng fact — cho phép người dùng (hoặc chuyên gia kiểm tra) truy vết nguồn gốc của từng thông tin trong quá trình suy luận.

**c) Dấu Vết Luật (Rule Trace):** Danh sách theo thứ tự thời gian các luật đã kích hoạt, bao gồm:
- Tên của luật (có thể đọc hiểu bởi con người).
- Các facts được thêm vào bởi luật.
- Chẩn đoán được kích hoạt (nếu có).
- Certainty Factor ở dạng phần trăm (%).

**d) Tường Thuật Ngôn Ngữ Tự Nhiên (Natural Language Narration):** Bộ giải thích tạo ra một chuỗi văn xuôi tiếng Việt mô tả toàn bộ quá trình chẩn đoán — phù hợp để trình bày kết quả cho người dùng không có nền tảng kỹ thuật.

**e) Tóm Tắt Thống Kê:** Số câu hỏi đã hỏi, số facts thu thập được, số luật đã kích hoạt, số chẩn đoán tìm được — cung cấp cái nhìn định lượng về quá trình suy luận.

**Ví dụ minh họa — một chuỗi giải thích:**

```
📋 Quá trình chẩn đoán:
  1. Máy tính đang gặp vấn đề gì? → "Máy không bật / không có điện"
  2. Khi nhấn nút nguồn, điều gì xảy ra? → "Hoàn toàn không có phản ứng"
  3. Laptop hay Desktop? → "Laptop"
  4. Tình trạng pin và sạc? → "Đèn sạc không sáng khi cắm adapter"

🔍 Luật đã kích hoạt:
  • Adapter hỏng — đèn pin đỏ + không sạc: thêm facts [probable_adapter_issue]
  • Xác nhận Adapter hỏng: → DIAG_PWR_01 (CF=90%)

✅ Kết quả chẩn đoán:
  🥇 Adapter nguồn hỏng — Độ tin cậy: 90%
     Mức độ: 🟠 Cao — cần xử lý ngay
     Cách xử lý: Kiểm tra đèn LED adapter · Thử ổ điện khác · Mua adapter chính hãng mới
```

Explanation Facility đóng vai trò kép: vừa **tăng tính tin cậy** (người dùng hiểu tại sao hệ thống đưa ra kết luận), vừa phục vụ cho **mục đích giáo dục** (giải thích quy trình chẩn đoán cho người học kỹ thuật máy tính).

---

## 5. Dynamic Questioning — Cơ Chế Chọn Câu Hỏi Động

**Dynamic Questioning** (Hỏi Đáp Động) là cơ chế cho phép hệ thống lựa chọn câu hỏi tiếp theo một cách *thông minh* thay vì tuân theo một thứ tự cố định. Mục tiêu là tối thiểu hoá số câu hỏi cần hỏi trong khi tối đa hoá lượng thông tin phân biệt thu thập được — nguyên lý tiếp cận gần với Information Gain trong lý thuyết decision tree.

### 5.1. Cơ Chế Near-Fire Detection

Trước khi chọn câu hỏi, hệ thống xác định tập **Near-Fire Rules** — các luật *gần thỏa mãn điều kiện kích hoạt*, tức là chỉ còn thiếu tối đa 3 facts (`MAX_MISSING = 3`):

```
near_fire_rules = {
    R ∈ Rules |
    ¬R.fired
    ∧ ¬blocked(R, WM)
    ∧ 0 < |{f ∈ R.conditions : f ∉ WM}| ≤ 3
}
```

Trong đó `blocked(R, WM)` là điều kiện đã vi phạm not_conditions. Tập này được sắp xếp theo số lượng facts còn thiếu tăng dần — luật gần thỏa mãn nhất xuất hiện đầu tiên.

### 5.2. Thuật Toán Scoring Câu Hỏi

`QuestionSelector` tính điểm cho mỗi câu hỏi ứng viên theo hàm đa tiêu chí:

```
score(Q) = w_cov × coverage(Q)
         + w_disc × discrimination(Q)
         + w_group × group_bonus(Q)
         + proximity_bonus(Q)
```

Với:
- `w_cov = 2.0`, `w_disc = 1.5`, `w_group = 0.5`

**Coverage Score** — Đo mức độ bao phủ missing facts:

```
coverage(Q) = |facts(Q) ∩ MissingFacts(NearFireRules)| × 2.0
```

Câu hỏi có thể trả lời được nhiều fact còn thiếu sẽ được ưu tiên — nguyên lý tương tự *Maximum Mutual Information* trong thiết kế câu hỏi tối ưu.

**Discrimination Score** — Đo khả năng phân biệt chẩn đoán:

```
discrimination(Q) = (|{D ∈ Diagnoses : facts(Q) ∩ symptoms(D) ≠ ∅}| / |Diagnoses|) × 1.5
```

Câu hỏi giúp phân biệt được nhiều chẩn đoán hơn được ưu tiên — cơ chế phân tách không gian chẩn đoán hiệu quả.

**Proximity Bonus** — Khoảng cách đến kích hoạt:

```
proximity(Q, R) = |facts(Q) ∩ MissingFacts(R)| / |MissingFacts(R)|
proximity_bonus(Q) = Σ_{R ∈ top3(NearFireRules)} proximity(Q, R)
```

Câu hỏi giúp kích hoạt sớm các luật gần nhất được thưởng điểm cao hơn.

**Group Bonus** — Tính liên tục ngữ cảnh:

```
group_bonus(Q) = 0.5 nếu Q.group = current_group, 0 nếu khác
```

Giữ cho phiên chẩn đoán tập trung vào một nhóm chủ đề thay vì nhảy nhóm tùy tiện — đảm bảo trải nghiệm hỏi đáp tự nhiên và logic.

### 5.3. Cơ Chế Fallback và Cân Bằng

Để đảm bảo Dynamic Questioning không phá vỡ luồng chẩn đoán có cấu trúc được thiết kế trong knowledge base, hệ thống áp dụng **chiến lược cân bằng**:

- Câu hỏi mặc định từ JSON flow (fallback_qid) được ưu tiên trừ khi có một câu hỏi động với điểm cao hơn **1.5 lần** — ngưỡng này được chọn để đảm bảo Dynamic Questioning chỉ can thiệp khi có lợi ích rõ ràng.
- Câu hỏi đã được hỏi trong phiên hiện tại (`asked_qids`) bị loại hoàn toàn khỏi tập ứng viên — tránh lặp câu hỏi gây khó chịu cho người dùng.
- Nếu không có câu hỏi động phù hợp, hệ thống trả về `fallback_qid` — đảm bảo luôn có câu hỏi tiếp theo.

**Cơ chế vào nhóm nhanh (NLU Integration):**

Trước khi bắt đầu phiên hỏi đáp, module NLU (`IntentClassifier`) phân tích văn bản tự do của người dùng. Nếu người dùng mô tả trực tiếp vấn đề (ví dụ: *"laptop không bật"*, *"màn hình đen"*, *"wifi không kết nối được"*), hệ thống xác định intent với độ tin cậy cao và **bỏ qua câu hỏi Q01** (câu hỏi phân loại nhóm đầu tiên), nhảy thẳng vào câu hỏi chuyên sâu của nhóm phù hợp — tiết kiệm một bước hỏi đáp không cần thiết.

---

## 6. Module NLU — Xử Lý Ngôn Ngữ Tự Nhiên

Hệ thống tích hợp một module **Natural Language Understanding (NLU)** nhẹ (lightweight) không dựa vào mô hình ngôn ngữ lớn, bao gồm hai thành phần độc lập nhưng phối hợp chặt chẽ: `IntentClassifier` và `FactExtractor`.

### 6.1. IntentClassifier — Phân Loại Ý Định

`IntentClassifier` sử dụng kỹ thuật **Weighted Keyword Counting** để xác định nhóm vấn đề mà người dùng đang đề cập. Quá trình phân loại diễn ra theo các bước:

1. **Chuẩn hóa văn bản**: Chuyển về chữ thường, loại bỏ ký tự đặc biệt, giữ nguyên dấu tiếng Việt (UTF-8 range `\u1E00-\u1EFF`).
2. **Tính điểm từng intent**: Với mỗi keyword khớp trong văn bản, cộng trọng số:
   ```
   weight = 1.0 + |tokens(keyword)| × 0.3
   ```
   Từ khóa nhiều từ (multi-word) được trọng số cao hơn — phản ánh tính đặc trưng (specificity) cao hơn của cụm từ ghép so với từ đơn.
3. **Chuẩn hóa điểm**: Toàn bộ điểm được normalize về khoảng [0, 1] theo tổng.
4. **Ngưỡng quyết định**:
   - `confidence ≥ INTENT_MIN_CONFIDENCE`: intent được xác định.
   - `confidence ≥ INTENT_HIGH_CONFIDENCE`: intent được xem là *chắc chắn* → cho phép bỏ qua Q01.

Kết quả: một trong 8 intent tương ứng với 8 nhóm chủ đề của knowledge base, hoặc `None` nếu không xác định được.

### 6.2. FactExtractor — Trích Xuất Facts

`FactExtractor` áp dụng **ordered pattern matching** trên `KEYWORD_FACT_MAP` — một bảng ánh xạ được thiết kế thủ công từ các cụm từ tiếng Việt thường gặp đến các fact symbols. Ví dụ:

| Pattern tiếng Việt | Facts được trích xuất |
|--------------------|----------------------|
| `"không bật được"` | `["no_power"]` |
| `"màn hình đen"` | `["screen_black"]` |
| `"máy tự tắt"` | `["machine_shuts_down_abruptly"]` |
| `"wifi không bắt sóng"` | `["wifi_not_visible"]` |
| `"đèn pin đỏ"` | `["battery_indicator_red"]` |

Mỗi pattern được so sánh với văn bản đã chuẩn hóa — một văn bản có thể khớp nhiều pattern và sinh ra nhiều facts đồng thời.

### 6.3. Luồng Xử Lý Văn Bản Tự Do

Khi người dùng nhập văn bản tự do (thay vì click option), hệ thống áp dụng chiến lược ưu tiên 3 bước trong route `/message`:

```
① Option Matching (ưu tiên nhất):
   Nếu facts trích được hoặc nhãn option khớp văn bản
   → Coi như người dùng chọn option đó → advance câu hỏi (ds.answer())

② Fact Injection (không advance câu hỏi):
   Nếu có facts cụ thể nhưng không khớp option rõ ràng
   → Thêm facts vào Working Memory → chạy forward chaining
   → Nếu intent rõ + đang ở Q01 → skip đến nhóm câu hỏi phù hợp

③ Fallback:
   Nếu không hiểu → hiển thị thông báo gợi ý dùng nút bấm
```

Thiết kế này cho phép hệ thống hỗ trợ cả tương tác dạng nút bấm (structured) lẫn văn bản tự nhiên (unstructured), tạo ra trải nghiệm hybrid linh hoạt.

---

## 7. Quản Lý Phiên Làm Việc (Session Management)

Hệ thống hỗ trợ **phiên chẩn đoán song song** — nhiều người dùng có thể sử dụng đồng thời, mỗi người với một phiên độc lập. Thành phần `SessionStore` (trong `services/session_store.py`) chịu trách nhiệm quản lý vòng đời phiên:

- **Tạo phiên**: Mỗi phiên nhận một UUID duy nhất làm định danh (`session_id`).
- **Lưu trữ**: In-memory dictionary (không persistence) — phù hợp với mục đích học thuật.
- **Trạng thái phiên**: Mỗi `DiagnosticSession` duy trì:
  - `current_question_id`: câu hỏi hiện tại.
  - `history`: toàn bộ lịch sử Q&A.
  - `asked_question_ids`: tập câu hỏi đã hỏi (cho Dynamic Questioning).
  - `current_group`: nhóm chủ đề đang chẩn đoán.
  - `is_complete`: trạng thái kết thúc phiên.
  - `final_diagnoses`: danh sách kết quả chẩn đoán (đã dedup, sắp xếp theo CF).

**Điểm cuối API (REST Endpoints):**

| Method | Route | Chức năng |
|--------|-------|-----------|
| GET | `/` | Giao diện chat HTML |
| POST | `/start` | Tạo phiên mới, trả Q01 |
| POST | `/message` | Xử lý văn bản tự do (NLU pipeline) |
| POST | `/select` | Xử lý lựa chọn đơn (single_choice / yes_no) |
| POST | `/submit` | Xử lý lựa chọn nhiều (multi_choice) |
| GET | `/explanation` | Lấy giải thích đầy đủ của phiên |
| POST | `/reset` | Khởi tạo lại phiên mới |
| GET | `/api/tree` | Trả toàn bộ DAG JSON (cached) |
| GET | `/api/tree-path` | Trả đường đi của phiên để highlight |
| GET | `/status` | Health check + thống kê KB |

---

## 8. Trực Quan Hóa Cây Quyết Định (Decision Tree Visualization)

Hệ thống tích hợp tính năng **trực quan hóa cây quyết định động** — một công cụ hỗ trợ học thuật và giải thích quan trọng. Module `DecisionTreeBuilder` xây dựng một **Directed Acyclic Graph (DAG)** từ knowledge base sử dụng thuật toán BFS (Breadth-First Search):

### Đặc điểm của DAG:

- **Root node**: Q01 (câu hỏi phân loại đầu tiên).
- **Internal nodes**: Các câu hỏi (Question nodes) — được tô màu theo nhóm.
- **Leaf nodes**: Các chẩn đoán (Diagnosis nodes) — được tô màu theo mức độ nghiêm trọng (CRITICAL/HIGH/MEDIUM/LOW).
- **Merged nodes**: Các câu hỏi được chia sẻ bởi nhiều nhánh chỉ xuất hiện một lần (DAG, không phải tree đơn thuần) — giảm kích thước đồ thị đáng kể.
- **Group propagation**: Nhóm chủ đề được lan truyền từ Q01 xuống toàn bộ subtree tương ứng qua BFS.

### Tính năng highlight đường đi:

Sau khi hoàn thành phiên chẩn đoán, route `/api/tree-path` trả về:
- `node_ids`: tập hợp ID các nút đã đi qua.
- `edge_keys`: các cạnh đã sử dụng, dưới dạng `"QID:OptionValue"` (ví dụ: `"Q03:A"`).
- `primary_group`: nhóm chủ đề chính của phiên.

Frontend sử dụng thông tin này để **highlight nhánh suy luận cụ thể** trên toàn cây — giúp người dùng hình dung trực quan quá trình chẩn đoán từ câu hỏi gốc đến kết luận cuối cùng, đồng thời tạo điều kiện giải thích kết quả theo phong cách trực quan.

---

## 9. Thống Kê Hệ Thống và Đánh Giá Định Lượng

### 9.1. Quy Mô Tri Thức

| Thành phần | Số lượng | Ghi chú |
|-----------|----------|---------|
| Câu hỏi (Questions) | 50 | Bao gồm yes/no, single_choice, multi_choice |
| Luật IF-THEN (Rules) | 103 | Phân bố đều trên 8 nhóm |
| Chẩn đoán (Diagnoses) | 50 | 0 dead-ends, 0 broken refs (audit CLEAN) |
| Nhóm chủ đề (Groups) | 8 | Power, Display, OS, Network, Audio, Peripherals, Performance, Storage |
| Facts symbols | ~120+ | Atomic symbolic facts |

### 9.2. Phân Bố Luật Theo Nhóm

| Nhóm | Số luật | Đặc trưng |
|------|---------|----------|
| power_startup | 16 | Chuỗi 2+ bước, phân biệt laptop/desktop |
| display | 10 | Phân nhánh theo triệu chứng hình ảnh |
| os_boot | 15 | BSOD classification + Safe Mode test |
| network | 9 | Phân tầng Wi-Fi vs LAN vs DNS vs ISP |
| audio_camera | 8 | Privacy vs Driver vs Hardware |
| peripherals | 14 | USB ports + Bluetooth + Touchpad |
| performance | 12 | Thermal + Malware + RAM + Disk |
| storage | 9 | SMART data + File system + BIOS |

### 9.3. Đặc Tính Chất Lượng

| Thuộc tính | Trạng thái |
|-----------|------------|
| Dead-ends (luật không thể kích hoạt) | 0 |
| Broken references (tham chiếu hỏng) | 0 |
| Unreachable nodes (nút cô lập) | 0 |
| Audit status | ✅ CLEAN — v2.0 FINAL |
| Monotonic reasoning | Có (facts chỉ thêm, không xóa) |
| CF model | MYCIN (0.0 – 1.0, combine formula) |
| Session isolation | Server-side in-memory (UUID per session) |
| Loop protection | MAX_ITERATIONS = 100, MAX_VISIT_PER_QUESTION = 3 |

### 9.4. Luồng Suy Luận Điển Hình

Một phiên chẩn đoán điển hình có thể được khép kín trong khoảng **3–7 câu hỏi**, tùy thuộc vào bản chất vấn đề và độ chắc chắn của các câu trả lời. Các phiên có đường dẫn ngắn nhất thường xảy ra khi:
- Người dùng mô tả vấn đề chi tiết ngay từ đầu → NLU extract được nhiều facts.
- Câu trả lời kích hoạt một luật `triggers_diagnosis` trực tiếp (không qua luật trung gian).

Các phiên có đường dẫn dài hơn thường xảy ra với các nhóm **os_boot** và **performance** — nơi phân tích cần nhiều bước xác nhận chéo (ví dụ: kiểm tra Safe Mode, chạy SFC/CHKDSK, xem kết quả Task Manager).

---

## 10. Đánh Giá Hệ Thống (Evaluation)

### 10.1. Độ Bao Phủ (Coverage)
Hệ thống đạt độ bao phủ toàn diện với **50 chẩn đoán (diagnoses)** trải rộng trên 8 lĩnh vực cốt lõi của lỗi máy tính thường gặp: *Power/Startup (Nguồn khởi động), Display (Màn hình), OS/Boot (Hệ điều hành), Network (Mạng), Audio/Camera (Âm thanh/Máy ảnh), Peripherals (Ngoại vi), Performance (Hiệu năng)* và *Storage (Lưu trữ)*. Các chẩn đoán bao phủ từ mức độ nhẹ (ví dụ: lỗi cấu hình DNS, thiếu driver Bluetooth) cho đến mức độ nghiêm trọng (ví dụ: hỏng bo mạch chủ, hỏng cơ HDD, xung đột màn hình xanh BSOD). Việc cấu trúc hơn **120 fact symbols** thông qua 50 câu hỏi đa dạng tạo ra một không gian trạng thái sự kiện đủ sức bao quát hầu hết các tình huống lỗi thực tế (real-world scenarios) trên máy tính cá nhân.

### 10.2. Tính Nhất Quán (Consistency)
Thông qua quá trình kiểm toán tri thức (knowledge engineering audit) ở phiên bản v2.0, kiến trúc logic của hệ thống đạt tỷ lệ hoàn thiện tuyệt đối (100% bug-free for rule interactions):
*   **Không có ngõ cụt (0 Dead-ends):** Mọi đường dẫn phân nhánh người dùng chọn đều đảm bảo dẫn tới ít nhất một chẩn đoán hợp lệ hoặc tiếp diễn suy luận. Các quy trình có câu hỏi phức tạp (đa lựa chọn) được chuẩn hóa triệt để thông qua mẫu SUBMIT-pattern.
*   **Không có luật cô lập hoặc tham chiếu gãy (0 Unreachable Rules & 0 Broken Refs):** Toàn bộ 103 luật IF-THEN đều có tối thiểu một nhánh thực (live path) kích hoạt. Mọi thuộc tính `triggers_diagnosis` ở luật hay câu hỏi đều ánh xạ đúng tới ID trong bảng thực thể chẩn đoán.
*   **Không có vòng lặp vô hạn (No Infinite Loops):** Cơ chế Forward Chaining chỉ chạy đến mức Fixed-Point Termination kết hợp cùng các Anti-loop guards giới hạn thăm viếng trên mỗi câu hỏi (MAX_VISIT). Sự đơn điệu của Fact Base (Monotonic - chỉ thêm, không xóa) triệt tiêu nguy cơ dao động lặp trạng thái.
*   **Mô hình phân giải xung đột tối ưu (Conflict Resolution):** Các luật được ưu tiên phân giải theo chuẩn đa tầng (Priority → Specificity → CF → Recency), đảm bảo đầu ra luôn mang tính xác định (deterministic) khi có nhiều luật đồng thời thỏa mãn (Conflict Set > 1).

### 10.3. Chiều Sâu Lập Luận (Reasoning Depth & Multi-branch)
Lập luận của hệ thống thể hiện sự tinh vi cả về chiều sâu lẫn cấu trúc bề ngang đa quy trình:
*   Mô hình Forward Chaining hỗ trợ **chuỗi suy luận liên kết nhiều bước (multi-step chaining)**. Hệ thống nhận dạng các facts đầu vào (ví dụ `no_power`) để kích hoạt các luật trung gian (tạo ra facts như `probable_adapter_issue`), sau đó mới tiếp tục suy diễn mức độ chẩn đoán cuối cấp thay vì thiết lập các kết luận chắp vá và nông cạn trực tiếp liền sau câu hỏi.
*   Sự hiện diện của thiết kế **đa nhánh (multi-branching)** sâu sát theo phân mảng phần cứng (chẳng hạn các nhánh con về *Touchpad, Bluetooth, BIOS Disk Detection, lỗi tự tắt đột ngột Sudden Shutdown*), cho thấy năng lực phân tích không phải là một cây tuần tự đơn giản, cấu trúc DAG có thể ghép hợp nhiều nhánh đi theo các yếu tố chồng chéo đan xen phức tạp.

### 10.4. Điểm Mạnh Nổi Bật (Strengths)
*   **Hỏi Đáp Động Tuyến Tính Khôn Ngoan (Dynamic Questioning):** Thay vì theo trình tự cố định, hệ thống liên tục tính toán điểm Information Gain dựa trên Coverage và Discrimination Score của luật Near-Fire cận kề, tối thiểu hóa đáng kể số lượng câu hỏi mà người dùng phải nhận.
*   **Fast-Track Intent Integration:** Phân loại ý định bằng NLP với khả năng trích xuất facts qua văn bản cho phép hệ chuyên gia vượt qua hỏi cung cơ bản, "nhảy cóc" luồng suy luận nếu người dùng đã biểu đạt cụ thể vấn đề từ đầu (giống hệ chuyên gia con người nhất).
*   **Minh Bạch Hóa Quá Trình (Explanation Facility - White-box AI):** Khả năng sinh trình bày lịch sử luật lập luận, hiển thị dấu vết fact base và xuất bản biểu đồ đồ thị Decision Tree lên web cho giúp minh bạch và làm rõ căn cứ ra quyết định của mình đối với người sử dụng.

### 10.5. Hạn Chế Và Điểm Mù (Limitations & Blind Spots)
Mặc dù đã hoàn chỉnh ở mức ứng dụng hệ chuyên gia lai quy tắc, vẫn còn một số điểm giới hạn:
*   **Điểm mù về lỗi vi mạch vật lý:** Không thể chẩn đoán tự động các lỗi sâu trong cấu trúc tụ mạch vi mạch (ví dụ đứt liên kết socket, chạm chập IC linh kiện dán). Đối với các ca nghiêm trọng, việc can thiệp đo điện bằng thiết bị đồng hồ vạn năng thực tế sẽ nằm ngoài giới hạn và vẫn phải đưa ra lời khuyên "Cần trực tiếp kỹ thuật viên".
*   **Hạn chế mạng doanh nghiệp (Enterprise Networking):** Do thiên hướng lập trình quy chuẩn PC và thiết bị cá nhân lẻ tẻ, hệ thống không mang đủ số lượng quy tắc chuyên môn sâu để dò tìm các lỗi bảo mật proxy doanh nghiệp, cấu hình switch ảo (VLANs), hệ thống DNS tường lửa đa lớp hoặc Domain Controllers.
*   **Vắng Móng Tự Động Định Sửa (No Auto-Resolution):** Mô hình vận hành như một đối tác "chẩn đoán và tư vấn" (Advisory Passive System). Không trực tiếp chạy các mã shell scripts nền hay fix lỗi Registry bên trong phần mềm mà chỉ có vai trò hướng dẫn quy trình bằng ngôn ngữ cho con người tự làm (User Manual Action).

---

## 11. Kết Luận

Hệ thống chuyên gia chẩn đoán lỗi máy tính được trình bày trong báo cáo này thể hiện một thiết kế kiến trúc nhất quán và có nền tảng lý thuyết vững chắc. Về tổng thể, hệ thống tích hợp các kỹ thuật kinh điển của ngành Trí Tuệ Nhân Tạo biểu tượng (Symbolic AI) vào một ứng dụng thực tế:

- **Biểu diễn tri thức** theo mô hình production rules kết hợp Certainty Factor (MYCIN) cho phép xử lý tri thức không chắc chắn (uncertain knowledge), phù hợp với tính chất mơ hồ của bài toán chẩn đoán kỹ thuật.
- **Cơ chế suy luận** Forward Chaining với Conflict Resolution đa tiêu chí (priority + specificity + CF) đảm bảo hiệu quả suy luận và chính xác hóa ưu tiên chẩn đoán trong mọi tình huống.
- **Explanation Facility** hai lớp (inline + full) cung cấp tính minh bạch và khả năng giải thích — yêu cầu thiết yếu của các hệ thống tư vấn ứng dụng trong thực tế, đồng thời là tiêu chí phân biệt hệ chuyên gia với hệ phân loại thông thường.
- **Dynamic Questioning** với hàm scoring đa thành phần (coverage, discrimination, proximity, group) tối ưu hoá quá trình thu thập thông tin, tiến gần đến mô hình hỏi đáp tối ưu theo lý thuyết thông tin.
- **Module NLU nhẹ** cho phép tương tác ngôn ngữ tự nhiên tiếng Việt mà không cần mô hình ngôn ngữ lớn — giải pháp thực tiễn và hiệu quả cho bài toán phân loại intent miền hẹp (narrow-domain intent classification).
- **Kiến trúc phân tầng** với tách biệt rõ ràng giữa Knowledge Base, Inference Engine và Presentation đảm bảo khả năng bảo trì và mở rộng — tri thức có thể cập nhật độc lập với cơ chế suy luận.

Hệ thống đạt trạng thái **audit CLEAN** với 103 luật, 50 câu hỏi và 50 chẩn đoán không có dead-end hay broken reference — thể hiện mức độ hoàn chỉnh và độ tin cậy của knowledge base sau quá trình thiết kế và kiểm thử có hệ thống.
