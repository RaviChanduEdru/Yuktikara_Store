"""Validate the ontology design against the data and keep docs/ep1/03-ontology-bindings.md in sync.

Usage: python scripts/check_ontology.py [--write]
"""

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
data = ROOT / "data"
doc = ROOT / "docs" / "ep1" / "03-ontology-bindings.md"
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

# --- Semantic enrichment: descriptions, synonyms and additional metadata ------------------------
# Confirmed against https://learn.microsoft.com/fabric/iq/ontology/how-to-add-semantic-enrichment
# (checked 2026-09-23): entity types take a description, synonyms and additional metadata;
# properties and relationships take a description and additional metadata, but no synonyms.
# Metadata keys must be unique within their own object, never globally.
#
# Microsoft: "Data agent doesn't use the semantic enrichment fields." This is documentation for
# people reading the model, never a substitute for the definitions in a data agent's instructions.

# entity name -> (description, [synonyms], {additional metadata})
ENTITY_META = {
    "Store": ("A Yuktikara selling location: one of 18 physical shops or the online channel ST900. "
              "Every order, return and stock position points back to a store.",
              ["Shop", "Location", "Branch"], {"domain": "Retail operations"}),
    "Supplier": ("A manufacturer Yuktikara buys finished styles from. Each style comes from exactly "
                 "one supplier, and suppliers vary in lead time, delivery reliability and quality.",
                 ["Vendor", "Manufacturer"], {}),
    "ProductStyle": ("A product design, for example the Cascade Ridge Hiking Boot. A style isn't "
                      "sellable on its own; a customer buys a ProductVariant, one size and colour of it.",
                      ["Style", "Product"], {}),
    "ProductVariant": ("A single sellable item: one style, in one colour and one size. Order lines, "
                        "returns and stock positions all point to a variant, never directly to a style.",
                        ["SKU", "Variant"], {}),
    "Customer": ("A synthetic shopper. No real names, emails or addresses exist anywhere in this dataset.",
                 ["Shopper", "Buyer"], {}),
    "SalesOrder": ("One customer order, placed in a store or online. Carries five money columns; picking "
                    "the wrong one is the most common way to misstate sales. Net sales is built from "
                    "SubTotal, only on Completed or Shipped orders.",
                    ["Order", "Sale"], {}),
    "SalesOrderLine": ("One variant on one order. An order with three items has three lines.",
                        ["Order line", "Line item"], {}),
    "SalesReturn": ("A returned order line. Returns only exist against orders that were Completed or "
                     "Shipped. Only Accepted returns, on their ReturnDate, reduce net sales.",
                     ["Return", "Refund"], {}),
    "ReturnReason": ("One of eight reasons a customer can give for a return, grouped into five categories.",
                      ["Reason"], {}),
    "StoreInventory": ("What the RFID stock count found on the shop floor and in the stockroom on the "
                        "last day of the window, for every store and variant combination the store "
                        "carries. A snapshot; InventoryBalance holds the months of movement behind it.",
                        ["Shelf stock", "Floor stock", "Stock snapshot"],
                        {"grain": "one store + one variant, current snapshot"}),
    "InventoryBalance": ("The monthly stock ledger for one store and variant. It balances exactly and "
                          "closes on the count in StoreInventory: opening plus received minus sold plus "
                          "returned plus adjusted equals closing.",
                          ["Stock ledger", "Stock movement"], {"grain": "one store + one variant + one month"}),
    "PurchaseOrder": ("One order a store placed with a supplier. Stores reorder from each supplier "
                       "roughly every two weeks. An order still in transit at the end of the window has "
                       "no DeliveredDate.",
                       ["Purchase order", "PO"], {}),
    "PurchaseOrderLine": ("One variant on a purchase order. A short delivery shows QuantityReceived "
                           "below QuantityOrdered.",
                           ["PO line"], {}),
    "Promotion": ("A named markdown campaign: a clearance after the holidays or at the end of summer, "
                   "or a smaller seasonal event in between.",
                   ["Campaign", "Sale event"], {}),
    "SalesTarget": ("One store's net sales target for one month. Targets follow the store's normal "
                     "trading pattern; the stores opened in 2023 and the online channel were set more "
                     "ambitious growth targets.",
                     ["Target", "Plan", "Quota"], {}),
}

# money-typed properties get {"unit": "USD"}; these three carry a sensitivity note instead, because
# they're the only fields shaped like personal data, even though every row is invented
MONEY_COLUMNS = {
    "GrossAmount", "DiscountAmount", "SubTotal", "TaxAmount", "OrderTotal", "LineTotal", "ReturnAmount",
    "ListPrice", "UnitCost", "POTotalCost", "POUnitCost", "POLineCost", "TargetNetSales",
}
SENSITIVE_COLUMNS = {"CustomerName", "HomeCity", "HomeStateCode"}

# (entity name, SOURCE column, as in the CSV header) -> description. The doc shows the bound
# (possibly renamed) property name; this key stays on the source column so one description works
# whichever entity it's renamed for.
PROP_META = {
    ("Store", "StoreID"): "Unique store code. ST001-ST018 are physical shops; ST900 is the online channel.",
    ("Store", "StoreName"): "Public-facing name shown in reports and the graph, for example Yuktikara Bend Outlet.",
    ("Store", "RegionName"): "One of four physical regions, or Online for the e-commerce channel.",
    ("Store", "City"): "City the store trades in, used to place it on a map.",
    ("Store", "StateCode"): "Two-letter US state code.",
    ("Store", "Latitude"): "Map coordinate, decimal degrees.",
    ("Store", "Longitude"): "Map coordinate, decimal degrees.",
    ("Store", "StoreFormat"): "Flagship, Standard, Outlet or Ecommerce. Drives typical daily order volume.",
    ("Store", "SquareFeet"): "Physical retail floor area; 0 for the online channel.",
    ("Store", "OpenedDate"): ("The day the store opened for trading. Stores opened partway through the "
                               "period aren't comparable to older ones on raw totals."),

    ("Supplier", "SupplierID"): "Unique supplier code, SUP01-SUP07.",
    ("Supplier", "SupplierName"): "The manufacturer's name.",
    ("Supplier", "Country"): "Country the goods are manufactured in.",
    ("Supplier", "LeadTimeDays"): ("Days the supplier quotes between placing a purchase order and "
                                    "delivery. Compare against actual delivery dates to see who is reliable."),
    ("Supplier", "QualityRating"): ("1.0-5.0 quality score. The lowest-rated supplier also has the "
                                     "weakest on-time delivery record."),

    ("ProductStyle", "ProductID"): "Unique style code, P0001-P0052.",
    ("ProductStyle", "StyleCode"): "Human-readable style code, for example YK-FOO-0001.",
    ("ProductStyle", "ProductName"): "The style's name, unique across the catalogue.",
    ("ProductStyle", "DepartmentName"): "Footwear, Apparel or Equipment.",
    ("ProductStyle", "CategoryName"): "Product category within the department, for example Hiking Boots or Rain Shells.",
    ("ProductStyle", "SupplierID"): "The manufacturer of this style.",
    ("ProductStyle", "SeasonCode"): "The season the style was designed for, for example SS26 or AllSeason.",
    ("ProductStyle", "ListPrice"): "List price before any markdown, shared by every variant of the style.",
    ("ProductStyle", "UnitCost"): "What Yuktikara pays the supplier per unit, 38-52% of list price.",
    ("ProductStyle", "LaunchDate"): "The date this style went on sale.",
    ("ProductStyle", "IsRfidTagged"): ("True for Footwear and Apparel, false for Equipment. Only "
                                        "RFID-tagged styles appear in the shop-floor stock data."),

    ("ProductVariant", "VariantID"): "Unique SKU code, V00001-.",
    ("ProductVariant", "ProductID"): "The style this variant belongs to.",
    ("ProductVariant", "SKU"): "Human-readable SKU, also the display name for this entity type.",
    ("ProductVariant", "ColorName"): "One of two or three colourways offered for the style.",
    ("ProductVariant", "SizeCode"): "Footwear sizes 7-13 in half sizes, Apparel XS-XXL, Equipment One Size.",
    ("ProductVariant", "SizeOrder"): ("Numeric sort order for SizeCode, because the text values don't "
                                       "sort correctly on their own (XS would sort after L)."),
    ("ProductVariant", "ListPrice"): "Inherited from the style; the same for every variant of it.",

    ("Customer", "CustomerID"): "Unique customer code, C00001-.",
    ("Customer", "CustomerName"): "Invented first and last name.",
    ("Customer", "LoyaltyTier"): "None, Trailhead, Summit or Alpine, in ascending order.",
    ("Customer", "JoinDate"): "When the customer joined the loyalty programme; may be before the sales window starts.",
    ("Customer", "HomeCity"): "Invented home city.",
    ("Customer", "HomeStateCode"): "Invented home state.",
    ("Customer", "PreferredStoreID"): ("The physical store the customer nominated as their preference. "
                                        "They may buy anywhere, including online."),

    ("SalesOrder", "OrderID"): "Unique order code, SO000001-.",
    ("SalesOrder", "OrderNumber"): "Customer-facing order reference, for example YK-2026-000123.",
    ("SalesOrder", "StoreID"): "The store, or ST900 online, where the order was placed.",
    ("SalesOrder", "CustomerID"): "The customer who placed the order.",
    ("SalesOrder", "Channel"): "Store or Online.",
    ("SalesOrder", "OrderDate"): "The day the order was placed.",
    ("SalesOrder", "OrderStatus"): ("Completed, Shipped, Pending or Cancelled. Only Completed and "
                                     "Shipped orders count as sales."),
    ("SalesOrder", "GrossAmount"): "Quantity times unit price, before any markdown.",
    ("SalesOrder", "DiscountAmount"): "Sum of the line-level markdowns on this order.",
    ("SalesOrder", "SubTotal"): ("GrossAmount minus the order's discount. This is the sales-recognised "
                                  "amount net sales is built from."),
    ("SalesOrder", "TaxAmount"): "Sales tax, 8.25% of SubTotal.",
    ("SalesOrder", "OrderTotal"): ("SubTotal plus TaxAmount, what the customer actually paid. Includes "
                                    "tax, so it is not a sales figure."),
    ("SalesOrder", "PaymentMethod"): "How the order was paid for.",

    ("SalesOrderLine", "OrderLineID"): "Unique line code, <OrderID>-<line number>, for example SO000001-1.",
    ("SalesOrderLine", "OrderID"): "The order this line belongs to.",
    ("SalesOrderLine", "OrderLineNumber"): "Position of this line within its order, restarting at 1 for each order.",
    ("SalesOrderLine", "VariantID"): "The variant sold on this line.",
    ("SalesOrderLine", "ProductID"): ("The style the variant belongs to, denormalised so product "
                                       "questions need one hop fewer."),
    ("SalesOrderLine", "Quantity"): "Units sold on this line, 1-3.",
    ("SalesOrderLine", "UnitPrice"): "Price per unit before markdown.",
    ("SalesOrderLine", "DiscountAmount"): "Markdown applied to this line.",
    ("SalesOrderLine", "LineTotal"): "Quantity times UnitPrice minus the line's discount.",

    ("SalesReturn", "ReturnID"): "Unique return code, RT000001-.",
    ("SalesReturn", "OrderID"): "The order the returned line belongs to.",
    ("SalesReturn", "OrderLineNumber"): "The line number within that order.",
    ("SalesReturn", "OrderLineID"): "The order line being returned.",
    ("SalesReturn", "VariantID"): "The variant being returned.",
    ("SalesReturn", "ProductID"): "The style being returned, denormalised.",
    ("SalesReturn", "ReturnDate"): ("The day the return was accepted, rejected or left pending. Net "
                                     "sales counts a return on this date, not the original order date, "
                                     "so a sale made in one quarter can reduce a later one."),
    ("SalesReturn", "ReturnStoreID"): ("The store that physically took the return back. Not always the "
                                        "store that made the sale: a customer can return an online order "
                                        "to any physical store."),
    ("SalesReturn", "QuantityReturned"): "Units returned; may be fewer than the quantity originally sold on the line.",
    ("SalesReturn", "ReturnAmount"): "The share of the line's total being refunded.",
    ("SalesReturn", "ReturnStatus"): "Accepted, Pending or Rejected. Only Accepted reduces net sales.",
    ("SalesReturn", "ReturnReasonID"): "Why the customer returned it.",
    ("SalesReturn", "RestockFlag"): ("True if the returned item can go back on sale; false when it's "
                                      "damaged or otherwise can't be restocked."),

    ("ReturnReason", "ReturnReasonID"): "Unique reason code, RR1-RR8.",
    ("ReturnReason", "ReturnReasonName"): "The reason text shown to the customer, for example Too small or Damaged or faulty.",
    ("ReturnReason", "ReturnCategory"): "Groups the eight reasons into Fit, Description, Quality, Logistics or Customer.",

    ("StoreInventory", "InventoryID"): "Unique position code, <StoreID>-<VariantID>.",
    ("StoreInventory", "StoreID"): "Physical stores only; the online channel's stock isn't counted here.",
    ("StoreInventory", "VariantID"): "The variant being counted.",
    ("StoreInventory", "ProductID"): "The style, denormalised.",
    ("StoreInventory", "SnapshotDate"): "The day this count was taken, the last day of the data window.",
    ("StoreInventory", "FloorQty"): "Units physically on the shop floor.",
    ("StoreInventory", "BackroomQty"): "Units in the stockroom, not yet on the floor.",
    ("StoreInventory", "OnHandQty"): "FloorQty plus BackroomQty.",
    ("StoreInventory", "FloorMinQty"): ("The shelf minimum for this variant at this store, set from how "
                                         "fast it sells there. Below this, the floor should be refilled "
                                         "from the backroom, the trigger the operations agent watches for."),
    ("StoreInventory", "ReorderPoint"): "Below this level, the store places a new purchase order with the supplier.",

    ("InventoryBalance", "BalanceID"): "Unique code, <StoreID>-<VariantID>-<YYYYMM>.",
    ("InventoryBalance", "StoreID"): "The store this month's movement belongs to.",
    ("InventoryBalance", "VariantID"): "The variant this month's movement belongs to.",
    ("InventoryBalance", "ProductID"): "The style, denormalised.",
    ("InventoryBalance", "BalanceMonth"): "First day of the month this row covers.",
    ("InventoryBalance", "OpeningQty"): "Units on hand at the start of the month, equal to the previous month's closing quantity.",
    ("InventoryBalance", "ReceivedQty"): "Units delivered by the supplier during the month.",
    ("InventoryBalance", "SoldQty"): "Units sold at this store on Completed or Shipped orders during the month.",
    ("InventoryBalance", "ReturnedQty"): "Accepted returns put back on sale at this store during the month.",
    ("InventoryBalance", "AdjustedQty"): ("Stock-count corrections: negative for a loss found at count "
                                           "time, positive for stock sent in from another store to cover "
                                           "a shortfall."),
    ("InventoryBalance", "ClosingQty"): ("Units on hand at the end of the month. The last month's value "
                                          "equals the on-hand quantity in StoreInventory for this position."),
    ("InventoryBalance", "DaysOutOfStock"): "Days during the month this position ended the day with zero stock.",
    ("InventoryBalance", "DaysBelowShelfMin"): "Days during the month this position ended the day below its shelf minimum.",

    ("PurchaseOrder", "PurchaseOrderID"): "Unique order code, PO000001-.",
    ("PurchaseOrder", "SupplierID"): "The supplier this order was placed with.",
    ("PurchaseOrder", "StoreID"): "The store the goods are being delivered to.",
    ("PurchaseOrder", "PurchaseOrderDate"): "The day the order was placed.",
    ("PurchaseOrder", "ExpectedDeliveryDate"): "The order date plus the supplier's quoted lead time.",
    ("PurchaseOrder", "DeliveredDate"): ("The day the order actually arrived. Empty while the order is "
                                          "still open. Compare against ExpectedDeliveryDate to measure a "
                                          "supplier's on-time performance."),
    ("PurchaseOrder", "POStatus"): "Received, Partially received or Open.",
    ("PurchaseOrder", "POTotalCost"): "What Yuktikara is paying for everything ordered on this purchase order.",

    ("PurchaseOrderLine", "PurchaseOrderLineID"): "Unique line code, <PurchaseOrderID>-<line number>.",
    ("PurchaseOrderLine", "PurchaseOrderID"): "The purchase order this line belongs to.",
    ("PurchaseOrderLine", "VariantID"): "The variant being ordered.",
    ("PurchaseOrderLine", "ProductID"): "The style, denormalised.",
    ("PurchaseOrderLine", "QuantityOrdered"): "Units ordered on this line.",
    ("PurchaseOrderLine", "QuantityReceived"): "Units that actually arrived; zero while the order is still open.",
    ("PurchaseOrderLine", "POUnitCost"): ("Cost per unit for this delivery. Some suppliers' unit costs "
                                           "rise partway through the current year."),
    ("PurchaseOrderLine", "POLineCost"): "QuantityOrdered times the unit cost.",

    ("Promotion", "PromotionID"): "Unique campaign code, for example PR2026-1.",
    ("Promotion", "PromotionName"): "The campaign's display name, for example Summer Clearance 2026.",
    ("Promotion", "PromotionType"): "Clearance or Seasonal event.",
    ("Promotion", "PromotionStartDate"): "First day of the campaign.",
    ("Promotion", "PromotionEndDate"): "Last day of the campaign; may fall after the data window for a campaign still running.",
    ("Promotion", "DiscountDepth"): "How deep the campaign's discounts go, for example 15-40% off.",

    ("SalesTarget", "TargetID"): "Unique code, <StoreID>-<YYYYMM>.",
    ("SalesTarget", "StoreID"): "The store this target belongs to.",
    ("SalesTarget", "TargetMonth"): "First day of the month the target covers.",
    ("SalesTarget", "TargetNetSales"): "The store's net sales target for the month, rounded to the nearest thousand.",
}

# relationship name -> description
REL_META = {
    "orderAtStore": "Which store, or the online channel, an order was placed at.",
    "orderByCustomer": "Which customer placed an order.",
    "lineInOrder": "Which order an order line belongs to.",
    "lineForVariant": "Which variant an order line is for.",
    "lineOfStyle": "Which style an order line is for, in one hop instead of going through the variant.",
    "variantOfStyle": "Which style a variant belongs to.",
    "styleFromSupplier": "Which supplier manufactures a style.",
    "returnOfLine": "Which order line a return applies to.",
    "returnOfStyle": "Which style a return applies to, in one hop instead of going through the order line and variant.",
    "returnHasReason": "Why a return was made.",
    "returnTakenAtStore": ("Which store physically took a return back. Separate from orderAtStore, "
                            "because a customer can return to a different store than the one that sold it."),
    "stockAtStore": "Which store a shelf-stock position belongs to.",
    "stockOfVariant": "Which variant a shelf-stock position is counting.",
    "balanceAtStore": "Which store a month of stock movement belongs to.",
    "balanceOfVariant": "Which variant a month of stock movement is for.",
    "poFromSupplier": "Which supplier a purchase order was placed with.",
    "poForStore": "Which store a purchase order is being delivered to.",
    "poLineOnOrder": "Which purchase order a line belongs to.",
    "poLineForVariant": "Which variant a purchase order line is for.",
    "poLineOfStyle": "Which style a purchase order line is for, in one hop instead of going through the variant.",
    "lineOnPromotion": "Which campaign a discounted order line was sold under.",
    "targetForStore": "Which store a monthly sales target belongs to.",
}

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

# --- Semantic enrichment: check every object has metadata, and build its markdown -----------------
meta_md = []
for name, table, csv_name, key, display, renames in ENTITIES:
    if name not in ENTITY_META:
        errors.append(f"{name}: no entry in ENTITY_META")
        continue
    description, synonyms, extra = ENTITY_META[name]
    meta_md.append(f"### {name}\n")
    meta_md.append(f"**Description:** {description}\n")
    if synonyms:
        meta_md.append(f"**Synonyms:** {', '.join(synonyms)}\n")
    if extra:
        meta_md.append("**Additional metadata:** " + "; ".join(f"`{k}` = `{v}`" for k, v in extra.items()) + "\n")
    meta_md.append("| Property | Description | Additional metadata |")
    meta_md.append("|---|---|---|")
    for col in headers[csv_name]:
        prop = renames.get(col, col)
        if (name, col) not in PROP_META:
            errors.append(f"{name}.{prop}: no entry in PROP_META")
            continue
        prop_extra = {}
        if col in MONEY_COLUMNS:
            prop_extra["unit"] = "USD"
        elif col == "QualityRating":
            prop_extra["unit"] = "1-5 rating"
        elif col in SENSITIVE_COLUMNS:
            prop_extra["sensitivity"] = "none - synthetic data"
        extra_cell = "; ".join(f"`{k}`=`{v}`" for k, v in prop_extra.items())
        meta_md.append(f"| `{prop}` | {PROP_META[(name, col)]} | {extra_cell} |")
    meta_md.append("")

rel_meta_md = ["| Relationship type | Description |", "|---|---|"]
for rel, origin, target, csv_name, ocol, tcol in RELATIONSHIPS:
    if rel not in REL_META:
        errors.append(f"{rel}: no entry in REL_META")
        continue
    rel_meta_md.append(f"| `{rel}` | {REL_META[rel]} |")

print(f"{len(ENTITIES)} entity types, {len(seen)} properties, {len(RELATIONSHIPS)} relationships")
print("renames:", sum(len(e[5]) for e in ENTITIES))
print("ERRORS:" if errors else "VALID: unique names, <=26 chars, no reserved words, keys unique, every edge resolves")
for e in errors:
    print("  ", e)

TABLE_OF = {csv: table for _, table, csv, *_ in ENTITIES} | {"OrderLinePromotion.csv": "sales.order_line_promotion"}
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

blocks = {"entities": "\n".join(out).strip(), "relationships": "\n".join(rel_md),
          "entity-metadata": "\n".join(meta_md).strip(), "relationship-metadata": "\n".join(rel_meta_md)}
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
