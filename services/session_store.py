"""
Session Store — Lưu trữ phiên chẩn đoán in-memory.

Features:
  - Dict-based storage (key: session_id UUID)
  - TTL: 30 phút không hoạt động → tự xóa
  - Thread-safe bằng threading.Lock
  - Cleanup thread chạy mỗi 5 phút
"""

from __future__ import annotations
import uuid
import threading
from datetime import datetime, timedelta
from typing import Optional

from engine.diagnostic_session import DiagnosticSession, KnowledgeBaseLoader


SESSION_TTL_MINUTES = 30
CLEANUP_INTERVAL_SECONDS = 300  # 5 phút


class ExtendedSession:
    """
    Wrapper bao quanh DiagnosticSession với metadata cho web.
    """

    def __init__(self, session_id: str, diagnostic_session: DiagnosticSession):
        self.session_id = session_id
        self.ds = diagnostic_session
        self.created_at = datetime.now()
        self.last_activity = datetime.now()

    def touch(self):
        """Cập nhật thời gian hoạt động cuối."""
        self.last_activity = datetime.now()

    def is_expired(self, ttl_minutes: int = SESSION_TTL_MINUTES) -> bool:
        """Kiểm tra session có hết hạn chưa."""
        return (datetime.now() - self.last_activity) > timedelta(minutes=ttl_minutes)

    @property
    def age_seconds(self) -> float:
        return (datetime.now() - self.created_at).total_seconds()


class SessionStore:
    """
    In-memory session store với TTL cleanup.
    Thread-safe.
    """

    def __init__(self, kb: KnowledgeBaseLoader, ttl_minutes: int = SESSION_TTL_MINUTES):
        self._kb = kb
        self._sessions: dict[str, ExtendedSession] = {}
        self._lock = threading.Lock()
        self._ttl = ttl_minutes

        # Start cleanup thread
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True,
            name="SessionCleanup"
        )
        self._cleanup_thread.start()

    def create(self) -> ExtendedSession:
        """Tạo session mới. Return ExtendedSession."""
        session_id = str(uuid.uuid4())
        ds = self._kb.create_session()
        ext = ExtendedSession(session_id, ds)

        with self._lock:
            self._sessions[session_id] = ext

        return ext

    def get(self, session_id: str) -> Optional[ExtendedSession]:
        """Lấy session và cập nhật last_activity. Return None nếu không tìm thấy."""
        with self._lock:
            ext = self._sessions.get(session_id)
            if ext and not ext.is_expired(self._ttl):
                ext.touch()
                return ext
            elif ext:
                # Expired
                del self._sessions[session_id]
                return None
            return None

    def delete(self, session_id: str) -> bool:
        """Xóa session. Return True nếu xóa thành công."""
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False

    def count(self) -> int:
        """Số session đang active."""
        with self._lock:
            return len(self._sessions)

    def stats(self) -> dict:
        """Thống kê sessions."""
        with self._lock:
            sessions = list(self._sessions.values())
        return {
            "active_sessions": len(sessions),
            "completed": sum(1 for s in sessions if s.ds.is_complete),
            "in_progress": sum(1 for s in sessions if not s.ds.is_complete),
        }

    def _cleanup_loop(self):
        """Background thread: dọn session hết hạn mỗi CLEANUP_INTERVAL_SECONDS."""
        import time
        while True:
            time.sleep(CLEANUP_INTERVAL_SECONDS)
            self._cleanup_expired()

    def _cleanup_expired(self):
        """Xóa tất cả sessions đã hết hạn."""
        with self._lock:
            expired = [
                sid for sid, s in self._sessions.items()
                if s.is_expired(self._ttl)
            ]
            for sid in expired:
                del self._sessions[sid]
