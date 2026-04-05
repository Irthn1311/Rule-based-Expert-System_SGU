"""
Fact Extractor — Trích xuất facts từ text người dùng.

Chiến lược:
  - Áp dụng KEYWORD_FACT_MAP (pattern matching, ordered)
  - Hỗ trợ nhiều facts trong một câu
  - Nếu trích được facts → chắc chắn
  - Nếu chỉ có intent → uncertain → cần hỏi thêm

⚠️ Fact extractor KHÔNG tự kết luận diagnosis.
"""

from __future__ import annotations
import re
from typing import Optional

from .patterns import KEYWORD_FACT_MAP, FACTS_UNDERSTOOD_PREFIX


def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s\u00C0-\u024F\u1E00-\u1EFF]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


class FactExtractor:
    """
    Trích xuất facts từ text người dùng.
    Dùng pattern matching trên KEYWORD_FACT_MAP.
    """

    def __init__(self):
        self._patterns = KEYWORD_FACT_MAP

    def extract(self, text: str) -> dict:
        """
        Trích xuất facts từ text.

        Returns:
        {
            "facts": list[str],         # facts được extract
            "matched_patterns": list,   # patterns đã match (debug)
            "has_facts": bool,          # True nếu extract được ít nhất 1 fact
            "understood_message": str,  # bot confirmation message
        }
        """
        normalized = _normalize(text)
        extracted_facts: list[str] = []
        matched_patterns: list[str] = []

        for pattern, facts in self._patterns:
            if pattern in normalized:
                for fact in facts:
                    if fact not in extracted_facts:
                        extracted_facts.append(fact)
                matched_patterns.append(pattern)

        # Build confirmation message
        understood_message = ""
        if extracted_facts:
            fact_display = self._facts_to_display(extracted_facts)
            understood_message = f"{FACTS_UNDERSTOOD_PREFIX}{fact_display}"

        return {
            "facts": extracted_facts,
            "matched_patterns": matched_patterns,
            "has_facts": len(extracted_facts) > 0,
            "understood_message": understood_message,
        }

    def _facts_to_display(self, facts: list[str]) -> str:
        """Chuyển fact IDs thành text đẹp hơn để hiển thị."""
        # Map fact ID → display text
        display_map = {
            "no_power": "máy không có điện",
            "no_charge": "không sạc được",
            "battery_indicator_red": "đèn pin đỏ/không sáng",
            "laptop_only_on_adapter": "chỉ chạy khi cắm điện",
            "screen_black": "màn hình đen",
            "screen_flickering": "màn hình nhấp nháy",
            "screen_lines": "có sọc trên màn hình",
            "screen_color_distorted": "màu sắc bị sai",
            "screen_white": "màn hình trắng",
            "bsod_appears": "màn hình xanh (BSOD)",
            "bsod_memory_error": "lỗi bộ nhớ RAM",
            "bsod_driver_error": "lỗi driver",
            "bsod_disk_error": "lỗi ổ đĩa",
            "boot_loop": "khởi động lại liên tục",
            "stuck_at_logo": "dừng ở màn hình logo",
            "wifi_not_visible": "không thấy WiFi",
            "wifi_connected_no_internet": "WiFi kết nối nhưng không có Internet",
            "no_sound": "không có âm thanh",
            "microphone_not_working": "microphone lỗi",
            "camera_not_detected": "camera không nhận",
            "usb_not_detected": "USB không nhận",
            "bluetooth_not_working": "Bluetooth lỗi",
            "touchpad_not_working": "touchpad lỗi",
            "system_very_slow": "máy chạy chậm",
            "laptop_very_hot": "máy quá nóng",
            "disk_full": "ổ đĩa đầy",
            "disk_error_sound": "tiếng kêu từ ổ cứng",
            "malware_suspected": "nghi có virus/malware",
            "is_laptop": "laptop",
            "is_desktop": "máy bàn (desktop)",
            "multiple_beeps": "nghe nhiều tiếng beep",
            "machine_shuts_down_abruptly": "máy tự tắt đột ngột",
            "physical_impact_suspected": "máy bị va đập/rơi",
            "recent_windows_update": "vừa cập nhật Windows",
            "recent_software_install": "vừa cài phần mềm mới",
        }
        parts = [display_map.get(f, f) for f in facts[:3]]  # max 3 để không dài quá
        if len(facts) > 3:
            parts.append(f"và {len(facts) - 3} thông tin khác")
        return ", ".join(parts)

    def extract_and_classify(self, text: str, intent_result: dict) -> dict:
        """
        Kết hợp fact extraction + intent classification.

        Returns:
        {
            "facts": list[str],
            "intent": str | None,
            "is_certain": bool,       # True nếu có facts cụ thể
            "uncertain": bool,        # True nếu cần hỏi thêm
            "understood_message": str,
            "skip_to_group": str | None,  # QID để skip thẳng vào nhóm
        }
        """
        fact_result = self.extract(text)
        intent = intent_result.get("intent")
        intent_certain = intent_result.get("is_certain", False)

        has_facts = fact_result["has_facts"]
        skip_to_group = None

        # Nếu có facts cụ thể → chắc chắn
        is_certain = has_facts

        # Nếu intent rõ ràng + chưa có facts → skip đến nhóm đó
        if intent_certain and not has_facts and intent:
            from .intent_classifier import IntentClassifier
            skip_to_group = IntentClassifier().get_group_question_start(intent)

        return {
            "facts": fact_result["facts"],
            "intent": intent,
            "is_certain": is_certain,
            "uncertain": not is_certain and not intent_certain,
            "understood_message": fact_result["understood_message"],
            "skip_to_group": skip_to_group,
            "debug": {
                "matched_patterns": fact_result["matched_patterns"],
                "intent_scores": intent_result.get("scores", {}),
            }
        }
