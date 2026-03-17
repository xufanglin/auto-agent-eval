#!/usr/bin/env python3
"""Smart mock: applies known-correct fixes to workspace files.

Usage: python3 smart_mock.py <workspace_path>

Used by the 'script' agent type to verify the eval pipeline end-to-end.
"""

import sys
from pathlib import Path


def fix_django_11099(ws: Path) -> bool:
    f = ws / "validators.py"
    if not f.exists() or "host_re" not in f.read_text():
        return False
    code = f.read_text().replace(
        '        r"|localhost"\n        r")"',
        '        r"|localhost"\n        r"|\\[[.0-9a-fA-F:]+\\]"\n        r")"',
    )
    f.write_text(code)
    return True


def fix_csv_stats(ws: Path) -> bool:
    f = ws / "stats.py"
    if not f.exists():
        return False
    f.write_text(
        'import csv\n\n'
        'def calculate_stats(filepath):\n'
        '    with open(filepath) as f:\n'
        '        rows = list(csv.DictReader(f))\n'
        '    stats = {}\n'
        '    for col in rows[0].keys():\n'
        '        values = []\n'
        '        for row in rows:\n'
        '            try: values.append(float(row[col]))\n'
        '            except (ValueError, TypeError): continue\n'
        '        if values:\n'
        '            stats[col] = {"mean": sum(values)/len(values), "max": max(values), "min": min(values)}\n'
        '    return stats\n\n'
        'if __name__ == "__main__":\n'
        '    import json, sys\n'
        '    print(json.dumps(calculate_stats(sys.argv[1]), indent=2))\n'
    )
    return True


def fix_wordfreq(ws: Path) -> bool:
    if not (ws / "sample.txt").exists():
        return False
    (ws / "wordfreq.py").write_text(
        'import argparse, json, re\nfrom collections import Counter\n\n'
        'def count_words(path, top=10):\n'
        '    words = re.findall(r"[a-z]+", open(path).read().lower())\n'
        '    return Counter(words).most_common(top)\n\n'
        'if __name__ == "__main__":\n'
        '    p = argparse.ArgumentParser()\n'
        '    p.add_argument("file")\n'
        '    p.add_argument("--top", type=int, default=10)\n'
        '    p.add_argument("--json", action="store_true", dest="as_json")\n'
        '    a = p.parse_args()\n'
        '    c = count_words(a.file, a.top)\n'
        '    if a.as_json: print(json.dumps(dict(c)))\n'
        '    else:\n'
        '        for w, n in c: print(f"{w}: {n}")\n'
    )
    return True


def fix_refactor(ws: Path) -> bool:
    f = ws / "processor.py"
    if not f.exists():
        return False
    f.write_text(
        '"""Data processor: classifies items by type and value."""\n\n'
        'import json\nfrom typing import Any\n\n'
        'def classify_item(item: dict[str, Any]) -> dict[str, Any]:\n'
        '    """Classify a single item based on type and value threshold."""\n'
        '    name, item_type, value = item["name"], item["type"], item["val"]\n'
        '    if item_type == "A":\n'
        '        return {"n": name, "v": value * 2, "t": "premium_a"} if value > 10 else {"n": name, "v": value, "t": "basic_a"}\n'
        '    if item_type == "B":\n'
        '        return {"n": name, "v": value * 1.5, "t": "premium_b"} if value > 20 else {"n": name, "v": value, "t": "basic_b"}\n'
        '    return {"n": name, "v": 0, "t": "unknown"}\n\n'
        'def process_items(data: list[dict[str, Any]]) -> list[dict[str, Any]]:\n'
        '    """Process a list of items."""\n'
        '    return [classify_item(item) for item in data]\n\n'
        'def main() -> None:\n'
        '    data = [{"name":"x","type":"A","val":15},{"name":"y","type":"B","val":25},\n'
        '            {"name":"z","type":"A","val":5},{"name":"w","type":"C","val":10},\n'
        '            {"name":"q","type":"B","val":10}]\n'
        '    print(json.dumps(process_items(data)))\n\n'
        'if __name__ == "__main__":\n    main()\n'
    )
    return True


def fix_sales_report(ws: Path) -> bool:
    if not (ws / "sales_data.csv").exists():
        return False
    (ws / "report.md").write_text(
        "# Q1 Sales Report\n\n"
        "## Executive Summary\n"
        "Total revenue: $112,300 across 3 products. Widget C is the top performer with $50,300.\n\n"
        "## Monthly Revenue Trend\n"
        "- January: $35,500\n- February: $37,500\n- March: $39,300\n\n"
        "## Product Comparison\n"
        "| Product | Revenue | Units |\n|---------|---------|-------|\n"
        "| Widget A | $36,500 | 460 |\n| Widget B | $25,500 | 600 |\n| Widget C | $50,300 | 330 |\n\n"
        "## Regional Breakdown\n"
        "- North: $75,800 (67.5%)\n- South: $36,500 (32.5%)\n\n"
        "## Recommendations\n"
        "1. Expand Widget C to South region\n"
        "2. Investigate Widget B pricing strategy\n"
        "3. Increase Q2 marketing spend\n"
    )
    return True


FIXES = [fix_django_11099, fix_csv_stats, fix_wordfreq, fix_refactor, fix_sales_report]


def main():
    ws = Path(sys.argv[1])
    for fix in FIXES:
        if fix(ws):
            print(f"Applied: {fix.__name__}")
            return
    print("No matching fix found")


if __name__ == "__main__":
    main()
