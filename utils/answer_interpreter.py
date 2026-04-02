"""
Answer Interpreter — Context-aware short-answer resolution.

When the system has an active question (e.g., 'power_response'),
this module maps short/ambiguous user replies like 'có', 'không',
'yes', 'no', 'ừ', 'máy tôi có lên nguồn' to a boolean value
relative to that question.

Priority order in chat_send:
1. answer_interpreter (if current_question exists)
2. nlp_parser (free-text keyword extraction)
3. Clarification fallback
"""

import re
import logging
from utils.nlp_parser import remove_accents

logger = logging.getLogger(__name__)

# ── Definite YES patterns ──
YES_PATTERNS = [
    'có', 'co', 'yes', 'yeah', 'yep', 'y',
    'ừ', 'uh', 'ờ', 'ok', 'đúng', 'rồi',
    'phải', 'đúng rồi', 'chính xác', 'vâng',
    'đúng vậy', 'có ạ', 'dạ có', 'dạ',
    'có chứ', 'tất nhiên', 'sure', 'vẫn có'
]

# ── Definite NO patterns ──
NO_PATTERNS = [
    'không', 'khong', 'no', 'nope', 'n',
    'không có', 'không ạ', 'dạ không',
    'chưa', 'không phải', 'không đúng',
    'không hề', 'hoàn toàn không', 'chắc chắn không',
    'không bao giờ',
]

# ── Contextual YES phrases (partial match) ──
# These are checked via word-boundary padded substring
CONTEXTUAL_YES_FRAGMENTS = [
    'có lên', 'có bật', 'có sáng', 'có quay', 'có chạy',
    'có hiển thị', 'có kết nối', 'có phản hồi',
    'có hoạt động', 'có nhận', 'lên được', 'bật được',
    'sáng rồi', 'quay rồi', 'chạy rồi', 'bình thường',
    'hoạt động', 'vẫn tốt', 'vẫn được', 'được',
    'sáng', 'hiện', 'hiển thị', 'chạy', 'lên', 'bật',
    'vẫn sáng', 'vẫn lên', 'vẫn chạy', 'vẫn hoạt động', 
    'vẫn hiện', 'vẫn hiển thị', 'vẫn phản hồi', 'vẫn còn',
    'vẫn quay'
]

# ── Contextual NO phrases (partial match) ──
CONTEXTUAL_NO_FRAGMENTS = [
    'không lên', 'không bật', 'không sáng', 'không quay',
    'không chạy', 'không hiển thị', 'không kết nối',
    'không phản hồi', 'không hoạt động', 'không nhận',
    'không được', 'không lên được', 'không bật được',
    'hỏng', 'lỗi', 'chết', 'tắt', 'mất',
    'hết rồi', 'không còn', 'chưa bao giờ',
]


def interpret_answer(user_input, current_question_code=None):
    """
    Interpret a user reply in the context of the current active question.

    Args:
        user_input: raw text from user
        current_question_code: the symptom_code currently being asked (or None)

    Returns:
        dict or None:
        {
            'value': bool,          # True = yes, False = no
            'source': str,          # 'exact_match' | 'contextual_match'
            'matched_pattern': str  # what pattern was matched
        }
        Returns None if not interpretable.
    """
    if not user_input or not current_question_code:
        return None

    text = _normalize(user_input)
    text_no_accents = remove_accents(text)

    if not text:
        return None

    # We use padded matching to ensure word boundaries (e.g. 'hỏng' doesn't match inside 'không')
    pad_text = f" {text} "
    pad_text_no = f" {text_no_accents} "

    # ── Step 1: Exact match against YES/NO word lists ──
    # Check NO first because "không có" contains "có"
    for pattern in NO_PATTERNS:
        pat_no_accents = remove_accents(pattern)
        if text == pattern or text == pattern + ' ạ' or text_no_accents == pat_no_accents or text_no_accents == pat_no_accents + ' a':
            logger.info(
                "Answer interpreter: exact NO match '%s' for %s",
                pattern, current_question_code
            )
            return {
                'value': False,
                'source': 'exact_match',
                'matched_pattern': pattern
            }

    for pattern in YES_PATTERNS:
        pat_no_accents = remove_accents(pattern)
        if text == pattern or text == pattern + ' ạ' or text_no_accents == pat_no_accents or text_no_accents == pat_no_accents + ' a':
            logger.info(
                "Answer interpreter: exact YES match '%s' for %s",
                pattern, current_question_code
            )
            return {
                'value': True,
                'source': 'exact_match',
                'matched_pattern': pattern
            }

    # ── Step 2: Contextual fragment matching ──
    # Check NO fragments first (to handle "không lên" before "lên")
    for frag in CONTEXTUAL_NO_FRAGMENTS:
        frag_no_accents = remove_accents(frag)
        if f" {frag} " in pad_text or f" {frag_no_accents} " in pad_text_no:
            logger.info(
                "Answer interpreter: contextual NO fragment '%s' in '%s' for %s",
                frag, text, current_question_code
            )
            return {
                'value': False,
                'source': 'contextual_match',
                'matched_pattern': frag
            }

    for frag in CONTEXTUAL_YES_FRAGMENTS:
        frag_no_accents = remove_accents(frag)
        if f" {frag} " in pad_text or f" {frag_no_accents} " in pad_text_no:
            logger.info(
                "Answer interpreter: contextual YES fragment '%s' in '%s' for %s",
                frag, text, current_question_code
            )
            return {
                'value': True,
                'source': 'contextual_match',
                'matched_pattern': frag
            }

    # ── Step 3: Could not interpret ──
    logger.debug(
        "Answer interpreter: could not interpret '%s' for %s",
        text, current_question_code
    )
    return None


def _normalize(text):
    """Lowercase, strip, collapse whitespace."""
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    # Remove trailing punctuation
    text = text.rstrip('?!.,;:')
    return text.strip()
