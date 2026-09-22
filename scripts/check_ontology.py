"""Validate the ontology design against the data and keep docs/ontology-bindings.md in sync.

Usage: python scripts/check_ontology.py [--write]
"""

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
data = ROOT / "data"
doc = ROOT / "docs" / "ontology-bindings.md"
WRITE = "--write" in sys.argv

# From https://learn.microsoft.com/en-us/fabric/graph/gql-reference-reserved-terms (updated 2026-06-02)
RESERVED = set("""
ABS ABSTRACT ACOS AGGREGATE AGGREGATES ALL ALL_DIFFERENT ALTER AND ANY ARRAY AS ASC ASCENDING ASIN AT ATAN AVG
BIG BIGINT BINARY BOOL BOOLEAN BOTH BTRIM BY BYTE_LENGTH BYTES CALL CARDINALITY CASE CAST CATALOG CEIL CEILING
CHAR CHAR_LENGTH CHARACTER_LENGTH CHARACTERISTICS CLEAR CLONE CLOSE COALESCE COLLECT_LIST COMMIT CONSTRAINT
CONSTRUCT CONTAINS COPY COS COSH COT COUNT CREATE CURRENT_DATE CURRENT_GRAPH CURRENT_PROPERTY_GRAPH CURRENT_ROLE
CURRENT_SCHEMA CURRENT_TIME CURRENT_TIMESTAMP CURRENT_USER DATA DATE DATETIME DEC DECIMAL DECLARE DEGREES DELETE
DESC DESCENDING DETACH DIRECTORY DISTINCT DOUBLE DROP DRYRUN DURATION DURATION_BETWEEN EDGE EDGES ELEMENT ELEMENTS
ELEMENT_ID ELSE END ENDS ENUM EXACT EXCEPT EXISTING EXISTS EXP FILTER FINISH FLOAT FLOAT16 FLOAT32 FLOAT64 FLOAT128
FLOAT256 FLOOR FOR FROM FULLTEXT FUNCTION GQL GQLSTATUS GRANT GROUP HAVING HOME_GRAPH HOME_PROPERTY_GRAPH HOME_SCHEMA
IF IN INCLUDE INDEX INFINITY INSERT INSTANT INT INTEGER INT8 INTEGER8 INT16 INTEGER16 INT32 INTEGER32 INT64
INTEGER64 INT96 INTEGER96 INT128 INTEGER128 INT256 INTEGER256 INTERSECT INTERVAL IS JSON KEY KEYS LABEL LABELS
LEADING LEFT LET LIKE LIMIT LIST LN LOCAL LOCAL_DATETIME LOCAL_TIME LOCAL_TIMESTAMP LOG LOG10 LOWER LTRIM MATCH MAX
MERGE MICROSOFT MIN MOD MSFTGQL NEXT NODE NODES NODETACH NORMALIZE NOT NOTHING NULL NULLIF NULLS NUMBER NUMERIC
OCTET_LENGTH OF OFFSET ON OPEN OPTIONAL OR ORDER OTHERWISE PARAMETER PARAMETERS PARTITION PATH PATH_LENGTH PATHS
PERCENTILE_CONT PERCENTILE_DISC POINT POWER PRAGMA PRECISION PREPARE PROCEDURE PRODUCT PROJECT PROPERTY_EXISTS QUERY
RADIANS RANGE REAL RECORD RECORDS REFERENCE REGEXP_CONTAINS RELATIONSHIP RELATIONSHIPS REMOVE RENAME REPLACE RESET
RETURN REVOKE RIGHT ROLLBACK RTRIM SAME SCHEMA SELECT SESSION SESSION_USER SET SHOW SIGNED SIN SINH SIZE SKIP SMALL
SMALLINT SQRT START STARTS STDDEV_POP STDDEV_SAMP STRING STRING_JOIN SUBSTRING SUM SYSTEM_USER TAN TANH TEMPORAL TEXT
THEN TIME TIMESTAMP TO_JSON TO_JSON_STRING TRAILING TRIM TYPED UBIGINT UINT UINT8 UINT16 UINT32 UINT64 UINT128 UINT256
UNION UNIQUE UNIT UNSIGNED UPDATE UPPER USE USMALLINT USING VALUE VALUES VARBINARY VARCHAR VARIABLE VECTOR VERTEX
VERTICES WHEN WHERE WITH XOR YIELD ZONED ZONED_DATETIME ZONED_TIME
""".split())

TYPES = {  # ontology property type per source column, matching the notebook's explicit schema
    "Latitude": "double", "Longitude": "double", "SquareFeet": "integer", "OpenedDate": "datetime",
    "LeadTimeDays": "integer", "QualityRating": "double", "ListPrice": "double", "UnitCost": "double",
    "LaunchDate": "datetime", "IsRfidTagged": "boolean", "SizeOrder": "integer", "JoinDate": "datetime",
    "OrderDate": "datetime", "GrossAmount": "double", "DiscountAmount": "double", "SubTotal": "double",
    "TaxAmount": "double", "OrderTotal": "double", "OrderLineNumber": "integer", "Quantity": "integer",
    "UnitPrice": "double", "LineTotal": "double", "ReturnDate": "datetime", "QuantityReturned": "integer",
    "ReturnAmount": "double", "RestockFlag": "boolean", "SnapshotDate": "datetime", "FloorQty": "integer",
    "BackroomQty": "integer", "OnHandQty": "integer", "FloorMinQty": "integer", "ReorderPoint": "integer",
    "PurchaseOrderDate": "datetime", "ExpectedDeliveryDate": "datetime", "DeliveredDate": "datetime",
    "POTotalCost": "double", "QuantityOrdered": "integer", "QuantityReceived": "integer",
    "POUnitCost": "double", "POLineCost": "double",
    "PromotionStartDate": "datetime", "PromotionEndDate": "datetime",
    "TargetMonth": "datetime", "TargetNetSales": "double",
    "BalanceMonth": "datetime", "OpeningQty": "integer", "ReceivedQty": "integer", "SoldQty": "integer",
    "ReturnedQty": "integer", "AdjustedQty": "integer", "ClosingQty": "integer",
    "DaysOutOfStock": "integer", "DaysBelowShelfMin": "integer",
}

# entity type, lakehouse schema.table (as the load notebook writes it), csv, key column, display column, {source column: property name}
ENTITIES = [
    ("Store", "store.store", "Store.csv", "StoreID", "StoreName", {}),
    ("Supplier", "product.supplier", "Supplier.csv", "SupplierID", "SupplierName", {}),
    ("ProductStyle", "product.product", "Product.csv", "ProductID", "ProductName",
     {"SupplierID": "StyleSupplierID", "ListPrice": "StyleListPrice"}),
    ("ProductVariant", "product.product_variant", "ProductVariant.csv", "VariantID", "SKU",
     {"ProductID": "VariantProductID", "ListPrice": "VariantListPrice"}),
    ("Customer", "customer.customer", "Customer.csv", "CustomerID", "CustomerName", {}),
    ("SalesOrder", "sales.sales_order", "SalesOrder.csv", "OrderID", "OrderNumber",
     {"StoreID": "OrderStoreID", "CustomerID": "OrderCustomerID", "DiscountAmount": "OrderDiscountAmount"}),
    ("SalesOrderLine", "sales.sales_order_line", "SalesOrderLine.csv", "OrderLineID", "OrderLineID",
     {"OrderID": "LineOrderID", "VariantID": "LineVariantID", "ProductID": "LineProductID",
      "DiscountAmount": "LineDiscountAmount"}),
    ("SalesReturn", "sales.sales_return", "SalesReturn.csv", "ReturnID", "ReturnID",
     {"OrderID": "ReturnOrderID", "OrderLineNumber": "ReturnOrderLineNumber", "OrderLineID": "ReturnOrderLineID",
      "VariantID": "ReturnVariantID", "ProductID": "ReturnProductID"}),
    ("ReturnReason", "sales.return_reason", "ReturnReason.csv", "ReturnReasonID", "ReturnReasonName",
     {"ReturnReasonID": "ReasonID"}),
    ("StoreInventory", "store.store_inventory", "StoreInventory.csv", "InventoryID", "InventoryID",
     {"StoreID": "InventoryStoreID", "VariantID": "InventoryVariantID", "ProductID": "InventoryProductID"}),
    ("InventoryBalance", "store.inventory_balance", "InventoryBalance.csv", "BalanceID", "BalanceID",
     {"StoreID": "BalanceStoreID", "VariantID": "BalanceVariantID", "ProductID": "BalanceProductID"}),
    ("PurchaseOrder", "supply.purchase_order", "PurchaseOrder.csv", "PurchaseOrderID", "PurchaseOrderID",
     {"SupplierID": "POSupplierID", "StoreID": "POStoreID"}),
    ("PurchaseOrderLine", "supply.purchase_order_line", "PurchaseOrderLine.csv", "PurchaseOrderLineID",
     "PurchaseOrderLineID",
     {"PurchaseOrderID": "POLineOrderID", "VariantID": "POLineVariantID", "ProductID": "POLineProductID"}),
    ("Promotion", "sales.promotion", "Promotion.csv", "PromotionID", "PromotionName", {}),
    ("SalesTarget", "sales.sales_target", "SalesTarget.csv", "TargetID", "TargetID",
     {"StoreID": "TargetStoreID"}),
]

# name, origin, target, mapping csv, matched origin column, matched target column
RELATIONSHIPS = [
    ("orderAtStore", "SalesOrder", "Store", "SalesOrder.csv", "OrderID", "StoreID"),
    ("orderByCustomer", "SalesOrder", "Customer", "SalesOrder.csv", "OrderID", "CustomerID"),
    ("lineInOrder", "SalesOrderLine", "SalesOrder", "SalesOrderLine.csv", "OrderLineID", "OrderID"),
    ("lineForVariant", "SalesOrderLine", "ProductVariant", "SalesOrderLine.csv", "OrderLineID", "VariantID"),
    ("lineOfStyle", "SalesOrderLine", "ProductStyle", "SalesOrderLine.csv", "OrderLineID", "ProductID"),
    ("variantOfStyle", "ProductVariant", "ProductStyle", "ProductVariant.csv", "VariantID", "ProductID"),
    ("styleFromSupplier", "ProductStyle", "Supplier", "Product.csv", "ProductID", "SupplierID"),
    ("returnOfLine", "SalesReturn", "SalesOrderLine", "SalesReturn.csv", "ReturnID", "OrderLineID"),
    ("returnOfStyle", "SalesReturn", "ProductStyle", "SalesReturn.csv", "ReturnID", "ProductID"),
    ("returnHasReason", "SalesReturn", "ReturnReason", "SalesReturn.csv", "ReturnID", "ReturnReasonID"),
    ("returnTakenAtStore", "SalesReturn", "Store", "SalesReturn.csv", "ReturnID", "ReturnStoreID"),
    ("stockAtStore", "StoreInventory", "Store", "StoreInventory.csv", "InventoryID", "StoreID"),
    ("stockOfVariant", "StoreInventory", "ProductVariant", "StoreInventory.csv", "InventoryID", "VariantID"),
    ("balanceAtStore", "InventoryBalance", "Store", "InventoryBalance.csv", "BalanceID", "StoreID"),
    ("balanceOfVariant", "InventoryBalance", "ProductVariant", "InventoryBalance.csv", "BalanceID", "VariantID"),
    ("poFromSupplier", "PurchaseOrder", "Supplier", "PurchaseOrder.csv", "PurchaseOrderID", "SupplierID"),
    ("poForStore", "PurchaseOrder", "Store", "PurchaseOrder.csv", "PurchaseOrderID", "StoreID"),
    ("poLineOnOrder", "PurchaseOrderLine", "PurchaseOrder", "PurchaseOrderLine.csv", "PurchaseOrderLineID", "PurchaseOrderID"),
    ("poLineForVariant", "PurchaseOrderLine", "ProductVariant", "PurchaseOrderLine.csv", "PurchaseOrderLineID", "VariantID"),
    ("poLineOfStyle", "PurchaseOrderLine", "ProductStyle", "PurchaseOrderLine.csv", "PurchaseOrderLineID", "ProductID"),
    ("lineOnPromotion", "SalesOrderLine", "Promotion", "OrderLinePromotion.csv", "OrderLineID", "PromotionID"),
    ("targetForStore", "SalesTarget", "Store", "SalesTarget.csv", "TargetID", "StoreID"),
]

NAME = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9_-]{0,24}[A-Za-z0-9])?$")
REL_NAME = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]{0,127}$")

rows = {}
headers = {}
for _, _, csv_name, *_ in ENTITIES:
    with (data / csv_name).open(encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        headers[csv_name] = reader.fieldnames
        rows[csv_name] = list(reader)

errors = []
seen = {}
entity = {}
md = []
for name, table, csv_name, key, display, renames in ENTITIES:
    if not NAME.match(name) or name.upper() in RESERVED:
        errors.append(f"bad entity type name {name}")
    for col in renames:
        if col not in headers[csv_name]:
            errors.append(f"{name}: rename of missing column {col}")
    props = []
    for col in headers[csv_name]:
        prop = renames.get(col, col)
        ptype = TYPES.get(col, "string")
        if not NAME.match(prop):
            errors.append(f"{name}.{prop}: breaks the 1-26 character rule")
        if prop.upper() in RESERVED:
            errors.append(f"{name}.{prop}: GQL reserved word")
        if prop in seen:
            errors.append(f"{prop} used by both {seen[prop]} and {name}")
        seen[prop] = name
        props.append((col, prop, ptype))
    key_prop = renames.get(key, key)
    keys = [r[key] for r in rows[csv_name]]
    if len(set(keys)) != len(keys):
        errors.append(f"{name}: key {key} is not unique")
    if TYPES.get(key, "string") not in ("string", "integer"):
        errors.append(f"{name}: key type not string/integer")
    entity[name] = (csv_name, key, set(keys))
    md.append((name, table, key_prop, renames.get(display, display), props, len(rows[csv_name])))

edges = []
for rel, origin, target, csv_name, ocol, tcol in RELATIONSHIPS:
    if not REL_NAME.match(rel):
        errors.append(f"bad relationship name {rel}")
    mapping = rows.get(csv_name)
    if mapping is None:
        with (data / csv_name).open(encoding="utf-8") as fh:
            mapping = list(csv.DictReader(fh))
    okeys, tkeys = entity[origin][2], entity[target][2]
    pairs = {(r[ocol], r[tcol]) for r in mapping}
    if any(o not in okeys for o, _ in pairs):
        errors.append(f"{rel}: matched origin column {ocol} has values that aren't {origin} keys")
    missing = sum(1 for _, t in pairs if t not in tkeys)
    if missing:
        errors.append(f"{rel}: {missing} target values in {tcol} aren't {target} keys")
    edges.append((rel, origin, target, csv_name, ocol, tcol, len(pairs)))
if len({r[0] for r in RELATIONSHIPS}) != len(RELATIONSHIPS):
    errors.append("duplicate relationship names")

print(f"{len(ENTITIES)} entity types, {len(seen)} properties, {len(RELATIONSHIPS)} relationships")
print("renames:", sum(len(e[5]) for e in ENTITIES))
print("ERRORS:" if errors else "VALID: unique names, <=26 chars, no reserved words, keys unique, every edge resolves")
for e in errors:
    print("  ", e)

TABLE_OF = {csv: table for _, table, csv, *_ in ENTITIES}
out = []
for name, table, key_prop, display_prop, props, count in md:
    out.append(f"### {name}\n")
    out.append(f"Table `{table}` · key **`{key_prop}`** · display name **`{display_prop}`** · "
               f"{count:,} instances in the committed snapshot\n")
    out.append("| Source column | Property name | Type |")
    out.append("|---|---|---|")
    for col, prop, ptype in props:
        shown = f"**`{prop}`** (rename)" if prop != col else f"`{prop}`"
        out.append(f"| `{col}` | {shown} | {ptype} |")
    out.append("")
rel_md = ["| # | Relationship type | Origin → Target | Mapping table | Matched origin column | Matched target column | Edges in snapshot |",
          "|---:|---|---|---|---|---|---:|"]
for i, (rel, origin, target, csv_name, ocol, tcol, n) in enumerate(edges, 1):
    rel_md.append(f"| {i} | `{rel}` | {origin} → {target} | `{TABLE_OF.get(csv_name, csv_name)}` | "
                  f"`{ocol}` | `{tcol}` | {n:,} |")

blocks = {"entities": "\n".join(out).strip(), "relationships": "\n".join(rel_md)}
text = doc.read_text(encoding="utf-8")
new = text
for tag, body in blocks.items():
    pattern = re.compile(rf"(<!-- generated:{tag} -->\n).*?(\n<!-- /generated:{tag} -->)", re.S)
    if not pattern.search(new):
        sys.exit(f"markers for {tag} missing in {doc.name}")
    new = pattern.sub(lambda m: m.group(1) + body + m.group(2), new)
if WRITE:
    doc.write_text(new, encoding="utf-8", newline="\n")
    print(f"rewrote the generated tables in {doc.name}")
elif new != text:
    errors.append(f"{doc.name} is out of date: run with --write")
    print(f"{doc.name} is out of date: run with --write")
else:
    print(f"{doc.name} matches the design")
sys.exit(1 if errors else 0)
