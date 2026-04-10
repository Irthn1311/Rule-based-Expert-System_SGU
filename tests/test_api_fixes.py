"""Integration test for all bug fixes."""
import sys
sys.path.insert(0, '.')
import app as flask_app

client = flask_app.app.test_client()
flask_app.init_app()

# Test 1: /start
r = client.post('/start', json={})
assert r.status_code == 200, f'/start failed: {r.status_code}'
data = r.get_json()
assert 'session_id' in data
assert 'session_state' in data, 'session_state missing from /start response'
assert data['question'] is not None
sid = data['session_id']
sstate = data['session_state']
qid = data['question']['id']
val = data['question']['options'][0]['value']
print(f'[OK] /start -> session_id={sid[:8]}... question={qid}')

# Test 2: /select stateless (dùng session_state thay vì session_id)
r2 = client.post('/select', json={'session_state': sstate, 'question_id': qid, 'value': val})
assert r2.status_code == 200, f'/select stateless failed: {r2.status_code} body={r2.get_data(as_text=True)}'
data2 = r2.get_json()
assert 'session_state' in data2, 'session_state missing from /select response'
next_q = data2['question']['id'] if data2.get('question') else 'complete'
print(f'[OK] /select stateless -> next_q={next_q}')

# Test 3: /select với stale question_id -> phải 200, KHÔNG phải 400
r3 = client.post('/select', json={'session_state': sstate, 'question_id': 'STALE_Q99', 'value': val})
assert r3.status_code == 200, f'/select stale q should be 200, got {r3.status_code}: {r3.get_data(as_text=True)}'
data3 = r3.get_json()
assert 'bot_message' in data3
print('[OK] /select stale question_id -> graceful 200 (not 400)')

# Test 4: /message stateless
r4 = client.post('/message', json={'session_state': sstate, 'text': 'máy không khởi động'})
assert r4.status_code == 200, f'/message failed: {r4.status_code}'
data4 = r4.get_json()
assert 'session_state' in data4
print('[OK] /message stateless -> OK')

# Test 5: /reset
r5 = client.post('/reset', json={'session_id': sid})
assert r5.status_code == 200, f'/reset failed: {r5.status_code}'
data5 = r5.get_json()
assert data5['session_id'] != sid, 'reset should create new session_id'
assert 'session_state' in data5
print(f'[OK] /reset -> new_sid={data5["session_id"][:8]}...')

# Test 6: /select với session_id không tồn tại -> phải 404
r6 = client.post('/select', json={'session_id': 'nonexistent-id-xyz', 'question_id': 'Q01', 'value': 'A'})
assert r6.status_code == 404, f'nonexistent session_id should 404, got {r6.status_code}'
print('[OK] /select nonexistent session_id -> 404')

# Test 7: /select thiếu value -> phải 400
r7 = client.post('/select', json={'session_state': sstate, 'question_id': qid})
assert r7.status_code == 400, f'missing value should 400, got {r7.status_code}'
print('[OK] /select missing value -> 400 (correct)')

print()
print('=' * 40)
print('ALL INTEGRATION TESTS PASSED')
print('=' * 40)
