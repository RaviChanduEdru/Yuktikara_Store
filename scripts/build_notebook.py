"""Build fabric/refresh_yuktikara_data.ipynb. Edit the cells here, never the .ipynb by hand."""

import json
import sys
from pathlib import Path

out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "fabric" / "refresh_yuktikara_data.ipynb"

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
# Refresh Yuktikara Store data to today

Regenerates the whole Yuktikara Store dataset for a window that ends on the day you choose, **yesterday by
default**, so that "last month", "last quarter" and "this year" always mean something. Run it again at any
time and the dates move with it.

What one run does:

1. Generates the 11 CSVs for **1 January of the previous year → end date**, with `scripts/generate_yuktikara.py`.
2. Computes the ground truth for that exact window, with `scripts/oracle_yuktikara.py`.
3. Writes the 11 lakehouse tables with **explicit types** (dates as `date`, money as `double`), the types that
   ontology binding needs, into five business schemas: `customer`, `product`, `sales`, `shared`, `store`.
4. Verifies row counts, column types and that no table has column mapping.

The run's CSVs, `manifest.json` and `expected_answers.json` are kept under `Files/yuktikara/runs/<end date>/`.

**Before the first run**

- Attach the Yuktikara lakehouse (`yuktikara_lh`) as this notebook's **default lakehouse**. It must be
  created with *Lakehouse schemas* checked and OneLake security off.
- Upload `generate_yuktikara.py` and `oracle_yuktikara.py` from the repo's `scripts/` folder to
  `Files/yuktikara/scripts/`. Upload them again whenever you change them.

**After every run**, refresh the ontology's graph model (workspace → graph model → … → Schedule → Refresh now).
The ontology doesn't see new rows until you do.

Never load `expected_answers.json` into a table, and never paste it into an agent. It is the answer key.
""")

code("""
# Parameters
END_DATE = "yesterday"   # "yesterday", "today" or "YYYY-MM-DD". Fabric's clock is UTC.
FILES_ROOT = "/lakehouse/default/Files/yuktikara"
""", tags=["parameters"])

md("## 1. Generate the data and its ground truth")

code("""
import json
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

scripts = Path(FILES_ROOT) / "scripts"
for name in ("generate_yuktikara.py", "oracle_yuktikara.py"):
    if not (scripts / name).exists():
        raise FileNotFoundError(f"Upload {name} to Files/yuktikara/scripts/ first, and check the default lakehouse.")

relative = {"today": date.today(), "yesterday": date.today() - timedelta(days=1)}
end = relative[END_DATE] if END_DATE in relative else date.fromisoformat(END_DATE)
run_dir = Path(FILES_ROOT) / "runs" / end.isoformat()
spark_dir = f"Files/yuktikara/runs/{end.isoformat()}"


def run(script, *args):
    result = subprocess.run([sys.executable, str(scripts / script), *args], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError(f"{script} failed")


run("generate_yuktikara.py", "--end", end.isoformat(), "--out", str(run_dir))
run("oracle_yuktikara.py", "--data", str(run_dir))
manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
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
    header = (run_dir / csv_name).open(encoding="utf-8").readline().rstrip("\\n").split(",")
    expected = [c for c, _ in cols]
    if header != expected:
        raise ValueError(f"{csv_name}: file columns {header} don't match the schema {expected}")
    df = (spark.read.format("csv")
          .option("header", True)
          .option("escape", '"')
          .option("mode", "FAILFAST")
          .schema(StructType([StructField(c, t) for c, t in cols]))
          .load(f"{spark_dir}/{csv_name}"))
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
print("\\nPASS: 11 tables, row counts match the manifest, dates are date, money is double, no column mapping.")
""")

md("## 4. This run's headline numbers")

code("""
import calendar

answers = json.loads((run_dir / "expected_answers.json").read_text(encoding="utf-8"))

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
    print(f"Last complete quarter      {last_quarter}")
    print(f"  gross, all statuses      {float(lq['gross_all_statuses']):>16,.2f}")
    print(f"  net sales                {float(lq['net_sales']):>16,.2f}")
top = answers["top_return_rate_products"][0]
print(f"Highest return rate        {top['ProductName']} {top['return_rate_pct']}%")
print(f"\\nAnswer key for this run: {spark_dir}/expected_answers.json")
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
