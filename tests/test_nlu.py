"""
test_nlu.py — Test NLU: intent classifier và fact extractor.

Chạy: pytest tests/test_nlu.py -v
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from nlu.intent_classifier import IntentClassifier
from nlu.fact_extractor import FactExtractor


@pytest.fixture
def clf():
    return IntentClassifier()


@pytest.fixture
def extractor():
    return FactExtractor()


class TestIntentClassifier:

    def test_power_intent(self, clf):
        result = clf.classify("máy tôi không bật được, bấm nút nguồn không có phản ứng gì")
        assert result["intent"] == "power_startup"
        assert result["confidence"] > 0.3

    def test_network_intent(self, clf):
        result = clf.classify("wifi có nhưng không vào được internet")
        assert result["intent"] == "network"

    def test_display_intent(self, clf):
        result = clf.classify("màn hình bị sọc ngang, nhấp nháy liên tục")
        assert result["intent"] == "display"

    def test_audio_intent(self, clf):
        result = clf.classify("loa không có tiếng gì cả, driver âm thanh lỗi")
        assert result["intent"] == "audio_camera"

    def test_performance_intent(self, clf):
        result = clf.classify("máy chạy rất chậm, nóng và quạt kêu to")
        assert result["intent"] == "performance"

    def test_storage_intent(self, clf):
        result = clf.classify("ổ cứng phát ra tiếng click lách cách")
        assert result["intent"] == "storage"

    def test_unknown_returns_none(self, clf):
        result = clf.classify("xin chào")
        # Có thể là None hoặc confidence thấp
        assert result["confidence"] < 0.5

    def test_group_question_mapping(self, clf):
        assert clf.get_group_question_start("power_startup") == "Q02"
        assert clf.get_group_question_start("display") == "Q09"
        assert clf.get_group_question_start("network") == "Q20"


class TestFactExtractor:

    def test_extract_power_facts(self, extractor):
        result = extractor.extract("máy không lên nguồn, bấm nút không có phản ứng")
        assert "no_power" in result["facts"]
        assert result["has_facts"] is True

    def test_extract_wifi_facts(self, extractor):
        result = extractor.extract("wifi có nhưng không có internet, thiết bị khác vào được bình thường")
        assert "wifi_connected_no_internet" in result["facts"]

    def test_extract_multiple_facts(self, extractor):
        result = extractor.extract("màn hình đen và nghe nhiều tiếng beep")
        assert "screen_black" in result["facts"]
        assert "multiple_beeps" in result["facts"]

    def test_no_facts_when_unclear(self, extractor):
        result = extractor.extract("xin chào bạn ơi")
        assert result["has_facts"] is False

    def test_extract_and_classify_combined(self, extractor):
        from nlu.intent_classifier import IntentClassifier
        clf = IntentClassifier()

        text = "không sạc được, đèn sạc không sáng"
        intent = clf.classify(text)
        combined = extractor.extract_and_classify(text, intent)

        assert "no_charge" in combined["facts"]
        assert len(combined["facts"]) > 0  # has_facts → check facts list directly
        assert combined["is_certain"] is True
