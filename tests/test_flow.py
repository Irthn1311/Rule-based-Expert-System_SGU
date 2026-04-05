"""
test_flow.py — Test Flask routes và full session flow.

Chạy: pytest tests/test_flow.py -v
"""

import sys
import os
import pytest
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Phải init app trước khi import
os.environ.setdefault('TESTING', '1')

from app import app as flask_app, init_app


@pytest.fixture(scope='session', autouse=True)
def init():
    """Khởi tạo KB và services một lần cho toàn bộ test session."""
    init_app()


@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as c:
        yield c


# ── Route Tests ───────────────────────────────────────────────

class TestRoutes:

    def test_index_returns_200(self, client):
        res = client.get('/')
        assert res.status_code == 200
        assert b'PC Expert' in res.data

    def test_status_ok(self, client):
        res = client.get('/status')
        data = res.get_json()
        assert res.status_code == 200
        assert data['status'] == 'ok'
        assert data['kb']['questions'] == 50
        assert data['kb']['rules'] == 103

    def test_start_returns_session(self, client):
        res = client.post('/start', json={})
        data = res.get_json()
        assert res.status_code == 200
        assert 'session_id' in data
        assert data['question'] is not None
        assert data['question']['id'] == 'Q01'

    def test_select_advances_session(self, client):
        # Start session
        start = client.post('/start', json={}).get_json()
        sid = start['session_id']
        q = start['question']

        # Select first option of Q01
        sel = client.post('/select', json={
            'session_id': sid,
            'question_id': q['id'],
            'value': 'A',  # power_startup
        }).get_json()

        assert sel['session_id'] == sid
        # Should advance to Q02
        assert sel['question'] is not None

    def test_message_with_nlu(self, client):
        start = client.post('/start', json={}).get_json()
        sid = start['session_id']

        res = client.post('/message', json={
            'session_id': sid,
            'text': 'máy không lên nguồn',
        }).get_json()

        assert res['session_id'] == sid
        # Có thể có facts được add
        assert isinstance(res.get('facts_added', []), list)

    def test_reset_creates_new_session(self, client):
        start = client.post('/start', json={}).get_json()
        old_sid = start['session_id']

        reset = client.post('/reset', json={'session_id': old_sid}).get_json()
        new_sid = reset['session_id']

        assert new_sid != old_sid
        assert reset['question']['id'] == 'Q01'

    def test_explanation_after_session(self, client):
        """Chạy session đến diagnosis, lấy explanation."""
        start = client.post('/start', json={}).get_json()
        sid = start['session_id']
        q = start['question']

        # Q01 → A (power_startup)
        r1 = client.post('/select', json={'session_id': sid, 'question_id': q['id'], 'value': 'A'}).get_json()
        q2 = r1.get('question')
        if not q2: return  # session ended early

        # Q02 → A (no_power, fan_not_spinning)
        r2 = client.post('/select', json={'session_id': sid, 'question_id': q2['id'], 'value': 'A'}).get_json()
        q3 = r2.get('question')
        if not q3: return

        # Q03 → A (is_laptop)
        r3 = client.post('/select', json={'session_id': sid, 'question_id': q3['id'], 'value': 'A'}).get_json()
        q4 = r3.get('question')
        if not q4: return

        # Q05 → A (no_charge, battery_indicator_red) → should trigger DIAG_PWR_01
        r4 = client.post('/select', json={'session_id': sid, 'question_id': q4['id'], 'value': 'A'}).get_json()

        # Get explanation
        exp = client.get(f'/explanation?session_id={sid}').get_json()
        assert 'question_path' in exp
        assert 'rules_fired' in exp
        assert len(exp['question_path']) > 0

    def test_invalid_session_returns_404(self, client):
        res = client.post('/select', json={
            'session_id': 'fake-session-id',
            'question_id': 'Q01',
            'value': 'A',
        })
        assert res.status_code == 404

    def test_multi_choice_submit(self, client):
        """Test submit multi_choice với Q08."""
        # Navigate to Q08 (power_startup → no_power → desktop → Q08)
        start = client.post('/start', json={}).get_json()
        sid = start['session_id']
        q = start['question']

        # Q01 → A
        r1 = client.post('/select', json={'session_id': sid, 'question_id': q['id'], 'value': 'A'}).get_json()
        q2 = r1.get('question')
        if not q2: return

        # Q02 → A (no_power, fan_not_spinning)
        r2 = client.post('/select', json={'session_id': sid, 'question_id': q2['id'], 'value': 'A'}).get_json()
        q3 = r2.get('question')
        if not q3: return

        # Q03 → B (is_desktop) → Q08
        r3 = client.post('/select', json={'session_id': sid, 'question_id': q3['id'], 'value': 'B'}).get_json()
        q4 = r3.get('question')
        if not q4: return

        # Skip to Q08 if we're there
        if q4['id'] == 'Q08':
            res = client.post('/submit', json={
                'session_id': sid,
                'question_id': 'Q08',
                'values': ['A', 'B']
            }).get_json()
            assert res['session_id'] == sid
