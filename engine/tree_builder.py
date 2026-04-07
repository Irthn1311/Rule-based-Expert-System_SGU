"""
tree_builder.py — Build Decision Tree DAG từ Knowledge Base JSON.

Thiết kế: Top→Down, Merge shared nodes (DAG, không duplicate).
Output: nodes dict + edges list + levels + stats
"""

from collections import defaultdict, deque
from typing import Optional


GROUP_ORDER = [
    'power_startup', 'display', 'os_boot', 'network',
    'audio_camera', 'peripherals', 'performance', 'storage', ''
]


class DecisionTreeBuilder:
    def __init__(self, questions_data: list[dict], diagnoses_data: list[dict]):
        self._q_map = {q['id']: q for q in questions_data}
        self._d_map = {d['id']: d for d in diagnoses_data}
        self._cache: Optional[dict] = None

    def build_dag(self) -> dict:
        """Build DAG từ Q01 bằng BFS. Merge shared nodes."""
        if self._cache:
            return self._cache

        nodes: dict = {}
        edges: list = []
        edge_set: set = set()
        node_level: dict = {}
        visited: set = set()

        queue = deque([('Q01', 0)])

        while queue:
            nid, level = queue.popleft()

            # Merge: update level nếu tìm thấy đường ngắn hơn
            if nid in visited:
                if node_level.get(nid, 999) > level:
                    node_level[nid] = level
                    if nid in nodes:
                        nodes[nid]['level'] = level
                continue

            visited.add(nid)
            node_level[nid] = level

            if nid not in self._q_map:
                continue

            q = self._q_map[nid]
            q_group = q.get('group', '')

            nodes[nid] = {
                'id': nid,
                'type': 'question',
                'text': q['text'],
                'purpose': q.get('purpose', ''),
                'q_type': q.get('type', 'single_choice'),
                'group': q_group,
                'level': level,
            }

            for opt in q.get('options', []):
                val = opt.get('value', '')
                if val == 'SUBMIT':
                    continue

                lbl = opt.get('label', '')
                if len(lbl) > 48:
                    lbl = lbl[:45] + '…'

                edge_group = opt.get('sets_group', q_group)

                # → Next question
                nxt = opt.get('next')
                if nxt:
                    ek = (nid, nxt, val)
                    if ek not in edge_set:
                        edge_set.add(ek)
                        edges.append({
                            'from': nid, 'to': nxt,
                            'label': lbl, 'value': val,
                            'adds_facts': opt.get('adds_facts', []),
                            'group': edge_group,
                            'is_terminal': False,
                        })
                    queue.append((nxt, level + 1))

                # → Diagnosis leaf
                did = opt.get('triggers_diagnosis')
                if did:
                    d_lv = max(node_level.get(did, level + 1), level + 1)
                    node_level[did] = d_lv
                    visited.discard(did)  # allow level update

                    if did not in nodes:
                        d = self._d_map.get(did, {})
                        nodes[did] = {
                            'id': did,
                            'type': 'diagnosis',
                            'name': d.get('name', did),
                            'severity': d.get('severity', 'UNKNOWN'),
                            'default_cf': d.get('default_cf', 0.8),
                            'user_fixable': d.get('user_fixable', True),
                            'needs_technician': d.get('needs_technician', False),
                            'group': edge_group or q_group,
                            'level': d_lv,
                        }
                    else:
                        nodes[did]['level'] = d_lv
                        if not nodes[did].get('group'):
                            nodes[did]['group'] = edge_group or q_group

                    ek = (nid, did, val)
                    if ek not in edge_set:
                        edge_set.add(ek)
                        edges.append({
                            'from': nid, 'to': did,
                            'label': lbl, 'value': val,
                            'adds_facts': opt.get('adds_facts', []),
                            'group': edge_group or q_group,
                            'is_terminal': True,
                        })

        # Propagate group từ Q01's options xuống subtree
        self._propagate_groups(nodes, edges)

        # Sync level vào nodes
        for nid, lv in node_level.items():
            if nid in nodes:
                nodes[nid]['level'] = lv

        max_lv = max(node_level.values()) if node_level else 0

        result = {
            'nodes': nodes,
            'edges': edges,
            'root': 'Q01',
            'max_level': max_lv,
            'stats': {
                'total_nodes': len(nodes),
                'question_nodes': sum(1 for n in nodes.values() if n['type'] == 'question'),
                'diagnosis_nodes': sum(1 for n in nodes.values() if n['type'] == 'diagnosis'),
                'total_edges': len(edges),
            }
        }
        self._cache = result
        return result

    def _propagate_groups(self, nodes: dict, edges: list):
        """BFS từ mỗi Q01 option → gán group cho toàn bộ subtree."""
        q01 = self._q_map.get('Q01', {})
        edge_map = defaultdict(list)  # from → [to]
        for e in edges:
            edge_map[e['from']].append(e['to'])

        for opt in q01.get('options', []):
            grp = opt.get('sets_group', '')
            nxt = opt.get('next', '')
            if not grp or not nxt:
                continue
            bq = deque([nxt])
            bvisited = set()
            while bq:
                bid = bq.popleft()
                if bid in bvisited or bid not in nodes:
                    continue
                bvisited.add(bid)
                if not nodes[bid].get('group'):
                    nodes[bid]['group'] = grp
                for child in edge_map.get(bid, []):
                    bq.append(child)

    def get_session_path(self, session) -> dict:
        """
        Trích xuất path của session → {node_ids, edge_keys, primary_group}.
        edge_keys format: "FROM_QID:OPTION_VALUE"  (e.g. "Q03:A")
        """
        node_ids: set = {'Q01'}
        edge_keys: set = set()
        primary_group: Optional[str] = None

        for entry in getattr(session, 'history', []):
            qid = entry.get('question_id', '')
            answers = entry.get('answers', [])
            if not qid:
                continue

            node_ids.add(qid)

            q = session.flow._questions.get(qid, {})
            for val in answers:
                if val == 'SUBMIT':
                    continue
                edge_keys.add(f'{qid}:{val}')

                for opt in q.get('options', []):
                    if opt.get('value') == val:
                        nxt = opt.get('next')
                        did = opt.get('triggers_diagnosis')
                        if nxt:
                            node_ids.add(nxt)
                        if did:
                            node_ids.add(did)
                        # Detect primary group from Q01 answer
                        if qid == 'Q01':
                            primary_group = opt.get('sets_group')
                        break

        # Final diagnoses
        for d in getattr(session, 'final_diagnoses', []):
            did = d.get('id')
            if did:
                node_ids.add(did)

        return {
            'node_ids': list(node_ids),
            'edge_keys': list(edge_keys),
            'primary_group': primary_group,
        }
