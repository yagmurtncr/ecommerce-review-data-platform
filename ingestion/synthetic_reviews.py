"""Deterministic synthetic e-commerce review generator.

Produces realistic-looking review records so the whole platform can be run and
demoed without any private or scraped data. Text is assembled from topic-specific
templates; a small, controlled fraction of anomalies (near-duplicate spam and
rating/sentiment mismatches) is injected on purpose so the anomaly-detection
stage has something to catch.

The generator is deterministic given a seed → the dataset is reproducible.
"""
from __future__ import annotations

import argparse
import csv
import random
from datetime import date, timedelta

CATEGORIES = {
    "Electronics": ["Wireless Earbuds", "Smart Watch", "Bluetooth Speaker", "Laptop Stand", "USB-C Hub"],
    "Home & Kitchen": ["Air Fryer", "Coffee Maker", "Knife Set", "Vacuum Cleaner", "Water Bottle"],
    "Books": ["Data Engineering Handbook", "Turkish Grammar", "Sci-Fi Novel", "Cookbook", "Kids Story"],
    "Fashion": ["Running Shoes", "Denim Jacket", "Leather Wallet", "Wool Scarf", "Backpack"],
    "Beauty": ["Face Serum", "Shampoo", "Lipstick", "Sunscreen", "Hair Dryer"],
}

# topic -> (positive templates, negative templates)
TOPICS = {
    "product_quality": (
        ["The build quality is excellent and it feels premium.",
         "Works perfectly, exactly as described. Very happy.",
         "Great quality for the price, highly recommend."],
        ["Poor quality, it broke after two days.",
         "Feels cheap and stopped working quickly.",
         "Not as described, the material is low quality."],
    ),
    "shipping": (
        ["Shipping was super fast, arrived a day early.",
         "Delivery was quick and well tracked."],
        ["Shipping took forever, arrived two weeks late.",
         "The delivery was delayed and no updates were given."],
    ),
    "price": (
        ["Amazing value for money, worth every penny.",
         "Great price compared to other stores."],
        ["Overpriced for what you get.",
         "Too expensive, found it cheaper elsewhere."],
    ),
    "packaging": (
        ["Came in neat, secure packaging.",
         "Well packaged, no damage at all."],
        ["The packaging was damaged and the item was dented.",
         "Box arrived crushed, item scratched."],
    ),
    "customer_service": (
        ["Customer service was helpful and quick to respond.",
         "Support resolved my issue right away."],
        ["Customer service never replied to my emails.",
         "Support was rude and unhelpful."],
    ),
    "return": (
        ["Easy return process, refund came fast.",
         "Returning was smooth and hassle-free."],
        ["Return was a nightmare, still waiting for a refund.",
         "They refused my return without a reason."],
    ),
}


OPENERS = ["", "Honestly,", "Overall,", "After a week,", "First impression:",
           "Just received it —", "Not gonna lie,", "For the price,", "So far,"]
CLOSERS = ["", "Would buy again.", "Not sure I'd repurchase.", "Recommended.",
           "Do better.", "Pretty satisfied.", "Lesson learned.", "Five stars from me.",
           "Mixed feelings overall.", "Exactly what I expected."]


def _rating_for(polarity: str, rng: random.Random) -> int:
    return rng.choice([4, 5, 5]) if polarity == "pos" else rng.choice([1, 1, 2])


def _compose(rng, product, phrase):
    """Compose a varied review sentence so legitimate reviews are mostly unique."""
    opener = rng.choice(OPENERS)
    closer = rng.choice(CLOSERS)
    mention = rng.choice([f"The {product.lower()} is fine.", f"Bought the {product.lower()}.",
                          f"This {product.lower()} —", ""])
    parts = [p for p in [opener, mention, phrase, closer] if p]
    return " ".join(parts)


def generate(n: int, seed: int = 42, anomaly_rate: float = 0.03):
    rng = random.Random(seed)
    start = date(2024, 1, 1)
    customers = [f"cust_{i:05d}" for i in range(max(50, n // 20))]
    rows = []
    for i in range(n):
        category = rng.choice(list(CATEGORIES))
        product = rng.choice(CATEGORIES[category])
        topic = rng.choice(list(TOPICS))
        polarity = rng.choice(["pos", "neg", "pos"])
        pos_t, neg_t = TOPICS[topic]
        phrase = rng.choice(pos_t if polarity == "pos" else neg_t)
        text = _compose(rng, product, phrase)
        rating = _rating_for(polarity, rng)
        d = start + timedelta(days=rng.randint(0, 640))
        rows.append({
            "review_id": f"r_{i:07d}",
            "product_id": f"p_{abs(hash(product)) % 100000:05d}",
            "product_name": product,
            "category": category,
            "customer_id": rng.choice(customers),
            "rating": rating,
            "review_text": text,
            "topic": topic,
            "review_date": d.isoformat(),
        })

    # Inject anomalies on purpose (for the fake-review / anomaly stage):
    n_anom = int(n * anomaly_rate)
    for _ in range(n_anom):
        kind = rng.random()
        base = rng.choice(rows)
        if kind < 0.5:
            # near-duplicate spam: same text pushed by many different customers
            clone = dict(base)
            clone["review_id"] = f"r_spam_{rng.randint(0, 10**9):09d}"
            clone["customer_id"] = rng.choice(customers)
            rows.append(clone)
        else:
            # rating/sentiment mismatch: 5 stars but clearly negative text
            mism = dict(base)
            mism["review_id"] = f"r_mismatch_{rng.randint(0, 10**9):09d}"
            mism["review_text"] = "Terrible product, broke immediately and support ignored me."
            mism["rating"] = 5
            rows.append(mism)

    rng.shuffle(rows)
    return rows


def write_csv(rows, path):
    fields = ["review_id", "product_id", "product_name", "category",
              "customer_id", "rating", "review_text", "topic", "review_date"]
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Generate synthetic e-commerce reviews")
    ap.add_argument("-n", "--rows", type=int, default=5000)
    ap.add_argument("-s", "--seed", type=int, default=42)
    ap.add_argument("-o", "--out", default="data/samples/reviews.csv")
    args = ap.parse_args()

    import os
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    data = generate(args.rows, args.seed)
    write_csv(data, args.out)
    print(f"Wrote {len(data)} reviews to {args.out}")
