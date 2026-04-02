"""
Response Generator — Generates natural, professional language for the chatbot.
"""

import json
import os
import random

def load_symptoms():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(base_dir, 'data', 'symptoms_master.json')
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Load symptoms as a global dictionary for quick lookup
try:
    SYMPTOMS_DICT = {item['symptom_code']: item['question_text'] for item in load_symptoms()}
except Exception:
    SYMPTOMS_DICT = {}

PREFIXES = [
    "Tôi ghi nhận thông tin:",
    "Đã lưu ý:",
    "Thông tin đã được ghi nhận:",
    "Tôi hiểu rồi,",
    "Như vậy là"
]

def get_natural_acknowledgment(symptom_code, value, is_contextual=False):
    """
    Generate a natural, professional response acknowledging a fact.
    """
    
    # Custom mapping for better natural phrasing
    custom_phrases = {
        'power_response': {
            True: 'máy có phản hồi khi bật nguồn',
            False: 'máy hoàn toàn không có phản hồi khi nhấn nút nguồn'
        },
        'led_on': {
            True: 'đèn báo nguồn vẫn sáng',
            False: 'không có đèn báo nào sáng'
        },
        'fan_running': {
            True: 'quạt tản nhiệt vẫn quay',
            False: 'quạt tản nhiệt không quay'
        },
        'display_on': {
            True: 'màn hình vẫn hiển thị',
            False: 'màn hình không hiển thị nội dung'
        },
        'system_slow': {
            True: 'máy tính đang chạy chậm / ì ạch',
            False: 'tốc độ máy tính vẫn bình thường'
        },
        'system_hot': {
            True: 'máy đang có hiện tượng quá nhiệt (nóng)',
            False: 'chưa thấy dấu hiệu quá nhiệt'
        },
        'wifi_connected': {
            True: 'máy vẫn kết nối được Wi-Fi',
            False: 'máy không kết nối được Wi-Fi'
        },
        'windows_accessible': {
            True: 'máy vẫn vào được Windows',
            False: 'không thể truy cập vào Windows'
        },
        'bsod': {
            True: 'máy bị lỗi màn hình xanh (BSOD)',
            False: 'không có hiện tượng màn hình xanh'
        },
        'boot_loop': {
            True: 'máy bị khởi động lại liên tục',
            False: 'máy không bị lỗi khởi động lặp'
        }
    }
    
    prefix = random.choice(PREFIXES)
    
    if symptom_code in custom_phrases:
        phrase = custom_phrases[symptom_code][value]
        return f"{prefix} {phrase}."
    
    # Fallback to generic translation of the question text
    q_text = SYMPTOMS_DICT.get(symptom_code, "")
    if q_text:
        # Simple heuristic to turn question into statement
        statement = q_text.lower().replace('không?', '').replace('có ', '').strip()
        if statement.endswith('?'):
            statement = statement[:-1]
            
        status = "đang xảy ra" if value else "không bị"
        if value:
            return f"{prefix} máy có hiện tượng: {statement}."
        else:
            return f"{prefix} máy không bị tình trạng: {statement}."
    
    # Ultimate fallback
    status = "có" if value else "không"
    return f"{prefix} {symptom_code} là '{status}'."

def get_nlp_natural_summary(extracted_facts):
    """
    Build a natural multi-line summary of extracted facts.
    """
    if not extracted_facts:
        return "Tôi chưa ghi nhận được thông tin gì rõ ràng."
        
    responses = ["Theo mô tả của bạn, tôi ghi nhận các vấn đề sau:"]
    for code, value in extracted_facts.items():
        # Clean prefix for lists
        ack = get_natural_acknowledgment(code, value)
        for prefix in PREFIXES:
            if ack.startswith(prefix):
                ack = ack.replace(prefix, "").strip().capitalize()
        responses.append(f"• {ack}")
        
    return "\n".join(responses)
