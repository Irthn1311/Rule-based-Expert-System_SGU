# README — Knowledge Base Hệ Chuyên Gia Chẩn Đoán Lỗi Máy Tính

> **FINAL VERSION 2.0 — AUDIT PASSED**  
> `audit_status: CLEAN | 0 critical | 0 high | 0 medium | 0 dead-ends | 0 broken refs`

---

## Tổng quan

Đây là **bộ tri thức hoàn chỉnh** cho hệ chuyên gia chẩn đoán lỗi máy tính Windows/PC/Laptop,  
được thiết kế theo tiêu chuẩn học thuật môn **Công nghệ Tri thức — SGU**.

---

## Thống kê Knowledge Base — FINAL VERSION 2.0

| Thành phần | Số lượng |
|-----------|---------|
| Nhóm lỗi cấp cao | 8 nhóm |
| Câu hỏi chẩn đoán | **50 câu hỏi** |
| Input facts (sự kiện quan sát được) | ~166 facts |
| Intermediate facts (kết luận trung gian) | ~20 facts |
| Luật IF-THEN | **103 luật** |
| Kết luận cuối (Diagnoses) | **50 chẩn đoán** |
| Đường suy luận trong cây | > 80 paths |
| Test cases | 38 ca kiểm thử |

---

## Source of Truth — Nguồn chính thức

> ⚠️ **Chỉ dùng 2 file JSON sau cho code và engine. Mọi file khác là tài liệu tham khảo.**

| File | Vai trò |
|------|---------|
| `06_questions.json` | **[SOURCE OF TRUTH]** 50 câu hỏi — cấu trúc flow, facts, triggers |
| `07_rules_and_diagnoses.json` | **[SOURCE OF TRUTH]** 103 luật + 50 diagnoses — IF-THEN logic |

---

## Danh sách files

| File | Nội dung |
|------|---------| 
| `01_strategy_and_design.md` | Phân tích chiến lược, lý do chọn Forward Chaining, giải thích học thuật |
| `02_fact_system.md` | Toàn bộ hệ facts: input (~166), intermediate (~20), final diagnosis facts |
| `03_questions_40.md` | Tài liệu mô tả câu hỏi dạng text (tham khảo học thuật — reflect JSON v2.0) |
| `04_rules_ifthen.md` | Luật IF-THEN dạng text (tài liệu học thuật — reflect JSON v2.0) |
| `05_diagnoses_table.md` | 50 chẩn đoán cuối với triệu chứng, nguyên nhân, giải pháp |
| `06_questions.json` | **[SOURCE OF TRUTH]** 50 câu hỏi dạng JSON |
| `07_rules_and_diagnoses.json` | **[SOURCE OF TRUTH]** 103 Luật + 50 Diagnoses dạng JSON |
| `08_inference_tree.md` | Cây suy luận dạng hierarchy + JSON structure |
| `09_quality_and_implementation.md` | Kiểm tra chất lượng + Code Python inference engine + FastAPI |
| `AUDIT_REPORT.md` | Báo cáo audit cuối — **FINAL AUDIT PASSED** |

---

## Kiến trúc hệ thống

```
Inference Strategy:   Forward Chaining (Data-Driven)
Working Memory:       Monotonic (facts chỉ được thêm, không xóa)
Conflict Resolution:  Priority → Specificity → CF → Recency
Certainty Factor:     MYCIN CF Model (0.0–1.0)
                      combine: CF_new = CF1 + CF2*(1-CF1)
Branching:            Octary (8-way) tại root Q01
                      Multi-way (2–6) tại các tầng sâu hơn
Multi-choice:         SUBMIT-pattern — collect all facts, run inference, then route
Explanation Facility: Full trace Q&A → Rules fired → Facts added → Diagnosis
```

---

## Cấu trúc câu hỏi (50 questions)

| Nhóm | IDs |
|------|-----|
| Power / Startup | Q01–Q08, Q_Q08_RESULT, Q_SHTDN1, Q_SHTDN2 |
| Display | Q09–Q12 |
| OS / Boot / BSOD | Q13–Q19, Q19_RETRY |
| Network / Wi-Fi | Q20–Q26 |
| Audio / Camera / Mic | Q27–Q31 |
| Peripherals / USB | Q32–Q35, Q_BT1, Q_BT2, Q_TOUCH1, Q_TOUCH2 |
| Performance / Heat | Q37–Q40 |
| Storage / Drive | Q36, Q_BIOS1, Q_BIOS2 |

---

## Multi-choice SUBMIT Pattern

Hệ thống sử dụng SUBMIT-pattern cho tất cả câu hỏi multi-choice:

```json
{ "value": "SUBMIT", "label": "▶ Đã chọn xong — Phân tích kết quả", "next": "Q_NEXT" }
```

**Lý do đúng với Forward Chaining:**
- Đây là cách chuẩn thống nhất với CLIPS/expert system: collect tất cả facts trước, rồi chạy inference
- Engine add tất cả facts từ các option đã chọn → `run_until_stable()` → route theo SUBMIT
- Không có string-logic nào ngoài JSON — engine thuần túy dựa vào facts + rules

---

## Cài đặt nhanh

```bash
pip install fastapi uvicorn pydantic

# Chạy backend (từ thư mục project/)
uvicorn backend.engine:app --reload

# Health check
GET http://localhost:8000/api/health

# Test
python validate_kb.py
```

---

## Điểm nổi bật học thuật

1. **Forward Chaining chuẩn** — Agenda, Conflict Resolution, Working Memory
2. **MYCIN Certainty Factor** — mỗi luật có CF 0.0–1.0, combine khi nhiều rules → cùng diagnosis
3. **Intermediate Conclusions** — ~20 facts trung gian trước khi đến diagnosis cuối
4. **Specificity-based selection** — rule nhiều điều kiện hơn được ưu tiên
5. **Explanation Facility** — giải thích "tại sao" bằng tiếng Việt (WHY/HOW)
6. **8-way root branching** — loại bỏ 7/8 hypothesis space ngay tầng 1
7. **50 final diagnoses** — đủ sâu, cover 8 nhóm lỗi thực tế
8. **SUBMIT multi-choice** — chuẩn hóa với CLIPS/expert system học thuật
9. **~166 input facts** — chi tiết, phân biệt rõ từng triệu chứng
10. **>80 inference paths** — đủ đa dạng để demo và bảo vệ

---

## Ghi chú cho bảo vệ đồ án

- Giải thích **tại sao dùng Forward Chaining**: file `01_strategy_and_design.md §1.1`
- Giải thích **cấu trúc cây suy luận**: file `08_inference_tree.md`
- Demo **test cases (38 ca)**: file `09_quality_and_implementation.md §9.3`
- **Điểm mạnh vs hệ thống khác**: file `01_strategy_and_design.md §1.3`
- **Source of truth cho code**: chỉ dùng `06_questions.json` và `07_rules_and_diagnoses.json`
- **Audit status**: xem `AUDIT_REPORT.md` — FINAL AUDIT PASSED

---

## FINAL_VERSION Block

```text
SYSTEM_NAME    = PC Diagnostic Expert System
VERSION        = 2.0.0
TOTAL_QUESTIONS = 50
TOTAL_RULES     = 103
TOTAL_DIAGNOSES = 50
TOTAL_FACTS     = ~166 input + ~20 intermediate
TOTAL_PATHS     = >80
AUDIT_STATUS    = CLEAN
DEAD_ENDS       = 0
BROKEN_REFS     = 0
UNREACHABLE_RULES = 0
INFERENCE_STRATEGY = Forward Chaining
CONFLICT_RESOLUTION = Priority > Specificity > CF > Recency
CF_MODEL        = MYCIN (0.0–1.0)
MULTI_CHOICE    = SUBMIT-pattern (no string logic)
ENGINE_MATCH    = 100% (adds_facts, triggers_diagnosis, next all handled)
READY_FOR_SUBMISSION = TRUE
```
