<div align="center">

# 🖥️ Hệ Chuyên Gia Chẩn Đoán Lỗi Máy Tính

### Rule-Based Expert System — Web Chat Interface

**Môn học:** Công nghệ Tri Thức &nbsp;|&nbsp; **Trường:** Đại học Sài Gòn (SGU)

[![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-black?logo=flask)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-Academic-green)]()

</div>

---

## 👥 Thông tin nhóm

| STT | MSSV | Họ và Tên | Nhóm |
|-----|------|-----------|------|
| 1 | 3123560073 | Đỗ Duy Quý | 1 |
| 2 | 3123410274 | Lư Hồng Phúc | 1 |
| 3 | 3123410387 | Nguyễn Hữu Tri | 1 |

**Đề tài:** Xây dựng Hệ Chuyên Gia Chẩn Đoán Lỗi Máy Tính (Rule-Based Expert System)

---

## 📋 Mục tiêu đề tài

Xây dựng hệ thống web dạng **chat** cho phép người dùng mô tả lỗi máy tính, từ đó hệ thống:

- 🔎 **Suy luận** nguyên nhân lỗi bằng luật **IF–THEN** (Forward Chaining)
- ❓ **Hỏi thêm** câu hỏi thông minh theo từng bước (Dynamic Questioning)
- ✅ **Đưa ra chẩn đoán** kèm hướng xử lý cụ thể
- 📋 **Giải thích** toàn bộ quá trình suy luận (Explainable AI)

---

## 📊 Quy mô Knowledge Base

> Yêu cầu giảng viên: "20–40 tình huống phổ biến" → **Nhóm đã vượt xa yêu cầu:**

| Thành phần | Số lượng | Ghi chú |
|---|---|---|
| **Câu hỏi** | **50** | Phân nhánh động, có purpose/purpose hint |
| **Luật IF–THEN** | **103** | Có priority + Certainty Factor |
| **Chẩn đoán** | **50** | Severity + solution steps |
| **Facts (triệu chứng)** | **~166** | Nguyên tử, không trùng lặp |
| **Nhóm lỗi** | **8** | Xem bên dưới |

### 🌳 8 Nhóm Lỗi (phân nhánh ≥ 6 = 9 điểm theo thang giảng viên)

| Nhóm | Mô tả | Số Q | Số Rules |
|------|--------|------|----------|
| ⚡ Nguồn / Khởi động | Không lên nguồn, pin, adapter, POST fail | Q02–Q08 | ~25 |
| 🖥️ Màn hình / Hiển thị | Màn đen, sọc, flicker, backlight, GPU | Q09–Q12 | ~15 |
| 🪟 Windows / Hệ điều hành | BSOD, boot loop, driver, startup repair | Q13–Q19 | ~20 |
| 🌐 Mạng / Internet | WiFi, LAN, DNS, IP conflict, adapter | Q20–Q26 | ~15 |
| 🔊 Âm thanh / Camera | Loa, micro, webcam, driver audio | Q27–Q31 | ~10 |
| 🖱️ Thiết bị ngoại vi | USB, Bluetooth, Touchpad, bàn phím | Q32–Q35 | ~10 |
| ⚙️ Hiệu năng / Nhiệt độ | Chậm, nóng, virus, RAM/CPU/Disk 100% | Q37–Q44 | ~5 |
| 💾 Ổ đĩa / Lưu trữ | HDD/SSD hỏng, bad sector, ổ đầy | Q36, Q45–Q50 | ~3 |

---

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────────────┐
│                 NGƯỜI DÙNG (Web Browser)                     │
│         Giao diện Chat — HTML / CSS / JavaScript             │
└───────────────────────┬─────────────────────────────────────┘
                        │  HTTP (REST API)
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              FLASK WEB SERVER  (app.py)                      │
│  /start  /message  /select  /submit  /explanation  /reset   │
└──────┬────────────────┬──────────────────┬──────────────────┘
       │                │                  │
       ▼                ▼                  ▼
  ┌─────────┐    ┌──────────────┐   ┌────────────────┐
  │   NLU   │    │    ENGINE    │   │   SERVICES     │
  │ Intent  │    │ WorkingMem   │   │ SessionStore   │
  │ Classify│    │ RuleModel    │   │ TTL=30min      │
  │ Fact    │    │ ForwardChain │   └────────────────┘
  │ Extract │    │ DiagSession  │
  └─────────┘    │ QuestionSel  │
                 │ Explanation  │
                 └──────┬───────┘
                        │
                        ▼
              ┌──────────────────────┐
              │   KNOWLEDGE BASE     │
              │  06_questions.json   │
              │  07_rules_diag.json  │
              └──────────────────────┘
```

---

## 🧠 Phương pháp suy luận: Forward Chaining

Hệ thống sử dụng **Forward Chaining** (suy luận tiến) theo vòng lặp:

```
        Khởi đầu: Facts thu thập từ người dùng
                         │
                         ▼
              ┌─────── MATCH ────────┐
              │ Tìm rules applicable │
              │ (thỏa IF-conditions) │
              └────────┬─────────────┘
                       │  Conflict Set rỗng?  ──► STOP (Fixed Point)
                       ▼
              ┌─────── SELECT ───────┐
              │ Conflict Resolution: │
              │  1. Priority (1–5)   │
              │  2. Specificity      │
              │  3. Certainty Factor │
              └────────┬─────────────┘
                       │
                       ▼
              ┌─────── FIRE ─────────┐
              │ Rule kích hoạt:      │
              │  + Thêm facts mới    │
              │  → Trigger diagnosis │
              └────────┬─────────────┘
                       │
                       └──────────► Lặp lại
```

### Certainty Factor (mô hình MYCIN)

Độ tin cậy của chẩn đoán được tính theo công thức MYCIN:

$$CF_{combined} = CF_1 + CF_2 \times (1 - CF_1)$$

Ví dụ: Nếu Rule_A kết luận DIAG_X với CF=0.85, Rule_B cũng kết luận DIAG_X với CF=0.70:
$$CF = 0.85 + 0.70 \times (1 - 0.85) = 0.85 + 0.105 = \mathbf{0.955}$$

---

## 📂 Cấu trúc thư mục

```
project/
│
├── app.py                          # Flask application (7 routes)
├── requirements.txt                # flask, pytest
│
├── data/                           # Knowledge Base (copy từ knowledge_base/)
│   ├── 06_questions.json           # 50 câu hỏi
│   └── 07_rules_and_diagnoses.json # 103 rules + 50 diagnoses
│
├── engine/                         # Core Inference Engine
│   ├── __init__.py
│   ├── working_memory.py           # Bộ nhớ làm việc (fact base)
│   ├── rule_model.py               # Rule, DiagnosisResult (CF MYCIN)
│   ├── forward_engine.py           # Forward Chaining (MATCH-SELECT-FIRE)
│   ├── diagnostic_session.py       # Session state + KB loader
│   ├── question_selector.py        # Dynamic Questioning (scoring)
│   └── explanation_builder.py      # Explanation Facility (XAI)
│
├── nlu/                            # Natural Language Understanding
│   ├── __init__.py
│   ├── patterns.py                 # Keyword → fact/intent mapping
│   ├── intent_classifier.py        # Phân loại nhóm lỗi từ text
│   └── fact_extractor.py           # Trích xuất facts từ text
│
├── services/                       # Web Services
│   ├── __init__.py
│   └── session_store.py            # In-memory session mgmt (TTL + ThreadLock)
│
├── templates/
│   └── chat.html                   # Giao diện chat (Jinja2)
│
├── static/
│   ├── css/style.css               # Thiết kế (white mode, Inter font)
│   └── js/chat.js                  # Frontend logic (fetch API)
│
├── knowledge_base/                 # Source of Truth (gốc, không sửa)
│   ├── 06_questions.json
│   └── 07_rules_and_diagnoses.json
│
├── tests/                          # Unit & Integration Tests
│   ├── test_engine.py              # 26 tests (WorkingMemory, Rule, Engine, E2E)
│   ├── test_nlu.py                 # 9 tests (Intent, Fact)
│   └── test_flow.py                # 9 tests (Flask routes, session)
│
└── report/
    └── YeuCauGiangVien.txt
```

---

## 🚀 Hướng dẫn chạy

### Yêu cầu

- Python 3.10+
- pip

### Cài đặt

```bash
# 1. Clone / mở project
cd project/

# 2. Cài thư viện
pip install -r requirements.txt

# 3. Chạy server
python app.py
```

### Truy cập

Mở trình duyệt và vào địa chỉ:

```
http://localhost:5000
```

### Chạy Tests

```bash
# Chạy toàn bộ test suite (43 tests)
python -m pytest tests/ -v

# Chạy riêng từng phần
python -m pytest tests/test_engine.py -v   # Engine tests
python -m pytest tests/test_nlu.py -v     # NLU tests
python -m pytest tests/test_flow.py -v    # Flask route tests
```

---

## 🎯 Tính năng nổi bật

### 1. Dynamic Questioning (Câu hỏi thông minh)

Thay vì hỏi theo thứ tự cứng nhắc, hệ thống **chọn câu hỏi tiếp theo thông minh** dựa trên:

| Tiêu chí | Trọng số | Ý nghĩa |
|---|---|---|
| Coverage Score | ×2.0 | Câu hỏi giúp cover nhiều missing facts |
| Discrimination | ×1.5 | Phân biệt được nhiều diagnoses |
| Group Bonus | ×0.5 | Ưu tiên cùng nhóm lỗi |
| Proximity | ×1.0 | Giúp fire rules gần nhất |

### 2. NLU Layer (Hiểu ngôn ngữ tự nhiên)

Người dùng có thể **gõ text tự nhiên** thay vì chỉ click nút:

```
User: "laptop không lên nguồn gì hết, bấm nút không có phản ứng"
         ↓ Intent Classifier
      Intent: "power_startup" (confidence: 0.91)
         ↓ Fact Extractor
      Facts: ["no_power", "fan_not_spinning"]
         ↓ Option Matcher
      Match Q02 → Option A → ds.answer(["A"])
         ↓
      Câu hỏi tiếp theo: Q03 (Laptop hay Desktop?)
```

### 3. Explanation Facility (Giải thích suy luận)

Người dùng có thể xem **toàn bộ quá trình** hệ thống đưa ra kết quả:

- 📋 Danh sách Q&A đã hỏi
- 📌 Facts đã thu thập được
- ⚡ Các luật đã kích hoạt + CF
- 🏥 Kết quả với độ tin cậy

### 4. Giao diện Web Chat

- ✅ Quick-reply buttons (single_choice)
- ✅ Checkbox + Submit (multi_choice)
- ✅ Text input với NLU
- ✅ Typing indicator khi chờ
- ✅ Side panel: facts + candidate diagnoses realtime
- ✅ Diagnosis card với CF meter
- ✅ "Bắt đầu lại" ở header và màn kết quả

---

## 📈 Kết quả kiểm thử

### Test Suite: 43/43 Tests Passed ✅

```
tests/test_engine.py  ::  26 passed
tests/test_nlu.py     ::   9 passed
tests/test_flow.py    ::   9 passed
─────────────────────────────────────
TOTAL                 ::  43 passed in 0.32s
```

### Test Cases E2E tiêu biểu

| TC | Kịch bản | Kết quả mong đợi | Trạng thái |
|----|----------|-----------------|------------|
| TC01 | Laptop không sạc → adapter hỏng | `DIAG_PWR_01` | ✅ |
| TC02 | Laptop không sạc → pin chai | `DIAG_PWR_02` | ✅ |
| TC05 | Màn hình lỗi sau cập nhật driver | `DIAG_DSP_02` | ✅ |
| TC08 | BSOD memory management | `DIAG_OS_03` | ✅ |
| TC15 | Không thấy WiFi adapter | `DIAG_NET_02` | ✅ |
| TC21 | Mất tiếng, driver âm thanh lỗi | `DIAG_AUD_01` | ✅ |
| TC24 | Cổng USB hỏng | `DIAG_PER_01` | ✅ |
| TC29 | HDD tiếng kêu lách cách | `DIAG_STR_02` | ✅ |

---

## 🗂️ Luồng chẩn đoán mẫu

**Tình huống:** "Laptop không lên nguồn, không sạc được"

```
Q01: Vấn đề chính là gì?
     → [A] Máy không bật / không có điện

Q02: Khi nhấn nút nguồn, điều gì xảy ra?
     → [A] Hoàn toàn không có phản ứng gì

Q03: Laptop hay Desktop?
     → [A] Laptop              ← User gõ "laptop" → NLU match tự động

Q05: Tình trạng pin và sạc?
     → [B] Đèn sạc sáng nhưng pin không tăng

                 ↓ Forward Chaining
    Working Memory: {no_power, fan_not_spinning, is_laptop, no_charge}
    
    Rule R012 FIRE: no_power + is_laptop → probable_power_issue_laptop
    Rule R015 FIRE: no_power + is_laptop + no_charge → DIAG_PWR_02 (CF=0.85)

╔══════════════════════════════════════════╗
║  🏥 KẾT QUẢ: Pin laptop chai hoặc hỏng  ║
║  Độ tin cậy: 85%  |  Mức độ: 🟠 Cao     ║
╚══════════════════════════════════════════╝
```

---

## 📚 Tài liệu tham khảo

1. Wikipedia — Expert System: https://en.wikipedia.org/wiki/Expert_system
2. Wikipedia — Forward Chaining: https://en.wikipedia.org/wiki/Forward_chaining
3. Wikipedia — Backward Chaining: https://en.wikipedia.org/wiki/Backward_chaining
4. Shortliffe, E.H. (1976) — *MYCIN: Computer-Based Medical Consultations* — Certainty Factor model
5. Russell & Norvig — *Artificial Intelligence: A Modern Approach* — Chapter 9: Inference in First-Order Logic
6. Flask Documentation: https://flask.palletsprojects.com/en/3.0.x/
7. Experta (CLIPS-like rules engine for Python): https://github.com/noxdafox/experta

---

## ⚖️ Đánh giá theo thang điểm giảng viên

| Tiêu chí | Yêu cầu | Nhóm đạt |
|---|---|---|
| Nhị phân (7đ) | 2 nhánh | ✅ Đã vượt |
| Tam phân (8đ) | 3 nhánh | ✅ Đã vượt |
| Tứ phân (8.5đ) | 4 nhánh | ✅ Đã vượt |
| **Lục phân (9đ)** | **≥ 6 nhánh** | ✅ **8 nhánh** |
| **≥ 9đ** | Nhiều nhánh, đẹp, hay | ✅ **8 nhóm lớn + 50 chẩn đoán + Web Chat + NLU + Explanation** |

> **Hệ thống đạt:** 8 nhóm lỗi · 103 luật · 50 chẩn đoán · Giao diện web đầy đủ · NLU layer · Dynamic Questioning · Explanation Facility

---

<div align="center">

**Đại học Sài Gòn — Khoa Công nghệ Thông tin**  
Năm học 2024–2025

</div>
