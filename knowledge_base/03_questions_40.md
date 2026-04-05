# PHẦN 3: BỘ 50 CÂU HỎI CHẨN ĐOÁN (FINAL v2.0)

> **Ghi chú**: File này là tài liệu học thuật (text format) — phản ánh đầy đủ 50 câu hỏi trong `06_questions.json`. Source of truth là JSON.

---

## Q01 — Câu hỏi gốc phân nhóm lỗi (ROOT — 8-way branching)

```yaml
question_id: Q01
question_text: "Máy tính của bạn đang gặp vấn đề gì chính?"
type: single_choice
purpose: Phân loại nhóm lỗi cấp cao — loại bỏ 7/8 nhánh không liên quan
related_facts: []
options:
  A: "Máy không bật / không có điện"         → group = power_startup
  B: "Vấn đề màn hình / hiển thị"            → group = display
  C: "Windows lỗi / BSOD / không vào được"  → group = os_boot
  D: "Wi-Fi / mạng / Internet không hoạt động" → group = network
  E: "Âm thanh / camera / micro không hoạt động" → group = audio_camera
  F: "USB / chuột / bàn phím / ngoại vi lỗi" → group = peripherals
  G: "Máy chạy chậm / nóng / quạt ồn"       → group = performance
  H: "Vấn đề ổ đĩa / lưu trữ / file"        → group = storage
next_branch_logic:
  A → Q02
  B → Q09
  C → Q13
  D → Q20
  E → Q27
  F → Q32
  G → Q37
  H → Q36
```

---

## NHÁNH A — NGUỒN / KHỞI ĐỘNG (Q02–Q08)

```yaml
question_id: Q02
question_text: "Khi bạn nhấn nút nguồn, điều gì xảy ra?"
type: single_choice
purpose: Phân biệt mức độ lỗi nguồn — không điện vs có điện nhưng không hiển thị
related_facts: [F001, F002, F012]
options:
  A: "Hoàn toàn không có phản ứng (đèn không sáng, quạt không quay)" → F001
  B: "Đèn nguồn sáng nhưng màn hình đen hoàn toàn"                   → F002, F012
  C: "Máy chạy bình thường nhưng sau đó tắt đột ngột"               → F002, F004
  D: "Nghe tiếng quạt quay nhưng không lên màn hình"                → F002, F004, F006
next_branch_logic:
  A → Q03
  B → Q04
  C → Q05 (kiểm tra pin/nguồn)
  D → Q04

---

question_id: Q03
question_text: "Máy tính của bạn là laptop hay máy bàn (desktop)?"
type: single_choice
purpose: Phân biệt nguồn gốc lỗi — laptop có adapter+pin, desktop có PSU
related_facts: []
options:
  A: "Laptop"   → is_laptop = true
  B: "Desktop"  → is_laptop = false
next_branch_logic:
  A → Q05
  B → Q08

---

question_id: Q04
question_text: "Khi bật máy, bạn có nghe thấy tiếng 'beep' từ loa/màn hình không?"
type: single_choice
purpose: Phân biệt POST thành công hay thất bại — số beep là mã lỗi BIOS
related_facts: [F005, F006, F007, F008]
options:
  A: "Không nghe thấy tiếng beep nào"          → F006
  B: "1 tiếng beep ngắn (bình thường)"         → F007
  C: "Nhiều tiếng beep lặp lại"                → F008
  D: "Tiếng beep lạ / dài (không phải 1 beep)" → F008
next_branch_logic:
  A → Q06 (không có tín hiệu)
  B → Q09 (POST OK → lỗi màn hình)
  C → Q05 (POST fail → kiểm tra RAM/hardware)
  D → Q05

---

question_id: Q05
question_text: "Tình trạng pin và sạc của laptop như thế nào?"
type: single_choice
purpose: Phân biệt lỗi pin vs lỗi adapter vs lỗi bo mạch
related_facts: [F009, F010, F011]
options:
  A: "Đèn sạc không sáng khi cắm adapter"           → F010, F009
  B: "Đèn sạc sáng nhưng pin không tăng"            → F010
  C: "Máy chỉ chạy khi cắm điện, không chạy bằng pin" → F011
  D: "Adapter nóng bất thường hoặc có mùi khét"     → F009, F010
next_branch_logic:
  A → (probable: adapter_faulty → DIAG_PWR_01)
  B → (probable: battery_failing → DIAG_PWR_02)
  C → (probable: battery_dead → DIAG_PWR_02)
  D → (probable: adapter_faulty → DIAG_PWR_01)

---

question_id: Q06
question_text: "Bạn đã thử tháo pin, giữ nút nguồn 30 giây rồi cắm lại chưa?"
type: yes_no
purpose: Xác nhận bước reset điện cơ bản — loại bỏ lỗi tĩnh điện
related_facts: []
options:
  YES: "Đã thử, vẫn không lên"  → continue diagnosis
  NO:  "Chưa thử"               → recommend_basic_reset
next_branch_logic:
  YES → Q07
  NO  → suggest_action: "Hãy thử bước này trước, nếu vẫn không được hãy tiếp tục"

---

question_id: Q07
question_text: "Điều gì xảy ra khi bạn rút hết thiết bị ngoại vi (USB, màn hình ngoài) và thử bật lại?"
type: single_choice
purpose: Loại bỏ thiết bị ngoại vi gây lỗi — short circuit hoặc USB device lỗi
related_facts: []
options:
  A: "Máy bật được bình thường"       → peripheral_causing_issue
  B: "Vẫn không bật được"             → F001 confirmed
  C: "Máy bật nhưng vẫn không có màn hình" → F001, F012
next_branch_logic:
  A → DIAG_PER: peripheral_short_circuit
  B → Q08 (kiểm tra phần cứng nguồn)
  C → Q09 (lỗi màn hình)

---

question_id: Q08
question_text: "Về nguồn điện — bạn có thể kiểm tra các điều sau không?"
type: multi_choice
purpose: Thu thập nhiều facts về nguồn để phân biệt PSU vs bo mạch vs socket
related_facts: [F001, F003]
options:
  A: "Đã thử ổ điện khác — vẫn không lên"
  B: "Đèn LED trên bo mạch chủ không sáng"
  C: "PSU/adapter đã kiểm tra là hoạt động tốt"
  D: "Có thể nghe tiếng 'tích' nhỏ khi cắm điện"
next_branch_logic:
  A+B+notC → DIAG_PWR_03 (PSU hỏng)
  A+B+C    → DIAG_PWR_04 (bo mạch chủ lỗi)
  D        → probable_short_circuit
```

---

## NHÁNH B — MÀN HÌNH / HIỂN THỊ (Q09–Q12)

```yaml
question_id: Q09
question_text: "Vấn đề màn hình bạn đang gặp là gì?"
type: single_choice
purpose: Phân biệt các loại lỗi màn hình — mỗi loại có nguyên nhân khác nhau
related_facts: [F020, F021, F022, F023, F024]
options:
  A: "Màn hình đen hoàn toàn (không có gì)"  → F020
  B: "Màn hình nhấp nháy / giật liên tục"    → F021
  C: "Xuất hiện sọc ngang hoặc dọc"          → F022
  D: "Màu sắc bị lạ / sai màu"              → F023
  E: "Màn hình trắng hoàn toàn"             → F024
  F: "Độ phân giải / kích thước sai"         → F028
next_branch_logic:
  A → Q10
  B → Q11
  C → Q12
  D → Q12
  E → Q10
  F → Q11 (thường do driver)

---

question_id: Q10
question_text: "Bạn có thể kết nối màn hình ngoài (qua HDMI/VGA) để kiểm tra không?"
type: single_choice
purpose: Phân biệt lỗi màn hình nội bộ vs GPU vs cáp kết nối màn hình
related_facts: [F025, F026]
options:
  A: "Màn hình ngoài hiển thị bình thường"     → F025 → display_panel_issue
  B: "Màn hình ngoài cũng đen / cùng vấn đề"  → F026 → gpu_or_driver_issue
  C: "Không có cổng/cáp HDMI để kiểm tra"     → cannot_verify
next_branch_logic:
  A → IF005, IF006 → DIAG_DSP_01 or DIAG_DSP_03
  B → Q12 (kiểm tra driver/GPU)
  C → Q11

---

question_id: Q11
question_text: "Khi nào màn hình bắt đầu gặp vấn đề này?"
type: single_choice
purpose: Xác định nguyên nhân gốc rễ dựa trên thời điểm xuất hiện lỗi
related_facts: [F027, F028, F029]
options:
  A: "Sau khi cài hoặc cập nhật driver màn hình/GPU"   → F029, IF007
  B: "Sau khi Windows Update"                          → F029, IF010
  C: "Máy bị va đập / rơi"                            → F022, IF008
  D: "Tự nhiên xuất hiện không rõ nguyên nhân"        → F021
  E: "Từ khi mua máy / ngay từ đầu"                  → F022, IF008
next_branch_logic:
  A → DIAG_DSP_02 (driver GPU lỗi)
  B → DIAG_DSP_02 (driver GPU lỗi do update)
  C → DIAG_DSP_03 or DIAG_DSP_04 (hardware damage)
  D → Q12
  E → DIAG_DSP_03 (hardware defect)

---

question_id: Q12
question_text: "Độ sáng màn hình có bình thường không? Thử nhìn nghiêng có thấy hình mờ không?"
type: single_choice
purpose: Phân biệt đèn nền (backlight) hỏng vs màn hình thực sự đen
related_facts: [F027]
options:
  A: "Màn hình hoàn toàn đen, không thấy gì kể cả nhìn nghiêng" → screen_totally_dark
  B: "Nhìn nghiêng thấy hình mờ mờ (backlight tắt)"             → F027, backlight_fail
  C: "Màn hình sáng nhưng quá tối (brightness thấp)"            → F027
  D: "Chức năng phím tắt brightness có thể bị kẹt"              → F027
next_branch_logic:
  A → IF008, IF006 → DIAG_DSP_03 or DIAG_DSP_04
  B → DIAG_DSP_03 (backlight/inverter lỗi)
  C → DIAG_DSP_10 (brightness setting)
  D → suggest: Fn + brightness key
```

---

## NHÁNH C — HỆ ĐIỀU HÀNH / BOOT (Q13–Q19)

```yaml
question_id: Q13
question_text: "Vấn đề hệ điều hành bạn đang gặp là gì?"
type: single_choice
purpose: Phân loại chính xác loại lỗi OS — mỗi loại có nguyên nhân và hướng xử lý khác nhau
related_facts: [F040, F044, F045, F046, F053]
options:
  A: "Màn hình xanh chết chóc (BSOD) xuất hiện"                  → F040
  B: "Máy khởi động lại liên tục (boot loop)"                    → F044
  C: "Máy dừng ở màn hình logo, không vào được Windows"          → F045
  D: "Windows load xong nhưng bị treo / đứng màn hình"          → F053
  E: "Không vào được Windows, màn hình đen sau logo"             → F046
next_branch_logic:
  A → Q14
  B → Q17
  C → Q16
  D → Q17
  E → Q16

---

question_id: Q14
question_text: "Màn hình BSOD hiển thị mã lỗi gì? (nhìn vào dòng chữ ở giữa màn hình xanh)"
type: single_choice
purpose: Mã lỗi BSOD trực tiếp chỉ ra nguyên nhân — memory, driver, hay disk
related_facts: [F041, F042, F043]
options:
  A: "MEMORY_MANAGEMENT / PAGE_FAULT_IN_NONPAGED_AREA / IRQL_NOT_LESS_OR_EQUAL"  → F041
  B: "DRIVER_IRQL_NOT_LESS / SYSTEM_SERVICE_EXCEPTION / DRIVER_POWER_STATE"       → F042
  C: "CRITICAL_PROCESS_DIED / NTFS_FILE_SYSTEM / INACCESSIBLE_BOOT_DEVICE"        → F043
  D: "Không kịp đọc / không có mã lỗi"                                            → need_event_log
  E: "Mã lỗi khác (ghi lại hoặc chụp ảnh)"                                       → generic_bsod
next_branch_logic:
  A → Q19 (kiểm tra RAM) → DIAG_OS_03
  B → Q17 (kiểm tra thay đổi gần đây) → DIAG_OS_02
  C → Q19 (kiểm tra disk) → DIAG_OS_04
  D → Q15
  E → Q17

---

question_id: Q15
question_text: "BSOD xảy ra khi nào?"
type: single_choice
purpose: Thời điểm BSOD giúp thu hẹp nguyên nhân
related_facts: [F041, F042, F043]
options:
  A: "Ngay khi bật máy / trong lúc boot"         → IF013 (disk/OS)
  B: "Khi chạy game hoặc ứng dụng nặng"         → IF008 (GPU) or IF012 (RAM)
  C: "Khi cắm/rút thiết bị USB"                 → F042 (driver USB)
  D: "Ngẫu nhiên, không có pattern"              → IF012 (RAM)
  E: "Sau khi cài phần mềm/driver cụ thể"       → F042, IF011
next_branch_logic:
  A → DIAG_OS_04 or DIAG_OS_06
  B → Q19 (kiểm tra RAM và GPU)
  C → DIAG_PER_02 (USB driver)
  D → DIAG_OS_03 (RAM lỗi)
  E → DIAG_OS_02 (driver lỗi)

---

question_id: Q16
question_text: "Bạn có thể vào Windows ở chế độ Safe Mode không? (F8 khi khởi động)"
type: single_choice
purpose: Safe Mode là bước chẩn đoán quan trọng — loại bỏ driver bên thứ 3
related_facts: [F047, F048]
options:
  A: "Có, Safe Mode hoạt động bình thường"        → F047
  B: "Không, Safe Mode cũng bị lỗi/đứng"        → F048
  C: "Không biết cách vào Safe Mode"             → guide_user
next_branch_logic:
  A → Q17 (Safe Mode OK → lỗi driver/startup)
  B → DIAG_OS_01 or DIAG_OS_06 (OS corruption nghiêm trọng)
  C → suggest_safemodeSteps then come back

---

question_id: Q17
question_text: "Sự kiện nào xảy ra TRƯỚC KHI máy bắt đầu gặp lỗi?"
type: multi_choice
purpose: Xác định nguyên nhân gốc rễ dựa trên sự thay đổi môi trường hệ thống
related_facts: [F049, F050, F051]
options:
  A: "Vừa cài phần mềm mới"          → F049, IF010
  B: "Vừa cập nhật Windows"          → F050, IF010
  C: "Vừa cập nhật driver"           → F051, IF010
  D: "Máy bị nhiễm virus/malware"    → F118
  E: "Không có thay đổi gì"          → no_recent_change
  F: "Vừa cài lại Windows"           → fresh_install_issue
next_branch_logic:
  A → DIAG_OS_02 (phần mềm gây conflict)
  B → DIAG_OS_05 (Windows Update loop)
  C → DIAG_OS_02 (driver conflict)
  D → DIAG_PERF_02 (malware)
  E → Q18 (không có thay đổi → kiểm tra phần cứng)
  F → DIAG_OS_06 (MBR/boot issue)

---

question_id: Q18
question_text: "Có System Restore point hoặc backup gần đây không?"
type: yes_no
purpose: Xác định khả năng recovery — ảnh hưởng đến giải pháp đề xuất
related_facts: [F052]
options:
  YES: "Có restore point"     → F052 → recommend_system_restore
  NO:  "Không có"            → no_restore → recommend_sfc_dism
next_branch_logic:
  YES → suggest_action: System Restore as first step
  NO  → Q19

---

question_id: Q19
question_text: "Bạn có thể chạy công cụ kiểm tra nào sau đây không?"
type: single_choice
purpose: Thu thập kết quả chẩn đoán từ công cụ hệ thống
related_facts: [F133, F136]
options:
  A: "Chạy Windows Memory Diagnostic — báo LỖI"    → F041 confirmed → DIAG_OS_03
  B: "Chạy CHKDSK — tìm thấy bad sectors"          → F133, F136 → DIAG_STR_02
  C: "Chạy SFC /scannow — tìm thấy file lỗi"       → DIAG_OS_01
  D: "Tất cả công cụ báo bình thường"               → need_deeper_diag
  E: "Không biết cách chạy các công cụ này"         → guide_user
next_branch_logic:
  A → DIAG_OS_03
  B → DIAG_STR_02 or DIAG_OS_04
  C → DIAG_OS_01
  D → Q17 (quay lại kiểm tra thay đổi)
```

---

## NHÁNH D — MẠNG / WI-FI / INTERNET (Q20–Q26)

```yaml
question_id: Q20
question_text: "Vấn đề mạng bạn đang gặp là gì?"
type: single_choice
purpose: Phân biệt không thấy Wi-Fi vs kết nối nhưng không có Internet vs chậm
related_facts: [F060, F061, F062, F072]
options:
  A: "Không thấy bất kỳ mạng Wi-Fi nào trong danh sách"    → F060
  B: "Kết nối Wi-Fi nhưng không vào được Internet"          → F061
  C: "Có kết nối Wi-Fi nhưng biểu tượng có dấu chấm than" → F072
  D: "Mạng rất chậm dù tín hiệu tốt"                       → F062
  E: "Mạng bị ngắt kết nối liên tục"                       → F061, F062
next_branch_logic:
  A → Q25 (kiểm tra adapter)
  B → Q21, Q22
  C → Q22
  D → Q22, Q24
  E → Q22

---

question_id: Q21
question_text: "Thử cắm cáp mạng (LAN/Ethernet) vào máy — kết quả thế nào?"
type: single_choice
purpose: Phân biệt lỗi Wi-Fi adapter vs lỗi mạng tổng quát (DNS/ISP/router)
related_facts: [F063, F064]
options:
  A: "Cắm cáp mạng → có Internet bình thường" → F063 (lỗi chỉ ở Wi-Fi)
  B: "Cắm cáp mạng cũng không có Internet"    → F064 (lỗi ở cấp router/ISP)
  C: "Không có cáp mạng để thử"               → cannot_verify
next_branch_logic:
  A → Q25 (lỗi Wi-Fi driver/hardware)
  B → Q22 (kiểm tra các thiết bị khác)
  C → Q22

---

question_id: Q22
question_text: "Các thiết bị khác (điện thoại, máy tính khác) dùng cùng Wi-Fi có vào Internet được không?"
type: single_choice
purpose: Phân biệt lỗi ở máy tính vs lỗi ở router/ISP
related_facts: [F065, F066]
options:
  A: "Có, thiết bị khác bình thường"     → F065 (lỗi ở máy này)
  B: "Không, tất cả đều không vào được" → F066 (lỗi ở router/ISP)
  C: "Chỉ có một thiết bị này nên không biết" → single_device
next_branch_logic:
  A → Q23 (lỗi ở máy: DNS/config/driver)
  B → DIAG_NET_04 (router hoặc ISP lỗi)
  C → Q23

---

question_id: Q23
question_text: "Trình duyệt báo lỗi gì khi không vào được Internet?"
type: single_choice
purpose: Thông báo lỗi trình duyệt là manh mối trực tiếp về nguyên nhân
related_facts: [F067, F068]
options:
  A: "DNS_PROBE_FINISHED_NXDOMAIN hoặc lỗi DNS" → F067 → DIAG_NET_03
  B: "ERR_CONNECTION_TIMED_OUT / không phản hồi" → timeout_issue
  C: "ERR_NETWORK_CHANGED"                        → F071 (IP conflict)
  D: "Chỉ một số website không vào được"          → F068 (VPN/firewall/DNS)
  E: "Không có thông báo lỗi"                     → general_no_internet
next_branch_logic:
  A → DIAG_NET_03 (DNS lỗi)
  B → Q24 (VPN/Firewall?)
  C → DIAG_NET_06 (IP conflict)
  D → Q24
  E → Q25

---

question_id: Q24
question_text: "Máy tính có đang sử dụng VPN, proxy hoặc phần mềm bảo mật đặc biệt không?"
type: yes_no
purpose: VPN/Proxy thường gây lỗi mạng — cần loại trừ
related_facts: [F069]
options:
  YES: "Có dùng VPN hoặc proxy"   → F069 → suggest: disable VPN first
  NO:  "Không dùng"               → continue
next_branch_logic:
  YES → DIAG_NET_troubleshoot: disable_vpn_then_test
  NO  → Q25

---

question_id: Q25
question_text: "Trong Device Manager, Wi-Fi adapter có hiển thị không?"
type: single_choice
purpose: Xác định lỗi phần cứng adapter vs lỗi driver
related_facts: [F070, F071]
options:
  A: "Không thấy Wi-Fi adapter trong Device Manager"    → F070, IF014 → DIAG_NET_02
  B: "Thấy adapter nhưng có dấu chấm than vàng"        → IF015 → DIAG_NET_01
  C: "Adapter hiển thị bình thường (không có lỗi)"      → IF016, IF017
  D: "Không biết cách mở Device Manager"               → guide_user
next_branch_logic:
  A → DIAG_NET_02 (hardware Wi-Fi fail)
  B → DIAG_NET_01 (driver lỗi)
  C → Q23 (lỗi ở cấp cấu hình mạng)
  D → suggest: Win + X → Device Manager

---

question_id: Q26
question_text: "Thử chạy 'ipconfig /release' rồi 'ipconfig /renew' trong CMD — kết quả thế nào?"
type: single_choice
purpose: Xác định lỗi DHCP/IP configuration
related_facts: [F071]
options:
  A: "Sau khi chạy lệnh, Internet hoạt động"          → DHCP_fix_worked → DIAG_NET_06
  B: "Lệnh báo lỗi không lấy được IP"                → IF019 → DIAG_NET_05
  C: "Không thay đổi gì"                              → IF016 → DIAG_NET_05
  D: "Không biết cách chạy lệnh CMD"                 → guide_user
next_branch_logic:
  A → resolved (IP conflict fixed)
  B → DIAG_NET_05 (network stack lỗi)
  C → DIAG_NET_05 or DIAG_NET_03
```

---

## NHÁNH E — ÂM THANH / CAMERA (Q27–Q31)

```yaml
question_id: Q27
question_text: "Thiết bị nào đang gặp vấn đề?"
type: single_choice
purpose: Phân biệt lỗi âm thanh vs lỗi micro vs lỗi camera — khác nhau về nguyên nhân
related_facts: [F080, F082, F083]
options:
  A: "Không có âm thanh từ loa"              → F080
  B: "Microphone không hoạt động"            → F082
  C: "Camera không được nhận / không hiển thị" → F083
  D: "Cả loa lẫn micro đều lỗi"             → F080, F082
  E: "Tai nghe/headset không hoạt động"      → F085
next_branch_logic:
  A → Q28
  B → Q30
  C → Q30
  D → Q28 (rồi Q30)
  E → Q29

---

question_id: Q28
question_text: "Về vấn đề âm thanh — bạn kiểm tra thấy điều gì?"
type: single_choice
purpose: Thu hẹp nguyên nhân lỗi âm thanh: hardware vs driver vs settings
related_facts: [F081, F084, F085]
options:
  A: "Trong Device Manager không thấy thiết bị âm thanh"     → F084, IF020 → DIAG_AUD_03
  B: "Thấy thiết bị âm thanh nhưng có dấu chấm than vàng"    → F087, IF021 → DIAG_AUD_01  
  C: "Thanh âm lượng ở 0 hoặc bị mute"                       → IF022 → DIAG_AUD_02
  D: "Loa OK nhưng cắm tai nghe không có tiếng"              → F085 → jack_issue
  E: "Âm thanh bị rè, nhiễu, méo"                            → F081 → DIAG_AUD_03
next_branch_logic:
  A → DIAG_AUD_03 (hardware)
  B → DIAG_AUD_01 (driver)
  C → DIAG_AUD_02 (settings)
  D → Q29
  E → DIAG_AUD_03

---

question_id: Q29
question_text: "Âm thanh có bao giờ hoạt động sau khi restart không?"
type: single_choice
purpose: Lỗi tạm thời sau restart gợi ý driver issue, lỗi cố định gợi ý hardware
related_facts: [F086, F087]
options:
  A: "Sau restart thì có âm thanh trong ít phút rồi mất"  → F086, driver_unstable
  B: "Sau restart vẫn không có âm thanh"                  → F087 or hardware
  C: "Chưa bao giờ có âm thanh (máy mới)"                → fresh_install_issue
  D: "Vừa cập nhật Windows/driver rồi mất âm thanh"      → F087, IF010, IF021
next_branch_logic:
  A → DIAG_AUD_01 (driver không ổn định)
  B → Q28 (kiểm tra lại device manager)
  C → DIAG_AUD_01 (cần cài driver)
  D → DIAG_AUD_01 (driver update gây lỗi)

---

question_id: Q30
question_text: "Về vấn đề camera — bạn kiểm tra thấy điều gì?"
type: single_choice
purpose: Phân biệt lỗi privacy settings vs driver vs phần cứng camera
related_facts: [F083, F088, F089]
options:
  A: "Camera bị chặn trong Windows Settings > Privacy" → F088, IF023 → DIAG_CAM_01
  B: "Camera hiển thị trong Device Manager nhưng lỗi" → IF023 → DIAG_CAM_02
  C: "Camera không hiển thị trong Device Manager"     → hardware_camera_issue
  D: "Camera hoạt động ở app này nhưng không ở app khác" → F089, app_permission
  E: "Có phần mềm khác đang dùng camera"              → resource_conflict
next_branch_logic:
  A → DIAG_CAM_01 (privacy)
  B → DIAG_CAM_02 (driver)
  C → DIAG_CAM_02 or hardware
  D → suggest: check app permissions
  E → suggest: close other apps using camera

---

question_id: Q31
question_text: "Micro không hoạt động — bạn kiểm tra cài đặt âm thanh thấy gì?"
type: single_choice
purpose: Micro thường bị vô hiệu hóa trong settings hoặc lỗi driver
related_facts: [F082]
options:
  A: "Micro bị disabled trong Sound Settings"              → settings_disabled → DIAG_AUD_02
  B: "Micro xuất hiện trong Device Manager nhưng lỗi"     → DIAG_AUD_01
  C: "Micro không xuất hiện trong Sound Devices"          → hardware_micro_issue
  D: "Micro hoạt động ở Windows nhưng không ở ứng dụng"  → app_permission_micro
next_branch_logic:
  A → DIAG_AUD_02
  B → DIAG_AUD_01
  C → hardware_micro_fail
  D → suggest: check app microphone permissions
```

---

## NHÁNH F — THIẾT BỊ NGOẠI VI / USB (Q32–Q36)

```yaml
question_id: Q32
question_text: "Thiết bị ngoại vi nào đang gặp vấn đề?"
type: single_choice
purpose: Phân biệt loại thiết bị — ảnh hưởng đến cách chẩn đoán
related_facts: [F090, F092, F093, F098, F099]
options:
  A: "Thiết bị USB (flash drive, chuột USB, ...)"   → F090
  B: "Chuột không hoạt động"                        → F092
  C: "Bàn phím không hoạt động"                    → F093
  D: "Bluetooth không kết nối được"                → F098
  E: "Máy in không được nhận"                      → F099
  F: "Touchpad laptop không hoạt động"              → F100
next_branch_logic:
  A → Q33
  B → Q34 (chuột USB → Q33, chuột PS2 → keyboard_mouse_bios)
  C → Q34
  D → DIAG_PER_04 (Bluetooth driver)
  E → Q35
  F → suggest: check touchpad hotkey / driver reinstall

---

question_id: Q33
question_text: "Vấn đề USB xảy ra ở bao nhiêu cổng?"
type: single_choice
purpose: Phân biệt 1 cổng hỏng vs tất cả cổng hỏng — hai nguyên nhân hoàn toàn khác
related_facts: [F094, F095]
options:
  A: "Chỉ một cổng USB cụ thể bị lỗi"           → F094, IF024 → DIAG_PER_01
  B: "Một số cổng bị lỗi, một số vẫn OK"         → IF024 (multiple port fail)
  C: "Tất cả cổng USB đều bị lỗi"               → F095, IF025 → DIAG_PER_02
next_branch_logic:
  A → Q34 (xác nhận thiết bị hay cổng lỗi)
  B → Q34
  C → DIAG_PER_02 (USB controller)

---

question_id: Q34
question_text: "Thiết bị USB hoạt động trên máy khác không?"
type: single_choice
purpose: Phân biệt thiết bị lỗi vs cổng lỗi vs driver lỗi
related_facts: [F096, F097]
options:
  A: "Thiết bị hoạt động bình thường trên máy khác"   → F096, IF024 → port_or_driver_issue
  B: "Thiết bị cũng lỗi trên máy khác"               → F097, IF026 → DIAG_PER_03
  C: "Không có máy khác để thử"                       → cannot_verify
next_branch_logic:
  A → DIAG_PER_01 or DIAG_PER_02 (tùy Q33)
  B → DIAG_PER_03 (thiết bị hỏng)
  C → Q35 (kiểm tra driver)

---

question_id: Q35
question_text: "Trong Device Manager, thiết bị ngoại vi hiển thị thế nào?"
type: single_choice
purpose: Device Manager phản ánh trạng thái driver và nhận dạng thiết bị
related_facts: [F091]
options:
  A: "Có biểu tượng dấu chấm than vàng"              → F091, driver_issue → DIAG_PER_04
  B: "Thiết bị không xuất hiện trong Device Manager" → device_not_recognized → Q33
  C: "Xuất hiện dưới 'Unknown Device'"               → driver_missing → DIAG_PER_04
  D: "Thiết bị hiển thị bình thường"                 → software_conflict
next_branch_logic:
  A → DIAG_PER_04 (driver)
  B → DIAG_PER_01 or DIAG_PER_03
  C → DIAG_PER_04
  D → suggest: check device specific software
```

---

## NHÁNH H — LƯU TRỮ / Ổ ĐĨA (Q36)

```yaml
question_id: Q36
question_text: "Vấn đề ổ đĩa/lưu trữ bạn đang gặp là gì?"
type: single_choice
purpose: Phân biệt đầy ổ đĩa vs HDD hỏng vs file system lỗi — cách xử lý khác nhau hoàn toàn
related_facts: [F130, F131, F132, F133, F135, F136, F137]
options:
  A: "Ổ C: gần đầy, máy chạy chậm"                           → F130, IF032 → DIAG_STR_01
  B: "HDD phát ra tiếng click lách cách khi chạy"            → F131, IF031 → DIAG_STR_02
  C: "File bị hỏng, không mở được, hoặc biến mất"           → F132, IF031 → DIAG_STR_04
  D: "CHKDSK báo lỗi bad sectors"                            → F133, F136 → DIAG_STR_02
  E: "Ổ đĩa thứ 2 không hiển thị trong My Computer"         → F135 → DIAG_STR_04
  F: "SSD: CrystalDiskInfo báo health thấp (<80%)"          → F137 → DIAG_STR_03
next_branch_logic:
  A → DIAG_STR_01
  B → DIAG_STR_02 (urgent)
  C → DIAG_STR_04
  D → DIAG_STR_02
  E → disk_detect_issue
  F → DIAG_STR_03
```

---

## NHÁNH G — HIỆU NĂNG / NHIỆT ĐỘ (Q37–Q40)

```yaml
question_id: Q37
question_text: "Vấn đề hiệu năng bạn đang gặp là gì?"
type: single_choice
purpose: Phân biệt nguyên nhân chậm — nhiệt độ vs phần mềm vs hardware
related_facts: [F110, F111, F112, F116, F117, F134]
options:
  A: "Máy rất chậm, đặc biệt là chạy nặng (quạt ồn, nóng)"     → F110, F111, F112
  B: "Khởi động Windows rất lâu (hơn 3 phút)"                   → F116
  C: "Máy chậm khi mở nhiều ứng dụng cùng lúc"                  → F110, F114
  D: "Chỉ chậm ở một số ứng dụng cụ thể"                        → F117
  E: "Copy/đọc file rất chậm dù dung lượng nhỏ"                 → F134, IF030
next_branch_logic:
  A → Q38, Q40 (nhiệt độ + tài nguyên)
  B → Q39 (startup programs) → DIAG_PERF_03
  C → Q38 (RAM)
  D → software_specific_issue
  E → DIAG_STR_02 or DIAG_STR_03 (storage failing)

---

question_id: Q38
question_text: "Mở Task Manager (Ctrl+Shift+Esc) — tài nguyên nào đang ở mức cao?"
type: multi_choice
purpose: Task Manager cung cấp dữ liệu thực tế về bottleneck hệ thống
related_facts: [F113, F114, F115]
options:
  A: "CPU: luôn ở 90-100%"        → F113 → Q39 (xem process gì chiếm CPU)
  B: "Memory/RAM: gần đầy (>85%)" → F114 → DIAG_PERF_04 (RAM không đủ)
  C: "Disk: luôn ở 100%"         → F115 → IF030, IF032
  D: "Tất cả bình thường"        → background_process_issue
next_branch_logic:
  A+F113 → Q40 (kiểm tra nhiệt độ/malware)
  B+F114 → DIAG_PERF_04
  C+F115 → Q36 (kiểm tra disk)
  D      → Q39 (startup programs)

---

question_id: Q39
question_text: "Về phần mềm và bảo mật — máy tính của bạn có dấu hiệu nào sau không?"
type: multi_choice
purpose: Phân biệt malware vs startup bloat vs thực sự thiếu tài nguyên
related_facts: [F118, F119]
options:
  A: "Máy chậm ngay từ khi bật"                              → F119, IF028
  B: "Thấy nhiều chương trình không rõ trong Task Manager"   → F118, IF029
  C: "Phần mềm diệt virus phát hiện mối đe dọa"             → F118, IF029
  D: "Máy chậm hơn hẳn so với vài tháng trước"              → gradual_slowdown
  E: "Đã lâu không restart/shutdown đúng cách"              → need_restart
next_branch_logic:
  A → DIAG_PERF_03 (startup programs)
  B+C → DIAG_PERF_02 (malware)
  D → Q40 (kiểm tra nhiệt độ)
  E → suggest_restart_first

---

question_id: Q40
question_text: "Về nhiệt độ và tản nhiệt — bạn kiểm tra thấy gì?"
type: single_choice
purpose: Quá nhiệt là nguyên nhân phổ biến nhất gây chậm laptop — thermal throttling
related_facts: [F120, F121]
options:
  A: "Máy nóng rất nhiều, đặc biệt ở đáy laptop"                  → F112, IF027
  B: "Quạt kêu to nhưng máy vẫn nóng"                             → F111, F112, IF027
  C: "Máy dùng lâu (>2 năm) chưa bao giờ vệ sinh"                → F121, IF027
  D: "Phần mềm HWMonitor báo CPU >90°C khi load"                  → IF027, F120 → DIAG_PERF_01
  E: "Nhiệt độ bình thường nhưng vẫn chậm"                        → IF028 → Q39
next_branch_logic:
  A+B → DIAG_PERF_01 (thermal throttling)
  C   → DIAG_PERF_01 (bụi + keo tản nhiệt)
  D   → DIAG_PERF_01 (urgent)
  E   → DIAG_PERF_03 or DIAG_PERF_04
```
