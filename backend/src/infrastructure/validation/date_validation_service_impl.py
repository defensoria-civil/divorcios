from datetime import datetime, date
from application.interfaces.validation.date_validation_service import DateValidationService
from application.dtos.validation_results import DateValidationResult

DATE_FMT = "%d/%m/%Y"

def parse_date(date_str: str) -> date | None:
    try:
        return datetime.strptime(date_str.strip(), DATE_FMT).date()
    except Exception:
        return None

def years_between(a: date, b: date) -> int:
    return b.year - a.year - ((b.month, b.day) < (a.month, a.day))

class SimpleDateValidationService(DateValidationService):
    def validate_birth_date(self, date_str: str) -> DateValidationResult:
        d = parse_date(date_str)
        errors = []
        if not d:
            errors.append("Formato de fecha inválido. Use DD/MM/AAAA.")
            return DateValidationResult(False, errors)
        today = date.today()
        if d > today:
            errors.append("La fecha no puede ser futura.")
        if d.year < 1900:
            errors.append("La fecha es demasiado antigua.")
        age = years_between(d, today)
        if age < 18:
            errors.append("Debe ser mayor de 18 años.")
        return DateValidationResult(len(errors) == 0, errors, normalized_date=d.strftime(DATE_FMT), age_years=age)

    def validate_marriage_date(self, date_str: str, birth_date_solicitante: str, birth_date_conyuge: str) -> DateValidationResult:
        d = parse_date(date_str)
        errors = []
        if not d:
            errors.append("Formato de fecha inválido. Use DD/MM/AAAA.")
            return DateValidationResult(False, errors)
        today = date.today()
        if d > today:
            errors.append("La fecha de matrimonio no puede ser futura.")
        b1 = parse_date(birth_date_solicitante)
        b2 = parse_date(birth_date_conyuge)
        if not b1 or not b2:
            errors.append("Fechas de nacimiento inválidas.")
            return DateValidationResult(False, errors)
        if d <= b1 or d <= b2:
            errors.append("La fecha de matrimonio debe ser posterior a las fechas de nacimiento.")
        if years_between(b1, d) < 18 or years_between(b2, d) < 18:
            errors.append("Ambas partes deben tener al menos 18 años al casarse.")
        return DateValidationResult(len(errors) == 0, errors, normalized_date=d.strftime(DATE_FMT))

    def validate_separation_date(self, date_str: str, marriage_date: str) -> DateValidationResult:
        d = parse_date(date_str)
        errors = []
        if not d:
            errors.append("Formato de fecha inválido. Use DD/MM/AAAA.")
            return DateValidationResult(False, errors)
        m = parse_date(marriage_date)
        if not m:
            errors.append("Fecha de matrimonio inválida.")
            return DateValidationResult(False, errors)
        today = date.today()
        if d > today:
            errors.append("La fecha de separación no puede ser futura.")
        if d < m:
            errors.append("La fecha de separación debe ser posterior a la fecha de matrimonio.")
        return DateValidationResult(len(errors) == 0, errors, normalized_date=d.strftime(DATE_FMT))
