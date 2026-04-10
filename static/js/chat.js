/**
 * chat.js — Frontend logic cho PC Expert Chat UI
 *
 * Flow:
 *   1. Page load → startSession() → /start
 *   2. Bot hiển thị greeting + Q01 (quick-reply buttons)
 *   3. User click option → sendSelect() → /select
 *   4. Hoặc user gõ text → sendMessage() → /message
 *   5. Multi-choice → check boxes → submitMultiChoice() → /submit
 *   6. Session complete → showDiagnosisModal()
 *   7. User click "Giải thích" → showExplanation() → /explanation
 *   8. User click "Bắt đầu lại" → restartSession() → /reset
 */

'use strict';

// ── State ──────────────────────────────────────────────────────
const state = {
  sessionId: null,
  sessionState: null,    // ← stateless Vercel support: blob gửi kèm mỗi request
  currentQuestion: null,
  inputMode: 'single_choice',  // text | single_choice | multi_choice
  isWaiting: false,
  lastDiagnoses: [],
};

// ── DOM Refs ──────────────────────────────────────────────────
const $ = id => document.getElementById(id);

const messagesEl    = $('chat-messages');
const quickReplies  = $('quick-replies');
const multiArea     = $('multi-select-area');
const multiList     = $('multi-select-list');
const textInputRow  = $('text-input-row');
const textInput     = $('user-text-input');
const btnSend       = $('btn-send');
const factsList     = $('facts-list');
const candidateList = $('candidate-list');
const wmCount       = $('wm-count');
const rulesList     = $('rules-list');
const rulesSection  = $('rules-section');

// ── Init ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  textInput.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
  startSession();
});

// ── Session Management ────────────────────────────────────────

async function startSession() {
  setWaiting(true);
  clearChat();
  showTyping();

  try {
    const res = await fetchJSON('/start', 'POST', {});
    hideTyping();
    applyResponse(res);
  } catch (err) {
    hideTyping();
    addBotMessage('❌ Không thể kết nối server. Vui lòng thử lại sau.');
  } finally {
    setWaiting(false);
  }
}

async function restartSession() {
  const oldId = state.sessionId;
  closeDiagnosisModal();
  setWaiting(true);
  // Fix Bug #5: KHÔNG clearChat() trước — chỉ show typing indicator
  // clearChat sẽ được gọi SAU KHI nhận response thành công
  showTyping();

  try {
    const res = await fetchJSON('/reset', 'POST', { session_id: oldId || '' });
    clearChat();       // ← Clear sau khi thành công, không phải trước
    hideTyping();
    applyResponse(res);
    updateSidePanel([], []);
  } catch (err) {
    hideTyping();
    addBotMessage('❌ Lỗi khi khởi động lại. Vui lòng tải lại trang.');
  } finally {
    setWaiting(false);
  }
}

// ── Message Sending ───────────────────────────────────────────

async function sendMessage() {
  const text = textInput.value.trim();
  if (!text || state.isWaiting || !state.sessionId) return;

  addUserMessage(text);
  textInput.value = '';

  // Fix Bug #3: disable stale buttons NGAY LẬP TỨC trước khi /message quay về
  // Tránh user click button cũ trong lúc server đang xử lý NLU skip
  disableQuickReplies();

  setWaiting(true);
  showTyping();

  try {
    const res = await fetchJSON('/message', 'POST', {
      session_id: state.sessionId,
      session_state: state.sessionState,  // ← stateless support
      text,
    });
    hideTyping();
    applyResponse(res);
  } catch (err) {
    hideTyping();
    addBotMessage('❌ Lỗi khi gửi tin nhắn. Vui lòng thử lại.');
    enableQuickReplies(); // khôi phục nếu lỗi
  } finally {
    setWaiting(false);
  }
}

async function sendSelect(questionId, value, label) {
  if (state.isWaiting || !state.sessionId) return;

  addUserMessage(label);
  setWaiting(true);
  showTyping();

  // Disable buttons
  disableQuickReplies();

  try {
    const res = await fetchJSON('/select', 'POST', {
      session_id: state.sessionId,
      session_state: state.sessionState,  // ← stateless support
      question_id: questionId,
      value,
    });
    hideTyping();
    applyResponse(res);
  } catch (err) {
    hideTyping();
    addBotMessage('❌ Lỗi. Vui lòng thử lại.');
    enableQuickReplies();
  } finally {
    setWaiting(false);
  }
}

async function submitMultiChoice() {
  if (state.isWaiting || !state.sessionId || !state.currentQuestion) return;

  const checkboxes = multiList.querySelectorAll('input[type="checkbox"]:checked');
  const values = Array.from(checkboxes).map(cb => cb.value);

  // Build display label
  const labels = Array.from(checkboxes).map(cb => cb.dataset.label);
  const displayText = labels.length > 0 ? labels.join(', ') : 'Không chọn gì';

  addUserMessage(`✅ ${displayText}`);
  setWaiting(true);
  showTyping();
  disableMultiSelect();

  try {
    const res = await fetchJSON('/submit', 'POST', {
      session_id: state.sessionId,
      session_state: state.sessionState,  // ← stateless support
      question_id: state.currentQuestion.id,
      values,
    });
    hideTyping();
    applyResponse(res);
  } catch (err) {
    hideTyping();
    addBotMessage('❌ Lỗi. Vui lòng thử lại.');
    enableMultiSelect();
  } finally {
    setWaiting(false);
  }
}

// ── Apply Server Response ─────────────────────────────────────

function applyResponse(res) {
  if (!res) return;

  // Update session state
  if (res.session_id) state.sessionId = res.session_id;
  if (res.input_mode !== undefined) state.inputMode = res.input_mode;

  // Fix Bug #4: luôn update currentQuestion kể cả khi null
  if ('question' in res) {
    state.currentQuestion = res.question || null;
  }
  // Explicit clear khi session hoàn tất
  if (res.session_complete) {
    state.currentQuestion = null;
  }

  // Stateless mode: lưu session_state để gửi lại lần sau
  if (res.session_state) {
    state.sessionState = res.session_state;
  }

  // Update side panel
  if (Array.isArray(res.top_diagnoses)) {
    updateSidePanel(res.top_diagnoses, []);
  }
  if (typeof res.wm_size === 'number') {
    wmCount.textContent = res.wm_size;
  }
  if (Array.isArray(res.facts_added) && res.facts_added.length > 0) {
    appendFactTags(res.facts_added);
  }

  // Bot message
  if (res.bot_message) {
    addBotMessage(res.bot_message);
  }

  // Render input
  if (res.session_complete) {
    // Show diagnosis result
    hideAllInputs();
    if (res.diagnoses && res.diagnoses.length > 0) {
      state.lastDiagnoses = res.diagnoses;
      renderDiagnosisInChat(res.primary_diagnosis || res.diagnoses[0]);
      setTimeout(() => showDiagnosisModal(res.diagnoses), 800);
    }
    return;
  }

  // Render question inputs
  if (res.question) {
    renderInputsForQuestion(res.question, res.input_mode || 'single_choice');
  }
}

// ── Render Inputs ─────────────────────────────────────────────

function renderInputsForQuestion(question, mode) {
  state.currentQuestion = question;
  const type = question.type || mode;

  if (type === 'multi_choice') {
    renderMultiChoice(question);
  } else {
    renderQuickReplies(question);
  }
}

function renderQuickReplies(question) {
  quickReplies.innerHTML = '';
  multiArea.style.display = 'none';
  textInputRow.style.display = 'flex';
  quickReplies.style.display = 'flex';

  question.options.forEach(opt => {
    if (opt.value === 'SUBMIT') return; // Skip SUBMIT pseudo-option
    const btn = document.createElement('button');
    btn.className = 'quick-reply-btn';
    btn.textContent = opt.label;
    btn.onclick = () => sendSelect(question.id, opt.value, opt.label);
    btn.id = `opt-${question.id}-${opt.value}`;
    quickReplies.appendChild(btn);
  });

  textInput.placeholder = 'Hoặc mô tả vấn đề bằng text...';
}

function renderMultiChoice(question) {
  quickReplies.innerHTML = '';
  quickReplies.style.display = 'none';
  multiList.innerHTML = '';
  multiArea.style.display = 'block';
  textInputRow.style.display = 'none';

  question.options.forEach(opt => {
    if (opt.value === 'SUBMIT') return;

    const label = document.createElement('label');
    label.className = 'multi-option';
    label.htmlFor = `mc-${opt.value}`;

    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.id = `mc-${opt.value}`;
    cb.value = opt.value;
    cb.dataset.label = opt.label;

    cb.addEventListener('change', () => {
      label.classList.toggle('checked', cb.checked);
    });

    const span = document.createElement('span');
    span.textContent = opt.label;

    label.appendChild(cb);
    label.appendChild(span);
    multiList.appendChild(label);
  });
}

function hideAllInputs() {
  quickReplies.innerHTML = '';
  quickReplies.style.display = 'none';
  multiArea.style.display = 'none';
  textInputRow.style.display = 'flex';
  textInput.placeholder = 'Phiên chẩn đoán đã hoàn tất.';
  textInput.disabled = true;
  btnSend.disabled = true;
}

// ── Chat Messages ─────────────────────────────────────────────

function addBotMessage(text) {
  const row = document.createElement('div');
  row.className = 'message bot-message';

  const avatar = document.createElement('div');
  avatar.className = 'avatar';
  avatar.textContent = '🤖';

  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.innerHTML = formatMarkdown(text);

  row.appendChild(avatar);
  row.appendChild(bubble);
  messagesEl.appendChild(row);
  scrollToBottom();
}

function addUserMessage(text) {
  const row = document.createElement('div');
  row.className = 'message user-message';

  const avatar = document.createElement('div');
  avatar.className = 'avatar';
  avatar.textContent = '👤';

  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.textContent = text;

  row.appendChild(avatar);
  row.appendChild(bubble);
  messagesEl.appendChild(row);
  scrollToBottom();
}

function renderDiagnosisInChat(diag) {
  if (!diag) return;

  const severityEmoji = {
    CRITICAL: '🔴', HIGH: '🟠', MEDIUM: '🟡', LOW: '🟢', UNKNOWN: '⚪'
  }[diag.severity] || '⚪';

  const row = document.createElement('div');
  row.className = 'message bot-message';

  const avatar = document.createElement('div');
  avatar.className = 'avatar';
  avatar.textContent = '🤖';

  const bubble = document.createElement('div');
  bubble.className = 'bubble';

  bubble.innerHTML = `
    <div class="diagnosis-inline">
      <div class="diag-inline-header">
        <span class="diag-inline-badge">🏥 Kết quả chẩn đoán</span>
        <span class="diag-severity-badge sev-${diag.severity || 'UNKNOWN'}">${severityEmoji} ${diag.severity || ''}</span>
      </div>
      <div class="diag-inline-name">${escHtml(diag.name || diag.id)}</div>
      <div class="diag-inline-cf">Độ tin cậy: <strong>${diag.cf_percent || Math.round((diag.cf||0)*100)}%</strong></div>
      <button class="diag-inline-btn" onclick="showDiagnosisModal(window._lastDiagnoses || [])">
        Xem chi tiết & hướng xử lý →
      </button>
    </div>
  `;

  row.appendChild(avatar);
  row.appendChild(bubble);
  messagesEl.appendChild(row);

  // Store for button access
  window._lastDiagnoses = state.lastDiagnoses;
  scrollToBottom();
}

// ── Typing Indicator ──────────────────────────────────────────

function showTyping() {
  const tpl = document.getElementById('typing-template');
  if (!tpl) return;
  const clone = tpl.content.cloneNode(true);
  messagesEl.appendChild(clone);
  scrollToBottom();
}

function hideTyping() {
  const ti = $('typing-indicator');
  if (ti) ti.remove();
}

// ── Side Panel ─────────────────────────────────────────────────

function updateSidePanel(topDiagnoses, rules) {
  // Candidates
  if (topDiagnoses.length === 0) {
    candidateList.innerHTML = '<span class="empty-hint">Đang phân tích...</span>';
  } else {
    candidateList.innerHTML = topDiagnoses.map((d, i) => {
      const cf = d.cf_percent || Math.round((d.cf || 0) * 100);
      return `
        <div class="candidate-item">
          <div class="candidate-name">${i === 0 ? '▶ ' : ''}${escHtml(d.name)}</div>
          <div class="candidate-cf">
            <div class="cf-bar-bg"><div class="cf-bar-fill" style="width:${cf}%"></div></div>
            <span class="cf-label">${cf}%</span>
          </div>
        </div>
      `;
    }).join('');
  }
}

function appendFactTags(newFacts) {
  const empty = factsList.querySelector('.empty-hint');
  if (empty) empty.remove();

  newFacts.forEach(fact => {
    const tag = document.createElement('span');
    tag.className = 'fact-tag';
    tag.textContent = fact;
    factsList.appendChild(tag);
  });
}

function addRuleToPanel(ruleName, diag) {
  rulesSection.style.display = 'block';
  const item = document.createElement('div');
  item.className = 'rule-item';
  item.textContent = diag ? `${ruleName} → ${diag}` : ruleName;
  rulesList.appendChild(item);
}

function togglePanel() {
  const panel = document.getElementById('side-panel');
  panel.style.display = panel.style.display === 'none' ? 'flex' : 'none';
}

// ── Diagnosis Modal ───────────────────────────────────────────

function showDiagnosisModal(diagnoses) {
  if (!diagnoses || diagnoses.length === 0) return;

  const modal = $('diagnosis-modal');
  const primaryEl = $('primary-diagnosis');
  const altEl = $('alt-diagnoses');

  const primary = diagnoses[0];
  const alts = diagnoses.slice(1);

  // Primary card
  const cf = primary.cf_percent || Math.round((primary.cf || 0) * 100);
  const sev = primary.severity || 'UNKNOWN';
  const severityLabel = { CRITICAL: '🔴 Nghiêm trọng', HIGH: '🟠 Cao', MEDIUM: '🟡 Trung bình', LOW: '🟢 Thấp', UNKNOWN: '⚪ Chưa rõ' }[sev] || sev;

  const stepsHtml = (primary.solution_steps || []).map((s, i) => `
    <div class="solution-step">
      <div class="step-num">${i + 1}</div>
      <div>${escHtml(s)}</div>
    </div>
  `).join('');

  primaryEl.innerHTML = `
    <div class="diag-severity-badge sev-${sev}">${severityLabel}</div>
    <div class="diag-name">${escHtml(primary.name || primary.id)}</div>
    <div class="diag-cf-row">
      <span class="diag-cf-num">${cf}%</span>
      <span class="diag-cf-label">Độ tin cậy</span>
      <div class="cf-track"><div class="cf-fill" style="width:${cf}%"></div></div>
    </div>
    ${stepsHtml ? `<div class="diag-solution"><h4>Hướng xử lý</h4>${stepsHtml}</div>` : ''}
    ${primary.warning ? `<div class="diag-warning">⚠️ ${escHtml(primary.warning)}</div>` : ''}
    ${primary.needs_technician ? '<div class="diag-warning">🔧 Nên mang máy đến kỹ thuật viên chuyên nghiệp.</div>' : ''}
  `;

  // Alt diagnoses
  if (alts.length > 0) {
    altEl.innerHTML = `
      <div class="alt-title">Khả năng khác</div>
      <div class="alt-list">
        ${alts.map(d => {
          const acf = d.cf_percent || Math.round((d.cf || 0) * 100);
          return `
            <div class="alt-item">
              <span class="alt-item-name">${escHtml(d.name || d.id)}</span>
              <span class="alt-cf-pill">${acf}%</span>
            </div>
          `;
        }).join('')}
      </div>
    `;
  } else {
    altEl.innerHTML = '';
  }

  modal.style.display = 'flex';
}

function closeDiagnosisModal() {
  $('diagnosis-modal').style.display = 'none';
}

// ── Explanation Modal ──────────────────────────────────────────

async function showExplanation() {
  const modal = $('explanation-modal');
  const body = $('explanation-body');
  modal.style.display = 'flex';
  body.innerHTML = '<div class="loading-spinner">⏳ Đang tải giải thích...</div>';

  try {
    const res = await fetch(`/explanation?session_id=${state.sessionId}`);
    const data = await res.json();
    renderExplanation(data, body);
  } catch (err) {
    body.innerHTML = '<div class="loading-spinner">❌ Không thể tải giải thích.</div>';
  }
}

function renderExplanation(data, container) {
  const qPath = data.question_path || [];
  const rules = data.rules_fired || [];
  const facts = data.facts_collected || [];
  const top = data.top_diagnoses || [];

  let html = '';

  // Q&A Path
  if (qPath.length > 0) {
    html += `<div class="exp-section"><h3>📋 Quá trình hỏi đáp</h3>`;
    qPath.forEach(step => {
      const answers = Array.isArray(step.answers) ? step.answers.join(', ') : step.answers;
      html += `
        <div class="exp-step">
          <div class="exp-step-num">${step.step}</div>
          <div class="exp-step-content">
            <div class="exp-q">${escHtml(step.question)}</div>
            <div class="exp-a">→ ${escHtml(answers || '—')}</div>
          </div>
        </div>`;
    });
    html += `</div>`;
  }

  // Facts
  if (facts.length > 0) {
    html += `<div class="exp-section"><h3>📌 Facts thu thập được (${facts.length})</h3>`;
    html += facts.map(f => `<span class="fact-chip">${escHtml(f)}</span>`).join('');
    html += `</div>`;
  }

  // Rules fired
  if (rules.length > 0) {
    html += `<div class="exp-section"><h3>⚡ Luật đã kích hoạt (${rules.length})</h3>`;
    rules.forEach(r => {
      const cfClass = r.certainty >= 0.85 ? 'high' : r.certainty >= 0.7 ? 'medium' : 'low';
      html += `
        <div class="rule-row">
          <div class="rule-icon">⚡</div>
          <div class="rule-detail">
            <div class="rule-name">${escHtml(r.rule_name)}</div>
            <div class="rule-meta">
              <span class="cf-badge ${cfClass}">CF ${r.certainty_percent}%</span>
              ${r.triggered_diagnosis ? `→ <strong>${escHtml(r.triggered_diagnosis)}</strong>` : ''}
              ${r.added_facts && r.added_facts.length > 0 ? `+ facts: ${r.added_facts.map(f=>`<span class="fact-chip">${escHtml(f)}</span>`).join('')}` : ''}
            </div>
          </div>
        </div>`;
    });
    html += `</div>`;
  }

  // Top diagnoses summary
  if (top.length > 0) {
    html += `<div class="exp-section"><h3>🏥 Kết quả</h3>`;
    top.forEach((d, i) => {
      const medal = ['🥇','🥈','🥉'][i] || '•';
      const cf = d.cf_percent || Math.round((d.cf||0)*100);
      html += `<div class="alt-item" style="margin-bottom:6px">
        <span class="alt-item-name">${medal} ${escHtml(d.name)}</span>
        <span class="alt-cf-pill">${cf}%</span>
      </div>`;
    });
    html += `</div>`;
  }

  container.innerHTML = html || '<div class="loading-spinner">Không có dữ liệu giải thích.</div>';
}

function openTree() {
  if (!state.sessionId) return;
  window.open(`/tree?session=${state.sessionId}`, '_blank');
}

function closeExplanationModal() {
  $('explanation-modal').style.display = 'none';
}

// ── Utility ───────────────────────────────────────────────────

function clearChat() {
  messagesEl.innerHTML = '';
  quickReplies.innerHTML = '';
  multiList.innerHTML = '';
  multiArea.style.display = 'none';
  textInputRow.style.display = 'flex';
  textInput.disabled = false;
  btnSend.disabled = false;
  textInput.placeholder = 'Mô tả vấn đề bạn đang gặp phải...';

  // Reset side panel
  factsList.innerHTML = '<span class="empty-hint">Chưa có thông tin nào được ghi nhận.</span>';
  candidateList.innerHTML = '<span class="empty-hint">Đang phân tích...</span>';
  rulesList.innerHTML = '';
  rulesSection.style.display = 'none';
  wmCount.textContent = '0';

  // Fix Bug #5: reset session state (bao gồm sessionState blob)
  state.sessionId = null;
  state.sessionState = null;   // ← thêm dòng này
  state.currentQuestion = null;
  state.isWaiting = false;
  state.lastDiagnoses = [];
  window._lastDiagnoses = [];
}

function scrollToBottom() {
  messagesEl.scrollTo({ top: messagesEl.scrollHeight, behavior: 'smooth' });
}

function setWaiting(val) {
  state.isWaiting = val;
  btnSend.disabled = val;
  if (val) {
    textInput.disabled = true;
  } else {
    if (!state.sessionId || !document.getElementById('typing-indicator')) {
      textInput.disabled = false;
    }
  }
}

function disableQuickReplies() {
  quickReplies.querySelectorAll('.quick-reply-btn').forEach(b => b.disabled = true);
}

function enableQuickReplies() {
  quickReplies.querySelectorAll('.quick-reply-btn').forEach(b => b.disabled = false);
}

function disableMultiSelect() {
  multiList.querySelectorAll('input').forEach(cb => cb.disabled = true);
  $('btn-submit-multi').disabled = true;
}

function enableMultiSelect() {
  multiList.querySelectorAll('input').forEach(cb => cb.disabled = false);
  $('btn-submit-multi').disabled = false;
}

async function fetchJSON(url, method, body) {
  const res = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || `HTTP ${res.status}`);
  }
  return res.json();
}

function escHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function formatMarkdown(text) {
  if (!text) return '';
  return escHtml(text)
    // **bold**
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    // *italic*
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    // `code`
    .replace(/`(.*?)`/g, '<code>$1</code>')
    // bullet points
    .replace(/^• (.+)$/gm, '<div style="margin:2px 0 2px 8px">• $1</div>')
    // newlines
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>');
}

// Close modals on overlay click
document.addEventListener('click', e => {
  if (e.target.classList.contains('modal-overlay')) {
    closeDiagnosisModal();
    closeExplanationModal();
  }
});
