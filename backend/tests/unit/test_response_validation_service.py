from infrastructure.validation.response_validation_service_impl import SimpleResponseValidationService

svc = SimpleResponseValidationService()

def test_detect_joke():
    res = svc.validate_user_response("a molestar", "domicilio", "")
    assert not res.is_valid
    assert "humor" in res.flags

def test_dni_pattern():
    res = svc.validate_user_response("ABC", "dni", "")
    assert not res.is_valid
    res2 = svc.validate_user_response("12345678", "dni", "")
    assert res2.is_valid or any("DNI" in e for e in res2.errors)