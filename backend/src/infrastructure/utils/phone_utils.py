"""
Utilidades para normalización y formato de números de teléfono de WhatsApp
"""
import re
from typing import Optional

def normalize_whatsapp_phone(whatsapp_id: str) -> str:
    """
    Normaliza un ID de WhatsApp a un número de teléfono limpio.
    
    Args:
        whatsapp_id: ID de WhatsApp en formato "261082623000696@lid" o similar
        
    Returns:
        Número de teléfono limpio sin el sufijo @lid o @c.us
        
    Examples:
        >>> normalize_whatsapp_phone("261082623000696@lid")
        "261082623000696"
        >>> normalize_whatsapp_phone("549261234567@c.us")
        "549261234567"
    """
    if not whatsapp_id:
        return ""
    
    # Remover sufijos comunes de WhatsApp
    phone = whatsapp_id.split('@')[0]
    
    # Limpiar caracteres no numéricos (excepto +)
    phone = re.sub(r'[^\d+]', '', phone)
    
    return phone


def format_phone_for_display(phone: str) -> str:
    """
    Formatea un número de teléfono para visualización en la UI.
    
    Args:
        phone: Número de teléfono (puede incluir @lid)
        
    Returns:
        Número formateado para visualización
        
    Examples:
        >>> format_phone_for_display("261082623000696@lid")
        "+26 108 2623000696"
        >>> format_phone_for_display("5492611234567")
        "+54 9 261 1234567"
    """
    clean_phone = normalize_whatsapp_phone(phone)
    
    if not clean_phone:
        return "No disponible"
    
    # Si es muy largo (15+ dígitos), probablemente tenga información duplicada
    if len(clean_phone) >= 15:
        # Intentar formatear como número internacional genérico
        return f"+{clean_phone[:2]} {clean_phone[2:5]} {clean_phone[5:]}"
    
    # Si tiene entre 11-14 dígitos, formato internacional estándar
    if len(clean_phone) >= 11:
        # Formato: +CC AAA NNNNNNN
        return f"+{clean_phone[:2]} {clean_phone[2:5]} {clean_phone[5:]}"
    
    # Si tiene menos de 11 dígitos, formato local
    if len(clean_phone) >= 8:
        # Formato local argentino: AAA NNNN-NNNN
        if len(clean_phone) == 10:
            return f"{clean_phone[:3]} {clean_phone[3:7]}-{clean_phone[7:]}"
        return clean_phone[:3] + " " + clean_phone[3:]
    
    return clean_phone


def format_phone_for_whatsapp(phone: str) -> str:
    """
    Formatea un número para usarlo en enlaces de WhatsApp (wa.me).
    
    Args:
        phone: Número de teléfono
        
    Returns:
        Número en formato internacional sin + ni espacios
        
    Examples:
        >>> format_phone_for_whatsapp("261082623000696@lid")
        "261082623000696"
        >>> format_phone_for_whatsapp("+54 9 261 1234567")
        "5492611234567"
    """
    clean_phone = normalize_whatsapp_phone(phone)
    
    # Remover el + inicial si existe
    if clean_phone.startswith('+'):
        clean_phone = clean_phone[1:]
    
    return clean_phone


def validate_phone_number(phone: str) -> tuple[bool, Optional[str]]:
    """
    Valida si un número de teléfono es potencialmente válido.
    
    Args:
        phone: Número de teléfono a validar
        
    Returns:
        Tupla (es_válido, mensaje_error)
        
    Examples:
        >>> validate_phone_number("261082623000696@lid")
        (True, None)
        >>> validate_phone_number("123")
        (False, "Número demasiado corto")
    """
    clean_phone = normalize_whatsapp_phone(phone)
    
    if not clean_phone:
        return False, "Número vacío"
    
    # Un número de teléfono internacional válido tiene al menos 8 dígitos
    if len(clean_phone) < 8:
        return False, "Número demasiado corto"
    
    # Máximo razonable: 15 dígitos (estándar E.164)
    # Pero permitimos hasta 20 por si hay información adicional
    if len(clean_phone) > 20:
        return False, "Número demasiado largo"
    
    # Solo debe contener dígitos (y opcionalmente + al inicio)
    if not re.match(r'^\+?\d+$', clean_phone):
        return False, "Formato inválido"
    
    return True, None


def extract_country_code(phone: str) -> Optional[str]:
    """
    Intenta extraer el código de país de un número.
    
    Args:
        phone: Número de teléfono
        
    Returns:
        Código de país o None si no se puede determinar
        
    Examples:
        >>> extract_country_code("5492611234567")
        "54"  # Argentina
        >>> extract_country_code("12025551234")
        "1"   # USA/Canadá
    """
    clean_phone = normalize_whatsapp_phone(phone)
    
    # Códigos de país comunes (1-3 dígitos)
    # Argentina: 54
    # USA/Canadá: 1
    # México: 52
    # Chile: 56
    # Brasil: 55
    
    if clean_phone.startswith('54'):
        return '54'
    elif clean_phone.startswith('52'):
        return '52'
    elif clean_phone.startswith('55'):
        return '55'
    elif clean_phone.startswith('56'):
        return '56'
    elif clean_phone.startswith('1'):
        return '1'
    
    # Para otros códigos, asumir 2-3 dígitos
    if len(clean_phone) >= 2:
        return clean_phone[:2]
    
    return None
