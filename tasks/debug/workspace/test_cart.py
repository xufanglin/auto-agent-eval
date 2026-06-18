"""Tests for cart.py — all should pass after bugs are fixed."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from cart import calculate_discount, apply_tax, cart_total, most_expensive

def test_calculate_discount():
    # 20% discount on $100 -> $80
    assert abs(calculate_discount(100, 20) - 80.0) < 0.01, \
        f"Expected 80.0, got {calculate_discount(100, 20)}"

def test_apply_tax():
    # 10% tax on $100 -> $110
    assert abs(apply_tax(100) - 110.0) < 0.01, \
        f"Expected 110.0, got {apply_tax(100)}"

def test_cart_total_includes_tax():
    items = [{"name": "Apple", "price": 100, "quantity": 2, "discount_percent": 0}]
    # 2 * $100 = $200, plus 10% tax = $220
    total = cart_total(items)
    assert abs(total - 220.0) < 0.01, f"Expected 220.0, got {total}"

def test_cart_total_with_discount():
    items = [{"name": "Laptop", "price": 1000, "quantity": 1, "discount_percent": 10}]
    # $1000 - 10% = $900, plus 10% tax = $990
    total = cart_total(items)
    assert abs(total - 990.0) < 0.01, f"Expected 990.0, got {total}"

def test_most_expensive_empty():
    # Should not raise, should return None or empty string
    result = most_expensive([])
    assert result is None or result == "", f"Expected None or '', got {result!r}"

if __name__ == "__main__":
    tests = [
        test_calculate_discount,
        test_apply_tax,
        test_cart_total_includes_tax,
        test_cart_total_with_discount,
        test_most_expensive_empty,
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
