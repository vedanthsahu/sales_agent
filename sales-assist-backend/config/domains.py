from __future__ import annotations

from typing import Iterable, Set


GENERAL_DOMAIN = "general"
BASE_DOMAINS: Set[str] = {"rpa", "it", "hr", "security"}
ALLOWED_DOMAINS: Set[str] = set(BASE_DOMAINS) | {GENERAL_DOMAIN}


def is_valid_domain(domain: str | None) -> bool:
    if not domain:
        return False
    return domain in ALLOWED_DOMAINS


def is_ingest_domain(domain: str | None) -> bool:
    if not domain:
        return False
    return domain in BASE_DOMAINS


def is_general_domain(domain: str | None) -> bool:
    return domain == GENERAL_DOMAIN


def list_domains(include_general: bool = True) -> Iterable[str]:
    return sorted(ALLOWED_DOMAINS if include_general else BASE_DOMAINS)
