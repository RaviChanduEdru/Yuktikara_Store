#!/usr/bin/env python3
"""Generate the Yuktikara Store dataset for the retail flagship series.

Standard library only. Deterministic: the same seed produces the same bytes.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 20260922
START = date(2025, 1, 1)
END = date(2026, 8, 31)
TAX_RATE = 0.0825

# Cascade Ridge runs small, so buyers of the common smaller sizes send it back as "Too small".
# The cause is recoverable from the data (one style, one reason, one size band), never asserted.
PLANTED_STYLE = "Cascade Ridge Hiking Boot"

STORES = [
    ("ST001", "Yuktikara Seattle Flagship", "Pacific Northwest", "Seattle", "WA", 47.6062, -122.3321, "Flagship", 24500, date(2019, 3, 14)),
    ("ST002", "Yuktikara Tacoma", "Pacific Northwest", "Tacoma", "WA", 47.2529, -122.4443, "Standard", 11200, date(2020, 9, 8)),
    ("ST003", "Yuktikara Spokane", "Pacific Northwest", "Spokane", "WA", 47.6588, -117.4260, "Standard", 10800, date(2021, 5, 20)),
    ("ST004", "Yuktikara Portland Pearl", "Pacific Northwest", "Portland", "OR", 45.5152, -122.6784, "Flagship", 22100, date(2018, 10, 2)),
    ("ST005", "Yuktikara Eugene", "Pacific Northwest", "Eugene", "OR", 44.0521, -123.0868, "Standard", 9600, date(2022, 4, 11)),
    ("ST006", "Yuktikara Bend Outlet", "Pacific Northwest", "Bend", "OR", 44.0582, -121.3153, "Outlet", 14300, date(2021, 11, 5)),
    ("ST007", "Yuktikara Boise", "Northern Rockies", "Boise", "ID", 43.6150, -116.2023, "Standard", 12400, date(2020, 6, 19)),
    ("ST008", "Yuktikara Coeur d'Alene", "Northern Rockies", "Coeur d'Alene", "ID", 47.6777, -116.7805, "Standard", 8900, date(2023, 3, 24)),
    ("ST009", "Yuktikara Missoula", "Northern Rockies", "Missoula", "MT", 46.8721, -113.9940, "Standard", 9200, date(2022, 8, 12)),
    ("ST010", "Yuktikara Bozeman", "Northern Rockies", "Bozeman", "MT", 45.6770, -111.0429, "Standard", 10100, date(2021, 7, 30)),
    ("ST011", "Yuktikara Denver LoDo", "Colorado Front Range", "Denver", "CO", 39.7392, -104.9903, "Flagship", 23800, date(2019, 8, 16)),
    ("ST012", "Yuktikara Boulder", "Colorado Front Range", "Boulder", "CO", 40.0150, -105.2705, "Standard", 11700, date(2020, 2, 28)),
    ("ST013", "Yuktikara Fort Collins", "Colorado Front Range", "Fort Collins", "CO", 40.5853, -105.0844, "Standard", 9800, date(2023, 9, 15)),
    ("ST014", "Yuktikara Salt Lake City", "Great Basin", "Salt Lake City", "UT", 40.7608, -111.8910, "Standard", 13100, date(2020, 11, 6)),
    ("ST015", "Yuktikara Park City Outlet", "Great Basin", "Park City", "UT", 40.6461, -111.4980, "Outlet", 13600, date(2022, 12, 9)),
    ("ST016", "Yuktikara Reno", "Great Basin", "Reno", "NV", 39.5296, -119.8138, "Standard", 10400, date(2021, 2, 26)),
    ("ST017", "Yuktikara Sacramento", "Great Basin", "Sacramento", "CA", 38.5816, -121.4944, "Standard", 12900, date(2022, 6, 3)),
    ("ST018", "Yuktikara Flagstaff", "Great Basin", "Flagstaff", "AZ", 35.1983, -111.6513, "Standard", 8700, date(2023, 5, 19)),
    ("ST900", "Yuktikara Online", "Online", "Seattle", "WA", 47.6062, -122.3321, "Ecommerce", 0, date(2017, 4, 1)),
]

STORE_DAILY_ORDERS = {"Flagship": 4.2, "Standard": 2.1, "Outlet": 2.6, "Ecommerce": 8.4}

SUPPLIERS = [
    ("SUP01", "Kestrel Technical Works", "Vietnam", 42, 4.6),
    ("SUP02", "Northaven Textiles", "Portugal", 28, 4.8),
    ("SUP03", "Granite Peak Manufacturing", "United States", 16, 4.7),
    ("SUP04", "Halden Footwear Group", "Vietnam", 55, 3.4),
    ("SUP05", "Selkirk Down Company", "Canada", 34, 4.5),
    ("SUP06", "Talus Hardgoods", "China", 48, 4.1),
    ("SUP07", "Juniper Mills", "India", 39, 4.3),
]

DEPARTMENTS = {
    "Footwear": ["Hiking Boots", "Trail Runners", "Approach Shoes", "Insulated Boots"],
    "Apparel": ["Rain Shells", "Insulated Jackets", "Fleece", "Base Layers", "Hiking Trousers", "Technical Tees"],
    "Equipment": ["Backpacks", "Tents", "Sleeping Bags", "Trekking Poles", "Headlamps", "Camp Stoves"],
}

SERIES = [
    "Cascade Ridge", "Sawtooth", "Glacier", "Timberline", "Kestrel", "Aspen",
    "Summit", "Ridgeline", "Wolverine", "Alpine", "Granite", "Juniper",
    "Basin", "Selkirk", "Talus", "Cirque", "Chinook", "Larkspur",
]

CATEGORY_NOUN = {
    "Hiking Boots": "Hiking Boot", "Trail Runners": "Trail Runner", "Approach Shoes": "Approach Shoe",
    "Insulated Boots": "Insulated Boot", "Rain Shells": "Rain Shell", "Insulated Jackets": "Down Jacket",
    "Fleece": "Fleece", "Base Layers": "Base Layer", "Hiking Trousers": "Hiking Trouser",
    "Technical Tees": "Technical Tee", "Backpacks": "Backpack", "Tents": "Tent",
    "Sleeping Bags": "Sleeping Bag", "Trekking Poles": "Trekking Poles", "Headlamps": "Headlamp",
    "Camp Stoves": "Camp Stove",
}

CATEGORY_PRICE = {
    "Hiking Boots": (149, 285), "Trail Runners": (115, 185), "Approach Shoes": (109, 165),
    "Insulated Boots": (159, 249), "Rain Shells": (129, 379), "Insulated Jackets": (189, 449),
    "Fleece": (79, 159), "Base Layers": (45, 95), "Hiking Trousers": (69, 139),
    "Technical Tees": (32, 65), "Backpacks": (89, 349), "Tents": (199, 649),
    "Sleeping Bags": (129, 429), "Trekking Poles": (79, 189), "Headlamps": (35, 119),
    "Camp Stoves": (59, 219),
}

FOOTWEAR_SIZES = ["7", "7.5", "8", "8.5", "9", "9.5", "10", "10.5", "11", "11.5", "12", "13"]
FOOTWEAR_SIZE_WEIGHTS = [3, 5, 8, 11, 14, 14, 13, 10, 8, 6, 5, 3]
APPAREL_SIZES = ["XS", "S", "M", "L", "XL", "XXL"]
APPAREL_SIZE_WEIGHTS = [5, 18, 28, 26, 16, 7]

COLORS = ["Slate", "Moss", "Ember", "Basalt", "Dune", "Storm Blue", "Clay", "Bone"]

RETURN_REASONS = [
    ("RR1", "Too small", "Fit"),
    ("RR2", "Too large", "Fit"),
    ("RR3", "Not as described", "Description"),
    ("RR4", "Damaged or faulty", "Quality"),
    ("RR5", "Wrong item shipped", "Logistics"),
    ("RR6", "Arrived too late", "Logistics"),
    ("RR7", "Changed mind", "Customer"),
    ("RR8", "Found a better price", "Customer"),
]

MONTH_FACTOR = {1: 0.70, 2: 0.72, 3: 0.92, 4: 1.10, 5: 1.26, 6: 1.30,
                7: 1.24, 8: 1.14, 9: 1.06, 10: 1.02, 11: 1.22, 12: 1.36}

DEPT_SEASON = {
    "Footwear": {1: 0.7, 2: 0.7, 3: 0.9, 4: 1.2, 5: 1.3, 6: 1.35, 7: 1.3, 8: 1.2, 9: 1.0, 10: 0.9, 11: 0.9, 12: 0.9},
    "Apparel": {1: 0.9, 2: 0.9, 3: 0.95, 4: 0.95, 5: 0.9, 6: 0.85, 7: 0.85, 8: 0.95, 9: 1.2, 10: 1.35, 11: 1.4, 12: 1.45},
    "Equipment": {1: 0.6, 2: 0.65, 3: 0.9, 4: 1.25, 5: 1.4, 6: 1.45, 7: 1.35, 8: 1.2, 9: 0.95, 10: 0.8, 11: 0.8, 12: 0.95},
}

ORDER_STATUS = ["Completed", "Shipped", "Pending", "Cancelled"]
ORDER_STATUS_WEIGHTS = [0.845, 0.075, 0.032, 0.048]
PAYMENT_METHODS = ["Credit Card", "Debit Card", "Yuktikara Rewards Card", "Gift Card", "Mobile Wallet"]
PAYMENT_WEIGHTS = [0.46, 0.21, 0.14, 0.05, 0.14]
LOYALTY_TIERS = ["None", "Trailhead", "Summit", "Alpine"]
LOYALTY_WEIGHTS = [0.38, 0.34, 0.21, 0.07]

FIRST_NAMES = [
    "Alina", "Marcus", "Priya", "Theo", "Noor", "Callum", "Freya", "Diego", "Imani", "Soren",
    "Rosa", "Kenji", "Elena", "Tobias", "Amara", "Felix", "Leila", "Hugo", "Saskia", "Mateo",
    "Nadia", "Emrys", "Yara", "Otto", "Sana", "Lucian", "Beatrix", "Ravi", "Greta", "Elias",
]
LAST_NAMES = [
    "Whitfield", "Okonkwo", "Marchetti", "Lindqvist", "Farrow", "Nakamura", "Delacroix", "Halvorsen",
    "Ashworth", "Barros", "Ferreira", "Kowalski", "Pemberton", "Rasmussen", "Sandoval", "Thorne",
    "Vasquez", "Wexford", "Yardley", "Zielinski", "Ellery", "Grimshaw", "Hollis", "Ibarra",
]


def money(cents: int) -> str:
    return f"{cents / 100:.2f}"


def daterange(start: date, end: date):
    day = start
    while day <= end:
        yield day
        day += timedelta(days=1)


def build_products(rng: random.Random):
    products = []
    variants = []
    pid = 0
    for dept, categories in DEPARTMENTS.items():
        for category in categories:
            style_count = 4 if dept == "Footwear" else 3
            for n in range(style_count):
                pid += 1
                if category == "Hiking Boots" and n == 0:
                    name = PLANTED_STYLE
                else:
                    series = SERIES[(pid * 7) % len(SERIES)]
                    name = f"{series} {CATEGORY_NOUN[category]}"
                lo, hi = CATEGORY_PRICE[category]
                price_cents = int(round(rng.uniform(lo, hi))) * 100 - 5
                cost_cents = int(price_cents * rng.uniform(0.38, 0.52))
                supplier = SUPPLIERS[(pid * 3) % len(SUPPLIERS)][0]
                if name == PLANTED_STYLE:
                    supplier = "SUP04"
                product_id = f"P{pid:04d}"
                products.append({
                    "ProductID": product_id,
                    "StyleCode": f"YK-{dept[:3].upper()}-{pid:04d}",
                    "ProductName": name,
                    "DepartmentName": dept,
                    "CategoryName": category,
                    "SupplierID": supplier,
                    "SeasonCode": rng.choice(["SS25", "FW25", "SS26", "AllSeason"]),
                    "ListPrice": money(price_cents),
                    "UnitCost": money(cost_cents),
                    "LaunchDate": (START - timedelta(days=rng.randint(30, 540))).isoformat(),
                    "IsRfidTagged": "true" if dept != "Equipment" else "false",
                })
                if dept == "Footwear":
                    sizes, size_weights, colors = FOOTWEAR_SIZES, FOOTWEAR_SIZE_WEIGHTS, 2
                elif dept == "Apparel":
                    sizes, size_weights, colors = APPAREL_SIZES, APPAREL_SIZE_WEIGHTS, 3
                else:
                    sizes, size_weights, colors = ["One Size"], [100], 2
                chosen_colors = rng.sample(COLORS, colors)
                for color in chosen_colors:
                    for order_idx, (size, weight) in enumerate(zip(sizes, size_weights)):
                        variants.append({
                            "VariantID": f"V{len(variants) + 1:05d}",
                            "ProductID": product_id,
                            "SKU": f"{product_id}-{color[:2].upper()}-{size.replace('.', '')}",
                            "ColorName": color,
                            "SizeCode": size,
                            "SizeOrder": order_idx + 1,
                            "ListPrice": money(price_cents),
                            "_dept": dept,
                            "_weight": weight * rng.uniform(0.6, 1.4),
                            "_price_cents": price_cents,
                            "_name": name,
                        })
    return products, variants


def build_customers(rng: random.Random, count: int):
    customers = []
    store_ids = [s[0] for s in STORES if s[7] != "Ecommerce"]
    for i in range(1, count + 1):
        first = rng.choice(FIRST_NAMES)
        last = rng.choice(LAST_NAMES)
        home = rng.choice(STORES[:-1])
        customers.append({
            "CustomerID": f"C{i:05d}",
            "CustomerName": f"{first} {last}",
            "LoyaltyTier": rng.choices(LOYALTY_TIERS, LOYALTY_WEIGHTS)[0],
            "JoinDate": (START - timedelta(days=rng.randint(1, 1800))).isoformat(),
            "HomeCity": home[3],
            "HomeStateCode": home[4],
            "PreferredStoreID": rng.choice(store_ids),
        })
    return customers


def markdown_rate(rng: random.Random, day: date, dept: str) -> float:
    clearance = day.month in (1, 2) or day.month in (7, 8)
    if clearance and rng.random() < 0.42:
        return rng.choice([0.15, 0.20, 0.25, 0.30, 0.40])
    if rng.random() < 0.11:
        return rng.choice([0.10, 0.15, 0.20])
    return 0.0


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the Yuktikara Store dataset.")
    parser.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "data"))
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    rng = random.Random(SEED)

    products, variants = build_products(rng)
    customers = build_customers(rng, 6200)

    by_dept: dict[str, list] = {"Footwear": [], "Apparel": [], "Equipment": []}
    for v in variants:
        by_dept[v["_dept"]].append(v)
    dept_cum: dict[str, list[float]] = {}
    for dept, items in by_dept.items():
        total = 0.0
        cum = []
        for v in items:
            total += v["_weight"]
            cum.append(total)
        dept_cum[dept] = cum

    product_by_id = {p["ProductID"]: p for p in products}
    variant_by_id = {v["VariantID"]: v for v in variants}

    orders = []
    lines = []
    order_seq = 0
    line_index = []

    for day in daterange(START, END):
        weekend = day.weekday() >= 5
        for store in STORES:
            store_id, _, _, _, _, _, _, fmt, _, opened = (
                store[0], store[1], store[2], store[3], store[4], store[5], store[6], store[7], store[8], store[9],
            )
            if day < opened:
                continue
            base = STORE_DAILY_ORDERS[fmt] * MONTH_FACTOR[day.month]
            if weekend and fmt != "Ecommerce":
                base *= 1.55
            count = max(0, int(rng.gauss(base, base * 0.35)))
            for _ in range(count):
                order_seq += 1
                order_id = f"SO{order_seq:06d}"
                channel = "Online" if fmt == "Ecommerce" else "Store"
                status = rng.choices(ORDER_STATUS, ORDER_STATUS_WEIGHTS)[0]
                if day > END - timedelta(days=6) and status == "Completed" and rng.random() < 0.45:
                    status = "Pending"
                n_lines = rng.choices([1, 2, 3, 4, 5], [0.42, 0.28, 0.17, 0.09, 0.04])[0]
                gross = 0
                discount = 0
                order_lines = []
                for line_no in range(1, n_lines + 1):
                    dept = rng.choices(
                        list(DEPT_SEASON.keys()),
                        [DEPT_SEASON[d][day.month] for d in DEPT_SEASON],
                    )[0]
                    pool = by_dept[dept]
                    variant = rng.choices(pool, cum_weights=dept_cum[dept])[0]
                    qty = rng.choices([1, 2, 3], [0.86, 0.11, 0.03])[0]
                    unit = variant["_price_cents"]
                    rate = markdown_rate(rng, day, dept)
                    line_gross = unit * qty
                    line_discount = int(round(line_gross * rate))
                    gross += line_gross
                    discount += line_discount
                    order_lines.append({
                        "OrderID": order_id,
                        "OrderLineNumber": line_no,
                        "VariantID": variant["VariantID"],
                        "ProductID": variant["ProductID"],
                        "Quantity": qty,
                        "UnitPrice": money(unit),
                        "DiscountAmount": money(line_discount),
                        "LineTotal": money(line_gross - line_discount),
                    })
                    line_index.append({
                        "OrderID": order_id, "LineNo": line_no, "VariantID": variant["VariantID"],
                        "ProductID": variant["ProductID"], "Qty": qty,
                        "Net": line_gross - line_discount, "Date": day, "Status": status,
                        "Channel": channel, "StoreID": store_id, "Dept": dept,
                        "Name": variant["_name"], "SizeOrder": variant["SizeOrder"],
                    })
                subtotal = gross - discount
                tax = int(round(subtotal * TAX_RATE))
                orders.append({
                    "OrderID": order_id,
                    "OrderNumber": f"YK-{day.year}-{order_seq:06d}",
                    "StoreID": store_id,
                    "CustomerID": rng.choice(customers)["CustomerID"],
                    "Channel": channel,
                    "OrderDate": day.isoformat(),
                    "OrderStatus": status,
                    "GrossAmount": money(gross),
                    "DiscountAmount": money(discount),
                    "SubTotal": money(subtotal),
                    "TaxAmount": money(tax),
                    "OrderTotal": money(subtotal + tax),
                    "PaymentMethod": rng.choices(PAYMENT_METHODS, PAYMENT_WEIGHTS)[0],
                })
                lines.extend(order_lines)

    base_return_rate = {"Footwear": 0.142, "Apparel": 0.108, "Equipment": 0.038}
    returns = []
    store_ids_physical = [s[0] for s in STORES if s[7] != "Ecommerce"]
    for item in line_index:
        if item["Status"] not in ("Completed", "Shipped"):
            continue
        rate = base_return_rate[item["Dept"]]
        if item["Channel"] == "Online":
            rate *= 1.8
        planted = item["Name"] == PLANTED_STYLE
        if planted:
            rate = 0.38 if item["SizeOrder"] <= 6 else 0.12
        if rng.random() >= rate:
            continue
        lag = rng.choices([7, 14, 21, 30, 45], [0.30, 0.28, 0.20, 0.14, 0.08])[0]
        lag += rng.randint(-5, 5)
        return_date = item["Date"] + timedelta(days=max(2, lag))
        if return_date > END:
            continue
        if planted and rng.random() < 0.62:
            reason = "RR1"
        else:
            reason = rng.choices(
                [r[0] for r in RETURN_REASONS],
                [0.18, 0.13, 0.11, 0.14, 0.06, 0.05, 0.22, 0.11],
            )[0]
        qty_returned = 1 if item["Qty"] == 1 else rng.choices([1, item["Qty"]], [0.7, 0.3])[0]
        amount = int(round(item["Net"] * qty_returned / item["Qty"]))
        status = rng.choices(["Accepted", "Pending", "Rejected"], [0.855, 0.075, 0.070])[0]
        if item["Channel"] == "Online":
            return_store = rng.choices(
                store_ids_physical,
                [3.0 if s == "ST006" else 1.0 for s in store_ids_physical],
            )[0]
        else:
            return_store = item["StoreID"] if rng.random() < 0.88 else rng.choice(store_ids_physical)
        returns.append({
            "ReturnID": f"RT{len(returns) + 1:06d}",
            "OrderID": item["OrderID"],
            "OrderLineNumber": item["LineNo"],
            "VariantID": item["VariantID"],
            "ProductID": item["ProductID"],
            "ReturnDate": return_date.isoformat(),
            "ReturnStoreID": return_store,
            "QuantityReturned": qty_returned,
            "ReturnAmount": money(amount),
            "ReturnStatus": status,
            "ReturnReasonID": reason,
            "RestockFlag": "true" if status == "Accepted" and reason not in ("RR4",) else "false",
        })

    inventory = []
    rfid_variants = [v for v in variants if product_by_id[v["ProductID"]]["IsRfidTagged"] == "true"]
    for store in STORES:
        if store[7] == "Ecommerce":
            continue
        for v in rfid_variants:
            if rng.random() > 0.55:
                continue
            floor_min = rng.choices([2, 3, 4, 6], [0.4, 0.3, 0.2, 0.1])[0]
            floor = max(0, int(rng.gauss(floor_min * 2.1, floor_min * 0.9)))
            backroom = max(0, int(rng.gauss(floor_min * 1.6, floor_min * 1.1)))
            inventory.append({
                "StoreID": store[0],
                "VariantID": v["VariantID"],
                "ProductID": v["ProductID"],
                "SnapshotDate": END.isoformat(),
                "FloorQty": floor,
                "BackroomQty": backroom,
                "OnHandQty": floor + backroom,
                "FloorMinQty": floor_min,
                "ReorderPoint": floor_min * 3,
            })

    dim_date = []
    for day in daterange(START, END):
        quarter = (day.month - 1) // 3 + 1
        dim_date.append({
            "DateKey": day.strftime("%Y%m%d"),
            "Date": day.isoformat(),
            "Year": day.year,
            "Quarter": f"Q{quarter}",
            "YearQuarter": f"{day.year}-Q{quarter}",
            "MonthNumber": day.month,
            "MonthName": day.strftime("%B"),
            "YearMonth": day.strftime("%Y-%m"),
            "DayOfWeek": day.isoweekday(),
            "DayName": day.strftime("%A"),
            "IsWeekend": "true" if day.weekday() >= 5 else "false",
        })

    store_rows = [{
        "StoreID": s[0], "StoreName": s[1], "RegionName": s[2], "City": s[3], "StateCode": s[4],
        "Latitude": s[5], "Longitude": s[6], "StoreFormat": s[7], "SquareFeet": s[8],
        "OpenedDate": s[9].isoformat(),
    } for s in STORES]

    supplier_rows = [{
        "SupplierID": s[0], "SupplierName": s[1], "Country": s[2],
        "LeadTimeDays": s[3], "QualityRating": s[4],
    } for s in SUPPLIERS]

    reason_rows = [{"ReturnReasonID": r[0], "ReturnReasonName": r[1], "ReturnCategory": r[2]} for r in RETURN_REASONS]

    for v in variants:
        for key in ("_dept", "_weight", "_price_cents", "_name"):
            v.pop(key)

    tables = {
        "Store.csv": store_rows,
        "Supplier.csv": supplier_rows,
        "Product.csv": products,
        "ProductVariant.csv": variants,
        "Customer.csv": customers,
        "DimDate.csv": dim_date,
        "SalesOrder.csv": orders,
        "SalesOrderLine.csv": lines,
        "SalesReturn.csv": returns,
        "ReturnReason.csv": reason_rows,
        "StoreInventory.csv": inventory,
    }

    manifest = {"company": "Yuktikara Store", "seed": SEED,
                "period": {"start": START.isoformat(), "end": END.isoformat()},
                "tax_rate": TAX_RATE, "tables": {}}

    for filename, rows in tables.items():
        path = out / filename
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        raw = path.read_bytes()
        manifest["tables"][filename] = {
            "rows": len(rows),
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }

    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"Yuktikara Store — {START} to {END}")
    for filename, meta in manifest["tables"].items():
        print(f"  {filename:24s} {meta['rows']:>7,} rows  {meta['bytes'] / 1_048_576:.2f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
