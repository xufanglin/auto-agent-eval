import json, subprocess, sys

r = subprocess.run(
    [sys.executable, "stats.py", "test_data.csv"],
    capture_output=True, text=True,
)

if r.returncode != 0:
    print(f"FAIL: script crashed: {r.stderr[:200]}")
    sys.exit(1)

try:
    result = json.loads(r.stdout)
except json.JSONDecodeError:
    print(f"FAIL: invalid JSON output: {r.stdout[:200]}")
    sys.exit(1)

errors = []

if "age" not in result:
    errors.append("missing 'age' in result")
else:
    age = result["age"]
    if abs(age["mean"] - 31.666) > 1:
        errors.append(f"age mean wrong: {age['mean']}")
    if age["max"] != 40:
        errors.append(f"age max wrong: {age['max']}")

if "score" not in result:
    errors.append("missing 'score' in result")
else:
    sc = result["score"]
    if abs(sc["mean"] - 86.75) > 1:
        errors.append(f"score mean wrong: {sc['mean']}")

if "name" in result:
    errors.append("'name' should be excluded (non-numeric)")

if errors:
    for e in errors:
        print(f"FAIL: {e}")
    sys.exit(1)

print("ALL PASS")
