# PHẦN 5: CÂY SUY LUẬN TỔNG THỂ

---

## 5.1 Dạng mô tả phân cấp dễ đọc

```
ROOT: Máy tính gặp vấn đề gì? (Q01 — 8-way branching)
│
├─ A: NGUỒN / KHỞI ĐỘNG ─────────────────────────────────────
│   │
│   ├─ Không có phản ứng gì (Q02-A)
│   │   ├─ Laptop? → Kiểm tra pin/adapter (Q05)
│   │   │   ├─ Đèn sạc không sáng             → DIAG_PWR_01 (Adapter hỏng)
│   │   │   ├─ Pin không tăng                 → DIAG_PWR_02 (Pin chai)
│   │   │   └─ Chỉ bật khi cắm điện           → DIAG_PWR_02 (Pin chết)
│   │   └─ Desktop? → Kiểm tra PSU (Q08)
│   │       ├─ Đèn bo mạch không sáng         → DIAG_PWR_03 (PSU hỏng)
│   │       └─ PSU OK nhưng không bật         → DIAG_PWR_04 (Bo mạch lỗi)
│   │
│   ├─ Đèn sáng, màn đen (Q02-B)
│   │   ├─ Beep nhiều lần (Q04-C)
│   │   │   └─ POST fail                      → DIAG_PWR_05 (RAM lỏng/hỏng)
│   │   └─ 1 beep (Q04-B) → (chuyển sang display branch Q09)
│   │
│   └─ Quạt quay, không màn hình (Q02-D)
│       └─ Single beep → system boots no display → Q09
│
├─ B: MÀN HÌNH / HIỂN THỊ ───────────────────────────────────
│   │
│   ├─ Màn hình đen hoàn toàn (Q09-A)
│   │   ├─ Màn hình ngoài OK (Q10-A)
│   │   │   ├─ Không có sọc                   → DIAG_DSP_01 (Cáp màn hình lỏng)
│   │   │   └─ Có sọc                         → DIAG_DSP_03 (LCD panel hỏng)
│   │   └─ Màn hình ngoài cũng lỗi (Q10-B)
│   │       ├─ Sau driver update              → DIAG_DSP_02 (Driver GPU lỗi)
│   │       └─ Màu sắc méo + không driver     → DIAG_DSP_04 (GPU hỏng)
│   │
│   ├─ Màn hình nhấp nháy (Q09-B)
│   │   └─ Sau driver update                  → DIAG_DSP_02 (Driver GPU lỗi)
│   │
│   ├─ Có sọc ngang/dọc (Q09-C)
│   │   ├─ Bị va đập                          → DIAG_DSP_03 (LCD vỡ)
│   │   └─ Nhìn nghiêng thấy hình            → DIAG_DSP_03 (Backlight hỏng)
│   │
│   ├─ Màu sắc lạ (Q09-D) → Q12
│   │
│   ├─ Màn hình trắng (Q09-E)                → DIAG_DSP_03 (Panel lỗi)
│   │
│   └─ Độ phân giải sai (Q09-F) → Q11
│       └─ Sau driver update                  → DIAG_DSP_02
│
├─ C: HỆ ĐIỀU HÀNH / BOOT ───────────────────────────────────
│   │
│   ├─ BSOD xuất hiện (Q13-A) → Q14 (xem mã lỗi)
│   │   ├─ Memory error code                  → DIAG_OS_03 (Lỗi RAM)
│   │   ├─ Driver error code → có thay đổi   → DIAG_OS_02 (Driver lỗi)
│   │   │               → không thay đổi    → DIAG_OS_01 (File hệ thống)
│   │   └─ Disk error code                   → DIAG_OS_04 (HDD/SSD gây BSOD)
│   │
│   ├─ Boot loop (Q13-B)
│   │   ├─ Sau Windows Update                → DIAG_OS_05 (Update loop)
│   │   └─ Không có thay đổi               → DIAG_OS_06 (MBR hỏng)
│   │
│   ├─ Dừng ở logo (Q13-C) → Q16 (Safe Mode?)
│   │   ├─ Safe Mode OK                     → DIAG_OS_02 (Driver startup)
│   │   └─ Safe Mode fail                   → DIAG_OS_01 (Corruption nghiêm trọng)
│   │
│   └─ Treo ngẫu nhiên (Q13-D)
│       ├─ Có thay đổi gần đây              → DIAG_OS_02
│       └─ SFC báo lỗi                      → DIAG_OS_01
│
├─ D: MẠNG / WI-FI / INTERNET ────────────────────────────────
│   │
│   ├─ Không thấy Wi-Fi trong danh sách (Q20-A)
│   │   ├─ Không có adapter trong DM        → DIAG_NET_02 (Adapter hardware hỏng)
│   │   └─ Có adapter nhưng lỗi            → DIAG_NET_01 (Driver Wi-Fi lỗi)
│   │
│   ├─ Kết nối nhưng không Internet (Q20-B)
│   │   ├─ Thiết bị khác cũng fail         → DIAG_NET_04 (Router/ISP)
│   │   └─ Thiết bị khác bình thường
│   │       ├─ Lỗi DNS                     → DIAG_NET_03 (DNS sai)
│   │       ├─ IP conflict                 → DIAG_NET_06 (IP trùng)
│   │       └─ LAN cũng fail               → DIAG_NET_05 (Network stack hỏng)
│   │
│   ├─ Dấu chấm than vàng (Q20-C) → Q22 → Q23
│   │
│   └─ Wi-Fi chậm (Q20-D) → thiết bị khác OK → DIAG_NET_01
│
├─ E: ÂM THANH / CAMERA / MICRO ─────────────────────────────
│   │
│   ├─ Không có âm thanh (Q27-A) → Q28
│   │   ├─ Không thấy device                → DIAG_AUD_03 (Hardware)
│   │   ├─ Driver chấm than vàng            → DIAG_AUD_01 (Driver)
│   │   └─ Device bình thường               → DIAG_AUD_02 (Muted/disabled)
│   │
│   ├─ Micro không hoạt động (Q27-B) → Q31
│   │   ├─ Disabled trong settings          → DIAG_AUD_02
│   │   └─ Driver lỗi                       → DIAG_AUD_01
│   │
│   └─ Camera không nhận (Q27-C) → Q30
│       ├─ Privacy bị chặn                  → DIAG_CAM_01
│       └─ Driver lỗi                       → DIAG_CAM_02
│
├─ F: THIẾT BỊ NGOẠI VI / USB ────────────────────────────────
│   │
│   ├─ Thiết bị USB (Q32-A) → Q33
│   │   ├─ Chỉ 1 cổng lỗi → thiết bị OK máy khác → DIAG_PER_01 (Cổng hỏng)
│   │   ├─ Tất cả cổng lỗi                 → DIAG_PER_02 (USB Controller)
│   │   └─ Thiết bị lỗi ở mọi nơi         → DIAG_PER_03 (Thiết bị hỏng)
│   │
│   ├─ Chuột/Bàn phím (Q32-B/C) → Q34 → Q35
│   │   ├─ Driver chấm than vàng           → DIAG_PER_04 (Driver)
│   │   └─ Cổng cụ thể fail               → DIAG_PER_01 (Cổng hỏng)
│   │
│   └─ Bluetooth (Q32-D)                   → DIAG_PER_04 (Driver BT)
│
├─ G: HIỆU NĂNG / NHIỆT ĐỘ ──────────────────────────────────
│   │
│   ├─ Nóng + quạt ồn + chậm (Q37-A)
│   │   ├─ CPU 100% + nóng               → DIAG_PERF_01 (Thermal throttling)
│   │   └─ CPU cao + malware nghi ngờ    → DIAG_PERF_02 (Malware)
│   │
│   ├─ Khởi động chậm (Q37-B) → Q39
│   │   └─ Nhiều startup programs        → DIAG_PERF_03 (Startup bloat)
│   │
│   └─ Chậm khi nhiều app (Q37-C) → Q38
│       ├─ RAM >85%                      → DIAG_PERF_04 (RAM không đủ)
│       └─ Disk 100%                     → (chuyển sang Storage)
│
└─ H: LƯU TRỮ / Ổ ĐĨA ───────────────────────────────────────
    │
    ├─ Ổ C: đầy (Q36-A)                  → DIAG_STR_01 (Disk full)
    ├─ Tiếng click HDD (Q36-B)           → DIAG_STR_02 (HDD hỏng — URGENT)
    ├─ File bị lỗi (Q36-C)
    │   └─ CHKDSK lỗi                    → DIAG_STR_04 (File system)
    ├─ Bad sectors (Q36-D)               → DIAG_STR_02 (HDD hỏng)
    ├─ Ổ thứ 2 không thấy (Q36-E)       → DIAG_STR_04 (File system/detection)
    └─ SSD health thấp (Q36-F)          → DIAG_STR_03 (SSD degraded)
```

---

## 5.2 Dạng JSON Tree Structure

```json
{
  "node": "ROOT",
  "question": "Q01",
  "branching_factor": 8,
  "children": [
    {
      "node": "POWER_ROOT",
      "option": "A",
      "question": "Q02",
      "branching_factor": 4,
      "children": [
        {
          "node": "NO_POWER",
          "option": "A",
          "question": "Q03",
          "branching_factor": 2,
          "children": [
            {
              "node": "LAPTOP_POWER",
              "option": "A",
              "question": "Q05",
              "branching_factor": 4,
              "children": [
                { "node": "LEAF", "option": "A", "diagnosis": "DIAG_PWR_01", "cf": 0.90 },
                { "node": "LEAF", "option": "B", "diagnosis": "DIAG_PWR_02", "cf": 0.85 },
                { "node": "LEAF", "option": "C", "diagnosis": "DIAG_PWR_02", "cf": 0.85 },
                { "node": "LEAF", "option": "D", "diagnosis": "DIAG_PWR_01", "cf": 0.90 }
              ]
            },
            {
              "node": "DESKTOP_POWER",
              "option": "B",
              "question": "Q08",
              "branching_factor": 4,
              "children": [
                { "node": "LEAF", "combination": "A+B+notC", "diagnosis": "DIAG_PWR_03", "cf": 0.85 },
                { "node": "LEAF", "combination": "A+B+C",    "diagnosis": "DIAG_PWR_04", "cf": 0.75 }
              ]
            }
          ]
        },
        {
          "node": "LED_ON_BLACK_SCREEN",
          "option": "B",
          "question": "Q04",
          "branching_factor": 4,
          "children": [
            { "node": "LEAF", "option": "B", "diagnosis": "DIAG_PWR_05", "cf": 0.80, "via_question": "Q05" },
            { "node": "REDIRECT", "option": "B", "target": "DISPLAY_ROOT" }
          ]
        }
      ]
    },
    {
      "node": "DISPLAY_ROOT",
      "option": "B",
      "question": "Q09",
      "branching_factor": 6,
      "children": [
        {
          "node": "BLACK_SCREEN",
          "option": "A",
          "question": "Q10",
          "branching_factor": 3,
          "children": [
            {
              "node": "EXTERNAL_OK",
              "option": "A",
              "adds_fact": "display_hardware_issue",
              "children": [
                { "node": "LEAF", "condition": "no_lines", "diagnosis": "DIAG_DSP_01", "cf": 0.75 },
                { "node": "LEAF", "condition": "screen_lines", "diagnosis": "DIAG_DSP_03", "cf": 0.85 }
              ]
            },
            {
              "node": "EXTERNAL_SAME_ISSUE",
              "option": "B",
              "question": "Q11",
              "children": [
                { "node": "LEAF", "condition": "after_driver_install", "diagnosis": "DIAG_DSP_02", "cf": 0.90 },
                { "node": "LEAF", "condition": "color_distorted", "diagnosis": "DIAG_DSP_04", "cf": 0.80 }
              ]
            }
          ]
        },
        {
          "node": "FLICKERING", "option": "B",
          "children": [{ "node": "LEAF", "condition": "after_driver", "diagnosis": "DIAG_DSP_02", "cf": 0.85 }]
        },
        {
          "node": "SCREEN_LINES", "option": "C", "question": "Q12",
          "children": [
            { "node": "LEAF", "condition": "physical_impact", "diagnosis": "DIAG_DSP_03", "cf": 0.95 },
            { "node": "LEAF", "condition": "backlight_fail", "diagnosis": "DIAG_DSP_03", "cf": 0.80 }
          ]
        },
        { "node": "COLOR_DISTORTED", "option": "D", "redirect": "SCREEN_LINES" },
        { "node": "WHITE_SCREEN", "option": "E", "diagnosis": "DIAG_DSP_03", "cf": 0.80 },
        {
          "node": "WRONG_RESOLUTION", "option": "F", "question": "Q11",
          "children": [{ "node": "LEAF", "condition": "after_driver", "diagnosis": "DIAG_DSP_02" }]
        }
      ]
    },
    {
      "node": "OS_ROOT",
      "option": "C",
      "question": "Q13",
      "branching_factor": 5,
      "children": [
        {
          "node": "BSOD",
          "option": "A",
          "question": "Q14",
          "branching_factor": 5,
          "children": [
            { "node": "MEMORY_BSOD", "option": "A", "via": "Q19", "children": [
              { "node": "LEAF", "condition": "memtest_fail", "diagnosis": "DIAG_OS_03" }
            ]},
            { "node": "DRIVER_BSOD", "option": "B", "via": "Q17", "children": [
              { "node": "LEAF", "condition": "recent_change", "diagnosis": "DIAG_OS_02" },
              { "node": "LEAF", "condition": "no_recent_change", "diagnosis": "DIAG_OS_01" }
            ]},
            { "node": "DISK_BSOD", "option": "C", "diagnosis": "DIAG_OS_04" }
          ]
        },
        { "node": "BOOT_LOOP", "option": "B", "via": "Q17", "children": [
          { "node": "LEAF", "condition": "after_windows_update", "diagnosis": "DIAG_OS_05" },
          { "node": "LEAF", "condition": "no_change", "diagnosis": "DIAG_OS_06" }
        ]},
        { "node": "STUCK_LOGO", "option": "C", "via": "Q16", "children": [
          { "node": "LEAF", "condition": "safe_mode_works", "diagnosis": "DIAG_OS_02" },
          { "node": "LEAF", "condition": "safe_mode_fails", "diagnosis": "DIAG_OS_01" }
        ]},
        { "node": "OS_FREEZE", "option": "D", "via": "Q17", "children": [
          { "node": "LEAF", "condition": "recent_change", "diagnosis": "DIAG_OS_02" },
          { "node": "LEAF", "condition": "sfc_errors", "diagnosis": "DIAG_OS_01" }
        ]},
        { "node": "WINDOWS_NOT_LOADING", "option": "E", "via": "Q16", "children": [
          { "node": "LEAF", "condition": "safe_mode_fails", "diagnosis": "DIAG_OS_06" }
        ]}
      ]
    },
    {
      "node": "NETWORK_ROOT",
      "option": "D",
      "question": "Q20",
      "branching_factor": 5,
      "children": [
        { "node": "NO_WIFI_VISIBLE", "option": "A", "via": "Q25", "children": [
          { "node": "LEAF", "condition": "adapter_missing", "diagnosis": "DIAG_NET_02" },
          { "node": "LEAF", "condition": "adapter_error", "diagnosis": "DIAG_NET_01" }
        ]},
        { "node": "CONNECTED_NO_INTERNET", "option": "B", "children": [
          { "node": "ALL_DEVICES_FAIL", "condition": "other_devices_fail", "diagnosis": "DIAG_NET_04" },
          { "node": "ONLY_THIS_DEVICE", "condition": "other_devices_ok", "via": "Q23", "children": [
            { "node": "LEAF", "condition": "dns_error", "diagnosis": "DIAG_NET_03" },
            { "node": "LEAF", "condition": "ip_conflict", "diagnosis": "DIAG_NET_06" },
            { "node": "LEAF", "condition": "ethernet_also_fail", "diagnosis": "DIAG_NET_05" }
          ]}
        ]},
        { "node": "YELLOW_EXCLAMATION", "option": "C", "redirect": "CONNECTED_NO_INTERNET" },
        { "node": "WIFI_SLOW", "option": "D", "children": [
          { "node": "LEAF", "condition": "other_devices_ok", "diagnosis": "DIAG_NET_01" }
        ]}
      ]
    },
    {
      "node": "AUDIO_ROOT",
      "option": "E",
      "question": "Q27",
      "branching_factor": 5,
      "children": [
        { "node": "NO_SOUND", "option": "A", "via": "Q28", "children": [
          { "node": "LEAF", "condition": "device_missing", "diagnosis": "DIAG_AUD_03" },
          { "node": "LEAF", "condition": "driver_error", "diagnosis": "DIAG_AUD_01" },
          { "node": "LEAF", "condition": "device_ok", "diagnosis": "DIAG_AUD_02" }
        ]},
        { "node": "MIC_FAIL", "option": "B", "via": "Q31", "children": [
          { "node": "LEAF", "condition": "disabled", "diagnosis": "DIAG_AUD_02" },
          { "node": "LEAF", "condition": "driver_error", "diagnosis": "DIAG_AUD_01" }
        ]},
        { "node": "CAMERA_FAIL", "option": "C", "via": "Q30", "children": [
          { "node": "LEAF", "condition": "privacy_blocked", "diagnosis": "DIAG_CAM_01" },
          { "node": "LEAF", "condition": "driver_error", "diagnosis": "DIAG_CAM_02" }
        ]}
      ]
    },
    {
      "node": "PERIPHERAL_ROOT",
      "option": "F",
      "question": "Q32",
      "branching_factor": 6,
      "children": [
        { "node": "USB_DEVICE", "option": "A", "via": "Q33", "children": [
          { "node": "ONE_PORT", "condition": "specific_port_fail", "via": "Q34", "children": [
            { "node": "LEAF", "condition": "device_ok_elsewhere", "diagnosis": "DIAG_PER_01" },
            { "node": "LEAF", "condition": "device_fails_everywhere", "diagnosis": "DIAG_PER_03" }
          ]},
          { "node": "LEAF", "condition": "all_ports_fail", "diagnosis": "DIAG_PER_02" }
        ]},
        { "node": "MOUSE", "option": "B", "via": "Q34-Q35", "children": [
          { "node": "LEAF", "condition": "driver_error", "diagnosis": "DIAG_PER_04" },
          { "node": "LEAF", "condition": "port_specific", "diagnosis": "DIAG_PER_01" }
        ]},
        { "node": "BT", "option": "D", "diagnosis": "DIAG_PER_04" }
      ]
    },
    {
      "node": "PERFORMANCE_ROOT",
      "option": "G",
      "question": "Q37",
      "branching_factor": 5,
      "children": [
        { "node": "HOT_AND_SLOW", "option": "A", "via": "Q38-Q40", "children": [
          { "node": "LEAF", "condition": "thermal", "diagnosis": "DIAG_PERF_01" },
          { "node": "LEAF", "condition": "malware", "diagnosis": "DIAG_PERF_02" }
        ]},
        { "node": "SLOW_BOOT", "option": "B", "via": "Q39", "children": [
          { "node": "LEAF", "condition": "many_startup", "diagnosis": "DIAG_PERF_03" }
        ]},
        { "node": "SLOW_MULTI_APP", "option": "C", "via": "Q38", "children": [
          { "node": "LEAF", "condition": "high_ram", "diagnosis": "DIAG_PERF_04" },
          { "node": "REDIRECT", "condition": "high_disk", "target": "STORAGE_ROOT" }
        ]}
      ]
    },
    {
      "node": "STORAGE_ROOT",
      "option": "H",
      "question": "Q36",
      "branching_factor": 6,
      "children": [
        { "node": "LEAF", "option": "A", "diagnosis": "DIAG_STR_01", "cf": 0.90 },
        { "node": "LEAF", "option": "B", "diagnosis": "DIAG_STR_02", "cf": 0.90, "urgent": true },
        { "node": "FILE_CORRUPT", "option": "C", "via": "Q19", "children": [
          { "node": "LEAF", "condition": "chkdsk_errors", "diagnosis": "DIAG_STR_04" }
        ]},
        { "node": "LEAF", "option": "D", "diagnosis": "DIAG_STR_02", "cf": 0.90 },
        { "node": "LEAF", "option": "E", "diagnosis": "DIAG_STR_04", "cf": 0.70 },
        { "node": "LEAF", "option": "F", "diagnosis": "DIAG_STR_03", "cf": 0.85 }
      ]
    }
  ]
}
```

---

## 5.3 Thống kê cây suy luận

| Tầng | Mô tả | Số nodes | Branching Factor |
|------|-------|----------|-----------------|
| 1 | Phân loại nhóm lỗi | 1 | 8 (octary) |
| 2 | Triệu chứng trong nhóm | 8 | 3–6 mỗi node |
| 3 | Phân biệt nguyên nhân | 20+ | 2–4 |
| 4 | Xác nhận triệu chứng phụ | 15+ | 2–3 |
| 5 | Chốt chẩn đoán (lá) | 39+ | — |

**Tổng số đường suy luận**: > 80 paths từ root đến diagnosis  
**Tổng số nodes**: > 100 nodes  
**Mức độ phân nhánh tổng thể**: **Rất cao — octary ở tầng 1, multi-way ở các tầng tiếp theo**
