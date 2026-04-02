"""
JSON Loader Utility
Provides functions to load JSON data files from the data directory.
"""

import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')


def load_json(filename):
    """Load and parse a JSON file from the data directory."""
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_symptoms():
    """Load symptoms master data."""
    return load_json('symptoms_master.json')


def load_rules():
    """Load rules master data."""
    return load_json('rules_master.json')


def load_question_flow():
    """Load question flow data."""
    return load_json('question_flow.json')
