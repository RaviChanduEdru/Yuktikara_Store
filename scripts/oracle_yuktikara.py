#!/usr/bin/env python3
"""Compute ground truth for the Yuktikara Store dataset from the generated CSVs.

Reads only the files that get loaded into Fabric, so every number here is one an
agent could in principle derive. Standard library only.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path

SALES_STATUSES = {"Completed", "Shipped"}
ZERO = Decimal("0.00")


def read(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def dec(value: str) -> Decimal:
    return Decimal(value)


def quarter_of(iso: str) -> str:
    year, month = int(iso[:4]), int(iso[5:7])
    return f"{year}-Q{(month - 1) // 3 + 1}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute Yuktikara Store ground truth.")
    parser.add_argument("--data", default=str(Path(__file__).resolve().parent.parent / "data"))
    args = parser.parse_args()
    data = Path(args.data)

    orders = read(data / "SalesOrder.csv")
    lines = read(data / "SalesOrderLine.csv")
    returns = read(data / "SalesReturn.csv")
    products = {p["ProductID"]: p for p in read(data / "Product.csv")}
    variants = {v["VariantID"]: v for v in read(data / "ProductVariant.csv")}
    stores = {s["StoreID"]: s for s in read(data / "Store.csv")}
    reasons = {r["ReturnReasonID"]: r for r in read(data / "ReturnReason.csv")}
    suppliers = {s["SupplierID"]: s for s in read(data / "Supplier.csv")}
    purchase_orders = read(data / "PurchaseOrder.csv")
    purchase_order_lines = read(data / "PurchaseOrderLine.csv")
    inventory = read(data / "StoreInventory.csv")
    balances = read(data / "InventoryBalance.csv")
    promotions = read(data / "Promotion.csv")
    line_promotions = read(data / "OrderLinePromotion.csv")
    targets = read(data / "SalesTarget.csv")

    order_by_id = {o["OrderID"]: o for o in orders}
    sales_orders = {o["OrderID"] for o in orders if o["OrderStatus"] in SALES_STATUSES}

    gross_all = sum(dec(o["GrossAmount"]) for o in orders)
    discount_all = sum(dec(o["DiscountAmount"]) for o in orders)
    subtotal_sales = sum(dec(o["SubTotal"]) for o in orders if o["OrderID"] in sales_orders)
    gross_sales_status = sum(dec(o["GrossAmount"]) for o in orders if o["OrderID"] in sales_orders)
    ordertotal_sales = sum(dec(o["OrderTotal"]) for o in orders if o["OrderID"] in sales_orders)

    accepted = [r for r in returns if r["ReturnStatus"] == "Accepted"]
    returns_total = sum(dec(r["ReturnAmount"]) for r in accepted)

    subtotal_by_period: dict[str, dict[str, Decimal]] = {"year": defaultdict(lambda: ZERO),
                                                         "quarter": defaultdict(lambda: ZERO),
                                                         "month": defaultdict(lambda: ZERO)}
    returns_by_period: dict[str, dict[str, Decimal]] = {"year": defaultdict(lambda: ZERO),
                                                        "quarter": defaultdict(lambda: ZERO),
                                                        "month": defaultdict(lambda: ZERO)}
    gross_by_period: dict[str, dict[str, Decimal]] = {"year": defaultdict(lambda: ZERO),
                                                      "quarter": defaultdict(lambda: ZERO),
                                                      "month": defaultdict(lambda: ZERO)}
    ordertotal_by_period: dict[str, dict[str, Decimal]] = {"year": defaultdict(lambda: ZERO),
                                                           "quarter": defaultdict(lambda: ZERO),
                                                           "month": defaultdict(lambda: ZERO)}

    for o in orders:
        day = o["OrderDate"]
        keys = {"year": day[:4], "quarter": quarter_of(day), "month": day[:7]}
        for grain, key in keys.items():
            gross_by_period[grain][key] += dec(o["GrossAmount"])
            if o["OrderID"] in sales_orders:
                subtotal_by_period[grain][key] += dec(o["SubTotal"])
                ordertotal_by_period[grain][key] += dec(o["OrderTotal"])

    for r in accepted:
        day = r["ReturnDate"]
        keys = {"year": day[:4], "quarter": quarter_of(day), "month": day[:7]}
        for grain, key in keys.items():
            returns_by_period[grain][key] += dec(r["ReturnAmount"])

    def net_series(grain: str) -> dict[str, dict[str, str]]:
        keys = sorted(set(subtotal_by_period[grain]) | set(returns_by_period[grain]))
        out = {}
        for key in keys:
            subtotal = subtotal_by_period[grain][key]
            returned = returns_by_period[grain][key]
            out[key] = {
                "gross_all_statuses": f"{gross_by_period[grain][key]:.2f}",
                "ordertotal_sales_statuses_includes_tax": f"{ordertotal_by_period[grain][key]:.2f}",
                "subtotal_sales_statuses": f"{subtotal:.2f}",
                "accepted_returns": f"{returned:.2f}",
                "net_sales": f"{subtotal - returned:.2f}",
            }
        return out

    cancelled_by_year: dict[str, Decimal] = defaultdict(lambda: ZERO)
    pending_by_year: dict[str, Decimal] = defaultdict(lambda: ZERO)
    for o in orders:
        if o["OrderStatus"] == "Cancelled":
            cancelled_by_year[o["OrderDate"][:4]] += dec(o["GrossAmount"])
        elif o["OrderStatus"] == "Pending":
            pending_by_year[o["OrderDate"][:4]] += dec(o["GrossAmount"])

    units_sold: dict[str, int] = defaultdict(int)
    for line in lines:
        if line["OrderID"] in sales_orders:
            units_sold[line["ProductID"]] += int(line["Quantity"])

    units_returned: dict[str, int] = defaultdict(int)
    value_returned: dict[str, Decimal] = defaultdict(lambda: ZERO)
    for r in accepted:
        units_returned[r["ProductID"]] += int(r["QuantityReturned"])
        value_returned[r["ProductID"]] += dec(r["ReturnAmount"])

    return_rates = []
    for product_id, sold in units_sold.items():
        if sold < 200:
            continue
        returned = units_returned.get(product_id, 0)
        return_rates.append({
            "ProductID": product_id,
            "ProductName": products[product_id]["ProductName"],
            "DepartmentName": products[product_id]["DepartmentName"],
            "SupplierID": products[product_id]["SupplierID"],
            "units_sold": sold,
            "units_returned": returned,
            "return_rate_pct": f"{returned / sold * 100:.2f}",
            "value_returned": f"{value_returned.get(product_id, ZERO):.2f}",
        })
    return_rates.sort(key=lambda r: float(r["return_rate_pct"]), reverse=True)

    dept_sold: dict[str, int] = defaultdict(int)
    dept_returned: dict[str, int] = defaultdict(int)
    for product_id, sold in units_sold.items():
        dept_sold[products[product_id]["DepartmentName"]] += sold
    for r in accepted:
        dept_returned[products[r["ProductID"]]["DepartmentName"]] += int(r["QuantityReturned"])
    dept_rates = {
        dept: {
            "units_sold": sold,
            "units_returned": dept_returned.get(dept, 0),
            "return_rate_pct": f"{dept_returned.get(dept, 0) / sold * 100:.2f}",
        }
        for dept, sold in sorted(dept_sold.items())
    }

    top_style = return_rates[0]["ProductID"]
    size_breakdown: dict[str, dict[str, int]] = defaultdict(lambda: {"sold": 0, "returned": 0})
    for line in lines:
        if line["OrderID"] in sales_orders and line["ProductID"] == top_style:
            size_breakdown[variants[line["VariantID"]]["SizeCode"]]["sold"] += int(line["Quantity"])
    for r in accepted:
        if r["ProductID"] == top_style:
            size_breakdown[variants[r["VariantID"]]["SizeCode"]]["returned"] += int(r["QuantityReturned"])
    size_rows = []
    for size, counts in size_breakdown.items():
        rate = counts["returned"] / counts["sold"] * 100 if counts["sold"] else 0.0
        size_rows.append({"SizeCode": size, **counts, "return_rate_pct": f"{rate:.2f}"})
    size_rows.sort(key=lambda r: float(r["SizeCode"]) if r["SizeCode"].replace(".", "").isdigit() else 0)

    reason_counts: dict[str, int] = defaultdict(int)
    top_style_reasons: dict[str, int] = defaultdict(int)
    for r in accepted:
        reason_counts[r["ReturnReasonID"]] += 1
        if r["ProductID"] == top_style:
            top_style_reasons[r["ReturnReasonID"]] += 1

    channel_subtotal: dict[str, Decimal] = defaultdict(lambda: ZERO)
    channel_returns: dict[str, Decimal] = defaultdict(lambda: ZERO)
    for o in orders:
        if o["OrderID"] in sales_orders:
            channel_subtotal[o["Channel"]] += dec(o["SubTotal"])
    for r in accepted:
        channel_returns[order_by_id[r["OrderID"]]["Channel"]] += dec(r["ReturnAmount"])
    channel = {
        ch: {
            "subtotal_sales_statuses": f"{channel_subtotal[ch]:.2f}",
            "accepted_returns": f"{channel_returns[ch]:.2f}",
            "net_sales": f"{channel_subtotal[ch] - channel_returns[ch]:.2f}",
        }
        for ch in sorted(channel_subtotal)
    }

    store_subtotal: dict[str, Decimal] = defaultdict(lambda: ZERO)
    for o in orders:
        if o["OrderID"] in sales_orders:
            store_subtotal[o["StoreID"]] += dec(o["SubTotal"])
    store_return_absorbed: dict[str, Decimal] = defaultdict(lambda: ZERO)
    online_returns_absorbed: dict[str, Decimal] = defaultdict(lambda: ZERO)
    for r in accepted:
        store_return_absorbed[r["ReturnStoreID"]] += dec(r["ReturnAmount"])
        if order_by_id[r["OrderID"]]["Channel"] == "Online":
            online_returns_absorbed[r["ReturnStoreID"]] += dec(r["ReturnAmount"])

    store_rows = []
    for store_id, subtotal in store_subtotal.items():
        store_rows.append({
            "StoreID": store_id,
            "StoreName": stores[store_id]["StoreName"],
            "RegionName": stores[store_id]["RegionName"],
            "subtotal_sales_statuses": f"{subtotal:.2f}",
            "returns_absorbed_at_store": f"{store_return_absorbed.get(store_id, ZERO):.2f}",
            "online_returns_absorbed": f"{online_returns_absorbed.get(store_id, ZERO):.2f}",
        })
    store_rows.sort(key=lambda r: Decimal(r["subtotal_sales_statuses"]), reverse=True)

    dept_subtotal: dict[str, Decimal] = defaultdict(lambda: ZERO)
    dept_returns: dict[str, Decimal] = defaultdict(lambda: ZERO)
    for line in lines:
        if line["OrderID"] in sales_orders:
            dept_subtotal[products[line["ProductID"]]["DepartmentName"]] += dec(line["LineTotal"])
    for r in accepted:
        dept_returns[products[r["ProductID"]]["DepartmentName"]] += dec(r["ReturnAmount"])
    department = {
        dept: {
            "subtotal_sales_statuses": f"{dept_subtotal[dept]:.2f}",
            "accepted_returns": f"{dept_returns[dept]:.2f}",
            "net_sales": f"{dept_subtotal[dept] - dept_returns[dept]:.2f}",
        }
        for dept in sorted(dept_subtotal, key=lambda d: dept_subtotal[d] - dept_returns[d], reverse=True)
    }

    # --- Buying and deliveries ------------------------------------------------------------------
    po_by_id = {p["PurchaseOrderID"]: p for p in purchase_orders}
    supplier_stats: dict[str, dict] = defaultdict(
        lambda: {"delivered": 0, "on_time": 0, "days_late": 0, "open": 0,
                 "ordered_units": 0, "received_units": 0, "spend": ZERO})
    for po in purchase_orders:
        stat = supplier_stats[po["SupplierID"]]
        if not po["DeliveredDate"]:
            stat["open"] += 1
            continue
        stat["delivered"] += 1
        late = (date.fromisoformat(po["DeliveredDate"]) - date.fromisoformat(po["ExpectedDeliveryDate"])).days
        if late <= 0:
            stat["on_time"] += 1
        else:
            stat["days_late"] += late
    open_units = 0
    open_value = ZERO
    for line in purchase_order_lines:
        po = po_by_id[line["PurchaseOrderID"]]
        stat = supplier_stats[po["SupplierID"]]
        if po["DeliveredDate"]:
            stat["ordered_units"] += int(line["QuantityOrdered"])
            stat["received_units"] += int(line["QuantityReceived"])
            stat["spend"] += dec(line["POUnitCost"]) * int(line["QuantityReceived"])
        else:
            open_units += int(line["QuantityOrdered"])
            open_value += dec(line["POLineCost"])
    supplier_performance = {}
    for supplier_id, stat in sorted(supplier_stats.items()):
        delivered = stat["delivered"]
        late_count = delivered - stat["on_time"]
        supplier_performance[suppliers[supplier_id]["SupplierName"]] = {
            "SupplierID": supplier_id,
            "promised_lead_time_days": int(suppliers[supplier_id]["LeadTimeDays"]),
            "quality_rating": suppliers[supplier_id]["QualityRating"],
            "deliveries": delivered,
            "on_time_pct": f"{stat['on_time'] / delivered * 100:.2f}" if delivered else "0.00",
            "avg_days_late_when_late": f"{stat['days_late'] / late_count:.2f}" if late_count else "0.00",
            "fill_rate_pct": f"{stat['received_units'] / stat['ordered_units'] * 100:.2f}" if stat["ordered_units"] else "0.00",
            "units_received": stat["received_units"],
            "spend": f"{stat['spend']:.2f}",
            "open_orders": stat["open"],
        }

    # --- Stock over time, and the checks that it reconciles ---------------------------------------
    snapshot_by_position = {(i["StoreID"], i["VariantID"]): i for i in inventory}
    last_month = max(b["BalanceMonth"] for b in balances)
    ledger_receipts: dict[tuple, int] = defaultdict(int)
    ledger_sold: dict[tuple, int] = defaultdict(int)
    for row in balances:
        key = (row["StoreID"], row["VariantID"], row["BalanceMonth"][:7])
        ledger_receipts[key] += int(row["ReceivedQty"])
        ledger_sold[key] += int(row["SoldQty"])
        assert (int(row["OpeningQty"]) + int(row["ReceivedQty"]) - int(row["SoldQty"]) + int(row["ReturnedQty"])
                + int(row["AdjustedQty"]) == int(row["ClosingQty"])), f"ledger does not balance: {row['BalanceID']}"
        if row["BalanceMonth"] == last_month:
            assert int(row["ClosingQty"]) == int(snapshot_by_position[(row["StoreID"], row["VariantID"])]["OnHandQty"]), \
                f"ledger does not close on the snapshot: {row['BalanceID']}"
    delivered_units: dict[tuple, int] = defaultdict(int)
    for line in purchase_order_lines:
        po = po_by_id[line["PurchaseOrderID"]]
        if po["DeliveredDate"]:
            delivered_units[(po["StoreID"], line["VariantID"], po["DeliveredDate"][:7])] += int(line["QuantityReceived"])
    for key, units in ledger_receipts.items():
        assert units == delivered_units.get(key, 0), f"ledger receipts do not match deliveries: {key}"
    sold_units: dict[tuple, int] = defaultdict(int)
    for line in lines:
        order = order_by_id[line["OrderID"]]
        if order["OrderID"] in sales_orders:
            sold_units[(order["StoreID"], line["VariantID"], order["OrderDate"][:7])] += int(line["Quantity"])
    for key, units in ledger_sold.items():
        assert units == sold_units.get(key, 0), f"ledger sales do not match orders: {key}"

    stock_by_supplier: dict[str, dict] = defaultdict(lambda: {"days_out": 0, "days_below": 0, "position_months": 0})
    stockout_by_style: dict[str, int] = defaultdict(int)
    for row in balances:
        supplier_id = products[row["ProductID"]]["SupplierID"]
        stat = stock_by_supplier[supplier_id]
        stat["days_out"] += int(row["DaysOutOfStock"])
        stat["days_below"] += int(row["DaysBelowShelfMin"])
        stat["position_months"] += 1
        stockout_by_style[products[row["ProductID"]]["ProductName"]] += int(row["DaysOutOfStock"])
    availability = {
        suppliers[supplier_id]["SupplierName"]: {
            "SupplierID": supplier_id,
            "stockout_days_per_position_month": f"{stat['days_out'] / stat['position_months']:.3f}",
            "below_shelf_min_days_per_position_month": f"{stat['days_below'] / stat['position_months']:.3f}",
            "position_months": stat["position_months"],
        }
        for supplier_id, stat in sorted(stock_by_supplier.items(),
                                        key=lambda kv: -kv[1]["days_out"] / kv[1]["position_months"])
    }
    below_min = [i for i in inventory if int(i["FloorQty"]) < int(i["FloorMinQty"])]
    shelf_state = {
        "positions": len(inventory),
        "below_shelf_minimum": len(below_min),
        "below_shelf_minimum_pct": f"{len(below_min) / len(inventory) * 100:.2f}",
        "empty_shelves": sum(1 for i in inventory if int(i["FloorQty"]) == 0),
        "units_on_hand": sum(int(i["OnHandQty"]) for i in inventory),
        "units_on_the_floor": sum(int(i["FloorQty"]) for i in inventory),
    }

    # --- Promotions --------------------------------------------------------------------------------
    promo_by_line = {link["OrderLineID"]: link["PromotionID"] for link in line_promotions}
    promo_stats: dict[str, dict] = defaultdict(lambda: {"lines": 0, "units": 0, "markdown": ZERO, "net": ZERO})
    for line in lines:
        promo_id = promo_by_line.get(line["OrderLineID"])
        if promo_id is None or line["OrderID"] not in sales_orders:
            continue
        stat = promo_stats[promo_id]
        stat["lines"] += 1
        stat["units"] += int(line["Quantity"])
        stat["markdown"] += dec(line["DiscountAmount"])
        stat["net"] += dec(line["LineTotal"])
    promotion_results = {
        promo["PromotionName"]: {
            "PromotionID": promo["PromotionID"],
            "type": promo["PromotionType"],
            "runs": f"{promo['PromotionStartDate']} to {promo['PromotionEndDate']}",
            "lines": promo_stats[promo["PromotionID"]]["lines"],
            "units": promo_stats[promo["PromotionID"]]["units"],
            "markdown": f"{promo_stats[promo['PromotionID']]['markdown']:.2f}",
            "sales_after_markdown": f"{promo_stats[promo['PromotionID']]['net']:.2f}",
        }
        for promo in promotions
    }

    # --- Plans against actuals ---------------------------------------------------------------------
    # A store's net sales: what it sold, less the returns of what it sold, on the day they were accepted.
    store_month_net: dict[tuple, Decimal] = defaultdict(lambda: ZERO)
    for order in orders:
        if order["OrderID"] in sales_orders:
            store_month_net[(order["StoreID"], order["OrderDate"][:7])] += dec(order["SubTotal"])
    for r in accepted:
        seller = order_by_id[r["OrderID"]]["StoreID"]
        store_month_net[(seller, r["ReturnDate"][:7])] -= dec(r["ReturnAmount"])
    target_by_store_month = {(t["StoreID"], t["TargetMonth"][:7]): dec(t["TargetNetSales"]) for t in targets}
    months_with_sales = sorted({m for (_, m) in store_month_net})
    plan_months = [m for m in months_with_sales if m < months_with_sales[-1]]  # skip the part month at the end
    against_plan = []
    for store_id, store in sorted(stores.items()):
        target = sum(target_by_store_month.get((store_id, m), ZERO) for m in plan_months)
        actual = sum(store_month_net.get((store_id, m), ZERO) for m in plan_months)
        against_plan.append({
            "StoreID": store_id,
            "StoreName": store["StoreName"],
            "opened": store["OpenedDate"],
            "target": f"{target:.2f}",
            "net_sales": f"{actual:.2f}",
            "pct_of_target": f"{actual / target * 100:.2f}" if target else "0.00",
        })
    against_plan.sort(key=lambda row: float(row["pct_of_target"]))

    oracle = {
        "company": "Yuktikara Store",
        "definition": (
            "Net sales = SubTotal of orders whose OrderStatus is Completed or Shipped, "
            "minus ReturnAmount of returns whose ReturnStatus is Accepted, counted on ReturnDate. "
            "Cancelled and Pending orders are not sales. Tax is not sales."
        ),
        "totals": {
            "gross_all_statuses": f"{gross_all:.2f}",
            "discount_all_statuses": f"{discount_all:.2f}",
            "gross_sales_statuses": f"{gross_sales_status:.2f}",
            "subtotal_sales_statuses": f"{subtotal_sales:.2f}",
            "ordertotal_sales_statuses_includes_tax": f"{ordertotal_sales:.2f}",
            "accepted_returns": f"{returns_total:.2f}",
            "net_sales": f"{subtotal_sales - returns_total:.2f}",
            "order_count": len(orders),
            "line_count": len(lines),
            "return_count": len(returns),
            "accepted_return_count": len(accepted),
        },
        "net_sales_by_year": net_series("year"),
        "net_sales_by_quarter": net_series("quarter"),
        "net_sales_by_month": net_series("month"),
        "cancelled_gross_by_year": {y: f"{v:.2f}" for y, v in sorted(cancelled_by_year.items())},
        "pending_gross_by_year": {y: f"{v:.2f}" for y, v in sorted(pending_by_year.items())},
        "return_rate_by_department": dept_rates,
        "top_return_rate_products": return_rates[:10],
        "top_style_size_breakdown": {
            "ProductID": top_style,
            "ProductName": products[top_style]["ProductName"],
            "sizes": size_rows,
            "reason_counts": {
                reasons[rid]["ReturnReasonName"]: count
                for rid, count in sorted(top_style_reasons.items(), key=lambda kv: kv[1], reverse=True)
            },
        },
        "return_reason_counts": {
            reasons[rid]["ReturnReasonName"]: count
            for rid, count in sorted(reason_counts.items(), key=lambda kv: kv[1], reverse=True)
        },
        "net_sales_by_channel": channel,
        "net_sales_by_department": department,
        "stores": store_rows,
        "supplier_performance": supplier_performance,
        "open_purchase_orders": {"orders": sum(v["open_orders"] for v in supplier_performance.values()),
                                 "units": open_units, "value": f"{open_value:.2f}"},
        "stock_availability_by_supplier": availability,
        "shelf_state_at_snapshot": shelf_state,
        "stockout_days_top_styles": dict(sorted(stockout_by_style.items(), key=lambda kv: -kv[1])[:10]),
        "promotions": promotion_results,
        "net_sales_against_plan": {"months": f"{plan_months[0]} to {plan_months[-1]}", "stores": against_plan},
    }

    out = data / "expected_answers.json"
    out.write_text(json.dumps(oracle, indent=2) + "\n", encoding="utf-8", newline="\n")

    t = oracle["totals"]
    print("Yuktikara Store ground truth")
    print(f"  orders {t['order_count']:,}  lines {t['line_count']:,}  returns {t['return_count']:,}")
    print(f"  gross, all statuses          {t['gross_all_statuses']:>16}")
    print(f"  subtotal, sales statuses     {t['subtotal_sales_statuses']:>16}")
    print(f"  accepted returns             {t['accepted_returns']:>16}")
    print(f"  NET SALES                    {t['net_sales']:>16}")
    gap = Decimal(t["gross_all_statuses"]) - Decimal(t["net_sales"])
    print(f"  gap gross to net             {gap:>16.2f}  ({gap / Decimal(t['gross_all_statuses']) * 100:.1f}%)")
    print()
    print("  top return rates:")
    for row in oracle["top_return_rate_products"][:4]:
        print(f"    {row['ProductName']:<34} {row['units_returned']:>5}/{row['units_sold']:<6} {row['return_rate_pct']:>6}%")
    print()
    print("  by department:")
    for dept, row in oracle["return_rate_by_department"].items():
        print(f"    {dept:<12} {row['return_rate_pct']:>6}%")
    print()
    print("  suppliers:")
    for name, row in oracle["supplier_performance"].items():
        print(f"    {name:<28}{row['on_time_pct']:>7}% on time {row['fill_rate_pct']:>7}% filled "
              f"{row['open_orders']:>4} open")
    print()
    print(f"  shelves below their minimum  {shelf_state['below_shelf_minimum']:>7,} of {shelf_state['positions']:,}"
          f" ({shelf_state['below_shelf_minimum_pct']}%)")
    behind = [row for row in against_plan if float(row["pct_of_target"]) < 100]
    print(f"  stores behind plan           {len(behind):>7} of {len(against_plan)}"
          f"  (lowest {against_plan[0]['StoreName']}, {against_plan[0]['pct_of_target']}%)")
    print("  the stock ledger, deliveries and sales reconcile")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
