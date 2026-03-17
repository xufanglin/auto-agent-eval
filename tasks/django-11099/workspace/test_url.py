import sys
sys.path.insert(0, ".")
from validators import URLValidator, ValidationError

validator = URLValidator()
results = []

valid_urls = [
    "http://localhost/",
    "http://example.com/",
    "https://example.com:8080/path",
    "http://[::ffff:127.0.0.1]/",
    "http://[2001:db8::1]/",
    "http://[::1]:8080/path?q=1",
]

invalid_urls = [
    "not-a-url",
    "http://",
    "://missing-scheme.com",
]

print("=== Valid URL tests ===")
for url in valid_urls:
    try:
        validator(url)
        print(f"  PASS: {url}")
        results.append(True)
    except ValidationError:
        print(f"  FAIL: {url} (should be valid)")
        results.append(False)

print("\n=== Invalid URL tests ===")
for url in invalid_urls:
    try:
        validator(url)
        print(f"  FAIL: {url} (should be invalid)")
        results.append(False)
    except ValidationError:
        print(f"  PASS: {url}")
        results.append(True)

passed = sum(results)
total = len(results)
print(f"\n=== Result: {passed}/{total} passed ===")
sys.exit(0 if all(results) else 1)
