# ─────────────────────────────────────────────────────────────
# IMPORTS
# ─────────────────────────────────────────────────────────────

from typing import Callable, Any, Dict, Tuple, Optional
# Callable  → a type hint meaning "something you can call like a function"
# Any       → "any type at all" (no restriction)
# Dict      → dictionary type hint: Dict[key_type, value_type]
# Tuple     → tuple type hint (immutable ordered collection)
# Optional  → means "either this type OR None" → Optional[Any] == Any | None

from functools import wraps
# wraps → a helper that copies metadata (name, docstring) from the original
# function onto the wrapper. Without it, expensive_computation.__name__
# would become "wrapper", which breaks debugging and introspection.

import time
# time → for time.time() (current Unix timestamp in seconds) and time.sleep()


# ─────────────────────────────────────────────────────────────
# CACHE CLASS — a simple in-memory key/value store with expiry
# ─────────────────────────────────────────────────────────────

class Cache:
    """Centralized cache. Think of it as a tiny dictionary with an alarm clock."""

    def __init__(self, ttl: int = 300):
        # ttl = "time to live" → how many seconds a cached value stays valid.
        # Default 300s = 5 minutes. Anything older than this is "stale" and thrown out.
        self.ttl = ttl

        # The actual storage. Structure:
        #   key   → some Tuple (like ("expensive_computation", (5, 10), ()))
        #   value → (cached_result, timestamp_when_stored)
        #
        # We store the timestamp ALONGSIDE the value so we can check age later.
        # Why a Dict? O(1) lookup. Fast as hell for "did we already compute this?"
        self._cache: Dict[Tuple, Tuple[Any, float]] = {}

    def get(self, key: Tuple) -> Optional[Any]:
        """Return cached value if it exists AND is fresh. Otherwise None."""

        # Step 1: Is the key even in the cache?
        if key in self._cache:
            # Step 2: Unpack the stored tuple → (value, timestamp)
            value, timestamp = self._cache[key]

            # Step 3: Is it still fresh? (now - stored_time) < ttl?
            if time.time() - timestamp < self.ttl:
                return value          # ✅ Fresh → return it
            else:
                # ❌ Too old → delete it so it doesn't waste memory
                del self._cache[key]

        # If key not found OR expired → return None (means "cache miss")
        return None

    def set(self, key: Tuple, value: Any) -> None:
        """Store value under key, stamped with the CURRENT time."""
        # We snapshot time.time() NOW so that later get() can measure age.
        self._cache[key] = (value, time.time())

    def clear(self) -> None:
        """Nuke everything. Useful for tests or forced refresh."""
        self._cache.clear()


# ─────────────────────────────────────────────────────────────
# GLOBAL CACHE INSTANCE
# ─────────────────────────────────────────────────────────────
# One shared cache for the whole program. Every function decorated with
# @cached will read/write this SAME dictionary. ttl=60 → values live 60s.
cache = Cache(ttl=60)


# ─────────────────────────────────────────────────────────────
# THE DECORATOR — wraps any function to add caching for free
# ─────────────────────────────────────────────────────────────

def cached(func: Callable) -> Callable:
    """
    Decorator: wraps `func` so its result is cached by (name, args, kwargs).

    Usage:
        @cached
        def slow_thing(x): ...

    Then `slow_thing(5)` will only actually run the body ONCE per unique args
    within the TTL window. After that, it returns the saved result instantly.
    """

    @wraps(func)   # preserves func's __name__, __doc__, etc. on `wrapper`
    def wrapper(*args, **kwargs):
        # *args   → captures all positional args as a tuple, e.g. (5, 10)
        # **kwargs → captures all keyword args as a dict, e.g. {"y": 10}

        # Build a UNIQUE cache key from:
        #   1. Function name (so two different functions don't collide)
        #   2. Positional args
        #   3. Keyword args, SORTED so order doesn't matter
        #      e.g. f(a=1, b=2) and f(b=2, a=1) produce the SAME key
        cache_key = (func.__name__, args, tuple(sorted(kwargs.items())))

        # ─── CACHE LOOKUP ───
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            print(f"Cache hit for {func.__name__}{args}")
            return cached_result   # ⚡ FAST PATH — no computation

        # ─── CACHE MISS → actually run the function ───
        print(f"Cache miss for {func.__name__}{args}")
        result = func(*args, **kwargs)   # call original function

        # ─── STORE FOR NEXT TIME ───
        cache.set(cache_key, result)

        return result

    return wrapper   # decorator returns the wrapper — this replaces the original


# ─────────────────────────────────────────────────────────────
# USAGE EXAMPLE
# ─────────────────────────────────────────────────────────────

@cached
def expensive_computation(x: int, y: int) -> int:
    """Simulate expensive computation."""
    time.sleep(2)   # pretend we're calling a slow API or doing heavy math
    return x + y


# First call → cache MISS → sleeps 2 seconds → returns 15
result = expensive_computation(5, 10)
print(result)   # 15

# Second call → cache HIT → returns instantly → 15
result = expensive_computation(5, 10)
print(result)   # 15