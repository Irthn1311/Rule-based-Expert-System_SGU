"""
NLU Patterns — Keyword mapping cho Intent Classification và Fact Extraction.

Cấu trúc:
  INTENT_KEYWORDS: {intent_group_id: [keywords]}
  KEYWORD_FACT_MAP: [(pattern, [facts])]  — ordered, first match wins
  FACT_QUESTION_HINTS: {fact: "câu hỏi gợi ý để xác nhận"}
"""

# ──────────────────────────────────────────────────────────────
# 1. INTENT KEYWORDS (nhận diện nhóm lỗi)
# ──────────────────────────────────────────────────────────────

INTENT_KEYWORDS: dict[str, list[str]] = {
    "power_startup": [
        "không bật", "không lên nguồn", "không lên được", "không khởi động",
        "không có điện", "không sạc", "sạc không vào", "pin hỏng", "pin chai",
        "adapter hỏng", "adapter không sạc", "đèn nguồn", "nút nguồn",
        "máy không bật", "bật không lên", "quạt không quay", "tắt đột ngột",
        "tự tắt", "tắt tự động", "shutdown bất ngờ", "restart liên tục",
        "beep", "post fail", "bios", "nguồn", "điện", "cắm điện",
        "chỉ chạy khi cắm", "không chạy pin",
    ],
    "display": [
        "màn hình", "màn đen", "black screen", "screen", "hiển thị",
        "nhấp nháy", "giật", "sọc", "sọc ngang", "sọc dọc",
        "màu sai", "màu lạ", "độ sáng", "quá tối", "quá sáng",
        "màn trắng", "white screen", "backlight", "độ phân giải",
        "resolution", "gpu", "card màn hình", "card đồ họa", "driver màn",
        "cáp màn", "hdmi", "vga", "displayport",
    ],
    "os_boot": [
        "bsod", "màn xanh", "màn hình xanh", "blue screen", "lỗi windows",
        "windows lỗi", "không vào windows", "không boot", "boot loop",
        "khởi động lại liên tục", "restart liên tục", "safe mode",
        "stuck at logo", "dừng ở logo", "treo màn hình logo",
        "windows không load", "không load được windows", "mbr",
        "file hệ thống", "sfc", "chkdsk", "winre", "startup repair",
        "driver lỗi", "xung đột phần mềm", "memory management",
        "page fault", "irql", "os", "hệ điều hành",
    ],
    "network": [
        "wifi", "wi-fi", "mạng", "internet", "không vào mạng", "không có internet",
        "không kết nối", "mất mạng", "mạng chậm", "tín hiệu yếu",
        "dns", "ip", "ip conflict", "vpn", "proxy", "router", "modem",
        "lan", "ethernet", "cáp mạng", "kết nối mạng", "không thấy wifi",
        "wifi chấm than", "không thể duyệt web", "trình duyệt lỗi",
        "err_connection", "err_network", "dns_probe",
    ],
    "audio_camera": [
        "âm thanh", "loa", "không có tiếng", "mất tiếng", "no sound",
        "micro", "microphone", "không nghe", "tiếng rè", "tiếng nhiễu",
        "headphone", "tai nghe", "headset", "audio", "sound",
        "camera", "webcam", "không nhận camera", "camera lỗi",
        "privacy camera", "không thấy camera", "camera không hoạt động",
        "driver âm thanh", "realtek", "audio driver",
    ],
    "peripherals": [
        "usb", "cổng usb", "chuột", "bàn phím", "keyboard", "mouse",
        "không nhận usb", "usb không hoạt động", "thiết bị ngoại vi",
        "bluetooth", "bt", "tai nghe bluetooth", "chuột bluetooth",
        "kết nối bluetooth", "pair", "pairing", "touchpad", "cảm ứng",
        "bàn di", "máy in", "printer", "không nhận thiết bị",
        "device manager", "driver thiết bị",
    ],
    "performance": [
        "chậm", "lag", "giật", "máy chậm", "chạy chậm", "hiệu năng",
        "nóng", "quá nhiệt", "overheat", "quạt ồn", "quạt chạy to",
        "cpu cao", "ram đầy", "disk 100%", "task manager",
        "virus", "malware", "trojan", "spyware", "phần mềm lạ",
        "boot chậm", "khởi động lâu", "startup chậm", "đơ", "freeze",
        "thermal", "tản nhiệt", "keo nhiệt", "bụi",
    ],
    "storage": [
        "ổ đĩa", "ổ cứng", "hdd", "ssd", "nvme", "hard drive",
        "ổ đầy", "không đủ dung lượng", "dung lượng", "disk full",
        "file lỗi", "không mở được file", "file bị hỏng", "corrupt",
        "bad sector", "chkdsk", "crystaldiskinfo", "smart",
        "click lách cách", "tiếng kêu ổ cứng", "ổ không nhận",
        "ổ không hiện", "không thấy ổ", "storage", "data",
    ],
}

# ──────────────────────────────────────────────────────────────
# 2. KEYWORD → FACT MAP
# Ordered: more specific patterns first
# ──────────────────────────────────────────────────────────────

KEYWORD_FACT_MAP: list[tuple[str, list[str]]] = [
    # Power / Startup
    ("không sạc được", ["no_charge"]),
    ("đèn sạc không sáng", ["no_charge", "battery_indicator_red"]),
    ("sạc không vào pin", ["no_charge"]),
    ("pin không tăng", ["no_charge"]),
    ("chỉ chạy khi cắm điện", ["laptop_only_on_adapter"]),
    ("không chạy bằng pin", ["laptop_only_on_adapter"]),
    ("không lên nguồn", ["no_power"]),
    ("không bật được", ["no_power"]),
    ("bật không lên", ["no_power"]),
    ("máy không lên", ["no_power"]),
    ("hoàn toàn không có phản ứng", ["no_power", "fan_not_spinning"]),
    ("đèn nguồn sáng nhưng màn đen", ["power_led_on", "no_display_after_power"]),
    ("tắt đột ngột", ["machine_shuts_down_abruptly"]),
    ("tự tắt", ["machine_shuts_down_abruptly"]),
    ("tắt khi chạy nặng", ["shuts_under_load"]),
    ("tắt ngẫu nhiên", ["shuts_randomly"]),
    ("nhiều tiếng beep", ["multiple_beeps"]),
    ("tiếng beep lạ", ["multiple_beeps"]),
    ("1 tiếng beep", ["single_beep"]),
    ("is laptop", ["is_laptop"]),
    ("laptop", ["is_laptop"]),
    ("desktop", ["is_desktop"]),
    ("máy bàn", ["is_desktop"]),

    # Display
    ("màn hình đen", ["screen_black"]),
    ("màn đen", ["screen_black"]),
    ("black screen", ["screen_black"]),
    ("màn hình nhấp nháy", ["screen_flickering"]),
    ("màn giật", ["screen_flickering"]),
    ("sọc ngang", ["screen_lines"]),
    ("sọc dọc", ["screen_lines"]),
    ("xuất hiện sọc", ["screen_lines"]),
    ("màu sắc bị lạ", ["screen_color_distorted"]),
    ("màu sai", ["screen_color_distorted"]),
    ("màn hình trắng", ["screen_white"]),
    ("độ phân giải sai", ["resolution_wrong"]),
    ("màn ngoài bình thường", ["external_monitor_ok", "system_boots_no_display"]),
    ("màn ngoài cũng đen", ["external_monitor_same_issue"]),
    ("nhìn nghiêng thấy hình", ["backlight_fail", "brightness_too_low"]),
    ("backlight", ["backlight_fail"]),
    ("quá tối", ["brightness_too_low"]),
    ("sau khi cập nhật driver", ["display_after_driver_install"]),
    ("sau khi update driver", ["display_after_driver_install"]),
    ("bị va đập", ["physical_impact_suspected"]),
    ("máy bị rơi", ["physical_impact_suspected"]),

    # OS / Boot
    ("bsod", ["bsod_appears"]),
    ("màn hình xanh", ["bsod_appears"]),
    ("blue screen", ["bsod_appears"]),
    ("memory management", ["bsod_appears", "bsod_memory_error"]),
    ("page fault", ["bsod_appears", "bsod_memory_error"]),
    ("irql not less", ["bsod_appears", "bsod_memory_error"]),
    ("driver irql", ["bsod_appears", "bsod_driver_error"]),
    ("critical process died", ["bsod_appears", "bsod_disk_error"]),
    ("ntfs file system", ["bsod_appears", "bsod_disk_error"]),
    ("boot loop", ["boot_loop"]),
    ("khởi động lại liên tục", ["boot_loop"]),
    ("dừng ở logo", ["stuck_at_logo"]),
    ("stuck at logo", ["stuck_at_logo"]),
    ("treo màn hình", ["os_freezes_randomly"]),
    ("windows không vào được", ["windows_not_loading"]),
    ("safe mode hoạt động", ["safe_mode_works"]),
    ("safe mode cũng lỗi", ["safe_mode_fails"]),
    ("vừa cài phần mềm", ["recent_software_install", "recent_change_caused_issue"]),
    ("vừa update windows", ["recent_windows_update", "recent_change_caused_issue"]),
    ("vừa cập nhật windows", ["recent_windows_update", "recent_change_caused_issue"]),
    ("sfc báo lỗi", ["sfc_errors_found"]),
    ("memory diagnostic lỗi", ["bsod_memory_error"]),
    ("chkdsk báo lỗi", ["chkdsk_errors", "bad_sectors_detected"]),

    # Network
    ("không thấy wifi nào", ["wifi_not_visible"]),
    ("không thấy bất kỳ wifi", ["wifi_not_visible"]),
    ("kết nối wifi nhưng không vào được", ["wifi_connected_no_internet"]),
    ("wifi có nhưng không có internet", ["wifi_connected_no_internet"]),
    ("wifi chấm than", ["wifi_connected_yellow_exclamation"]),
    ("mạng chậm", ["wifi_slow"]),
    ("dns_probe", ["dns_error_message"]),
    ("lỗi dns", ["dns_error_message"]),
    ("err_network_changed", ["ip_conflict"]),
    ("xung đột ip", ["ip_conflict"]),
    ("cáp mạng có internet", ["ethernet_works"]),
    ("lan có internet", ["ethernet_works"]),
    ("cáp mạng cũng không có", ["ethernet_no_internet"]),
    ("thiết bị khác bình thường", ["other_devices_same_wifi_ok"]),
    ("tất cả thiết bị không vào được", ["other_devices_same_wifi_fail"]),
    ("không thấy wifi adapter", ["wifi_adapter_missing"]),
    ("vpn", ["vpn_related"]),
    ("proxy", ["vpn_related"]),

    # Audio / Camera
    ("không có tiếng", ["no_sound"]),
    ("mất tiếng", ["no_sound"]),
    ("loa không có tiếng", ["no_sound"]),
    ("micro không hoạt động", ["microphone_not_working"]),
    ("microphone lỗi", ["microphone_not_working"]),
    ("camera không được nhận", ["camera_not_detected"]),
    ("camera lỗi", ["camera_not_detected"]),
    ("không thấy thiết bị âm thanh", ["audio_device_missing"]),
    ("driver âm thanh chấm than", ["audio_driver_yellow_mark"]),
    ("tai nghe không có tiếng", ["audio_works_headphone_not"]),
    ("camera bị chặn privacy", ["camera_privacy_blocked"]),
    ("camera driver lỗi", ["camera_driver_error"]),
    ("micro bị tắt", ["micro_disabled_in_settings"]),

    # Peripherals
    ("usb không nhận", ["usb_not_detected"]),
    ("không nhận usb", ["usb_not_detected"]),
    ("chuột không hoạt động", ["mouse_not_working"]),
    ("bàn phím không hoạt động", ["keyboard_not_working"]),
    ("bluetooth không kết nối", ["bluetooth_not_working"]),
    ("bluetooth lỗi", ["bluetooth_not_working"]),
    ("touchpad không hoạt động", ["touchpad_not_working"]),
    ("máy in không nhận", ["printer_not_detected"]),
    ("tất cả cổng usb lỗi", ["all_usb_ports_fail"]),
    ("một cổng usb lỗi", ["specific_usb_port_fail"]),

    # Performance
    ("máy chậm", ["system_very_slow"]),
    ("chạy chậm", ["system_very_slow"]),
    ("rất chậm", ["system_very_slow"]),
    ("máy nóng", ["laptop_very_hot"]),
    ("quá nhiệt", ["laptop_very_hot"]),
    ("quạt kêu to", ["fan_very_loud"]),
    ("cpu 100%", ["high_cpu_usage"]),
    ("ram gần đầy", ["high_memory_usage"]),
    ("disk 100%", ["high_disk_usage"]),
    ("virus", ["malware_suspected"]),
    ("malware", ["malware_suspected"]),
    ("boot chậm", ["slow_boot_time"]),
    ("khởi động lâu", ["slow_boot_time"]),

    # Storage
    ("ổ đầy", ["disk_full"]),
    ("ổ cứng đầy", ["disk_full"]),
    ("click lách cách", ["disk_error_sound"]),
    ("tiếng kêu ổ cứng", ["disk_error_sound"]),
    ("file bị hỏng", ["file_corruption"]),
    ("không mở được file", ["file_corruption"]),
    ("bad sector", ["bad_sectors_detected"]),
    ("ssd health thấp", ["ssd_health_low"]),
    ("ổ không hiển thị", ["disk_not_detected"]),
    ("không thấy ổ", ["disk_not_detected"]),
]

# ──────────────────────────────────────────────────────────────
# 3. INTENT CONFIDENCE THRESHOLDS
# ──────────────────────────────────────────────────────────────

INTENT_MIN_CONFIDENCE = 0.3   # Dưới ngưỡng này → uncertain
INTENT_HIGH_CONFIDENCE = 0.6  # Trên ngưỡng này → chắc chắn

# ──────────────────────────────────────────────────────────────
# 4. RESPONSE TEMPLATES (bot messages)
# ──────────────────────────────────────────────────────────────

GREETING_MESSAGE = (
    "Xin chào! Tôi là **PC Expert** — hệ chuyên gia chẩn đoán lỗi máy tính. 🖥️\n\n"
    "Tôi sẽ hỏi một số câu hỏi để xác định chính xác vấn đề của bạn và đưa ra hướng xử lý. "
    "Hãy bắt đầu bằng cách chọn vấn đề bạn đang gặp phải:"
)

UNDERSTOOD_TEMPLATES = {
    "power_startup": "Tôi hiểu máy bạn đang gặp vấn đề về **nguồn điện / khởi động**. Hãy để tôi hỏi thêm để xác định chính xác.",
    "display": "Tôi hiểu máy bạn đang gặp vấn đề về **màn hình / hiển thị**. Hãy để tôi hỏi thêm.",
    "os_boot": "Tôi hiểu máy bạn đang gặp vấn đề về **hệ điều hành Windows**. Hãy để tôi hỏi thêm.",
    "network": "Tôi hiểu máy bạn đang gặp vấn đề về **mạng / Internet**. Hãy để tôi hỏi thêm.",
    "audio_camera": "Tôi hiểu máy bạn đang gặp vấn đề về **âm thanh / camera**. Hãy để tôi hỏi thêm.",
    "peripherals": "Tôi hiểu máy bạn đang gặp vấn đề về **thiết bị ngoại vi**. Hãy để tôi hỏi thêm.",
    "performance": "Tôi hiểu máy bạn đang gặp vấn đề về **hiệu năng / tốc độ**. Hãy để tôi hỏi thêm.",
    "storage": "Tôi hiểu máy bạn đang gặp vấn đề về **ổ đĩa / lưu trữ**. Hãy để tôi hỏi thêm.",
}

UNCERTAIN_MESSAGE = (
    "Tôi chưa xác định rõ vấn đề của bạn từ thông tin đó. "
    "Hãy chọn từ danh sách bên dưới để tôi có thể hỗ trợ chính xác hơn:"
)

FACTS_UNDERSTOOD_PREFIX = "✅ Đã ghi nhận: "
