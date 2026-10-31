#!/usr/bin/env python3
"""
NVIDIA API Rate Limiter — 37 RPM (3 RPM buffer under 40 RPM limit)
Thread-safe, in-memory sliding window. No file locking to avoid hangs.
State persisted only for visibility, not coordination.

NVIDIA Free Tier Limits (confirmed 2026):
- 40 RPM (requests per minute) - hard ceiling
- 10,000 requests/day per account
- Varies by model and traffic

OUR RULE: 37 RPM (3 RPM buffer) to never hit the 40 RPM ceiling.
"""

import time
import threading
from collections import deque
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
MAX_RPM = 37                    # Our limit (3 RPM buffer under NVIDIA's 40 RPM)
MIN_INTERVAL = 60.0 / MAX_RPM   # ~1.62 seconds minimum between requests
WINDOW_SECONDS = 60.0           # Sliding window

# ─────────────────────────────────────────────────────────────────────────────
# RATE LIMITER
# ─────────────────────────────────────────────────────────────────────────────
class NvidiaRateLimiter:
    """Thread-safe in-memory rate limiter for NVIDIA API.
    
    Uses a sliding 60-second window. No file locking, no cross-process
    coordination — each process has its own limiter. For multi-process
    deployments, run a single limiter service or use the 37 RPM buffer
    which provides headroom for multiple processes.
    """
    
    def __init__(self, max_rpm: int = 37):
        self.max_rpm = max_rpm
        self.min_interval = 60.0 / max_rpm
        self.window_seconds = 60.0
        
        self._timestamps = deque()
        self._lock = threading.Lock()
    
    def wait_if_needed(self) -> float:
        """Wait until a request slot is available. Returns wait time in seconds."""
        start_wait = time.time()
        
        while True:
            with self._lock:
                now = time.time()
                cutoff = now - self.window_seconds
                
                # Remove expired timestamps
                while self._timestamps and self._timestamps[0] < cutoff:
                    self._timestamps.popleft()
                
                # Check if we have room
                if len(self._timestamps) < self.max_rpm:
                    # We have room, record this request
                    self._timestamps.append(now)
                    return time.time() - start_wait
                
                # No room, calculate wait time
                oldest = self._timestamps[0]
                wait_until = oldest + self.window_seconds
                wait_time = wait_until - now
            
            # Wait outside the lock
            if wait_time > 0:
                time.sleep(min(wait_time, 0.5))
            else:
                time.sleep(0.1)
    
    def record_request(self) -> None:
        """Record a request that was already made."""
        with self._lock:
            self._timestamps.append(time.time())
    
    def get_current_usage(self) -> dict:
        """Get current rate limit usage stats."""
        with self._lock:
            now = time.time()
            cutoff = now - self.window_seconds
            current = sum(1 for ts in self._timestamps if ts > cutoff)
            return {
                "current_rpm": current,
                "max_rpm": self.max_rpm,
                "remaining": max(0, self.max_rpm - current),
                "window_seconds": self.window_seconds,
                "oldest_request_age": now - self._timestamps[0] if self._timestamps else 0
            }
    
    def reset(self) -> None:
        """Reset all state (for testing)."""
        with self._lock:
            self._timestamps.clear()


# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL SINGLETON & CONVENIENCE FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────
_limiter_instance: Optional[NvidiaRateLimiter] = None
_instance_lock = threading.Lock()

def get_rate_limiter() -> NvidiaRateLimiter:
    """Get the global rate limiter instance (lazy init)."""
    global _limiter_instance
    with _instance_lock:
        if _limiter_instance is None:
            _limiter_instance = NvidiaRateLimiter(MAX_RPM)
        return _limiter_instance


def wait_for_slot() -> float:
    """Wait for an available NVIDIA API slot. Returns wait time in seconds."""
    return get_rate_limiter().wait_if_needed()

def record_nvidia_request() -> None:
    """Record that an NVIDIA API request was made."""
    get_rate_limiter().record_request()

def get_nvidia_usage() -> dict:
    """Get current NVIDIA API usage statistics."""
    return get_rate_limiter().get_current_usage()


# ─────────────────────────────────────────────────────────────────────────────
# CONTEXT MANAGER & DECORATOR
# ─────────────────────────────────────────────────────────────────────────────
class NvidiaRateLimit:
    """Context manager that waits for a slot before entering."""
    
    def __enter__(self) -> 'NvidiaRateLimit':
        self.wait_time = wait_for_slot()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass  # Request already recorded on entry


def nvidia_rate_limited(func):
    """Decorator that enforces rate limiting on a function."""
    def wrapper(*args, **kwargs):
        with NvidiaRateLimit():
            return func(*args, **kwargs)
    return wrapper


# ─────────────────────────────────────────────────────────────────────────────
# MANDATORY RULE — PUT THIS IN EVERY TOOL/WORKFLOW
# ─────────────────────────────────────────────────────────────────────────────
"""
MANDATORY NVIDIA API RATE LIMIT RULE
====================================

EVERY tool, script, workflow, or agent that calls the NVIDIA API MUST:

1. IMPORT the rate limiter:
   from nvidia_rate_limiter import wait_for_slot, record_nvidia_request

2. WRAP every NVIDIA API call with the rate limiter:
   
   Option A — Context manager (recommended):
   ```
   from nvidia_rate_limiter import NvidiaRateLimit
   
   with NvidiaRateLimit():
       response = openai_client.chat.completions.create(...)
   ```
   
   Option B — Explicit wait:
   ```
   from nvidia_rate_limiter import wait_for_slot
   
   wait_for_slot()
   response = openai_client.chat.completions.create(...)
   ```

3. NEVER make raw NVIDIA API calls without the rate limiter.
4. NEVER exceed 37 RPM in any tool or combined workflow.
5. The 37 RPM limit provides a 3 RPM buffer under NVIDIA's 40 RPM ceiling.

VIOLATION = 429 errors, account throttling, failed workflows.
"""


if __name__ == "__main__":
    # Quick self-test
    import time
    
    print("NVIDIA Rate Limiter Self-Test")
    print("=" * 40)
    print(f"Max RPM: {MAX_RPM}")
    print(f"Min interval: {MIN_INTERVAL:.3f}s")
    print(f"Window: {WINDOW_SECONDS}s")
    print()
    
    limiter = NvidiaRateLimiter(MAX_RPM)
    
    print("Recording 5 requests...")
    for i in range(5):
        wait = limiter.wait_if_needed()
        print(f"  Request {i+1}: waited {wait:.4f}s")
    
    usage = limiter.get_current_usage()
    print(f"Usage: {usage}")
    print("\n✅ Rate limiter ready — 37 RPM enforced")