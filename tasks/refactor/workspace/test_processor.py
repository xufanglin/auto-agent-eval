import subprocess, sys, json

r = subprocess.run([sys.executable, "processor.py"], capture_output=True, text=True)
if r.returncode != 0:
    print(f"FAIL: crashed: {r.stderr[:200]}")
    sys.exit(1)

result = json.loads(r.stdout)
expected = [
    {"n": "x", "v": 30, "t": "premium_a"},
    {"n": "y", "v": 37.5, "t": "premium_b"},
    {"n": "z", "v": 5, "t": "basic_a"},
    {"n": "w", "v": 0, "t": "unknown"},
    {"n": "q", "v": 10, "t": "basic_b"},
]

if result != expected:
    print(f"FAIL: output mismatch")
    print(f"  got:      {result}")
    print(f"  expected: {expected}")
    sys.exit(1)

print("ALL PASS")
