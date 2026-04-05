"""
Intent Classifier — Phân loại nhóm lỗi từ text người dùng.

Chiến lược:
  - Lowercase + normalize text (bỏ dấu câu thừa)
  - Đếm keyword hits cho mỗi intent group
  - Return top intent nếu confidence > threshold
  - Return None nếu không chắc chắn (→ hiển thị Q01)

⚠️ Không tự kết luận diagnosis — chỉ classify intent.
"""

from __future__ import annotations
import re
import unicodedata
from typing import Optional

from .patterns import INTENT_KEYWORDS, INTENT_MIN_CONFIDENCE, INTENT_HIGH_CONFIDENCE


def _normalize(text: str) -> str:
    """Normalize text: lowercase, trim, xóa ký tự thừa."""
    text = text.lower().strip()
    # Giữ dấu tiếng Việt, chỉ xóa ký tự đặc biệt không cần thiết
    text = re.sub(r"[^\w\s\u00C0-\u024F\u1E00-\u1EFF]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


class IntentClassifier:
    """
    Phân loại intent (nhóm lỗi) từ text người dùng.
    Dùng weighted keyword counting.
    """

    def __init__(self):
        self._keywords = INTENT_KEYWORDS
        self._min_confidence = INTENT_MIN_CONFIDENCE
        self._high_confidence = INTENT_HIGH_CONFIDENCE

    def classify(self, text: str) -> dict:
        """
        Phân loại intent từ text.

        Returns:
        {
            "intent": str | None,
            "confidence": float,          # 0.0 – 1.0
            "is_certain": bool,
            "scores": {intent: score},    # debug info
        }
        """
        normalized = _normalize(text)
        scores: dict[str, float] = {}

        for intent, keywords in self._keywords.items():
            score = 0.0
            for kw in keywords:
                if kw in normalized:
                    # Trọng số: keyword dài hơn = cụ thể hơn = weight cao hơn
                    weight = 1.0 + len(kw.split()) * 0.3
                    score += weight
            if score > 0:
                scores[intent] = round(score, 2)

        if not scores:
            return {
                "intent": None,
                "confidence": 0.0,
                "is_certain": False,
                "scores": {},
            }

        # Normalize scores to [0, 1]
        total = sum(scores.values())
        normalized_scores = {k: v / total for k, v in scores.items()}

        top_intent = max(normalized_scores, key=normalized_scores.get)
        top_conf = normalized_scores[top_intent]

        return {
            "intent": top_intent if top_conf >= self._min_confidence else None,
            "confidence": round(top_conf, 3),
            "is_certain": top_conf >= self._high_confidence,
            "scores": normalized_scores,
        }

    def get_group_question_start(self, intent: str) -> Optional[str]:
        """
        Map intent → câu hỏi đầu tiên của nhóm đó.
        Dùng để skip Q01 khi intent rõ ràng.
        """
        mapping = {
            "power_startup": "Q02",
            "display": "Q09",
            "os_boot": "Q13",
            "network": "Q20",
            "audio_camera": "Q27",
            "peripherals": "Q32",
            "performance": "Q37",
            "storage": "Q36",
        }
        return mapping.get(intent)
