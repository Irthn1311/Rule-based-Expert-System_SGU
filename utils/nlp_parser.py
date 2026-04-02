"""
NLP Parser — Lightweight Vietnamese keyword-based intent extractor.

Converts free-text user input to structured symptom facts.
Uses keyword + synonym matching with negation handling.
NO machine learning required.

Usage:
    from utils.nlp_parser import parse_input
    facts = parse_input("máy không lên nguồn, đèn không sáng")
    # {'power_response': False, 'led_on': False}
"""

import re
import logging

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# Keyword Map: symptom_code -> (positive_keywords, default_value)
#   positive_keywords: if found, set fact to default_value
#   Negation detection inverts the value automatically.
# ──────────────────────────────────────────────────────────────
KEYWORD_MAP = {
    # === POWER ===
    'power_response': {
        'keywords': [
            'không lên nguồn', 'không khởi động', 'không bật được',
            'nhấn nguồn không', 'bấm nguồn không', 'không phản hồi',
            'máy không lên', 'không chạy', 'máy chết',
        ],
        'value_when_matched': False,
    },
    'led_on': {
        'keywords': [
            'đèn không sáng', 'không có đèn', 'đèn nguồn tắt',
            'đèn led không', 'không đèn',
        ],
        'value_when_matched': False,
    },
    'fan_running': {
        'keywords': [
            'quạt không quay', 'quạt không chạy', 'không thấy quạt',
        ],
        'value_when_matched': False,
    },
    'shutdown_immediately': {
        'keywords': [
            'bật rồi tắt', 'tắt ngay', 'tắt liền', 'tự tắt',
            'bật lên tắt', 'mở lên tắt',
        ],
        'value_when_matched': True,
    },
    'system_hot': {
        'keywords': [
            'nóng', 'quá nhiệt', 'nóng ran', 'nóng bỏng tay',
        ],
        'value_when_matched': True,
    },
    'laptop_device': {
        'keywords': [
            'laptop', 'máy xách tay', 'notebook',
        ],
        'value_when_matched': True,
    },
    'battery_ok': {
        'keywords': [
            'pin hết', 'hết pin', 'pin lỗi', 'pin hỏng',
            'pin không sạc', 'pin chai',
        ],
        'value_when_matched': False,
    },
    'beep_sound': {
        'keywords': [
            'tiếng beep', 'kêu beep', 'bíp', 'tiếng bíp',
            'có tiếng kêu', 'beep',
        ],
        'value_when_matched': True,
    },
    'post_success': {
        'keywords': [
            'không qua post', 'không post', 'không hiện post',
        ],
        'value_when_matched': False,
    },

    # === DISPLAY ===
    'display_on': {
        'keywords': [
            'không hiển thị', 'không lên hình', 'không lên màn',
            'màn hình đen', 'màn đen', 'tối đen', 'không có hình',
        ],
        'value_when_matched': False,
    },
    'signal_detected': {
        'keywords': [
            'không nhận tín hiệu', 'no signal', 'không tín hiệu',
        ],
        'value_when_matched': False,
    },
    'screen_lines': {
        'keywords': [
            'bị sọc', 'sọc ngang', 'sọc dọc', 'sọc màn',
            'vạch ngang', 'vạch dọc',
        ],
        'value_when_matched': True,
    },
    'screen_flicker': {
        'keywords': [
            'nhấp nháy', 'nháy màn', 'chớp', 'flicker',
            'màn nháy', 'giật hình',
        ],
        'value_when_matched': True,
    },
    'screen_black': {
        'keywords': [
            'đen hoàn toàn', 'hoàn toàn đen', 'màn đen ngòm',
        ],
        'value_when_matched': True,
    },

    # === OS ===
    'bsod': {
        'keywords': [
            'màn hình xanh', 'blue screen', 'bsod', 'xanh chết',
            'màn xanh', 'lỗi xanh',
        ],
        'value_when_matched': True,
    },
    'windows_accessible': {
        'keywords': [
            'không vào windows', 'không vào được', 'không vào win',
            'không vào desktop', 'không load windows',
        ],
        'value_when_matched': False,
    },
    'startup_freeze': {
        'keywords': [
            'treo khi khởi động', 'đứng khi bật', 'treo lúc mở',
            'treo logo', 'đứng logo',
        ],
        'value_when_matched': True,
    },
    'boot_loop': {
        'keywords': [
            'khởi động lặp', 'boot loop', 'bật tắt liên tục',
            'restart liên tục', 'khởi động lại hoài',
        ],
        'value_when_matched': True,
    },
    'boot_device_found': {
        'keywords': [
            'không nhận ổ cứng', 'no boot device', 'không nhận ssd',
            'không nhận hdd', 'không nhận ổ',
        ],
        'value_when_matched': False,
    },
    'login_success': {
        'keywords': [
            'không đăng nhập', 'sai mật khẩu', 'không login',
        ],
        'value_when_matched': False,
    },
    'black_after_login': {
        'keywords': [
            'đen sau login', 'đen sau đăng nhập', 'login xong đen',
        ],
        'value_when_matched': True,
    },

    # === NETWORK ===
    'wifi_connected': {
        'keywords_true': [
            'có kết nối wifi', 'có wifi', 'bắt được wifi', 'vào được wifi',
            'vẫn có wifi'
        ],
        'keywords_false': [
            'không kết nối wifi', 'mất wifi', 'wifi không kết nối',
            'không bắt wifi', 'wifi bị mất',
        ]
    },
    'wifi_available': {
        'keywords': [
            'không thấy wifi', 'không hiện wifi', 'không có wifi',
        ],
        'value_when_matched': False,
    },
    'internet_access': {
        'keywords': [
            'không có mạng', 'không có internet', 'mất mạng',
            'mất internet', 'không vào mạng', 'không có net',
        ],
        'value_when_matched': False,
    },
    'web_accessible': {
        'keywords': [
            'không mở web', 'không vào web', 'không duyệt web',
            'không mở trang web', 'không vào trang',
        ],
        'value_when_matched': False,
    },
    'ping_gateway': {
        'keywords_true': [
            'ping được gateway', 'ping tới gateway ok', 'gateway kết nối được'
        ],
        'keywords_false': [
            'không ping gateway', 'ping gateway không được',
        ]
    },
    'ping_external': {
        'keywords_true': [
            'ping được internet', 'ping google được', 'ping ra ngoài được'
        ],
        'keywords_false': [
            'không ping ra ngoài', 'ping internet không được', 'không ping được ngoài'
        ]
    },

    # === PERFORMANCE ===
    'system_slow': {
        'keywords': [
            'chậm', 'chạy chậm', 'lag', 'giật', 'ì ạch',
            'đơ', 'chạy ì',
        ],
        'value_when_matched': True,
    },
    'app_lag': {
        'keywords': [
            'mở app lag', 'ứng dụng lag', 'mở phần mềm chậm',
            'app giật', 'phần mềm chậm',
        ],
        'value_when_matched': True,
    },
    'system_freeze': {
        'keywords': [
            'bị treo', 'đứng máy', 'treo máy', 'đơ máy',
            'freeze', 'not responding',
        ],
        'value_when_matched': True,
    },
    'disk_usage_high': {
        'keywords': [
            'disk 100', 'ổ đĩa 100', 'disk full', 'ổ đĩa đầy',
            'disk usage',
        ],
        'value_when_matched': True,
    },
    'fan_noise_loud': {
        'keywords': [
            'quạt kêu to', 'quạt ồn', 'quạt kêu', 'tiếng quạt',
        ],
        'value_when_matched': True,
    },

    # === PERIPHERAL ===
    'usb_detected': {
        'keywords': [
            'không nhận usb', 'usb không nhận', 'cắm usb không',
        ],
        'value_when_matched': False,
    },
    'keyboard_working': {
        'keywords': [
            'bàn phím hỏng', 'bàn phím không', 'keyboard không',
            'không gõ được', 'bàn phím lỗi',
        ],
        'value_when_matched': False,
    },
    'mouse_working': {
        'keywords': [
            'chuột hỏng', 'chuột không', 'mouse không',
            'chuột lỗi', 'chuột đơ',
        ],
        'value_when_matched': False,
    },
    'audio_output': {
        'keywords': [
            'không có âm thanh', 'không nghe', 'mất tiếng',
            'mất âm thanh', 'không phát âm', 'loa không',
        ],
        'value_when_matched': False,
    },
}


def remove_accents(text):
    """Remove Vietnamese diacritics (accents) for fuzzy matching."""
    text = re.sub(r'[àáạảãâầấậẩẫăằắặẳẵ]', 'a', text)
    text = re.sub(r'[èéẹẻẽêềếệểễ]', 'e', text)
    text = re.sub(r'[ìíịỉĩ]', 'i', text)
    text = re.sub(r'[òóọỏõôồốộổỗơờớợởỡ]', 'o', text)
    text = re.sub(r'[ùúụủũưừứựửữ]', 'u', text)
    text = re.sub(r'[ỳýỵỷỹ]', 'y', text)
    text = re.sub(r'[đ]', 'd', text)
    return text


def _normalize(text):
    """Normalize Vietnamese text for matching."""
    text = text.lower().strip()
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    return text


def parse_input(text):
    """
    Parse Vietnamese free-text input and extract symptom facts.

    Args:
        text: raw user input string

    Returns:
        dict mapping symptom_code -> bool value
    """
    if not text or not text.strip():
        return {}

    normalized = _normalize(text)
    normalized_no_accents = remove_accents(normalized)
    extracted = {}

    for symptom_code, config in KEYWORD_MAP.items():
        # Check explicit true keywords
        for kw in config.get('keywords_true', []):
            kw_norm = _normalize(kw)
            kw_no_accents = remove_accents(kw_norm)
            if kw_norm in normalized or kw_no_accents in normalized_no_accents:
                extracted[symptom_code] = True
                logger.debug("NLP: '%s' matched -> %s = True", kw, symptom_code)
                break
                
        # Check explicit false keywords
        if symptom_code not in extracted:
            for kw in config.get('keywords_false', []):
                kw_norm = _normalize(kw)
                kw_no_accents = remove_accents(kw_norm)
                if kw_norm in normalized or kw_no_accents in normalized_no_accents:
                    extracted[symptom_code] = False
                    logger.debug("NLP: '%s' matched -> %s = False", kw, symptom_code)
                    break

        # Check legacy mapping format
        if symptom_code not in extracted and 'keywords' in config:
            for kw in config['keywords']:
                kw_norm = _normalize(kw)
                kw_no_accents = remove_accents(kw_norm)
                
                # Check exact match first, then diacritic-free match
                if kw_norm in normalized or kw_no_accents in normalized_no_accents:
                    extracted[symptom_code] = config['value_when_matched']
                    logger.debug(
                        "NLP: '%s' matched -> %s = %s",
                        kw, symptom_code, config['value_when_matched']
                    )
                    break  # first keyword match wins for this symptom

    logger.info("NLP parsed %d facts from input: %s", len(extracted), text[:80])
    return extracted


def get_nlp_summary(extracted_facts):
    """
    Build a human-readable summary of what the NLP extracted.

    Args:
        extracted_facts: dict from parse_input()

    Returns:
        list of Vietnamese description strings
    """
    descriptions = []
    for code, value in extracted_facts.items():
        if code in KEYWORD_MAP:
            val_str = "Có" if value else "Không"
            descriptions.append(f"• {code}: {val_str}")
    return descriptions
