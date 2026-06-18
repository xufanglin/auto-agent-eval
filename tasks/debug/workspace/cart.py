"""
Shopping cart with multiple bugs. Do NOT fix the bugs yet — this is intentional.
"""

def calculate_discount(price, discount_percent):
    """Return discounted price."""
    # Bug 1: should be (1 - discount_percent / 100), not (1 - discount_percent)
    return price * (1 - discount_percent)


def apply_tax(price, tax_rate=0.1):
    """Return price with tax applied."""
    return price + tax_rate  # Bug 2: should be price * (1 + tax_rate), not price + tax_rate


def cart_total(items):
    """
    Calculate total for a list of items.
    Each item is a dict: {name, price, quantity, discount_percent}
    """
    total = 0
    for item in items:
        discounted = calculate_discount(item["price"], item["discount_percent"])
        subtotal = discounted * item["quantity"]
        total += subtotal
    return total  # Bug 3: tax is never applied — should call apply_tax(total) before returning


def most_expensive(items):
    """Return the name of the most expensive item (after discount)."""
    best = None
    best_price = 0
    for item in items:
        p = calculate_discount(item["price"], item["discount_percent"])
        if p > best_price:
            best_price = p
            best = item
    return best["name"]  # Bug 4: if items is empty, best is None and this will raise KeyError


def summarize(items):
    """Print a summary of the cart."""
    print(f"Items: {len(items)}")
    print(f"Total (with tax): {cart_total(items):.2f}")
    if items:
        print(f"Most expensive: {most_expensive(items)}")
