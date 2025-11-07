"""
Utilidades de infraestructura
"""
from .phone_utils import (
    normalize_whatsapp_phone,
    format_phone_for_display,
    format_phone_for_whatsapp,
    validate_phone_number,
    extract_country_code
)

__all__ = [
    'normalize_whatsapp_phone',
    'format_phone_for_display',
    'format_phone_for_whatsapp',
    'validate_phone_number',
    'extract_country_code',
]
