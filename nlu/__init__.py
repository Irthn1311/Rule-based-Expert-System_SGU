"""
NLU package — Natural Language Understanding (Rule-Based)

Exports:
    IntentClassifier, FactExtractor, classify_intent, extract_facts
"""

from .intent_classifier import IntentClassifier
from .fact_extractor import FactExtractor

__all__ = ["IntentClassifier", "FactExtractor"]
