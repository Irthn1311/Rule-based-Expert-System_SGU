# PHẦN 4: HỆ FACTS CHUẨN HÓA

---

## 4.1 Input Facts (Triệu chứng đầu vào từ người dùng)

### Nhóm A — Nguồn / Khởi động (power_startup)

| Fact ID | Tên fact | Mô tả | Nguồn |
|---------|----------|-------|-------|
| F001 | no_power | Máy không có dấu hiệu điện nào | Q02 |
| F002 | power_led_on | Đèn nguồn sáng | Q02 |
| F003 | fan_not_spinning | Quạt không quay | Q03 |
| F004 | fan_spinning | Quạt quay | Q03 |
| F005 | beep_sound | Có tiếng beep khi bật | Q04 |
| F006 | no_beep | Không có tiếng beep | Q04 |
| F007 | single_beep | Một tiếng beep ngắn (POST OK) | Q04 |
| F008 | multiple_beeps | Nhiều tiếng beep (POST ERROR) | Q04 |
| F009 | battery_indicator_red | Đèn pin màu đỏ hoặc nhấp nháy | Q05 |
| F010 | no_charge | Pin không sạc được | Q05 |
| F011 | laptop_only_on_adapter | Chỉ bật được khi cắm điện | Q06 |
| F012 | no_display_after_power | Màn hình không hiển thị sau khi bật | Q02 |

### Nhóm B — Màn hình / Hiển thị (display)

| Fact ID | Tên fact | Mô tả | Nguồn |
|---------|----------|-------|-------|
| F020 | screen_black | Màn hình đen hoàn toàn | Q09 |
| F021 | screen_flickering | Màn hình nhấp nháy/giật | Q09 |
| F022 | screen_lines | Có sọc ngang/dọc trên màn hình | Q09 |
| F023 | screen_color_distorted | Màu sắc bị méo/lạ | Q09 |
| F024 | screen_white | Màn hình trắng toàn bộ | Q09 |
| F025 | external_monitor_ok | Màn hình ngoài hiển thị OK | Q10 |
| F026 | external_monitor_same_issue | Màn hình ngoài cũng bị lỗi | Q10 |
| F027 | brightness_too_low | Độ sáng rất thấp | Q11 |
| F028 | resolution_wrong | Độ phân giải sai | Q11 |
| F029 | display_after_driver_install | Lỗi sau khi cài driver | Q12 |

### Nhóm C — Hệ điều hành / Boot (os_boot)

| Fact ID | Tên fact | Mô tả | Nguồn |
|---------|----------|-------|-------|
| F040 | bsod_appears | Màn hình xanh chết chóc (BSOD) | Q14 |
| F041 | bsod_memory_error | BSOD liên quan memory | Q15 |
| F042 | bsod_driver_error | BSOD liên quan driver | Q15 |
| F043 | bsod_disk_error | BSOD liên quan disk/storage | Q15 |
| F044 | boot_loop | Máy khởi động lại liên tục | Q13 |
| F045 | stuck_at_logo | Dừng ở màn hình logo | Q13 |
| F046 | windows_not_loading | Windows không load được | Q13 |
| F047 | safe_mode_works | Chế độ Safe Mode hoạt động | Q16 |
| F048 | safe_mode_fails | Safe Mode cũng không vào được | Q16 |
| F049 | recent_software_install | Vừa cài phần mềm mới | Q17 |
| F050 | recent_windows_update | Vừa cập nhật Windows | Q17 |
| F051 | recent_driver_update | Vừa cập nhật driver | Q17 |
| F052 | system_restore_available | Có System Restore point | Q18 |
| F053 | os_freezes_randomly | Hệ điều hành treo ngẫu nhiên | Q13 |

### Nhóm D — Mạng / Wi-Fi / Internet (network)

| Fact ID | Tên fact | Mô tả | Nguồn |
|---------|----------|-------|-------|
| F060 | wifi_not_visible | Không thấy Wi-Fi trong danh sách | Q20 |
| F061 | wifi_connected_no_internet | Kết nối Wi-Fi nhưng không có Internet | Q20 |
| F062 | wifi_slow | Wi-Fi chậm bất thường | Q20 |
| F063 | ethernet_works | Cáp mạng hoạt động bình thường | Q21 |
| F064 | ethernet_no_internet | Cáp mạng cũng không có Internet | Q21 |
| F065 | other_devices_same_wifi_ok | Thiết bị khác dùng cùng Wi-Fi OK | Q22 |
| F066 | other_devices_same_wifi_fail | Các thiết bị khác cũng không vào mạng | Q22 |
| F067 | dns_error_message | Trình duyệt báo lỗi DNS | Q23 |
| F068 | specific_sites_blocked | Chỉ một số website không vào được | Q23 |
| F069 | vpn_related | Máy đang dùng VPN | Q24 |
| F070 | wifi_adapter_missing | Wi-Fi adapter không hiển thị trong Device Manager | Q25 |
| F071 | ip_conflict | Báo lỗi IP conflict | Q25 |
| F072 | wifi_connected_yellow_exclamation | Biểu tượng Wi-Fi có dấu chấm than vàng | Q20 |

### Nhóm E — Âm thanh / Micro / Camera (audio_camera)

| Fact ID | Tên fact | Mô tả | Nguồn |
|---------|----------|-------|-------|
| F080 | no_sound | Không có âm thanh | Q27 |
| F081 | sound_quality_bad | Âm thanh bị rè/nhiễu | Q27 |
| F082 | microphone_not_working | Microphone không ghi âm được | Q27 |
| F083 | camera_not_detected | Camera không được nhận | Q27 |
| F084 | audio_device_missing | Thiết bị âm thanh không hiển thị | Q28 |
| F085 | audio_works_headphone_not | Loa OK nhưng tai nghe không | Q28 |
| F086 | audio_works_after_restart | Âm thanh có sau khi restart | Q29 |
| F087 | audio_driver_yellow_mark | Driver âm thanh có dấu chấm than | Q29 |
| F088 | camera_privacy_blocked | Camera bị chặn bởi privacy setting | Q30 |
| F089 | camera_works_some_apps | Camera chỉ hoạt động ở một số ứng dụng | Q30 |

### Nhóm F — Thiết bị ngoại vi / USB (peripherals)

| Fact ID | Tên fact | Mô tả | Nguồn |
|---------|----------|-------|-------|
| F090 | usb_not_detected | USB cắm vào không được nhận | Q32 |
| F091 | usb_device_error | USB recognized nhưng báo lỗi | Q32 |
| F092 | mouse_not_working | Chuột không hoạt động | Q32 |
| F093 | keyboard_not_working | Bàn phím không hoạt động | Q32 |
| F094 | specific_usb_port_fail | Chỉ một cổng USB bị lỗi | Q33 |
| F095 | all_usb_ports_fail | Tất cả cổng USB bị lỗi | Q33 |
| F096 | usb_device_works_on_other_pc | USB hoạt động trên máy khác | Q34 |
| F097 | usb_device_fails_all_ports | Thiết bị USB lỗi ở mọi cổng máy này | Q34 |
| F098 | bluetooth_not_working | Bluetooth không kết nối được | Q35 |
| F099 | printer_not_detected | Máy in không được nhận | Q35 |
| F100 | touchpad_not_working | Touchpad không hoạt động | Q35 |

### Nhóm G — Hiệu năng / Nhiệt độ (performance)

| Fact ID | Tên fact | Mô tả | Nguồn |
|---------|----------|-------|-------|
| F110 | system_very_slow | Máy chạy rất chậm | Q37 |
| F111 | fan_very_loud | Quạt kêu to liên tục | Q37 |
| F112 | laptop_very_hot | Máy rất nóng | Q37 |
| F113 | high_cpu_usage | CPU usage cao bất thường (>90%) | Q38 |
| F114 | high_memory_usage | RAM usage cao (>85%) | Q38 |
| F115 | high_disk_usage | Disk usage cao bất thường | Q38 |
| F116 | slow_boot_time | Thời gian khởi động rất lâu | Q37 |
| F117 | slow_only_specific_apps | Chậm chỉ ở một số ứng dụng | Q37 |
| F118 | malware_suspected | Nghi ngờ có virus/malware | Q39 |
| F119 | startup_programs_many | Nhiều chương trình khởi động cùng Windows | Q39 |
| F120 | thermal_paste_old | Máy dùng lâu, chưa thay keo tản nhiệt | Q40 |
| F121 | dust_in_vents | Lỗ thông gió bị bụi | Q40 |

### Nhóm H — Lưu trữ / Ổ đĩa (storage)

| Fact ID | Tên fact | Mô tả | Nguồn |
|---------|----------|-------|-------|
| F130 | disk_full | Ổ đĩa C: gần đầy (>90%) | Q36 |
| F131 | disk_error_sound | Ổ HDD phát ra tiếng click/cào | Q36 |
| F132 | file_corruption | File bị lỗi/không mở được | Q36 |
| F133 | chkdsk_errors | CHKDSK báo lỗi | Q36 |
| F134 | slow_file_transfer | Copy file rất chậm | Q37 |
| F135 | disk_not_detected | Ổ đĩa không hiển thị trong Windows | Q36 |
| F136 | bad_sectors_detected | Phần mềm phát hiện Bad Sectors | Q36 |
| F137 | ssd_health_low | SSD health < 80% | Q36 |

---

## 4.2 Intermediate Facts (Kết luận trung gian)

| Fact ID | Tên fact | Điều kiện sinh ra | Ý nghĩa |
|---------|----------|------------------|---------|
| IF001 | probable_power_hardware | F001 AND F003 | Có thể lỗi phần cứng nguồn |
| IF002 | probable_battery_issue | F009 OR F010 OR F011 | Có thể lỗi pin/adapter |
| IF003 | probable_adapter_issue | F001 AND F003 AND NOT F009 | Có thể adapter hỏng |
| IF004 | bios_post_fail | F008 AND NOT F040 | POST thất bại (BIOS error) |
| IF005 | system_boots_no_display | F004 AND F020 AND NOT F040 | Máy boot nhưng không có màn hình |
| IF006 | display_hardware_issue | IF005 AND NOT F025 | Lỗi phần cứng màn hình |
| IF007 | display_driver_issue | F021 OR F028 OR F029 | Có thể lỗi driver màn hình |
| IF008 | probable_gpu_issue | F022 OR F023 OR F024 | GPU có thể bị lỗi |
| IF009 | os_corruption | F044 OR F045 OR F046 | OS có thể bị hỏng |
| IF010 | recent_change_caused_issue | F049 OR F050 OR F051 | Thay đổi gần đây gây lỗi |
| IF011 | driver_related_bsod | F040 AND F042 AND IF010 | BSOD do driver |
| IF012 | ram_related_bsod | F040 AND F041 | BSOD do RAM |
| IF013 | disk_related_bsod | F040 AND F043 | BSOD do disk |
| IF014 | wifi_adapter_issue | F060 AND F070 | Lỗi adapter Wi-Fi |
| IF015 | wifi_driver_issue | F060 AND NOT F070 | Lỗi driver Wi-Fi |
| IF016 | network_config_issue | F061 AND F063 AND F065 | Cấu hình mạng máy bị lỗi |
| IF017 | dns_issue | F061 AND F067 AND F065 | DNS bị lỗi |
| IF018 | router_isp_issue | F061 AND F066 | Lỗi router hoặc ISP |
| IF019 | network_stack_corrupt | F061 AND F064 | Network stack bị hỏng |
| IF020 | audio_hardware_missing | F080 AND F084 | Thiết bị âm thanh không nhận được |
| IF021 | audio_driver_problem | F080 AND F087 | Driver âm thanh có vấn đề |
| IF022 | audio_settings_muted | F080 AND NOT F084 AND NOT F087 | Có thể bị tắt tiếng |
| IF023 | camera_software_issue | F083 AND F088 OR F089 | Lỗi phần mềm camera |
| IF024 | usb_port_hardware_fail | F090 AND F094 AND F096 | Cổng USB cụ thể bị hỏng |
| IF025 | usb_controller_fail | F090 AND F095 | USB controller bị lỗi |
| IF026 | usb_device_faulty | F090 AND NOT F096 | Thiết bị USB bị hỏng |
| IF027 | thermal_throttling | F111 AND F112 AND F113 | Throttle nhiệt độ |
| IF028 | software_slowdown | F110 AND F113 AND NOT F112 | Chậm do phần mềm |
| IF029 | malware_causing_slow | F118 AND F113 | Malware làm chậm máy |
| IF030 | storage_causing_slow | F115 AND F110 | Ổ đĩa gây chậm |
| IF031 | hdd_failing | F131 AND F132 OR F136 | HDD sắp hỏng |
| IF032 | disk_space_issue | F130 AND F115 | Đầy ổ đĩa gây chậm |

---

## 4.3 Final Diagnosis Facts

| Fact ID | Mã chẩn đoán | Tên lỗi | Nhóm |
|---------|-------------|---------|------|
| DF001 | DIAG_PWR_01 | Adapter nguồn hỏng | power_startup |
| DF002 | DIAG_PWR_02 | Pin laptop chai/hỏng | power_startup |
| DF003 | DIAG_PWR_03 | Nguồn máy bàn hỏng (PSU) | power_startup |
| DF004 | DIAG_PWR_04 | Bo mạch chủ lỗi điện | power_startup |
| DF005 | DIAG_PWR_05 | RAM lỏng/hỏng (POST fail) | power_startup |
| DF006 | DIAG_DSP_01 | Cáp LVDS/màn hình lỏng | display |
| DF007 | DIAG_DSP_02 | Driver card đồ họa lỗi | display |
| DF008 | DIAG_DSP_03 | Màn hình LCD hỏng | display |
| DF009 | DIAG_DSP_04 | Card đồ họa hỏng | display |
| DF010 | DIAG_DSP_05 | Độ sáng/brightness bị tắt | display |
| DF011 | DIAG_OS_01 | Windows bị hỏng file hệ thống | os_boot |
| DF012 | DIAG_OS_02 | Driver gây BSOD | os_boot |
| DF013 | DIAG_OS_03 | RAM lỗi gây BSOD | os_boot |
| DF014 | DIAG_OS_04 | HDD/SSD gây BSOD | os_boot |
| DF015 | DIAG_OS_05 | Boot loop do update Windows | os_boot |
| DF016 | DIAG_OS_06 | MBR/Boot sector hỏng | os_boot |
| DF017 | DIAG_NET_01 | Driver Wi-Fi bị lỗi | network |
| DF018 | DIAG_NET_02 | Wi-Fi adapter hỏng | network |
| DF019 | DIAG_NET_03 | Lỗi DNS | network |
| DF020 | DIAG_NET_04 | Router hoặc ISP lỗi | network |
| DF021 | DIAG_NET_05 | Network stack (TCP/IP) hỏng | network |
| DF022 | DIAG_NET_06 | IP conflict | network |
| DF023 | DIAG_AUD_01 | Driver âm thanh lỗi | audio_camera |
| DF024 | DIAG_AUD_02 | Thiết bị âm thanh bị tắt | audio_camera |
| DF025 | DIAG_AUD_03 | Phần cứng loa/soundcard hỏng | audio_camera |
| DF026 | DIAG_CAM_01 | Camera bị chặn bởi Windows Privacy | audio_camera |
| DF027 | DIAG_CAM_02 | Driver camera lỗi | audio_camera |
| DF028 | DIAG_PER_01 | Cổng USB vật lý hỏng | peripherals |
| DF029 | DIAG_PER_02 | USB Controller driver lỗi | peripherals |
| DF030 | DIAG_PER_03 | Thiết bị USB bị hỏng | peripherals |
| DF031 | DIAG_PER_04 | Driver thiết bị ngoại vi lỗi | peripherals |
| DF032 | DIAG_PERF_01 | Thermal throttling — quá nhiệt | performance |
| DF033 | DIAG_PERF_02 | Malware/Virus gây chậm | performance |
| DF034 | DIAG_PERF_03 | Quá nhiều startup programs | performance |
| DF035 | DIAG_PERF_04 | RAM không đủ | performance |
| DF036 | DIAG_STR_01 | Ổ đĩa đầy (C: drive full) | storage |
| DF037 | DIAG_STR_02 | HDD sắp hỏng (failing) | storage |
| DF038 | DIAG_STR_03 | SSD suy giảm hiệu năng | storage |
| DF039 | DIAG_STR_04 | File system bị lỗi (corruption) | storage |
