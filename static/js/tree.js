'use strict';

// ── Constants ─────────────────────────────────────────────────
const NODE_W   = 190, NODE_H   = 82;   // question node
const DIAG_W   = 168, DIAG_H   = 72;   // diagnosis node
const H_GAP    = 30;                    // horizontal gap
const V_GAP    = 88;                    // vertical gap between levels
const PAD      = 60;                    // canvas padding

const GROUP_ORDER = [
  'power_startup','display','os_boot','network',
  'audio_camera','peripherals','performance','storage',''
];

const SEV_EMOJI = { CRITICAL:'🔴', HIGH:'🟠', MEDIUM:'🟡', LOW:'🟢', UNKNOWN:'⚪' };

// ── State ─────────────────────────────────────────────────────
let treeData  = null;
let pathData  = null;
let coords    = {};
let canvasW   = 0, canvasH = 0;
let zoom      = 0.55;
let panX      = 0, panY  = 0;
let isDragging = false, dragStart = { x:0, y:0 }, panStart = { x:0, y:0 };

const $ = id => document.getElementById(id);

// ── Init ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  const params    = new URLSearchParams(location.search);
  const sessionId = params.get('session');

  try {
    treeData = await fetch('/api/tree').then(r => r.json());

    if (sessionId) {
      pathData = await fetch(`/api/tree-path?session_id=${sessionId}`).then(r => r.json());
      updatePathInfo(pathData);
    }

    coords = layoutDAG(treeData);
    renderTree();

    if (pathData && pathData.node_ids.length > 0) {
      applyPath(pathData);
      fitToPath();
    } else {
      fitAll();
    }
  } catch (e) {
    $('tree-loading').innerHTML = `<p style="color:#ef4444">❌ Lỗi: ${e.message}</p>`;
    return;
  }

  $('tree-loading').style.display = 'none';
  setupPanZoom();
  setupToolbar();
});


// ── Layout DAG (Top → Down, Barycenter) ───────────────────────
function layoutDAG(data) {
  const { nodes, edges } = data;

  // Group nodes by level
  const byLevel = {};
  for (const [id, n] of Object.entries(nodes)) {
    const lv = n.level || 0;
    if (!byLevel[lv]) byLevel[lv] = [];
    byLevel[lv].push({ ...n, id });
  }

  // Build parent map
  const parents = {};
  for (const e of edges) {
    if (!parents[e.to]) parents[e.to] = [];
    parents[e.to].push(e.from);
  }

  const result = {};
  const maxLevel = Math.max(...Object.keys(byLevel).map(Number));

  for (let lv = 0; lv <= maxLevel; lv++) {
    const list = byLevel[lv] || [];

    // Sort: barycenter of parents, then by group order, then by id
    list.sort((a, b) => {
      const baryA = _bary(a.id, parents, result);
      const baryB = _bary(b.id, parents, result);
      if (Math.abs(baryA - baryB) > 5) return baryA - baryB;
      const ga = GROUP_ORDER.indexOf(a.group || '');
      const gb = GROUP_ORDER.indexOf(b.group || '');
      if (ga !== gb) return ga - gb;
      return a.id.localeCompare(b.id);
    });

    const nodeW = NODE_W;  // use question width for spacing
    const total = list.length * (nodeW + H_GAP) - H_GAP;
    let x = -total / 2 + nodeW / 2;

    for (const n of list) {
      result[n.id] = { x, y: lv * (NODE_H + V_GAP) };
      x += nodeW + H_GAP;
    }
  }

  return result;
}

function _bary(id, parents, coords) {
  const pids = parents[id] || [];
  if (!pids.length) return 0;
  const sum = pids.reduce((s, pid) => s + (coords[pid]?.x ?? 0), 0);
  return sum / pids.length;
}


// ── Render Tree (HTML nodes + SVG edges) ─────────────────────
function renderTree() {
  const { nodes, edges } = treeData;

  // Calculate canvas bounds
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  for (const [id] of Object.entries(nodes)) {
    const c = coords[id];
    if (!c) continue;
    const w = nodes[id].type === 'diagnosis' ? DIAG_W : NODE_W;
    const h = nodes[id].type === 'diagnosis' ? DIAG_H : NODE_H;
    minX = Math.min(minX, c.x - w/2);
    maxX = Math.max(maxX, c.x + w/2);
    minY = Math.min(minY, c.y);
    maxY = Math.max(maxY, c.y + h);
  }

  const offsetX = -minX + PAD;
  const offsetY = PAD;
  canvasW = maxX - minX + PAD * 2;
  canvasH = maxY - minY + PAD * 2;

  const canvas = $('tree-canvas');
  canvas.style.width  = `${canvasW}px`;
  canvas.style.height = `${canvasH}px`;

  // SVG
  const svg = $('tree-svg');
  svg.setAttribute('width',  canvasW);
  svg.setAttribute('height', canvasH);

  // Arrow markers
  svg.innerHTML = `
    <defs>
      <marker id="arrow-default" markerWidth="8" markerHeight="8"
        refX="6" refY="3" orient="auto">
        <path d="M0,0 L0,6 L8,3 z" fill="#cbd5e1"/>
      </marker>
      <marker id="arrow-active" markerWidth="8" markerHeight="8"
        refX="6" refY="3" orient="auto">
        <path d="M0,0 L0,6 L8,3 z" fill="#2563eb"/>
      </marker>
    </defs>
  `;

  // Draw edges first (behind nodes)
  for (const edge of edges) {
    const c1 = coords[edge.from];
    const c2 = coords[edge.to];
    if (!c1 || !c2) continue;

    const n1 = nodes[edge.from];
    const n2 = nodes[edge.to];
    const nH1 = (n1?.type === 'diagnosis' ? DIAG_H : NODE_H);
    const nH2 = (n2?.type === 'diagnosis' ? DIAG_H : NODE_H);

    const x1 = c1.x + offsetX;
    const y1 = c1.y + offsetY + nH1;
    const x2 = c2.x + offsetX;
    const y2 = c2.y + offsetY;
    const cy = (y2 - y1) * 0.45;

    const edgeKey = `${edge.from}:${edge.value}`;
    const pathEl = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    pathEl.setAttribute('d',
      `M ${x1} ${y1} C ${x1} ${y1+cy} ${x2} ${y2-cy} ${x2} ${y2}`
    );
    pathEl.setAttribute('class', 'tree-edge');
    pathEl.setAttribute('data-edge', edgeKey);
    pathEl.setAttribute('marker-end', 'url(#arrow-default)');
    svg.appendChild(pathEl);

    // Edge label at midpoint (short)
    if (edge.label) {
      const mx = (x1 + x2) / 2;
      const my = (y1 + y2) / 2;
      const shortLabel = edge.label.length > 32
        ? edge.label.substring(0, 30) + '…'
        : edge.label;

      const textEl = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      textEl.setAttribute('x', mx);
      textEl.setAttribute('y', my);
      textEl.setAttribute('text-anchor', 'middle');
      textEl.setAttribute('class', 'edge-label');
      textEl.setAttribute('data-edge-label', edgeKey);
      textEl.textContent = shortLabel;
      svg.appendChild(textEl);
    }
  }

  // Draw nodes
  const nodesEl = $('tree-nodes');
  for (const [id, node] of Object.entries(nodes)) {
    const c = coords[id];
    if (!c) continue;

    const isQ = node.type === 'question';
    const nW  = isQ ? NODE_W : DIAG_W;
    const nH  = isQ ? NODE_H : DIAG_H;

    const div = document.createElement('div');
    div.id        = `node-${id}`;
    div.className = `tree-node ${node.type}${node.severity ? ' sev-' + node.severity : ''}`;
    div.style.left   = `${c.x + offsetX - nW/2}px`;
    div.style.top    = `${c.y + offsetY}px`;
    div.style.width  = `${nW}px`;
    div.style.height = `${nH}px`;

    if (isQ) {
      div.innerHTML = `
        <div class="node-qid">${id}</div>
        <div class="node-text">${escHtml(node.text)}</div>
        ${node.purpose ? `<div class="node-purpose">${escHtml(node.purpose)}</div>` : ''}
      `;
    } else {
      const sev   = node.severity || 'UNKNOWN';
      const emoji = SEV_EMOJI[sev] || '⚪';
      div.innerHTML = `
        <div class="node-diag-sev">${emoji} ${sev}</div>
        <div class="node-diag-name">${escHtml(node.name)}</div>
        <div class="node-diag-id">${id}</div>
      `;
    }

    nodesEl.appendChild(div);
  }

  // Init zoom to center-top
  const vp = $('tree-viewport');
  panX = (vp.offsetWidth - canvasW * zoom) / 2;
  panY = 20;
  applyTransform();
}


// ── Apply Path Highlight ──────────────────────────────────────
function applyPath(path) {
  if (!path || !path.node_ids.length) return;

  const nodeSet = new Set(path.node_ids);
  const edgeSet = new Set(path.edge_keys);

  // Nodes
  document.querySelectorAll('.tree-node').forEach(el => {
    const id = el.id.replace('node-', '');
    el.classList.remove('state-active', 'state-dimmed', 'state-default');
    if (nodeSet.has(id)) {
      el.classList.add('state-active');
    } else {
      el.classList.add('state-dimmed');
    }
  });

  // Edges
  document.querySelectorAll('.tree-edge').forEach(el => {
    const ek = el.getAttribute('data-edge');
    el.classList.remove('state-active', 'state-dimmed');
    if (edgeSet.has(ek)) {
      el.classList.add('state-active');
      el.setAttribute('marker-end', 'url(#arrow-active)');
    } else {
      el.classList.add('state-dimmed');
    }
  });

  // Edge labels
  document.querySelectorAll('.edge-label').forEach(el => {
    const ek = el.getAttribute('data-edge-label');
    el.classList.remove('state-active', 'state-dimmed');
    el.classList.add(edgeSet.has(ek) ? 'state-active' : 'state-dimmed');
  });
}

function clearPath() {
  document.querySelectorAll('.tree-node').forEach(el => {
    el.classList.remove('state-active', 'state-dimmed', 'state-default');
  });
  document.querySelectorAll('.tree-edge, .edge-label').forEach(el => {
    el.classList.remove('state-active', 'state-dimmed');
  });
  document.querySelectorAll('.tree-edge').forEach(el => {
    el.setAttribute('marker-end', 'url(#arrow-default)');
  });
}


// ── Fit View ─────────────────────────────────────────────────
function fitAll() {
  const vp = $('tree-viewport');
  const scaleX = vp.offsetWidth  / (canvasW + 40);
  const scaleY = (vp.offsetHeight - 10) / (canvasH + 40);
  zoom = Math.min(scaleX, scaleY, 0.8);
  panX = (vp.offsetWidth  - canvasW * zoom) / 2;
  panY = 20;
  applyTransform();
}

function fitToPath() {
  if (!pathData || !pathData.node_ids.length) return fitAll();

  // Find bounding box of active nodes
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  const { nodes } = treeData;

  for (const id of pathData.node_ids) {
    const c = coords[id];
    const n = nodes[id];
    if (!c || !n) continue;
    const nW = n.type === 'diagnosis' ? DIAG_W : NODE_W;
    const nH = n.type === 'diagnosis' ? DIAG_H : NODE_H;
    minX = Math.min(minX, c.x - nW/2);
    maxX = Math.max(maxX, c.x + nW/2);
    minY = Math.min(minY, c.y);
    maxY = Math.max(maxY, c.y + nH);
  }

  const vp   = $('tree-viewport');
  const pathW = maxX - minX + 120;
  const pathH = maxY - minY + 120;
  const scaleX = (vp.offsetWidth * 0.8)  / pathW;
  const scaleY = (vp.offsetHeight * 0.85) / pathH;
  zoom = Math.min(scaleX, scaleY, 1.4);

  // Center on path center (in canvas coords → offset applied in layoutDAG)
  const { nodes: ns } = treeData;
  const firstNode = ns['Q01'];
  const offsetX = PAD - Math.min(...Object.values(coords).map(c => c.x)) + PAD;
  const cx = (minX + maxX) / 2 + offsetX;
  const cy = (minY + maxY) / 2 + PAD;

  panX = vp.offsetWidth  / 2 - cx * zoom;
  panY = vp.offsetHeight / 2 - cy * zoom;
  applyTransform();
}


// ── Pan & Zoom ────────────────────────────────────────────────
function setupPanZoom() {
  const vp = $('tree-viewport');

  vp.addEventListener('wheel', e => {
    e.preventDefault();
    const delta  = e.deltaY > 0 ? -0.1 : 0.1;
    const newZ   = Math.max(0.15, Math.min(2.5, zoom + delta));
    // Zoom toward cursor
    const rect   = vp.getBoundingClientRect();
    const cx     = e.clientX - rect.left;
    const cy     = e.clientY - rect.top;
    panX = cx - (cx - panX) * (newZ / zoom);
    panY = cy - (cy - panY) * (newZ / zoom);
    zoom = newZ;
    applyTransform();
  }, { passive: false });

  vp.addEventListener('mousedown', e => {
    if (e.button !== 0) return;
    isDragging = true;
    dragStart  = { x: e.clientX, y: e.clientY };
    panStart   = { x: panX,      y: panY      };
    vp.classList.add('dragging');
  });

  window.addEventListener('mousemove', e => {
    if (!isDragging) return;
    panX = panStart.x + e.clientX - dragStart.x;
    panY = panStart.y + e.clientY - dragStart.y;
    applyTransform();
  });

  window.addEventListener('mouseup', () => {
    isDragging = false;
    $('tree-viewport').classList.remove('dragging');
  });
}

function applyTransform() {
  $('tree-wrapper').style.transform = `translate(${panX}px, ${panY}px) scale(${zoom})`;
  $('zoom-display').textContent = Math.round(zoom * 100) + '%';
}


// ── Toolbar ───────────────────────────────────────────────────
function setupToolbar() {
  $('btn-zoom-in').onclick  = () => { zoom = Math.min(zoom + 0.15, 2.5); applyTransform(); };
  $('btn-zoom-out').onclick = () => { zoom = Math.max(zoom - 0.15, 0.15); applyTransform(); };
  $('btn-fit-all').onclick  = fitAll;
  $('btn-fit-path').onclick = fitToPath;
  $('btn-highlight').onclick = () => {
    if (pathData) {
      applyPath(pathData);
    }
  };
  $('btn-clear-hl').onclick = clearPath;
}

function updatePathInfo(path) {
  const el = $('path-info');
  if (!el || !path) return;
  const n = path.node_ids.length;
  const e = path.edge_keys.length;
  el.innerHTML = `
    <span>Phiên chẩn đoán:</span>
    <span class="path-badge">${e} bước · ${n} node</span>
    ${path.primary_group ? `<span class="path-badge">${path.primary_group}</span>` : ''}
  `;
  // Show fit-path button only when there's a path
  $('btn-fit-path').style.display = 'inline-block';
}


// ── Helpers ───────────────────────────────────────────────────
function escHtml(s) {
  return String(s || '')
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
