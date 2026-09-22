# Data model

Eleven tables. The committed snapshot in `data/` covers 2025-01-01 to 2026-08-31, and the row counts below
describe it. A run of `fabric/refresh_yuktikara_data.ipynb` covers 1 January of the previous year to its end
date, so its counts are larger or smaller; the schema is identical. Every file is UTF-8 CSV with a header
row and LF line endings. Money is written with two decimal places and no thousands separator or currency
symbol.

In Fabric, the notebook writes each CSV to a snake_case table (`SalesOrder.csv` → `sales_order`) with the
types listed here: `date` for dates, `double` for money, `integer` for counts and `boolean` for flags.

Keep the load order below when you build the lakehouse: dimensions first, then the fact tables that
reference them.

---

## Store.csv — 19 rows

One row per selling location. `ST900` is the online channel and is deliberately modelled as a store so
that every order has a store, however it was placed.

| Column | Type | Notes |
|---|---|---|
| `StoreID` | string | Primary key. `ST001`-`ST018` physical, `ST900` online |
| `StoreName` | string | Display name, for example `Yuktikara Bend Outlet` |
| `RegionName` | string | `Pacific Northwest`, `Northern Rockies`, `Colorado Front Range`, `Great Basin`, `Online` |
| `City` | string | Real city, used for the map |
| `StateCode` | string | Two-letter US state code |
| `Latitude` | double | Decimal degrees |
| `Longitude` | double | Decimal degrees |
| `StoreFormat` | string | `Flagship`, `Standard`, `Outlet`, `Ecommerce` |
| `SquareFeet` | integer | `0` for the online channel |
| `OpenedDate` | date | Some stores open partway through the period, so per-store trends are not all comparable |

## Supplier.csv — 7 rows

| Column | Type | Notes |
|---|---|---|
| `SupplierID` | string | Primary key, `SUP01`-`SUP07` |
| `SupplierName` | string | Invented |
| `Country` | string | Manufacturing country |
| `LeadTimeDays` | integer | Quoted replenishment lead time |
| `QualityRating` | double | 1.0 to 5.0. `SUP04` is the lowest and supplies the high-return boot |

## Product.csv — 52 rows

A **style**, not a sellable item. What a customer buys is a variant.

| Column | Type | Notes |
|---|---|---|
| `ProductID` | string | Primary key, `P0001`-`P0052` |
| `StyleCode` | string | `YK-<DEP>-<nnnn>` |
| `ProductName` | string | Unique across the catalogue |
| `DepartmentName` | string | `Footwear`, `Apparel`, `Equipment` |
| `CategoryName` | string | For example `Hiking Boots`, `Rain Shells`, `Tents` |
| `SupplierID` | string | Foreign key to `Supplier` |
| `SeasonCode` | string | `SS25`, `FW25`, `SS26`, `AllSeason` |
| `ListPrice` | double | Style-level price before markdown |
| `UnitCost` | double | Landed cost, 38-52% of list |
| `LaunchDate` | date | Before the start of the period |
| `IsRfidTagged` | boolean | `true` for Footwear and Apparel, `false` for Equipment. Drives which variants appear in `StoreInventory` |

## ProductVariant.csv — 744 rows

The sellable SKU: style x colour x size. Order lines and returns point here.

| Column | Type | Notes |
|---|---|---|
| `VariantID` | string | Primary key, `V00001`- |
| `ProductID` | string | Foreign key to `Product` |
| `SKU` | string | Human-readable code |
| `ColorName` | string | Two or three colourways per style |
| `SizeCode` | string | Footwear `7`-`13` in half sizes, Apparel `XS`-`XXL`, Equipment `One Size` |
| `SizeOrder` | integer | Sort order, because `SizeCode` is text and `XS` must not sort after `L` |
| `ListPrice` | double | Inherited from the style |

## Customer.csv — 6,200 rows

Synthetic. No email addresses, phone numbers or street addresses exist anywhere in this dataset.

| Column | Type | Notes |
|---|---|---|
| `CustomerID` | string | Primary key, `C00001`- |
| `CustomerName` | string | Invented first and last name |
| `LoyaltyTier` | string | `None`, `Trailhead`, `Summit`, `Alpine` |
| `JoinDate` | date | May precede the sales period |
| `HomeCity` | string | |
| `HomeStateCode` | string | |
| `PreferredStoreID` | string | Foreign key to a physical `Store`. Need not match where they actually shopped |

## DimDate.csv — 608 rows

One row per day across the period. Build the semantic model's date relationship against `Date`.

| Column | Type | Notes |
|---|---|---|
| `DateKey` | integer | `yyyyMMdd` |
| `Date` | date | Join key |
| `Year` | integer | |
| `Quarter` | string | `Q1`-`Q4` |
| `YearQuarter` | string | For example `2026-Q1` |
| `MonthNumber` | integer | 1-12 |
| `MonthName` | string | Full name |
| `YearMonth` | string | `yyyy-MM`, sorts correctly as text |
| `DayOfWeek` | integer | 1 = Monday |
| `DayName` | string | |
| `IsWeekend` | boolean | |

---

## SalesOrder.csv — 33,757 rows

The order header, and where the net sales trap lives. Five money columns, and choosing the wrong one is
the most common way to get the answer wrong.

| Column | Type | Notes |
|---|---|---|
| `OrderID` | string | Primary key, `SO000001`- |
| `OrderNumber` | string | `YK-<year>-<nnnnnn>`, the customer-facing reference |
| `StoreID` | string | Foreign key to `Store` |
| `CustomerID` | string | Foreign key to `Customer` |
| `Channel` | string | `Store` or `Online` |
| `OrderDate` | date | |
| `OrderStatus` | string | `Completed`, `Shipped`, `Pending`, `Cancelled`. **Only Completed and Shipped are sales** |
| `GrossAmount` | double | Quantity x unit price, before any markdown |
| `DiscountAmount` | double | Sum of line markdowns. Non-zero, concentrated in clearance months |
| `SubTotal` | double | `GrossAmount - DiscountAmount`. **This is the sales-recognised amount** |
| `TaxAmount` | double | `SubTotal` x 8.25% |
| `OrderTotal` | double | `SubTotal + TaxAmount`. Includes tax, so it is not sales |
| `PaymentMethod` | string | |

## SalesOrderLine.csv — 69,198 rows

| Column | Type | Notes |
|---|---|---|
| `OrderLineID` | string | Primary key, `<OrderID>-<OrderLineNumber>`, for example `SO000001-1`. A single-column key, because ontology relationships match one column per side |
| `OrderID` | string | Foreign key to `SalesOrder` |
| `OrderLineNumber` | integer | Restarts at 1 per order |
| `VariantID` | string | Foreign key to `ProductVariant` |
| `ProductID` | string | Denormalised from the variant, so product questions need one hop fewer |
| `Quantity` | integer | 1-3 |
| `UnitPrice` | double | Before markdown |
| `DiscountAmount` | double | Line markdown |
| `LineTotal` | double | `Quantity x UnitPrice - DiscountAmount` |

## SalesReturn.csv — 6,749 rows

A returned order line. Returns only exist against orders that were `Completed` or `Shipped`.

| Column | Type | Notes |
|---|---|---|
| `ReturnID` | string | Primary key, `RT000001`- |
| `OrderID` | string | The order the returned line belongs to |
| `OrderLineNumber` | integer | |
| `OrderLineID` | string | Foreign key to `SalesOrderLine` |
| `VariantID` | string | Foreign key to `ProductVariant` |
| `ProductID` | string | Denormalised |
| `ReturnDate` | date | **Net sales counts a return on this date, not on the order date.** A Q1 sale returned in Q2 reduces Q2 |
| `ReturnStoreID` | string | The store that took the return, which need not be the store that sold it |
| `QuantityReturned` | integer | May be fewer than the quantity sold |
| `ReturnAmount` | double | The share of `LineTotal` being returned |
| `ReturnStatus` | string | `Accepted`, `Pending`, `Rejected`. **Only Accepted reduces net sales** |
| `ReturnReasonID` | string | Foreign key to `ReturnReason` |
| `RestockFlag` | boolean | `false` when the item cannot go back on the floor |

Of the 6,749 returns, 5,724 are `Accepted`, totalling 970,051.76.

## ReturnReason.csv — 8 rows

| Column | Type | Notes |
|---|---|---|
| `ReturnReasonID` | string | Primary key, `RR1`-`RR8` |
| `ReturnReasonName` | string | `Too small`, `Too large`, `Not as described`, `Damaged or faulty`, `Wrong item shipped`, `Arrived too late`, `Changed mind`, `Found a better price` |
| `ReturnCategory` | string | `Fit`, `Description`, `Quality`, `Logistics`, `Customer` |

## StoreInventory.csv — 7,025 rows

A single snapshot dated 2026-08-31, covering RFID-tagged variants only. This is the batch counterpart to
the live RFID stream: `FloorMinQty` is the threshold the operations agent watches.

| Column | Type | Notes |
|---|---|---|
| `InventoryID` | string | Primary key, `<StoreID>-<VariantID>`, for example `ST001-V00002` |
| `StoreID` | string | Physical stores only |
| `VariantID` | string | Foreign key to `ProductVariant` |
| `ProductID` | string | Denormalised |
| `SnapshotDate` | date | `2026-08-31` for every row |
| `FloorQty` | integer | On the shop floor |
| `BackroomQty` | integer | In the stockroom |
| `OnHandQty` | integer | `FloorQty + BackroomQty` |
| `FloorMinQty` | integer | Below this, the floor needs replenishing from the backroom |
| `ReorderPoint` | integer | Below this, the store reorders |

---

## Types when you load into Fabric

Use `double` for every money and quantity column. Fabric Graph does not support `decimal`, and a decimal
property returns null on every ontology query — a failure that is quiet and slow to diagnose.

Load `SizeCode` as text. `7.5` and `XS` share a column, and an inferred numeric type drops the apparel
sizes entirely.

## Relationships

```
Store 1─* SalesOrder *─1 Customer
SalesOrder 1─* SalesOrderLine *─1 ProductVariant *─1 Product *─1 Supplier
SalesOrderLine 1─* SalesReturn *─1 ReturnReason
SalesReturn *─1 Store            (via ReturnStoreID — the store that absorbed it)
Store 1─* StoreInventory *─1 ProductVariant
DimDate 1─* SalesOrder           (OrderDate)
DimDate 1─* SalesReturn          (ReturnDate)
```

`SalesReturn` reaching `Store` twice — once through its order and once through `ReturnStoreID` — is what
makes "which store absorbs the most online returns" answerable, and it is the kind of question that is
awkward against raw tables and natural against an ontology.

In the ontology these become 13 named relationship types, and `Product` becomes the entity type
`ProductStyle` because `PRODUCT` is a GQL reserved word. The full binding, with every property name, is in
[ontology-bindings.md](ontology-bindings.md).
