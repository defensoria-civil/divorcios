from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class AddressValidationResult:
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    normalized_address: Optional[str] = None
    components: Optional[Dict[str, Any]] = None

@dataclass
class DateValidationResult:
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    normalized_date: Optional[str] = None
    age_years: Optional[int] = None

@dataclass
class ResponseValidationResult:
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    flags: List[str] = field(default_factory=list)
