# PHẦN 1: PHÂN TÍCH CHIẾN LƯỢC THIẾT KẾ
## Hệ Chuyên Gia Chẩn Đoán Lỗi Máy Tính (Rule-Based Expert System)

---

## 1.1 Lý do chọn Forward Chaining

### Định nghĩa học thuật
Forward chaining (suy diễn tiến) là chiến lược suy diễn xuất phát từ **facts đã biết** (triệu chứng đầu vào từ người dùng), áp dụng các luật IF-THEN để dần dần rút ra **kết luận mới** (intermediate conclusions), cuối cùng đạt đến **final diagnosis**.

Đây là chiến lược **data-driven**: bắt đầu từ dữ liệu → suy ra kết quả.

### Lý do phù hợp với bài toán chẩn đoán lỗi máy tính

| Tiêu chí | Forward Chaining | Backward Chaining |
|----------|-----------------|-------------------|
| Xuất phát điểm | Facts/Triệu chứng người dùng biết | Hypothesis cần chứng minh |
| Phù hợp khi | Người dùng không biết nguyên nhân | Hỏi "có phải lỗi X không?" |
| Giao diện web | Hỏi từng bước, tự nhiên | Cần biết trước mục tiêu |
| Trải nghiệm | Giống kỹ thuật viên thực tế | Giống thủ tục xác nhận |
| Khám phá | Tốt — tự khám phá ra nhiều diagnoses | Kém — phải đặt hypothesis trước |

**Kết luận**: Forward chaining phù hợp vì:
- Người dùng **KHÔNG biết** nguyên nhân lỗi — họ chỉ biết triệu chứng
- Hệ thống cần **hỏi từng bước**, tích lũy facts, rồi suy ra kết luận
- Một máy tính có thể có **nhiều vấn đề đồng thời** → forward chaining xác định tất cả
- Phù hợp với **giao diện web chatbot** theo dạng wizard/step-by-step

### Cơ chế hoạt động của Forward Chaining trong hệ này

```
Fact Base (Working Memory)
    ↓
Conflict Set (tập luật có thể kích hoạt)
    ↓
Conflict Resolution (chọn luật ưu tiên cao nhất)
    ↓
Firing the Rule (áp dụng luật → thêm fact mới)
    ↓
Lặp lại (Rete Algorithm cicle) cho đến khi:
    - Có final diagnosis, HOẶC
    - Không còn luật nào có thể kích hoạt
```

---

## 1.2 Lý do phân chia 8 nhóm lỗi cấp cao

Thay vì phân loại theo bộ phận phần cứng (CPU, RAM, HDD...), hệ thống phân loại theo **triệu chứng người dùng quan sát được**. Điều này vì:

1. **Người dùng không phải kỹ thuật viên** — họ mô tả **hiện tượng**, không mô tả được "linh kiện lỗi"
2. **Một triệu chứng có thể từ nhiều nguyên nhân** → cần phân nhánh sâu
3. **Phù hợp mô hình expert system** — tri thức bắt đầu từ observable facts

### 8 nhóm lỗi và lý do tách riêng

| STT | Nhóm | Lý do tách riêng |
|-----|------|-----------------|
| 1 | Nguồn / Khởi động | Triệu chứng sớm nhất, trước khi OS load |
| 2 | Màn hình / Hiển thị | Tách khỏi OS — có thể lỗi hardware display độc lập |
| 3 | Hệ điều hành / Boot | Sau khi POST thành công, lỗi ở tầng OS |
| 4 | Mạng / Wi-Fi / Internet | Lỗi kết nối — có nhánh riêng phức tạp |
| 5 | Âm thanh / Micro / Camera | Thiết bị I/O đặc thù, cần driver riêng |
| 6 | Thiết bị ngoại vi / USB | Lỗi giao tiếp — không ảnh hưởng OS chính |
| 7 | Hiệu năng / Nhiệt độ | Lỗi hệ thống chạy nhưng chậm — chẩn đoán khác |
| 8 | Lưu trữ / Ổ đĩa | Lỗi data/storage — liên quan HDD/SSD/file system |

---

## 1.3 Tại sao cấu trúc này phù hợp môn Công nghệ Tri Thức

### Thể hiện đầy đủ các thành phần của Expert System

```
Expert System = Knowledge Base + Inference Engine + User Interface + Explanation Facility
```

| Thành phần | Triển khai trong đồ án |
|------------|----------------------|
| Knowledge Base | 8 nhóm, 40+ facts, 50+ rules, 30+ diagnoses |
| Inference Engine | Forward chaining với conflict resolution |
| User Interface | Web chatbot hỏi đáp từng bước |
| Explanation Facility | Giải thích tại sao → why/how path |

### Thể hiện đủ mức độ phân nhánh (yêu cầu điểm cao)

- **Tầng 1**: 8 nhánh (octary branching — rất cao)
- **Tầng 2**: 3–6 nhánh mỗi nhóm (multi-way branching)
- **Tầng 3**: 2–4 nhánh (xác nhận triệu chứng phụ)
- **Tầng 4–5**: 2–3 nhánh (chốt diagnosis)

Tổng cộng: cây suy luận có **hơn 200 nodes**, đủ để thể hiện độ phức tạp học thuật.

### Thể hiện đúng bản chất tri thức

Tri thức trong hệ thống được **elicited** từ:
- Tài liệu hỗ trợ Microsoft Windows
- Kinh nghiệm kỹ thuật viên thực tế
- Hướng dẫn sửa chữa laptop phổ biến

Tri thức được **codified** thành:
- Explicit knowledge (IF-THEN rules)
- Intermediate conclusions (chaining)
- Confidence levels (high/medium/low)

---

## 1.4 Cơ chế Conflict Resolution

Khi nhiều luật cùng có thể kích hoạt, hệ thống áp dụng độ ưu tiên sau:

```
Priority 1: Specificity (luật cụ thể hơn → ưu tiên cao hơn)
Priority 2: Recency (fact mới hơn → ưu tiên cao hơn)  
Priority 3: Rule Order (luật được định nghĩa trước → ưu tiên cao hơn)
Priority 4: Certainty Factor (độ tin cậy cao hơn → ưu tiên)
```

### Certainty Factor (CF) Model

Mỗi luật có CF (0.0 → 1.0):
- **CF ≥ 0.8**: High confidence → kết luận chắc chắn
- **CF 0.5–0.79**: Medium confidence → cần xác nhận thêm
- **CF < 0.5**: Low confidence → chỉ là gợi ý

Khi nhiều luật cùng dẫn đến 1 conclusion:
```
CF_combined = CF1 + CF2 × (1 - CF1)
```

---

## 1.5 Giải thích học thuật cho từng tầng suy luận

### Tầng 1 — Phân loại triệu chứng gốc
**Mục đích**: Loại bỏ không gian tìm kiếm không liên quan
**Kỹ thuật**: Câu hỏi root với nhiều lựa chọn (8-way branching)
**Học thuật**: Tương đương "goal-directed initial classification"

### Tầng 2 — Nhận diện hiện tượng đặc trưng
**Mục đích**: Xác định pattern triệu chứng trong nhóm
**Kỹ thuật**: Multi-choice questions với 3–6 options
**Học thuật**: "Symptom pattern matching"

### Tầng 3 — Tách nguyên nhân khả dĩ
**Mục đích**: Generate candidate diagnoses từ working memory
**Kỹ thuật**: Áp dụng intermediate rules → intermediate facts
**Học thuật**: "Hypothesis generation through chaining"

### Tầng 4 — Xác nhận bằng triệu chứng phụ
**Mục đích**: Disambiguate khi nhiều diagnoses cùng khớp
**Kỹ thuật**: Confirmatory yes/no questions
**Học thuật**: "Differential diagnosis / evidence accumulation"

### Tầng 5 — Chốt kết luận và giải pháp
**Mục đích**: Final diagnosis với actionable solution
**Kỹ thuật**: Apply final rules, fire diagnosis fact
**Học thuật**: "Decision crystallization"
