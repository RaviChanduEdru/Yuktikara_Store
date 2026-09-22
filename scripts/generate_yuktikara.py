#!/usr/bin/env python3
"""Generate the Yuktikara Store dataset for the retail flagship series.

Standard library only. Deterministic: the same seed produces the same bytes.
"""

from __future__ import annotations

import argparse
import calendar
import csv
import hashlib
import json
import math
import random
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

SEED = 20260922
# The snapshot committed in data/. Pass --end for a window that ends on another day.
DEFAULT_END = date(2026, 8, 31)
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


# --- Operations: buying, stock over time, promotions and plans ------------------------------------
# These tables are built after the sales, returns and stock snapshot, from them alone, and with their
# own random streams, so adding them leaves the original eleven tables byte for byte the same.

SALE_STATUSES = ("Completed", "Shipped")  # orders that took stock and count as sales
REVIEW_DAYS = 14  # each store reorders from each supplier every two weeks

# Supplier: (share of deliveries that arrive late, fewest days late, most days late, share of lines short-shipped).
# Halden, who make the Cascade Ridge boot, are the least reliable: late about half the time, often short.
SUPPLIER_DELIVERY = {
    "SUP01": (0.12, 3, 8, 0.04),
    "SUP02": (0.08, 2, 5, 0.03),
    "SUP03": (0.05, 1, 3, 0.02),
    "SUP04": (0.45, 7, 21, 0.30),
    "SUP05": (0.10, 2, 6, 0.04),
    "SUP06": (0.22, 4, 12, 0.08),
    "SUP07": (0.18, 3, 10, 0.06),
}
# Cost increases that take effect on 1 January of the current year.
SUPPLIER_PRICE_RISE = {"SUP04": 1.04, "SUP06": 1.06}

# The promotions calendar every discounted sale line belongs to: (first month, last month, name, type, depth).
# It follows the markdown pattern the sales were generated with.
PROMOTION_CALENDAR = [
    (1, 2, "Winter Clearance", "Clearance", "15-40% off"),
    (3, 6, "Spring Trail Days", "Seasonal event", "10-20% off selected lines"),
    (7, 8, "Summer Clearance", "Clearance", "15-40% off"),
    (9, 10, "Autumn Layers Event", "Seasonal event", "10-20% off selected lines"),
    (11, 12, "Holiday Gift Event", "Seasonal event", "10-20% off selected lines"),
]

# How far above the plain forecast each store's sales target was set. The newest stores were given the
# growth plans of established ones, and online an ambitious one.
NEW_STORE_PLAN_UPLIFT = 1.22
ONLINE_PLAN_UPLIFT = 1.12


def money(cents: int) -> str:
    return f"{cents / 100:.2f}"


def cents(value: str) -> int:
    return int(round(float(value) * 100))


def month_starts(start: date, end: date):
    first = date(start.year, start.month, 1)
    while first <= end:
        yield first
        first = date(first.year + (first.month == 12), first.month % 12 + 1, 1)


def build_promotions(start: date, end: date, orders: list, lines: list):
    """Named promotions, and the promotion each discounted order line was sold under."""
    promotions = []
    promo_for_month = {}
    for year in range(start.year, end.year + 1):
        for index, (first_month, last_month, name, kind, depth) in enumerate(PROMOTION_CALENDAR, 1):
            first = date(year, first_month, 1)
            if first > end:
                continue
            promo_id = f"PR{year}-{index}"
            promotions.append({
                "PromotionID": promo_id,
                "PromotionName": f"{name} {year}",
                "PromotionType": kind,
                "PromotionStartDate": first.isoformat(),
                "PromotionEndDate": date(year, last_month, calendar.monthrange(year, last_month)[1]).isoformat(),
                "DiscountDepth": depth,
            })
            for month in range(first_month, last_month + 1):
                promo_for_month[(year, month)] = promo_id
    order_date = {o["OrderID"]: o["OrderDate"] for o in orders}
    links = []
    for line in lines:
        if line["DiscountAmount"] != "0.00":
            day = order_date[line["OrderID"]]
            links.append({"OrderLineID": line["OrderLineID"], "PromotionID": promo_for_month[(int(day[:4]), int(day[5:7]))]})
    return promotions, links


def build_targets(rng: random.Random, start: date, end: date, orders: list, returns: list):
    """Monthly net sales targets per store, for the window and the rest of the current year.

    The plan is built from each store's trading pattern, then calibrated so that the chain's plan matches
    the rate it actually trades at. On top of that, the newest stores and online were given growth plans.
    """
    sale_ids = {o["OrderID"] for o in orders if o["OrderStatus"] in SALE_STATUSES}
    store_of_order = {o["OrderID"]: o["StoreID"] for o in orders}
    actual = defaultdict(int)  # (store, month) -> net cents
    for o in orders:
        if o["OrderID"] in sale_ids:
            actual[(o["StoreID"], o["OrderDate"][:7])] += cents(o["SubTotal"])
    for r in returns:
        if r["ReturnStatus"] == "Accepted":
            actual[(store_of_order[r["OrderID"]], r["ReturnDate"][:7])] -= cents(r["ReturnAmount"])

    def trading_pattern(store, first, last):
        fmt, opened = store[7], store[9]
        expected = 0.0
        for day in daterange(first, last):
            if day < opened:
                continue
            weekend = day.weekday() >= 5 and fmt != "Ecommerce"
            expected += STORE_DAILY_ORDERS[fmt] * MONTH_FACTOR[day.month] * (1.55 if weekend else 1.0)
        return expected

    plan_end = date(end.year, 12, 31)
    months = []
    for first in month_starts(start, plan_end):
        last = date(first.year, first.month, calendar.monthrange(first.year, first.month)[1])
        months.append((first, last, last <= end))
    shape = {(store[0], first): trading_pattern(store, first, last) for store in STORES for first, last, _ in months}
    # One value per expected order, taken from the months already traded, so the plan lands on the real run rate.
    traded_shape = sum(shape[(store[0], first)] for store in STORES for first, _, complete in months if complete)
    traded_net = sum(actual[(store[0], f"{first:%Y-%m}")] for store in STORES for first, _, complete in months if complete)
    per_order = traded_net / traded_shape if traded_shape else 0

    targets = []
    for store in STORES:
        store_id, fmt, opened = store[0], store[7], store[9]
        uplift = NEW_STORE_PLAN_UPLIFT if opened.year >= 2023 else ONLINE_PLAN_UPLIFT if fmt == "Ecommerce" else 1.0
        for first, _, _ in months:
            target = shape[(store_id, first)] * per_order * uplift * rng.uniform(0.97, 1.03)
            targets.append({
                "TargetID": f"{store_id}-{first:%Y%m}",
                "StoreID": store_id,
                "TargetMonth": first.isoformat(),
                "TargetNetSales": money(int(round(target / 1000)) * 1000),
            })
    return targets


def build_supply_and_stock(rng: random.Random, start: date, end: date, products: list, variants: list,
                           line_index: list, returns: list):
    """Purchase orders and deliveries, and a monthly stock ledger for every RFID position in the snapshot.

    Each store reorders from each supplier every two weeks. For the snapshot's positions the ledger is
    built backwards from the snapshot, so it closes on exactly the counted stock: stock on the day before a
    delivery is what the delivery tops up from. A late delivery leaves the shelf low or empty first, so
    unreliable suppliers show up as stockout days. Other store and variant pairs, including online and
    equipment, are replenished with what they sold in the two weeks before each order.
    """
    product_by_id = {p["ProductID"]: p for p in products}
    lead_of = {s[0]: s[3] for s in SUPPLIERS}
    months = list(month_starts(start, end))
    variant_product = {v["VariantID"]: v["ProductID"] for v in variants}
    supplier_of_variant = {v: product_by_id[p]["SupplierID"] for v, p in variant_product.items()}
    days = list(daterange(start, end))
    day_index = {day: i for i, day in enumerate(days)}
    n_days = len(days)

    sold = defaultdict(lambda: defaultdict(int))  # (store, variant) -> day index -> units
    for item in line_index:
        if item["Status"] in SALE_STATUSES:
            sold[(item["StoreID"], item["VariantID"])][day_index[item["Date"]]] += item["Qty"]
    restocked = defaultdict(lambda: defaultdict(int))
    for r in returns:
        if r["ReturnStatus"] == "Accepted" and r["RestockFlag"] == "true":
            restocked[(r["ReturnStoreID"], r["VariantID"])][day_index[date.fromisoformat(r["ReturnDate"])]] += r["QuantityReturned"]

    # Delivery cycles per store and supplier: ordered, expected after the supplier's lead time, delivered.
    schedule = {}
    for store in STORES:
        for sup_id, _, _, lead_days, _ in SUPPLIERS:
            late_share, fewest, most, _ = SUPPLIER_DELIVERY[sup_id]
            expected = start - timedelta(days=REVIEW_DAYS - rng.randrange(REVIEW_DAYS))
            cycles = []
            while expected - timedelta(days=lead_days) <= end:
                late = rng.random() < late_share
                delivered = expected + timedelta(days=rng.randint(fewest, most) if late else 0)
                if delivered >= start:
                    cycles.append({"ordered": expected - timedelta(days=lead_days), "expected": expected,
                                   "delivered": delivered, "late": late})
                expected += timedelta(days=REVIEW_DAYS)
            schedule[(store[0], sup_id)] = cycles

    def demand_before(key, ordered_on):
        """Units the pair sold in the two weeks before an order (the window's first two weeks for earlier orders)."""
        first = max(start, ordered_on - timedelta(days=REVIEW_DAYS))
        if ordered_on <= start:
            first = start
        history = sold.get(key, {})
        return sum(history.get(day_index[first + timedelta(days=k)], 0)
                   for k in range(REVIEW_DAYS) if first + timedelta(days=k) <= end)

    # What each store keeps of each variant: what it sells there, plus some ranged but slow lines.
    # The shelf minimum and the order-up-to level follow how fast the pair actually sells.
    positions = []
    for store in STORES:
        if store[7] == "Ecommerce":
            continue
        for variant in variants:
            key = (store[0], variant["VariantID"])
            units = sum(sold.get(key, {}).values())
            if not units and rng.random() >= 0.22:
                continue
            monthly = units / max(1, len(months))
            floor_min = max(1, min(6, round(monthly * 0.6)))
            cover = monthly / 30 * (REVIEW_DAYS + lead_of[supplier_of_variant[variant["VariantID"]]])
            positions.append({
                "store": store[0], "variant": variant["VariantID"], "product": variant["ProductID"],
                "floor_min": floor_min,
                "reorder": max(floor_min, math.ceil(cover * 0.5)),
                "upto": floor_min + max(1, math.ceil(cover)),
            })

    # Forwards through the window. Every two weeks a store orders each pair back up to its level,
    # counting what is already on the way, and the supplier delivers it a lead time later, sometimes
    # late and sometimes short. A late or short delivery leaves the shelf low or empty, so unreliable
    # suppliers cost availability.
    ordered_by_cycle, received_by_cycle = {}, {}
    ledger, inventory, transfers = [], [], 0
    for pos in positions:
        store_id, variant_id = pos["store"], pos["variant"]
        key = (store_id, variant_id)
        sup_id = supplier_of_variant[variant_id]
        short_share = SUPPLIER_DELIVERY[sup_id][3]
        cycles = schedule[(store_id, sup_id)]
        orders_on, deliveries = defaultdict(list), defaultdict(list)
        for ci, cycle in enumerate(cycles):
            if start <= cycle["ordered"] <= end:
                orders_on[day_index[cycle["ordered"]]].append(ci)
            if cycle["delivered"] <= end:
                deliveries[day_index[cycle["delivered"]]].append(ci)
        pos_sold, pos_back = sold.get(key, {}), restocked.get(key, {})
        close = [0] * n_days
        received = [0] * n_days
        adjusted = [0] * n_days
        stock = pos["upto"]
        opening = stock
        on_order = 0
        for i in range(n_days):
            for ci in deliveries.get(i, []):
                got = received_by_cycle.get((store_id, sup_id, ci, variant_id))
                if got is None:  # ordered before the window: the pipeline the store started with
                    got = max(0, pos["upto"] - stock)
                    if got:
                        ordered_by_cycle[(store_id, sup_id, ci, variant_id)] = got
                        received_by_cycle[(store_id, sup_id, ci, variant_id)] = got
                received[i] += got
                stock += got
                on_order -= ordered_by_cycle.get((store_id, sup_id, ci, variant_id), 0)
            for ci in orders_on.get(i, []):
                # Reorder only once the pair is down to its reorder point, as a store would.
                if stock + on_order > pos["reorder"]:
                    continue
                want = max(0, pos["upto"] - stock - on_order)
                if not want:
                    continue
                got = max(0, int(want * rng.uniform(0.70, 0.92))) if rng.random() < short_share else want
                ordered_by_cycle[(store_id, sup_id, ci, variant_id)] = want
                received_by_cycle[(store_id, sup_id, ci, variant_id)] = got
                on_order += want
            stock += pos_back.get(i, 0)
            want = pos_sold.get(i, 0)
            if want > stock:  # the shelf was short, so another store sent some over
                short = want - stock
                adjusted[i] += short
                transfers += short
                stock += short
            stock -= want
            if (days[i] + timedelta(days=1)).month != days[i].month and stock and rng.random() < 0.07:
                loss = min(1 if rng.random() < 0.8 else 2, stock)  # the month-end count finds a loss
                adjusted[i] -= loss
                stock -= loss
            close[i] = stock

        # What the RFID count finds on the shop floor at the end. The rest is in the stockroom, and
        # shelves that have fallen below their minimum are the ones staff should refill.
        floor = max(0, min(stock, round(rng.gauss(pos["floor_min"] * 1.25, pos["floor_min"] * 0.6))))
        inventory.append({
            "InventoryID": f"{store_id}-{variant_id}",
            "StoreID": store_id,
            "VariantID": variant_id,
            "ProductID": pos["product"],
            "SnapshotDate": end.isoformat(),
            "FloorQty": floor,
            "BackroomQty": stock - floor,
            "OnHandQty": stock,
            "FloorMinQty": pos["floor_min"],
            "ReorderPoint": pos["reorder"],
        })
        for first in months:
            a = day_index[first]
            b = day_index[min(end, date(first.year, first.month, calendar.monthrange(first.year, first.month)[1]))]
            row = {
                "BalanceID": f"{store_id}-{variant_id}-{first:%Y%m}",
                "StoreID": store_id,
                "VariantID": variant_id,
                "ProductID": pos["product"],
                "BalanceMonth": first.isoformat(),
                "OpeningQty": close[a - 1] if a else opening,
                "ReceivedQty": sum(received[a:b + 1]),
                "SoldQty": sum(pos_sold.get(k, 0) for k in range(a, b + 1)),
                "ReturnedQty": sum(pos_back.get(k, 0) for k in range(a, b + 1)),
                "AdjustedQty": sum(adjusted[a:b + 1]),
                "ClosingQty": close[b],
                "DaysOutOfStock": sum(1 for k in range(a, b + 1) if close[k] == 0),
                "DaysBelowShelfMin": sum(1 for k in range(a, b + 1) if close[k] < pos["floor_min"]),
            }
            assert (row["OpeningQty"] + row["ReceivedQty"] - row["SoldQty"] + row["ReturnedQty"]
                    + row["AdjustedQty"] == row["ClosingQty"]), row["BalanceID"]
            ledger.append(row)
    tracked = {(p["store"], p["variant"]) for p in positions}

    # Purchase orders: one per store, supplier and cycle that has anything on it.
    variants_by_supplier = defaultdict(set)
    for (store_id, variant_id) in set(sold) | tracked:
        variants_by_supplier[(store_id, supplier_of_variant[variant_id])].add(variant_id)

    drafts = []
    for store in STORES:
        for sup_id, _, _, _, _ in SUPPLIERS:
            _, _, _, short_share = SUPPLIER_DELIVERY[sup_id]
            for ci, cycle in enumerate(schedule[(store[0], sup_id)]):
                is_open = cycle["delivered"] > end
                unit_rise = SUPPLIER_PRICE_RISE.get(sup_id, 1.0) if cycle["ordered"] >= date(end.year, 1, 1) else 1.0
                po_lines = []
                for variant_id in sorted(variants_by_supplier.get((store[0], sup_id), ())):
                    key = (store[0], variant_id)
                    if key in tracked and not is_open:
                        ordered = ordered_by_cycle.get((store[0], sup_id, ci, variant_id), 0)
                        if not ordered:
                            continue
                        got = received_by_cycle[(store[0], sup_id, ci, variant_id)]
                        product_id = variant_product[variant_id]
                        unit_cost = int(round(cents(product_by_id[product_id]["UnitCost"]) * unit_rise))
                        po_lines.append({"VariantID": variant_id, "ProductID": product_id, "QuantityOrdered": ordered,
                                         "QuantityReceived": got, "unit": unit_cost})
                        continue
                    qty = (ordered_by_cycle.get((store[0], sup_id, ci, variant_id), 0) if key in tracked
                           else demand_before(key, cycle["ordered"]))
                    if not qty:
                        continue
                    if is_open:
                        ordered, got = qty, 0
                    elif rng.random() < short_share:
                        fill = rng.uniform(0.75, 0.95)
                        if key in tracked:
                            ordered, got = max(qty + 1, math.ceil(qty / fill)), qty
                        else:
                            ordered, got = qty, int(qty * fill)
                    else:
                        ordered, got = qty, qty
                    product_id = variant_product[variant_id]
                    unit_cost = int(round(cents(product_by_id[product_id]["UnitCost"]) * unit_rise))
                    po_lines.append({"VariantID": variant_id, "ProductID": product_id, "QuantityOrdered": ordered,
                                     "QuantityReceived": got, "unit": unit_cost})
                if po_lines:
                    drafts.append((cycle, store[0], sup_id, is_open, po_lines))

    drafts.sort(key=lambda d: (d[0]["ordered"], d[1], d[2]))
    purchase_orders, purchase_order_lines = [], []
    for n, (cycle, store_id, sup_id, is_open, po_lines) in enumerate(drafts, 1):
        po_id = f"PO{n:06d}"
        complete = all(l["QuantityReceived"] == l["QuantityOrdered"] for l in po_lines)
        purchase_orders.append({
            "PurchaseOrderID": po_id,
            "SupplierID": sup_id,
            "StoreID": store_id,
            "PurchaseOrderDate": cycle["ordered"].isoformat(),
            "ExpectedDeliveryDate": cycle["expected"].isoformat(),
            "DeliveredDate": "" if is_open else cycle["delivered"].isoformat(),
            "POStatus": "Open" if is_open else "Received" if complete else "Partially received",
            "POTotalCost": money(sum(l["QuantityOrdered"] * l["unit"] for l in po_lines)),
        })
        for k, l in enumerate(po_lines, 1):
            purchase_order_lines.append({
                "PurchaseOrderLineID": f"{po_id}-{k}",
                "PurchaseOrderID": po_id,
                "VariantID": l["VariantID"],
                "ProductID": l["ProductID"],
                "QuantityOrdered": l["QuantityOrdered"],
                "QuantityReceived": l["QuantityReceived"],
                "POUnitCost": money(l["unit"]),
                "POLineCost": money(l["QuantityOrdered"] * l["unit"]),
            })
    return purchase_orders, purchase_order_lines, ledger, inventory, transfers


def daterange(start: date, end: date):
    day = start
    while day <= end:
        yield day
        day += timedelta(days=1)


def window_start(end: date) -> date:
    # A complete previous year plus the current year to date, so "last year" is always answerable.
    return date(end.year - 1, 1, 1)


def parse_end(value: str) -> date:
    if value == "today":
        return date.today()
    if value == "yesterday":
        return date.today() - timedelta(days=1)
    return date.fromisoformat(value)


def build_products(rng: random.Random, start: date):
    yy = start.year % 100
    seasons = [f"SS{yy:02d}", f"FW{yy:02d}", f"SS{(yy + 1) % 100:02d}", "AllSeason"]
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
                    "SeasonCode": rng.choice(seasons),
                    "ListPrice": money(price_cents),
                    "UnitCost": money(cost_cents),
                    "LaunchDate": (start - timedelta(days=rng.randint(30, 540))).isoformat(),
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


def build_customers(rng: random.Random, count: int, start: date):
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
            "JoinDate": (start - timedelta(days=rng.randint(1, 1800))).isoformat(),
            "HomeCity": home[3],
            "HomeStateCode": home[4],
            "PreferredStoreID": rng.choice(store_ids),
        })
    return customers


def markdown_rate(rng: random.Random, day: date) -> float:
    clearance = day.month in (1, 2) or day.month in (7, 8)
    if clearance and rng.random() < 0.42:
        return rng.choice([0.15, 0.20, 0.25, 0.30, 0.40])
    if rng.random() < 0.11:
        return rng.choice([0.10, 0.15, 0.20])
    return 0.0


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the Yuktikara Store dataset.")
    parser.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "data"))
    parser.add_argument(
        "--end", type=parse_end, default=DEFAULT_END,
        help="Last day of data: YYYY-MM-DD, 'yesterday' or 'today' (machine's local date; UTC in Fabric). "
             f"Default {DEFAULT_END}, the committed snapshot.",
    )
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    end = args.end
    start = window_start(end)

    rng = random.Random(SEED)

    products, variants = build_products(rng, start)
    customers = build_customers(rng, 6200, start)

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

    for day in daterange(start, end):
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
                if day > end - timedelta(days=6) and status == "Completed" and rng.random() < 0.45:
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
                    rate = markdown_rate(rng, day)
                    line_gross = unit * qty
                    line_discount = int(round(line_gross * rate))
                    gross += line_gross
                    discount += line_discount
                    order_lines.append({
                        "OrderLineID": f"{order_id}-{line_no}",
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
        if return_date > end:
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
            "OrderLineID": f"{item['OrderID']}-{item['LineNo']}",
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

    dim_date = []
    for day in daterange(start, end):
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

    # Buying, stock, promotions and plans, from the sales above and their own random streams.
    purchase_orders, purchase_order_lines, inventory_balance, inventory, transfers = build_supply_and_stock(
        random.Random(SEED + 11), start, end, products, variants, line_index, returns)
    promotions, line_promotions = build_promotions(start, end, orders, lines)
    targets = build_targets(random.Random(SEED + 22), start, end, orders, returns)

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
        "PurchaseOrder.csv": purchase_orders,
        "PurchaseOrderLine.csv": purchase_order_lines,
        "InventoryBalance.csv": inventory_balance,
        "Promotion.csv": promotions,
        "OrderLinePromotion.csv": line_promotions,
        "SalesTarget.csv": targets,
    }

    manifest = {"company": "Yuktikara Store", "seed": SEED,
                "period": {"start": start.isoformat(), "end": end.isoformat()},
                "tax_rate": TAX_RATE, "tables": {}}

    for filename, rows in tables.items():
        path = out / filename
        with path.open("w", newline="", encoding="utf-8") as fh:
            # LF, not the csv module's default CRLF, so the hashes match a git checkout (.gitattributes).
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        raw = path.read_bytes()
        manifest["tables"][filename] = {
            "rows": len(rows),
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }

    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")

    print(f"Yuktikara Store — {start} to {end}")
    for filename, meta in manifest["tables"].items():
        print(f"  {filename:24s} {meta['rows']:>7,} rows  {meta['bytes'] / 1_048_576:.2f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
