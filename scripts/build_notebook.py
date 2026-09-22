"""Build fabric/load_yuktikara_data.ipynb. Edit the cells here, never the .ipynb by hand."""

import json
import sys
from pathlib import Path

out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "fabric" / "load_yuktikara_data.ipynb"

cells = []


def md(text):
    cells.append({"cell_type": "markdown", "metadata": {}, "source": text.strip("\n")})


def code(text, tags=None):
    cells.append({
        "cell_type": "code",
        "metadata": {"tags": tags} if tags else {},
        "execution_count": None,
        "outputs": [],
        "source": text.strip("\n"),
    })


md("""
# Load the Yuktikara Store data

Reads the dataset's CSV files from **Files** and writes them as lakehouse tables with **explicit column
types** (dates as `date`, money as `double`), which is what ontology binding needs and what point-and-click
loading can't give you. Then it checks every table and prints the run's headline numbers.

No data is generated here: Fabric runs no code in this build that isn't loading data.

**Before the first run**

- Attach the Yuktikara lakehouse (`yuktikara_lh`) as this notebook's **default lakehouse**. It must be
  created with *Lakehouse schemas* checked and OneLake security off.
- Upload the repo's `data/` folder to `Files/yuktikara/data/`: the 17 CSVs, plus `manifest.json` (the row
  counts this notebook verifies against) and `expected_answers.json` (the answer key it reports from).

**To move the data's dates on**, regenerate it on your own machine, which takes seconds, then upload the new
files and run this again:

```
python scripts/generate_yuktikara.py --end yesterday
python scripts/oracle_yuktikara.py
```

**After every run**, refresh the ontology's graph model (workspace → graph model → … → Schedule → Refresh
now). The ontology doesn't see new rows until you do.

Never load `expected_answers.json` into a table, and never paste it into an agent. It is the answer key.
""")

code("""
# Parameters
DATA_FOLDER = "Files/yuktikara/data"   # where you uploaded the repo's data/ folder
""", tags=["parameters"])

md("## 1. Find the files")

code("""
import json
from datetime import date
from pathlib import Path

local = Path("/lakehouse/default") / DATA_FOLDER
if not (local / "manifest.json").exists():
    raise FileNotFoundError(
        f"No manifest.json under {DATA_FOLDER}. Upload the repo's data/ folder there, and check that the "
        "Yuktikara lakehouse is this notebook's default lakehouse."
    )
manifest = json.loads((local / "manifest.json").read_text(encoding="utf-8"))
period = manifest["period"]
end = date.fromisoformat(period["end"])
print(f"{len(manifest['tables'])} files, {period['start']} to {period['end']}")
""")

md("## 2. Write the lakehouse tables with explicit types")

code("""
from pyspark.sql.types import (BooleanType, DateType, DoubleType, IntegerType, StringType, StructField,
                               StructType)

S, I, D, DT, B = StringType(), IntegerType(), DoubleType(), DateType(), BooleanType()

# csv file: (schema.table, columns). Schemas group tables by business area, as in Microsoft's IQ accelerator.
TABLES = {
    "Store.csv": ("store.store", [
        ("StoreID", S), ("StoreName", S), ("RegionName", S), ("City", S), ("StateCode", S),
        ("Latitude", D), ("Longitude", D), ("StoreFormat", S), ("SquareFeet", I), ("OpenedDate", DT)]),
    "Supplier.csv": ("product.supplier", [
        ("SupplierID", S), ("SupplierName", S), ("Country", S), ("LeadTimeDays", I), ("QualityRating", D)]),
    "Product.csv": ("product.product", [
        ("ProductID", S), ("StyleCode", S), ("ProductName", S), ("DepartmentName", S), ("CategoryName", S),
        ("SupplierID", S), ("SeasonCode", S), ("ListPrice", D), ("UnitCost", D), ("LaunchDate", DT),
        ("IsRfidTagged", B)]),
    "ProductVariant.csv": ("product.product_variant", [
        ("VariantID", S), ("ProductID", S), ("SKU", S), ("ColorName", S), ("SizeCode", S), ("SizeOrder", I),
        ("ListPrice", D)]),
    "Customer.csv": ("customer.customer", [
        ("CustomerID", S), ("CustomerName", S), ("LoyaltyTier", S), ("JoinDate", DT), ("HomeCity", S),
        ("HomeStateCode", S), ("PreferredStoreID", S)]),
    "DimDate.csv": ("shared.dim_date", [
        ("DateKey", I), ("Date", DT), ("Year", I), ("Quarter", S), ("YearQuarter", S), ("MonthNumber", I),
        ("MonthName", S), ("YearMonth", S), ("DayOfWeek", I), ("DayName", S), ("IsWeekend", B)]),
    "SalesOrder.csv": ("sales.sales_order", [
        ("OrderID", S), ("OrderNumber", S), ("StoreID", S), ("CustomerID", S), ("Channel", S),
        ("OrderDate", DT), ("OrderStatus", S), ("GrossAmount", D), ("DiscountAmount", D), ("SubTotal", D),
        ("TaxAmount", D), ("OrderTotal", D), ("PaymentMethod", S)]),
    "SalesOrderLine.csv": ("sales.sales_order_line", [
        ("OrderLineID", S), ("OrderID", S), ("OrderLineNumber", I), ("VariantID", S), ("ProductID", S), ("Quantity", I),
        ("UnitPrice", D), ("DiscountAmount", D), ("LineTotal", D)]),
    "SalesReturn.csv": ("sales.sales_return", [
        ("ReturnID", S), ("OrderID", S), ("OrderLineNumber", I), ("OrderLineID", S), ("VariantID", S),
        ("ProductID", S),
        ("ReturnDate", DT), ("ReturnStoreID", S), ("QuantityReturned", I), ("ReturnAmount", D),
        ("ReturnStatus", S), ("ReturnReasonID", S), ("RestockFlag", B)]),
    "ReturnReason.csv": ("sales.return_reason", [
        ("ReturnReasonID", S), ("ReturnReasonName", S), ("ReturnCategory", S)]),
    "StoreInventory.csv": ("store.store_inventory", [
        ("InventoryID", S), ("StoreID", S), ("VariantID", S), ("ProductID", S), ("SnapshotDate", DT), ("FloorQty", I),
        ("BackroomQty", I), ("OnHandQty", I), ("FloorMinQty", I), ("ReorderPoint", I)]),
    "InventoryBalance.csv": ("store.inventory_balance", [
        ("BalanceID", S), ("StoreID", S), ("VariantID", S), ("ProductID", S), ("BalanceMonth", DT),
        ("OpeningQty", I), ("ReceivedQty", I), ("SoldQty", I), ("ReturnedQty", I), ("AdjustedQty", I),
        ("ClosingQty", I), ("DaysOutOfStock", I), ("DaysBelowShelfMin", I)]),
    "PurchaseOrder.csv": ("supply.purchase_order", [
        ("PurchaseOrderID", S), ("SupplierID", S), ("StoreID", S), ("PurchaseOrderDate", DT),
        ("ExpectedDeliveryDate", DT), ("DeliveredDate", DT), ("POStatus", S), ("POTotalCost", D)]),
    "PurchaseOrderLine.csv": ("supply.purchase_order_line", [
        ("PurchaseOrderLineID", S), ("PurchaseOrderID", S), ("VariantID", S), ("ProductID", S),
        ("QuantityOrdered", I), ("QuantityReceived", I), ("POUnitCost", D), ("POLineCost", D)]),
    "Promotion.csv": ("sales.promotion", [
        ("PromotionID", S), ("PromotionName", S), ("PromotionType", S), ("PromotionStartDate", DT),
        ("PromotionEndDate", DT), ("DiscountDepth", S)]),
    "OrderLinePromotion.csv": ("sales.order_line_promotion", [
        ("OrderLineID", S), ("PromotionID", S)]),
    "SalesTarget.csv": ("sales.sales_target", [
        ("TargetID", S), ("StoreID", S), ("TargetMonth", DT), ("TargetNetSales", D)]),
}


for schema in sorted({table.split(".")[0] for table, _ in TABLES.values()}):
    try:
        spark.sql(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    except Exception as err:
        raise RuntimeError(
            f"Couldn't create schema '{schema}'. Check the default lakehouse was created with Lakehouse schemas, "
            "or create the schema by hand: lakehouse explorer → Tables → … → New schema."
        ) from err

for csv_name, (table, cols) in TABLES.items():
    header = (local / csv_name).open(encoding="utf-8").readline().rstrip("\\n").split(",")
    expected = [c for c, _ in cols]
    if header != expected:
        raise ValueError(f"{csv_name}: file columns {header} don't match the schema {expected}")
    df = (spark.read.format("csv")
          .option("header", True)
          .option("escape", '"')
          .option("mode", "FAILFAST")
          .schema(StructType([StructField(c, t) for c, t in cols]))
          .load(f"{DATA_FOLDER}/{csv_name}"))
    (df.write.format("delta")
       .mode("overwrite")
       .option("overwriteSchema", "true")
       .saveAsTable(table))
    print(f"wrote {table}")
""")

md("## 3. Verify")

code("""
failures = 0
for csv_name, (name, cols) in TABLES.items():
    df = spark.table(name)
    rows = df.count()
    expected_rows = manifest["tables"][csv_name]["rows"]
    actual = {f.name: f.dataType for f in df.schema.fields}
    wrong_types = [c for c, t in cols if actual.get(c) != t]
    props = {r["key"]: r["value"] for r in spark.sql(f"SHOW TBLPROPERTIES {name}").collect()}
    mapping = props.get("delta.columnMapping.mode", "none")
    problems = []
    if rows != expected_rows:
        problems.append(f"{rows:,} rows, expected {expected_rows:,}")
    if wrong_types:
        problems.append(f"wrong types: {wrong_types}")
    if mapping != "none":
        problems.append(f"column mapping '{mapping}' (ontology can't bind this table)")
    failures += bool(problems)
    print(f"{'FAIL' if problems else 'PASS'}  {name:<24} {rows:>7,} rows  {'; '.join(problems)}")

if failures:
    raise RuntimeError(f"{failures} table(s) failed verification")
print(f"\\nPASS: {len(TABLES)} tables, row counts match the manifest, dates are date, money is double, no column mapping.")
""")

md("## 4. The data's headline numbers")

code("""
import calendar

answers = json.loads((local / "expected_answers.json").read_text(encoding="utf-8"))

q = (end.month - 1) // 3 + 1
quarter_last_day = date(end.year, q * 3, calendar.monthrange(end.year, q * 3)[1])
if end == quarter_last_day:
    last_quarter = f"{end.year}-Q{q}"
else:
    last_quarter = f"{end.year}-Q{q - 1}" if q > 1 else f"{end.year - 1}-Q4"

t = answers["totals"]
lq = answers["net_sales_by_quarter"].get(last_quarter)
print(f"Window                     {manifest['period']['start']} to {manifest['period']['end']}")
print(f"Net sales, whole window    {float(t['net_sales']):>16,.2f}")
print(f"Gross, all statuses        {float(t['gross_all_statuses']):>16,.2f}")
if lq:
    year, qn = int(last_quarter[:4]), int(last_quarter[-1])
    q_start = date(year, qn * 3 - 2, 1)
    q_end = date(year, qn * 3, calendar.monthrange(year, qn * 3)[1])
    print(f"Last complete quarter      {last_quarter}  ({q_start} to {q_end})")
    print(f"  1 gross, every order     {float(lq['gross_all_statuses']):>16,.2f}")
    print(f"  2 order total, sales     {float(lq['ordertotal_sales_statuses_includes_tax']):>16,.2f}")
    print(f"  3 subtotal, sales        {float(lq['subtotal_sales_statuses']):>16,.2f}")
    print(f"  4 NET SALES              {float(lq['net_sales']):>16,.2f}")
    gap = (float(lq["gross_all_statuses"]) - float(lq["net_sales"])) / float(lq["gross_all_statuses"]) * 100
    print(f"  gap, 1 to 4              {gap:>15.1f}%")
top = answers["top_return_rate_products"][0]
print(f"Highest return rate        {top['ProductName']} {top['return_rate_pct']}%")
reasons = answers["top_style_size_breakdown"]["reason_counts"]
too_small = reasons.get("Too small", 0)
print(f"  its accepted returns     {sum(reasons.values()):,}, of which 'Too small' {too_small:,} "
      f"({too_small / sum(reasons.values()) * 100:.0f}%)")
print(f"  its supplier             {top['SupplierID']}")
print(f"\\nAnswer key: {DATA_FOLDER}/expected_answers.json")
print("Next: refresh the ontology's graph model so it sees the new rows.")
""")

nb = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {"name": "synapse_pyspark", "display_name": "Synapse PySpark", "language": "Python"},
        "language_info": {"name": "python"},
    },
    "cells": [],
}
for i, cell in enumerate(cells):
    cell["id"] = f"cell-{i:02d}"
    lines = cell["source"].split("\n")
    cell["source"] = [line + "\n" for line in lines[:-1]] + [lines[-1]]
    nb["cells"].append(cell)

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cells)} cells)")
