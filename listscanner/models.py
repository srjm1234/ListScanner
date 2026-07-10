from dataclasses import dataclass


@dataclass
class ScanResult:
    path: str
    url: str
    status_code: int
    size: int
    content_type: str
    risk_type: str
    risk_level: str


@dataclass
class ScanStats:
    total: int = 0
    found: int = 0
    not_found: int = 0
    errors: int = 0
