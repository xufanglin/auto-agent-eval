"""Tests for auth.py after conflict resolution."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from auth import validate_password, hash_password, is_account_locked, MIN_PASSWORD_LENGTH, MAX_LOGIN_ATTEMPTS

def test_hash_password():
    h = hash_password("secret")
    assert len(h) == 64, f"Expected 64-char hex, got {len(h)}"
    assert h == hash_password("secret"), "Same password should produce same hash"

def test_validate_password_valid():
    # Must work with the resolved MIN_PASSWORD_LENGTH
    password = "A" * MIN_PASSWORD_LENGTH + "1!"
    valid, msg = validate_password(password)
    assert valid, f"Expected valid, got: {msg}"

def test_validate_password_too_short():
    password = "Ab1!" * 1  # definitely short
    valid, msg = validate_password(password)
    if len(password) < MIN_PASSWORD_LENGTH:
        assert not valid, "Short password should be invalid"

def test_is_account_locked_at_limit():
    # At exactly MAX_LOGIN_ATTEMPTS, should be locked
    assert is_account_locked(MAX_LOGIN_ATTEMPTS), \
        f"Should be locked at {MAX_LOGIN_ATTEMPTS} attempts"

def test_is_account_locked_below_limit():
    assert not is_account_locked(0), "0 attempts should not be locked"

def test_no_conflict_markers():
    content = open(__file__.replace("test_auth.py", "auth.py")).read()
    assert "<<<<<<" not in content, "Conflict markers still present"
    assert "=======" not in content, "Conflict markers still present"
    assert ">>>>>>>" not in content, "Conflict markers still present"

if __name__ == "__main__":
    tests = [
        test_hash_password,
        test_validate_password_valid,
        test_validate_password_too_short,
        test_is_account_locked_at_limit,
        test_is_account_locked_below_limit,
        test_no_conflict_markers,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"PASS  {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"FAIL  {t.__name__}: {e}")
    print(f"\n{passed}/{len(tests)} passed")
    sys.exit(0 if passed == len(tests) else 1)
