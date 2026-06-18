"""
Sets up a SQLite DB, loads the fixed queries.sql, and verifies correctness.
"""
import sqlite3, re, sys

def setup_db():
    conn = sqlite3.connect(":memory:")
    conn.executescript("""
        CREATE TABLE customers(id INTEGER PRIMARY KEY, name TEXT, email TEXT, created_at TEXT);
        CREATE TABLE products(id INTEGER PRIMARY KEY, name TEXT, category TEXT, price REAL);
        CREATE TABLE orders(id INTEGER PRIMARY KEY, customer_id INTEGER, created_at TEXT, status TEXT);
        CREATE TABLE order_items(id INTEGER PRIMARY KEY, order_id INTEGER, product_id INTEGER, quantity INTEGER, unit_price REAL);

        INSERT INTO customers VALUES (1,'Alice','a@x.com','2025-01-01'),
                                     (2,'Bob','b@x.com','2025-02-01'),
                                     (3,'Carol','c@x.com','2025-03-01');
        INSERT INTO products VALUES (1,'Widget','gadget',10.0),
                                    (2,'Gadget','gadget',20.0),
                                    (3,'Donut','food',5.0),   -- never ordered
                                    (4,'Thingamajig','gadget',15.0);  -- never ordered
        -- Alice: 2 paid orders, Bob: 1 paid order, Carol: 1 cancelled
        INSERT INTO orders VALUES (1,1,'2025-06-01','paid'),
                                  (2,1,'2025-06-15','paid'),
                                  (3,2,'2025-06-10','paid'),
                                  (4,3,'2025-06-20','cancelled');
        -- order 1: 2 widgets($10) + 1 gadget($20)  => 40
        -- order 2: 3 widgets($10)                  => 30
        -- order 3: 1 gadget($20)                   => 20
        -- total revenue: 90
        INSERT INTO order_items VALUES (1,1,1,2,10.0),(2,1,2,1,20.0),
                                       (3,2,1,3,10.0),
                                       (4,3,2,1,20.0);
    """)
    return conn


def parse_queries(sql: str) -> list[str]:
    """Split SQL file into individual queries (strip comments)."""
    # Remove single-line comments then split on semicolons
    cleaned = re.sub(r'--[^\n]*', '', sql)
    queries = [q.strip() for q in cleaned.split(';') if q.strip()]
    return queries


def run_tests():
    conn = setup_db()
    sql = open("queries.sql").read()
    queries = parse_queries(sql)

    if len(queries) < 5:
        print(f"FAIL  Expected 5 queries, found {len(queries)}")
        sys.exit(1)

    passed = 0
    total = 5

    # Query 1: total revenue should be 90
    try:
        rows = conn.execute(queries[0]).fetchall()
        val = rows[0][0]
        if abs(val - 90.0) < 0.01:
            print(f"PASS  Query 1 (total revenue): {val}")
            passed += 1
        else:
            print(f"FAIL  Query 1 (total revenue): got {val}, expected 90.0")
    except Exception as e:
        print(f"FAIL  Query 1: {e}")

    # Query 2: top customers — Alice should be first with 2 orders
    try:
        rows = conn.execute(queries[1]).fetchall()
        if rows and rows[0][0] == 'Alice' and rows[0][1] == 2:
            print(f"PASS  Query 2 (top customers): Alice=2")
            passed += 1
        else:
            print(f"FAIL  Query 2 (top customers): {rows[:3]}")
    except Exception as e:
        print(f"FAIL  Query 2: {e}")

    # Query 3: monthly revenue — June (month 6) should have 90
    try:
        rows = conn.execute(queries[2]).fetchall()
        june = [r for r in rows if str(r[0]) == '06']
        if june and abs(june[0][1] - 90.0) < 0.01:
            print(f"PASS  Query 3 (monthly revenue): June={june[0][1]}")
            passed += 1
        else:
            print(f"FAIL  Query 3 (monthly revenue): {rows}")
    except Exception as e:
        print(f"FAIL  Query 3: {e}")

    # Query 4: never-ordered products — should include Donut(3) and Thingamajig(4)
    try:
        rows = conn.execute(queries[3]).fetchall()
        ids = {r[0] for r in rows}
        if 3 in ids and 4 in ids and 1 not in ids and 2 not in ids:
            print(f"PASS  Query 4 (never ordered): {ids}")
            passed += 1
        else:
            print(f"FAIL  Query 4 (never ordered): got ids {ids}, expected {{3,4}}")
    except Exception as e:
        print(f"FAIL  Query 4: {e}")

    # Query 5: avg order value — Alice(2 orders) should appear, Bob(1 order) should not
    try:
        rows = conn.execute(queries[4]).fetchall()
        names = {r[0] for r in rows}
        if 'Alice' in names and 'Bob' not in names:
            print(f"PASS  Query 5 (avg order value): {rows}")
            passed += 1
        else:
            print(f"FAIL  Query 5 (avg order value): {rows}")
    except Exception as e:
        print(f"FAIL  Query 5: {e}")

    print(f"\n{passed}/{total} passed")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    run_tests()
