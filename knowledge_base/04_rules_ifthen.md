# PHẦN 6: BỘ LUẬT IF–THEN ĐẦY ĐỦ (103 LUẬT — FINAL v2.0)

> **Ghi chú**: File này là tài liệu học thuật (text format). Source of truth đầy đủ 103 luật là `07_rules_and_diagnoses.json`. File này mô tả các luật gốc; các luật mở rộng (BT, Touchpad, SHTDN, BIOS, R_Q38_*, R_Q39_*) nằm trong JSON.

## Ký hiệu
- `AND`: tất cả điều kiện phải đúng
- `OR`: ít nhất một điều kiện đúng
- `NOT`: điều kiện phải sai
- `→`: suy ra kết luận
- `[CF=x]`: Certainty Factor (0.0–1.0)
- `[PRIORITY=x]`: độ ưu tiên khi xung đột (1=thấp nhất)

---

## NHÓM 1: LUẬT NGUỒN / KHỞI ĐỘNG (R001–R015)

```
R001: Nguồn hoàn toàn chết — Adapter hỏng (Laptop)
IF   no_power
AND  fan_not_spinning
AND  battery_indicator_red
AND  is_laptop
THEN probable_adapter_issue   [CF=0.85] [PRIORITY=3]
NOTE: Đèn pin đỏ/nhấp nháy khi cắm adapter = adapter không cấp đủ điện

R002: Adapter hỏng — xác nhận
IF   probable_adapter_issue
AND  no_charge
THEN DIAG_PWR_01: faulty_adapter   [CF=0.90] [PRIORITY=4]

R003: Nguồn chết — Pin chai (Laptop)
IF   power_led_on
AND  laptop_only_on_adapter
AND  NOT no_charge
AND  is_laptop
THEN DIAG_PWR_02: dead_battery   [CF=0.85] [PRIORITY=3]
NOTE: Máy chỉ sống khi cắm điện = pin đã chết hoàn toàn

R004: Nguồn hoàn toàn chết — PSU hỏng (Desktop)
IF   no_power
AND  fan_not_spinning
AND  NOT is_laptop
THEN probable_power_hardware   [CF=0.80] [PRIORITY=3]

R005: Xác nhận PSU hỏng
IF   probable_power_hardware
AND  NOT power_led_on
THEN DIAG_PWR_03: faulty_psu   [CF=0.85] [PRIORITY=3]

R006: Bo mạch chủ lỗi điện
IF   probable_power_hardware
AND  power_led_on
AND  fan_not_spinning
THEN DIAG_PWR_04: motherboard_power_fault   [CF=0.75] [PRIORITY=2]
NOTE: Đèn LED bo mạch sáng nhưng không boot → bo mạch lỗi, không phải PSU

R007: POST thất bại — Beep lỗi
IF   multiple_beeps
AND  power_led_on
AND  fan_spinning
THEN bios_post_fail   [CF=0.90] [PRIORITY=4]

R008: POST fail → RAM lỏng/hỏng
IF   bios_post_fail
AND  no_display_after_power
THEN DIAG_PWR_05: ram_loose_or_faulty   [CF=0.80] [PRIORITY=3]
NOTE: Beep lỗi + không lên màn hình là dấu hiệu RAM phổ biến nhất

R009: Máy boot nhưng không có màn hình
IF   power_led_on
AND  fan_spinning
AND  single_beep
AND  screen_black
THEN system_boots_no_display   [CF=0.85] [PRIORITY=3]

R010: Pin không sạc — Cổng sạc hỏng
IF   no_charge
AND  battery_indicator_red
AND  NOT laptop_only_on_adapter
THEN DIAG_PWR_01: faulty_adapter   [CF=0.70] [PRIORITY=2]
NOTE: CF thấp hơn vì cũng có thể do cổng sạc của laptop bị hỏng

R011: Máy bật được sau khi rút ngoại vi → ngoại vi gây lỗi
IF   no_power
AND  peripheral_removed
AND  power_restored
THEN DIAG_PER: peripheral_short_circuit   [CF=0.80] [PRIORITY=3]
```

---

## NHÓM 2: LUẬT MÀN HÌNH / HIỂN THỊ (R016–R028)

```
R016: Màn hình đen + màn hình ngoài OK → Lỗi màn hình nội bộ
IF   system_boots_no_display
AND  external_monitor_ok
THEN display_hardware_issue   [CF=0.90] [PRIORITY=4]

R017: Lỗi màn hình nội bộ → Cáp màn hình lỏng
IF   display_hardware_issue
AND  NOT screen_lines
AND  NOT screen_color_distorted
THEN DIAG_DSP_01: loose_display_cable   [CF=0.75] [PRIORITY=2]
NOTE: Cáp màn hình lỏng thường gây đen màn hình đột ngột, không có sọc

R018: Lỗi màn hình nội bộ → Panel LCD hỏng
IF   display_hardware_issue
AND  screen_lines
THEN DIAG_DSP_03: lcd_panel_defective   [CF=0.85] [PRIORITY=3]
NOTE: Sọc thẳng đứng/nằm ngang = panel LCD bị vỡ matrix hoặc mạch điều khiển

R019: Màn hình ngoài cũng lỗi → GPU / Driver
IF   screen_black
AND  external_monitor_same_issue
THEN probable_gpu_issue   [CF=0.85] [PRIORITY=3]

R020: GPU issue + Driver mới cài → Lỗi driver GPU
IF   probable_gpu_issue
AND  display_after_driver_install
THEN DIAG_DSP_02: gpu_driver_corrupted   [CF=0.90] [PRIORITY=4]

R021: GPU issue + Không có thay đổi driver → Hardware GPU hỏng
IF   probable_gpu_issue
AND  NOT display_after_driver_install
AND  screen_color_distorted
THEN DIAG_DSP_04: gpu_hardware_failure   [CF=0.80] [PRIORITY=3]

R022: Màn hình nhấp nháy + sau driver update → Driver lỗi
IF   screen_flickering
AND  display_after_driver_install
THEN DIAG_DSP_02: gpu_driver_corrupted   [CF=0.85] [PRIORITY=3]

R023: Màn hình trắng → LCD panel lỗi
IF   screen_white
AND  NOT external_monitor_same_issue
THEN DIAG_DSP_03: lcd_panel_defective   [CF=0.80] [PRIORITY=3]
NOTE: Màn hình trắng thường = lỗi signal processing trong panel

R024: Độ sáng bị tắt → Không phải lỗi hardware
IF   brightness_too_low
AND  NOT screen_lines
AND  NOT screen_flickering
THEN DIAG_DSP_05: brightness_setting_issue   [CF=0.85] [PRIORITY=3]

R025: Nhìn nghiêng thấy hình → Backlight hỏng
IF   brightness_too_low
AND  backlight_fail
THEN DIAG_DSP_03: lcd_panel_defective   [CF=0.80] [PRIORITY=3]
NOTE: Thấy hình mờ khi nhìn nghiêng = backlight/inverter hỏng, matrix OK

R026: Màn hình bị va đập + sọc/màu sai → Vỡ panel
IF   screen_lines
AND  physical_impact_suspected
THEN DIAG_DSP_03: lcd_panel_defective   [CF=0.95] [PRIORITY=5]
NOTE: Độ tin cậy rất cao khi có bằng chứng va đập vật lý
```

---

## NHÓM 3: LUẬT HỆ ĐIỀU HÀNH / BOOT (R029–R048)

```
R029: BSOD + Mã lỗi Memory → Lỗi RAM
IF   bsod_appears
AND  bsod_memory_error
THEN ram_related_bsod   [CF=0.85] [PRIORITY=3]

R030: RAM lỗi → Chẩn đoán cuối
IF   ram_related_bsod
AND  NOT recent_driver_update
THEN DIAG_OS_03: faulty_ram   [CF=0.85] [PRIORITY=3]

R031: RAM lỗi do update → Kiểm tra driver trước
IF   ram_related_bsod
AND  recent_driver_update
THEN driver_related_bsod   [CF=0.75] [PRIORITY=2]
NOTE: Một số driver kém sử dụng bộ nhớ sai cách, gây BSOD memory-type

R032: BSOD + Mã lỗi Driver → Lỗi driver
IF   bsod_appears
AND  bsod_driver_error
THEN driver_related_bsod   [CF=0.90] [PRIORITY=4]

R033: Driver BSOD + Thay đổi gần đây → Cài đặt gây lỗi
IF   driver_related_bsod
AND  recent_change_caused_issue
THEN DIAG_OS_02: bad_driver_installed   [CF=0.90] [PRIORITY=4]

R034: Driver BSOD + Không có thay đổi → File hệ thống hỏng
IF   driver_related_bsod
AND  NOT recent_change_caused_issue
THEN DIAG_OS_01: windows_system_file_corrupt   [CF=0.75] [PRIORITY=2]

R035: BSOD + Mã lỗi Disk → Lỗi ổ đĩa
IF   bsod_appears
AND  bsod_disk_error
THEN disk_related_bsod   [CF=0.90] [PRIORITY=4]

R036: Disk BSOD → HDD/SSD lỗi
IF   disk_related_bsod
THEN DIAG_OS_04: hdd_ssd_causing_bsod   [CF=0.85] [PRIORITY=3]

R037: Boot loop sau Windows Update → Update gây lỗi
IF   boot_loop
AND  recent_windows_update
THEN DIAG_OS_05: windows_update_boot_loop   [CF=0.90] [PRIORITY=4]

R038: Boot loop không có update → MBR hỏng
IF   boot_loop
AND  NOT recent_windows_update
AND  NOT recent_software_install
THEN DIAG_OS_06: mbr_bootloader_corrupt   [CF=0.80] [PRIORITY=3]

R039: Dừng ở logo + Safe Mode OK → Driver startup lỗi
IF   stuck_at_logo
AND  safe_mode_works
THEN DIAG_OS_02: bad_driver_installed   [CF=0.80] [PRIORITY=3]

R040: Dừng ở logo + Safe Mode fail → OS hỏng nghiêm trọng
IF   stuck_at_logo
AND  safe_mode_fails
THEN DIAG_OS_01: windows_system_file_corrupt   [CF=0.85] [PRIORITY=3]

R041: Windows không load + Không có thay đổi → MBR
IF   windows_not_loading
AND  NOT recent_change_caused_issue
AND  safe_mode_fails
THEN DIAG_OS_06: mbr_bootloader_corrupt   [CF=0.85] [PRIORITY=3]

R042: Hệ điều hành treo + recent change → Software conflict
IF   os_freezes_randomly
AND  recent_change_caused_issue
THEN DIAG_OS_02: bad_driver_installed   [CF=0.75] [PRIORITY=2]

R043: Hệ điều hành treo + không thay đổi → RAM hoặc disk
IF   os_freezes_randomly
AND  NOT recent_change_caused_issue
AND  NOT bsod_appears
THEN probable_hardware_instability   [CF=0.70] [PRIORITY=2]

R044: SFC báo lỗi → File hệ thống hỏng
IF   sfc_errors_found
AND  os_freezes_randomly
THEN DIAG_OS_01: windows_system_file_corrupt   [CF=0.85] [PRIORITY=3]
```

---

## NHÓM 4: LUẬT MẠNG / WI-FI (R049–R065)

```
R049: Không thấy Wi-Fi + Không có adapter → Adapter hỏng
IF   wifi_not_visible
AND  wifi_adapter_missing
THEN DIAG_NET_02: wifi_adapter_hardware_fail   [CF=0.90] [PRIORITY=4]

R050: Không thấy Wi-Fi + Có adapter nhưng lỗi → Driver
IF   wifi_not_visible
AND  NOT wifi_adapter_missing
THEN probable_wifi_driver_issue   [CF=0.85] [PRIORITY=3]

R051: Driver Wi-Fi lỗi → Chẩn đoán
IF   probable_wifi_driver_issue
THEN DIAG_NET_01: wifi_driver_problem   [CF=0.85] [PRIORITY=3]

R052: Có Wi-Fi nhưng không Internet + Thiết bị khác OK → Lỗi ở máy này
IF   wifi_connected_no_internet
AND  other_devices_same_wifi_ok
THEN probable_local_network_config_issue   [CF=0.85] [PRIORITY=3]

R053: Lỗi cấu hình mạng + Lỗi DNS → DNS sai
IF   probable_local_network_config_issue
AND  dns_error_message
THEN DIAG_NET_03: dns_configuration_error   [CF=0.90] [PRIORITY=4]

R054: Lỗi cấu hình mạng + IP conflict → IP trùng
IF   probable_local_network_config_issue
AND  ip_conflict
THEN DIAG_NET_06: ip_address_conflict   [CF=0.90] [PRIORITY=4]

R055: Lỗi cấu hình mạng + Cáp LAN cũng lỗi → Network stack hỏng
IF   probable_local_network_config_issue
AND  ethernet_no_internet
THEN DIAG_NET_05: network_stack_corrupted   [CF=0.85] [PRIORITY=3]

R056: Cả Wi-Fi và LAN đều lỗi + Thiết bị khác cũng lỗi → Router/ISP
IF   wifi_connected_no_internet
AND  ethernet_no_internet
AND  other_devices_same_wifi_fail
THEN DIAG_NET_04: router_or_isp_problem   [CF=0.90] [PRIORITY=4]

R057: Biểu tượng chấm than + thiết bị khác OK → Cấu hình máy lỗi
IF   wifi_connected_yellow_exclamation
AND  other_devices_same_wifi_ok
THEN probable_local_network_config_issue   [CF=0.80] [PRIORITY=3]

R058: Chỉ một số website không vào được → DNS hoặc VPN
IF   specific_sites_blocked
AND  NOT vpn_related
THEN DIAG_NET_03: dns_configuration_error   [CF=0.75] [PRIORITY=2]

R059: VPN đang bật + mạng lỗi → VPN gây lỗi
IF   vpn_related
AND  wifi_connected_no_internet
THEN DIAGNOTE: disable_vpn_first   [CF=0.90] [PRIORITY=4]
NOTE: Đây là troubleshooting step, không phải final diagnosis

R060: Wi-Fi chậm + thiết bị khác bình thường → Driver/adapter máy
IF   wifi_slow
AND  other_devices_same_wifi_ok
THEN DIAG_NET_01: wifi_driver_problem   [CF=0.70] [PRIORITY=2]
```

---

## NHÓM 5: LUẬT ÂM THANH / CAMERA (R066–R078)

```
R066: Không âm thanh + Không thấy device → Hardware soundcard lỗi
IF   no_sound
AND  audio_device_missing
THEN DIAG_AUD_03: audio_hardware_failure   [CF=0.85] [PRIORITY=3]

R067: Không âm thanh + Driver có lỗi → Driver lỗi
IF   no_sound
AND  audio_driver_yellow_mark
THEN DIAG_AUD_01: audio_driver_problem   [CF=0.90] [PRIORITY=4]

R068: Không âm thanh + Volume bị mute → Cài đặt
IF   no_sound
AND  NOT audio_device_missing
AND  NOT audio_driver_yellow_mark
THEN DIAG_AUD_02: audio_muted_or_disabled   [CF=0.85] [PRIORITY=3]
NOTE: Nhiều trường hợp đơn giản là volume 0 hoặc device bị disabled

R069: Âm thanh sau restart rồi mất → Driver không ổn định
IF   audio_works_after_restart
AND  no_sound
THEN DIAG_AUD_01: audio_driver_problem   [CF=0.80] [PRIORITY=3]

R070: Âm thanh bị rè/nhiễu → Hardware hoặc driver lỗi
IF   sound_quality_bad
AND  audio_driver_yellow_mark
THEN DIAG_AUD_01: audio_driver_problem   [CF=0.75] [PRIORITY=2]

R071: Âm thanh bị rè/nhiễu + Driver OK → Hardware
IF   sound_quality_bad
AND  NOT audio_driver_yellow_mark
THEN DIAG_AUD_03: audio_hardware_failure   [CF=0.70] [PRIORITY=2]

R072: Camera bị chặn Privacy → Privacy setting
IF   camera_not_detected
AND  camera_privacy_blocked
THEN DIAG_CAM_01: camera_blocked_by_privacy   [CF=0.95] [PRIORITY=5]
NOTE: Windows 10/11 có privacy toggle riêng cho camera — rất hay bị tắt nhầm

R073: Camera lỗi + không phải privacy → Driver
IF   camera_not_detected
AND  NOT camera_privacy_blocked
THEN DIAG_CAM_02: camera_driver_problem   [CF=0.85] [PRIORITY=3]

R074: Camera chỉ lỗi ở một vài app → App permission
IF   camera_works_some_apps
AND  NOT camera_privacy_blocked
THEN DIAGNOTE: check_app_camera_permission   [CF=0.85] [PRIORITY=3]

R075: Micro bị disabled → Settings lỗi
IF   microphone_not_working
AND  micro_disabled_in_settings
THEN DIAG_AUD_02: audio_muted_or_disabled   [CF=0.90] [PRIORITY=4]

R076: Micro lỗi + Driver có vấn đề → Driver
IF   microphone_not_working
AND  audio_driver_yellow_mark
THEN DIAG_AUD_01: audio_driver_problem   [CF=0.85] [PRIORITY=3]
```

---

## NHÓM 6: LUẬT THIẾT BỊ NGOẠI VI / USB (R079–R090)

```
R079: USB không được nhận + Chỉ 1 cổng + Thiết bị OK máy khác → Cổng USB hỏng
IF   usb_not_detected
AND  specific_usb_port_fail
AND  usb_device_works_on_other_pc
THEN DIAG_PER_01: usb_port_physically_damaged   [CF=0.90] [PRIORITY=4]

R080: USB không được nhận + Tất cả cổng → USB Controller lỗi
IF   usb_not_detected
AND  all_usb_ports_fail
THEN DIAG_PER_02: usb_controller_driver_failed   [CF=0.85] [PRIORITY=3]

R081: USB không nhận + Thiết bị lỗi ở mọi nơi → Thiết bị hỏng
IF   usb_not_detected
AND  usb_device_fails_all_ports
THEN DIAG_PER_03: usb_device_itself_faulty   [CF=0.90] [PRIORITY=4]

R082: USB nhận được nhưng lỗi → Driver
IF   usb_device_error
AND  usb_device_works_on_other_pc
THEN DIAG_PER_04: peripheral_driver_missing   [CF=0.85] [PRIORITY=3]

R083: Chuột/Bàn phím không hoạt động + Driver lỗi → Driver
IF   mouse_not_working OR keyboard_not_working
AND  usb_device_error
THEN DIAG_PER_04: peripheral_driver_missing   [CF=0.80] [PRIORITY=3]

R084: Chuột/Bàn phím không hoạt động + Không nhận device → Cổng hoặc thiết bị hỏng
IF   mouse_not_working OR keyboard_not_working
AND  NOT usb_device_error
AND  specific_usb_port_fail
THEN DIAG_PER_01: usb_port_physically_damaged   [CF=0.80] [PRIORITY=3]

R085: Bluetooth không kết nối được + Driver lỗi → Driver Bluetooth
IF   bluetooth_not_working
AND  audio_driver_yellow_mark
THEN DIAG_PER_04: peripheral_driver_missing   [CF=0.80] [PRIORITY=3]

R086: Touchpad không hoạt động → Phím tắt hoặc driver
IF   touchpad_not_working
THEN DIAGNOTE: check_touchpad_hotkey_or_driver   [CF=0.75] [PRIORITY=2]
NOTE: Fn+F6 hoặc Fn+F7 (tuỳ hãng) thường tắt touchpad nhầm
```

---

## NHÓM 7: LUẬT HIỆU NĂNG / NHIỆT ĐỘ (R091–R105)

```
R091: Quạt ồn + Nóng + CPU cao → Thermal throttling
IF   fan_very_loud
AND  laptop_very_hot
AND  high_cpu_usage
THEN thermal_throttling   [CF=0.90] [PRIORITY=4]

R092: Thermal throttling → Chẩn đoán quá nhiệt
IF   thermal_throttling
THEN DIAG_PERF_01: thermal_throttling_overheating   [CF=0.90] [PRIORITY=4]

R093: Nhiệt độ cao + Máy cũ + Chưa vệ sinh → Bụi + keo cũ
IF   thermal_throttling
AND  thermal_paste_old
AND  dust_in_vents
THEN DIAG_PERF_01: thermal_throttling_overheating   [CF=0.95] [PRIORITY=5]
NOTE: Máy cũ + bụi + keo tản nhiệt cứng là nguyên nhân #1 quá nhiệt

R094: CPU cao + Process lạ + Nghi malware → Malware
IF   high_cpu_usage
AND  malware_suspected
THEN malware_causing_slow   [CF=0.85] [PRIORITY=3]

R095: Malware xác nhận → Chẩn đoán
IF   malware_causing_slow
THEN DIAG_PERF_02: malware_virus_infection   [CF=0.85] [PRIORITY=3]

R096: Chậm từ khi bật + Nhiều startup → Startup bloat
IF   slow_boot_time
AND  startup_programs_many
THEN DIAG_PERF_03: too_many_startup_programs   [CF=0.90] [PRIORITY=4]

R097: RAM gần đầy + Chậm khi nhiều app → RAM không đủ
IF   high_memory_usage
AND  system_very_slow
AND  NOT thermal_throttling
THEN DIAG_PERF_04: insufficient_ram   [CF=0.85] [PRIORITY=3]

R098: Disk 100% + Chậm → Ổ đĩa bottleneck
IF   high_disk_usage
AND  system_very_slow
THEN storage_causing_slow   [CF=0.85] [PRIORITY=3]

R099: Disk bottleneck + Disk đầy → Đầy ổ đĩa
IF   storage_causing_slow
AND  disk_full
THEN DIAG_STR_01: disk_space_exhaustion   [CF=0.90] [PRIORITY=4]

R100: Disk bottleneck + Click sound → HDD hỏng
IF   storage_causing_slow
AND  disk_error_sound
THEN DIAG_STR_02: hdd_failing   [CF=0.90] [PRIORITY=4]

R101: Chậm chỉ ở 1 app + Không có triệu chứng khác → App-specific
IF   slow_only_specific_apps
AND  NOT high_cpu_usage
AND  NOT thermal_throttling
THEN DIAGNOTE: app_specific_performance_issue   [CF=0.75] [PRIORITY=2]
```

---

## NHÓM 8: LUẬT LƯU TRỮ / Ổ ĐĨA (R106–R115)

```
R106: Ổ đĩa đầy + Hệ thống chậm → Dọn dung lượng
IF   disk_full
AND  system_very_slow
THEN DIAG_STR_01: disk_space_exhaustion   [CF=0.90] [PRIORITY=4]

R107: Click sound + Chậm copy file → HDD sắp hỏng
IF   disk_error_sound
AND  slow_file_transfer
THEN hdd_failing   [CF=0.90] [PRIORITY=4]

R108: HDD failing → Chẩn đoán
IF   hdd_failing
THEN DIAG_STR_02: hdd_mechanical_failure   [CF=0.90] [PRIORITY=4]

R109: File bị lỗi + CHKDSK lỗi → File system hỏng
IF   file_corruption
AND  chkdsk_errors
THEN DIAG_STR_04: file_system_corruption   [CF=0.90] [PRIORITY=4]

R110: Bad sectors + File lỗi → HDD hỏng + File system
IF   bad_sectors_detected
AND  file_corruption
THEN DIAG_STR_02: hdd_mechanical_failure   [CF=0.85] [PRIORITY=3]

R111: SSD health thấp + Chậm → SSD degraded
IF   ssd_health_low
AND  slow_file_transfer
THEN DIAG_STR_03: ssd_performance_degraded   [CF=0.85] [PRIORITY=3]

R112: Ổ đĩa thứ 2 không hiển thị → Connection hoặc file system
IF   disk_not_detected
AND  NOT bsod_disk_error
THEN DIAG_STR_04: file_system_corruption   [CF=0.70] [PRIORITY=2]

R113: BSOD disk + Click sound → Ổ đĩa gây BSOD
IF   bsod_disk_error
AND  disk_error_sound
THEN DIAG_OS_04: hdd_ssd_causing_bsod   [CF=0.95] [PRIORITY=5]

R114: File system lỗi + Boot lỗi → MBR/Boot sector
IF   file_corruption
AND  windows_not_loading
AND  NOT recent_change_caused_issue
THEN DIAG_OS_06: mbr_bootloader_corrupt   [CF=0.80] [PRIORITY=3]

R115: Disk 100% + SSD health OK + Disk không đầy → Process chiếm disk
IF   high_disk_usage
AND  NOT disk_full
AND  NOT ssd_health_low
THEN DIAGNOTE: check_disk_intensive_process   [CF=0.80] [PRIORITY=3]
NOTE: Windows Search, antivirus scan, Windows Update thường chiếm disk 100%
```

---

## BẢNG TỔNG QUAN QUY TẮC XỬ LÝ XUNG ĐỘT

| Tình huống | Rule liên quan | Cách giải quyết |
|-----------|---------------|----------------|
| RAM BSOD + Driver update gần đây | R030 vs R031 | Ưu tiên R031 (recent_driver_update cao hơn) |
| Display đen: Cáp vs Panel vs GPU | R017 vs R018 vs R019 | Kiểm tra external_monitor trước (R016) |
| Không Internet: DNS vs Router vs Stack | R053 vs R056 vs R055 | Dùng ethernet_check (R055) để phân biệt |
| Không âm thanh: Hardware vs Driver vs Muted | R066 vs R067 vs R068 | Theo thứ tự: muted → driver → hardware |
| Thermal: Bụi vs Paste vs Fan hỏng | R092 vs R093 | Kết hợp (thermal_paste_old AND dust strengthen CF) |

---

## LUẬT ĐẶC BIỆT — META RULES

```
META_R01: Ưu tiên Specificity
IF   rule_A covers facts {F1, F2, F3}
AND  rule_B covers facts {F1, F2}
AND  both lead to same category
THEN fire rule_A first (more specific)

META_R02: Recent Change Override
IF   recent_change_caused_issue IS TRUE
THEN increase CF of all driver/software rules by 0.10

META_R03: Physical Damage Override
IF   physical_impact_suspected IS TRUE
THEN increase CF of hardware rules by 0.15
AND  decrease CF of software rules by 0.15

META_R04: Laptep vs Desktop differentiation
IF   is_laptop IS FALSE
THEN disable all rules containing: battery, adapter_laptop, thermal_paste_laptop
AND  enable: psu_rules, desktop_power_rules
```
