import csv


def calculate_stats(filepath):
    """Read a CSV and return {column: {mean, max, min}} for numeric columns."""
    with open(filepath) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    stats = {}
    for col in rows[0].keys():
        values = [float(row[col]) for row in rows]  # BUG: crashes on non-numeric & empty
        stats[col] = {
            "mean": sum(values) / len(values),
            "max": max(values),
            "min": min(values),
        }
    return stats


if __name__ == "__main__":
    import json, sys
    result = calculate_stats(sys.argv[1])
    print(json.dumps(result, indent=2))
