import re
import os
from typing import Dict
from application.interfaces.validation.address_validation_service import AddressValidationService
from application.dtos.validation_results import AddressValidationResult

ALLOWED_JURIS = [j.strip().lower() for j in os.getenv("ALLOWED_JURISDICTIONS", "San Rafael,Mendoza").split(",")]

class SimpleAddressValidationService(AddressValidationService):
    STREET_REGEX = re.compile(r"(?P<street>[A-Za-zÀ-ÿ'.\s]+)\s+(?P<number>\d+[A-Za-z0-9/-]*)", re.UNICODE)
    # Aceptar tanto "Ciudad, Provincia" como "Ciudad Provincia"
    CITY_PROV_REGEX = re.compile(r"(?P<city>[A-Za-zÀ-ÿ'.\s]+)[,\s]+(?P<province>[A-Za-zÀ-ÿ'.\s]+)", re.UNICODE)

    def validate_address(self, address_text: str, is_marital_address: bool = False) -> AddressValidationResult:
        if not address_text or len(address_text.strip()) < 5:
            return AddressValidationResult(False, ["Dirección vacía o demasiado corta"])
        text = address_text.strip()
        errors = []
        m1 = self.STREET_REGEX.search(text)
        m2 = self.CITY_PROV_REGEX.search(text)
        components: Dict[str, str] = {}
        if m1:
            components.update(m1.groupdict())
        else:
            errors.append("Falta calle y número (ej: 'San Martín 123')")
        if m2:
            components.update(m2.groupdict())
        else:
            errors.append("Falta ciudad y provincia (ej: 'San Rafael, Mendoza')")

        norm = None
        if components:
            norm = f"{components.get('street','').strip()} {components.get('number','').strip()}, {components.get('city','').strip()}, {components.get('province','').strip()}".strip(", ").replace("  "," ")

        if is_marital_address:
            city = components.get("city", "").lower()
            prov = components.get("province", "").lower()
            ok = any(j in city or j in prov for j in ALLOWED_JURIS)
            if not ok:
                errors.append("Domicilio conyugal fuera de jurisdicción (San Rafael/Mendoza).")

        return AddressValidationResult(len(errors) == 0, errors, normalized_address=norm, components=components if components else None)
