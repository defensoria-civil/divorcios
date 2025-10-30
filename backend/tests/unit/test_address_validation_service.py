from infrastructure.validation.address_validation_service_impl import SimpleAddressValidationService

svc = SimpleAddressValidationService()

def test_address_ok():
    res = svc.validate_address("San Martín 123, San Rafael, Mendoza")
    assert res.is_valid
    assert res.normalized_address

def test_address_missing_parts():
    res = svc.validate_address("San Martín")
    assert not res.is_valid
