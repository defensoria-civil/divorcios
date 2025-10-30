from infrastructure.validation.date_validation_service_impl import SimpleDateValidationService

svc = SimpleDateValidationService()

def test_birth_date_valid():
    res = svc.validate_birth_date("01/01/1990")
    assert res.is_valid

def test_birth_date_underage():
    res = svc.validate_birth_date("01/01/2010")
    assert not res.is_valid
    assert any("18" in e for e in res.errors)

def test_marriage_sequence():
    res = svc.validate_marriage_date("01/01/2010", "01/01/1980", "01/01/1981")
    assert res.is_valid

def test_separation_after_marriage():
    res = svc.validate_separation_date("01/01/2015", "01/01/2010")
    assert res.is_valid
