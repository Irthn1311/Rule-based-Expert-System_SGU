"""
Timer Utility
Provides timing functionality for diagnosis sessions.
"""

import time


class DiagnosisTimer:
    """Timer to track diagnosis duration."""

    def __init__(self):
        self._start_time = None
        self._end_time = None

    def start(self):
        """Start the timer."""
        self._start_time = time.time()
        self._end_time = None

    def stop(self):
        """Stop the timer."""
        self._end_time = time.time()

    @property
    def elapsed(self):
        """Get elapsed time in seconds."""
        if self._start_time is None:
            return 0.0
        end = self._end_time if self._end_time else time.time()
        return round(end - self._start_time, 2)

    @property
    def start_time(self):
        """Get the start timestamp."""
        return self._start_time
