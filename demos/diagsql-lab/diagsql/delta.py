from __future__ import annotations

from typing import Callable, Sequence


def ddmin(items: Sequence[str], fails: Callable[[tuple[str, ...]], bool]) -> tuple[str, ...]:
    current = tuple(items)
    if not fails(current):
        raise ValueError("full input does not fail")
    n = 2
    while len(current) >= 2:
        chunk_size = (len(current) + n - 1) // n
        spans = [(i, min(i + chunk_size, len(current))) for i in range(0, len(current), chunk_size)]
        reduced = False
        for start, end in spans:
            complement = current[:start] + current[end:]
            if complement and fails(complement):
                current = complement
                n = max(n - 1, 2)
                reduced = True
                break
        if reduced:
            continue
        if n >= len(current):
            break
        n = min(len(current), n * 2)
    return current
