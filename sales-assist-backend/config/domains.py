from __future__ import annotations

from typing import Iterable, Set


ALLOWED_DOMAINS: Set[str] = {"rpa", "it", "hr", "security"}


def is_valid_domain(domain: str | None) -> bool:
    if not domain:
        return False
    return domain in ALLOWED_DOMAINS


def list_domains() -> Iterable[str]:
    return sorted(ALLOWED_DOMAINS)
