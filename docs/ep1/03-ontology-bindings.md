# Building the Yuktikara ontology by hand

Every entity type, binding and relationship in the Yuktikara Store ontology, in the order you create them
in the Fabric portal. Each entity type is bound directly to a lakehouse table, so every mapping is visible
and nothing is generated for you.

The design on this page is checked by `scripts/check_ontology.py` on every push: property names are unique
and 26 characters or fewer, none is a GQL reserved word, every key is unique, and every relationship's
matched columns resolve to real keys at both ends.

Ontology is in preview. The entity type steps below were checked in the portal on 2026-09-23. If a label
has moved since, the concept hasn't.

## Before you start

| Check | How |
|---|---|
| Tenant settings **Ontology item (preview)** and **Graph** are on | Workspace → **+ New item** lists **Ontology (preview)** |
| The workspace is on a Fabric capacity | **Workspace settings** → workspace type. A trial is enough for everything on this page; only Episode 2's data agents need a paid F2 or higher |
| `yuktikara_lh` has **Lakehouse schemas** on and OneLake security off | **Tables** shows `customer`, `product`, `sales`, `shared`, `store`, `supply` and the empty `dbo`. If you only see `dbo`: **Tables** → **…** → **Refresh** |
| The 17 tables are loaded | The load notebook's *Verify* cell ends in `PASS: 17 tables` |

## Three design decisions to understand first

**Property names are unique across the whole ontology.** Microsoft's pages differ on this: the data
binding page says names must be unique across all entity types, while the entity type page allows a name
to repeat if the type matches. This design follows the stricter rule, so it's valid under both. `StoreID`
appears in seven tables, so only `Store` keeps that name; the order's copy becomes `OrderStoreID` and the
stock ledger's becomes `BalanceStoreID`. The rule: an entity type's own key keeps its column name, and a
reference to something else takes its owner's prefix. That's 29 renames, marked **(rename)** below. One
exception: `ReturnReason`'s key becomes `ReasonID`, so a return keeps the natural `ReturnReasonID`.

**`Product`, `Order` and `Return` can't be entity type names.** They're GQL reserved words. The style
table becomes **`ProductStyle`** (the sellable size-and-colour item is **`ProductVariant`**), and orders
and returns become **`SalesOrder`** and **`SalesReturn`**.

**Every entity type has a single-column key.** Order lines, stock positions and monthly stock balances are
naturally identified by several columns, but a relationship matches one column per side. So the data
carries `OrderLineID` (`SO000001-1`), `InventoryID` (`ST001-V00002`) and `BalanceID`
(`ST001-V00002-202501`).

Two tables get no entity type: `dim_date`, because dates are properties on the things that happen (the
date table is for the semantic model in Episode 2), and `order_line_promotion`, which is only the mapping
table behind the `lineOnPromotion` relationship.

## Step 1: create the ontology item

From the task flow's **Ontology** task: **+ New item** → **Ontology (preview)**. In the **New Ontology**
dialog: **Name** `Yuktikara_Ontology` (letters, numbers and underscores only), **Location** the
`ontology` folder, **Assign to task** `Ontology` → **Create**.

Fabric also creates three items that belong to the ontology: a **graph model**, a lakehouse named
`Yuktikara_Ontology_lh_…` and that lakehouse's SQL analytics endpoint. They land in the `ontology` folder
under the **Ontology** task, which then shows 4 items. Leave all three alone; you only use the graph model,
in step 4.

## Step 2: entity types and their data bindings

Build **all 15 entity types before any relationship**: a relationship needs a key at both ends.

Each entity type needs a name, its properties, a key, a data binding, a display name property and its
metadata (a description, synonyms and, where useful, additional metadata). The portal says this metadata
"helps AI agents better understand and work with your data", so it's part of the build, not an extra.
Everything for each entity type is in one section below; property descriptions are in step 5.

There are two ways to add the properties:

- **From the data** (quicker, recommended for all 15): **Add binding and properties** creates one property
  per column of the table, typed from the table. You rename only the ones marked **(rename)**.
- **By hand, then bind**: **Add properties** first, entering each name and choosing its **Property type**,
  then bind the table to them. Same result, more typing. The Episode 1 article shows this route on Store.

Either way, the **Type** column in the tables below is what the **Configure** page should show once the
binding is saved.

### Walkthrough, using Store

1. **Create it.** On the canvas: **Add entity type** (ribbon, or the middle of an empty canvas) →
   **Entity type name** `Store` → **Add Entity Type**. Names are 1 to 26 characters: letters, numbers,
   hyphens and underscores.
2. **Open it.** Select `Store` in the **Explorer** → **View entity type details**. The **Configure** tab
   opens.
3. **Bind the table.** **Manage property bindings** → **Add binding and properties** → **Add data binding**
   → in the OneLake catalog: `yuktikara_lh` → **Tables** → `store` → `store`.
4. **Fill in the Bind data to properties page:**
   - **Entity type key**: **Define entity type key** → `StoreID` → **Save**. Keys must be string or
     integer.
   - **Binding selection**: the source table, `store`.
   - **Entity type key mapping**: source column `StoreID` → property `StoreID`.
   - **Timeseries data**: appears on any table with a date column, with **Timestamp column** marked
     required. Leave it empty; the binding still saves as static. Every binding here is static, and each
     entity type takes exactly one. The live RFID feed arrives in Episode 3 as a time-series binding.
   - **Properties**: **Source column** on the left, **Property name** on the right, for every column
     except the key. Change only the names marked **(rename)** in the tables below. There's no type to
     set here: each property takes its column's type from the table. The icon before each source column
     hints at it (**ABC** text, **1.2** decimal, **123** whole number, a calendar for dates).
5. **Save**, wait for *entity type updated successfully*, then **Cancel** back to **Configure**.
6. **Check it and set the display name.** On **Configure**, every property should show `store` under
   **Data source**, and its **Type** should match the tables below. Then **Choose display name property** →
   `StoreName`, so the graph shows store names instead of IDs.
7. **Describe it.** Further down **Configure**, in **Entity metadata**: paste the **Description**, add each
   **Synonym** with **+**, add any **Additional metadata** with **+** (a key and a value), then **Update**.
   For Store: the description from its table below, synonyms *Shop*, *Location*, *Branch*, and
   `domain` = `Retail operations`.
8. **Home** takes you back to the canvas.

Property descriptions come later, in step 5.

Repeat for the other 14, in this order. Instance counts are for the committed snapshot. After regenerating
the data, compare against the `manifest.json` you uploaded with it.

<!-- generated:entities -->
| # | Entity type | Table | Entity type key | Display name property |
|---:|---|---|---|---|
| 1 | Store | `store.store` | `StoreID` | `StoreName` |
| 2 | Supplier | `product.supplier` | `SupplierID` | `SupplierName` |
| 3 | ProductStyle | `product.product` | `ProductID` | `ProductName` |
| 4 | ProductVariant | `product.product_variant` | `VariantID` | `SKU` |
| 5 | Customer | `customer.customer` | `CustomerID` | `CustomerName` |
| 6 | SalesOrder | `sales.sales_order` | `OrderID` | `OrderNumber` |
| 7 | SalesOrderLine | `sales.sales_order_line` | `OrderLineID` | `OrderLineID` (no name column, so the key) |
| 8 | SalesReturn | `sales.sales_return` | `ReturnID` | `ReturnID` (no name column, so the key) |
| 9 | ReturnReason | `sales.return_reason` | `ReasonID` | `ReturnReasonName` |
| 10 | StoreInventory | `store.store_inventory` | `InventoryID` | `InventoryID` (no name column, so the key) |
| 11 | InventoryBalance | `store.inventory_balance` | `BalanceID` | `BalanceID` (no name column, so the key) |
| 12 | PurchaseOrder | `supply.purchase_order` | `PurchaseOrderID` | `PurchaseOrderID` (no name column, so the key) |
| 13 | PurchaseOrderLine | `supply.purchase_order_line` | `PurchaseOrderLineID` | `PurchaseOrderLineID` (no name column, so the key) |
| 14 | Promotion | `sales.promotion` | `PromotionID` | `PromotionName` |
| 15 | SalesTarget | `sales.sales_target` | `TargetID` | `TargetID` (no name column, so the key) |

### Store

| Setting | Value |
|---|---|
| Table | `store.store` |
| Entity type key | `StoreID` |
| Display name property | `StoreName` |
| Description | A Yuktikara selling location: one of 18 physical shops or the online channel ST900. Every order, return and stock position points back to a store. |
| Synonyms | Shop, Location, Branch |
| Additional metadata | `domain` = `Retail operations` |
| Instances (committed snapshot) | 19 |

| Source column | Property name | Type |
|---|---|---|
| `StoreID` | `StoreID` | string |
| `StoreName` | `StoreName` | string |
| `RegionName` | `RegionName` | string |
| `City` | `City` | string |
| `StateCode` | `StateCode` | string |
| `Latitude` | `Latitude` | double |
| `Longitude` | `Longitude` | double |
| `StoreFormat` | `StoreFormat` | string |
| `SquareFeet` | `SquareFeet` | integer |
| `OpenedDate` | `OpenedDate` | datetime |

### Supplier

| Setting | Value |
|---|---|
| Table | `product.supplier` |
| Entity type key | `SupplierID` |
| Display name property | `SupplierName` |
| Description | A manufacturer Yuktikara buys finished styles from. Each style comes from exactly one supplier, and suppliers vary in lead time, delivery reliability and quality. |
| Synonyms | Vendor, Manufacturer |
| Additional metadata | None |
| Instances (committed snapshot) | 7 |

| Source column | Property name | Type |
|---|---|---|
| `SupplierID` | `SupplierID` | string |
| `SupplierName` | `SupplierName` | string |
| `Country` | `Country` | string |
| `LeadTimeDays` | `LeadTimeDays` | integer |
| `QualityRating` | `QualityRating` | double |

### ProductStyle

| Setting | Value |
|---|---|
| Table | `product.product` |
| Entity type key | `ProductID` |
| Display name property | `ProductName` |
| Description | A product design, for example the Cascade Ridge Hiking Boot. A style isn't sellable on its own; a customer buys a ProductVariant, one size and colour of it. |
| Synonyms | Style, Product |
| Additional metadata | None |
| Instances (committed snapshot) | 52 |

| Source column | Property name | Type |
|---|---|---|
| `ProductID` | `ProductID` | string |
| `StyleCode` | `StyleCode` | string |
| `ProductName` | `ProductName` | string |
| `DepartmentName` | `DepartmentName` | string |
| `CategoryName` | `CategoryName` | string |
| `SupplierID` | **`StyleSupplierID`** (rename) | string |
| `SeasonCode` | `SeasonCode` | string |
| `ListPrice` | **`StyleListPrice`** (rename) | double |
| `UnitCost` | `UnitCost` | double |
| `LaunchDate` | `LaunchDate` | datetime |
| `IsRfidTagged` | `IsRfidTagged` | boolean |

### ProductVariant

| Setting | Value |
|---|---|
| Table | `product.product_variant` |
| Entity type key | `VariantID` |
| Display name property | `SKU` |
| Description | A single sellable item: one style, in one colour and one size. Order lines, returns and stock positions all point to a variant, never directly to a style. |
| Synonyms | SKU, Variant |
| Additional metadata | None |
| Instances (committed snapshot) | 744 |

| Source column | Property name | Type |
|---|---|---|
| `VariantID` | `VariantID` | string |
| `ProductID` | **`VariantProductID`** (rename) | string |
| `SKU` | `SKU` | string |
| `ColorName` | `ColorName` | string |
| `SizeCode` | `SizeCode` | string |
| `SizeOrder` | `SizeOrder` | integer |
| `ListPrice` | **`VariantListPrice`** (rename) | double |

### Customer

| Setting | Value |
|---|---|
| Table | `customer.customer` |
| Entity type key | `CustomerID` |
| Display name property | `CustomerName` |
| Description | A synthetic shopper. No real names, emails or addresses exist anywhere in this dataset. |
| Synonyms | Shopper, Buyer |
| Additional metadata | None |
| Instances (committed snapshot) | 6,200 |

| Source column | Property name | Type |
|---|---|---|
| `CustomerID` | `CustomerID` | string |
| `CustomerName` | `CustomerName` | string |
| `LoyaltyTier` | `LoyaltyTier` | string |
| `JoinDate` | `JoinDate` | datetime |
| `HomeCity` | `HomeCity` | string |
| `HomeStateCode` | `HomeStateCode` | string |
| `PreferredStoreID` | `PreferredStoreID` | string |

### SalesOrder

| Setting | Value |
|---|---|
| Table | `sales.sales_order` |
| Entity type key | `OrderID` |
| Display name property | `OrderNumber` |
| Description | One customer order, placed in a store or online. Carries five money columns; picking the wrong one is the most common way to misstate sales. Net sales is built from SubTotal, only on Completed or Shipped orders. |
| Synonyms | Order, Sale |
| Additional metadata | None |
| Instances (committed snapshot) | 33,757 |

| Source column | Property name | Type |
|---|---|---|
| `OrderID` | `OrderID` | string |
| `OrderNumber` | `OrderNumber` | string |
| `StoreID` | **`OrderStoreID`** (rename) | string |
| `CustomerID` | **`OrderCustomerID`** (rename) | string |
| `Channel` | `Channel` | string |
| `OrderDate` | `OrderDate` | datetime |
| `OrderStatus` | `OrderStatus` | string |
| `GrossAmount` | `GrossAmount` | double |
| `DiscountAmount` | **`OrderDiscountAmount`** (rename) | double |
| `SubTotal` | `SubTotal` | double |
| `TaxAmount` | `TaxAmount` | double |
| `OrderTotal` | `OrderTotal` | double |
| `PaymentMethod` | `PaymentMethod` | string |

### SalesOrderLine

| Setting | Value |
|---|---|
| Table | `sales.sales_order_line` |
| Entity type key | `OrderLineID` |
| Display name property | `OrderLineID` (no name column, so the key) |
| Description | One variant on one order. An order with three items has three lines. |
| Synonyms | Order line, Line item |
| Additional metadata | None |
| Instances (committed snapshot) | 69,198 |

| Source column | Property name | Type |
|---|---|---|
| `OrderLineID` | `OrderLineID` | string |
| `OrderID` | **`LineOrderID`** (rename) | string |
| `OrderLineNumber` | `OrderLineNumber` | integer |
| `VariantID` | **`LineVariantID`** (rename) | string |
| `ProductID` | **`LineProductID`** (rename) | string |
| `Quantity` | `Quantity` | integer |
| `UnitPrice` | `UnitPrice` | double |
| `DiscountAmount` | **`LineDiscountAmount`** (rename) | double |
| `LineTotal` | `LineTotal` | double |

### SalesReturn

| Setting | Value |
|---|---|
| Table | `sales.sales_return` |
| Entity type key | `ReturnID` |
| Display name property | `ReturnID` (no name column, so the key) |
| Description | A returned order line. Returns only exist against orders that were Completed or Shipped. Only Accepted returns, on their ReturnDate, reduce net sales. |
| Synonyms | Return, Refund |
| Additional metadata | None |
| Instances (committed snapshot) | 6,749 |

| Source column | Property name | Type |
|---|---|---|
| `ReturnID` | `ReturnID` | string |
| `OrderID` | **`ReturnOrderID`** (rename) | string |
| `OrderLineNumber` | **`ReturnOrderLineNumber`** (rename) | integer |
| `OrderLineID` | **`ReturnOrderLineID`** (rename) | string |
| `VariantID` | **`ReturnVariantID`** (rename) | string |
| `ProductID` | **`ReturnProductID`** (rename) | string |
| `ReturnDate` | `ReturnDate` | datetime |
| `ReturnStoreID` | `ReturnStoreID` | string |
| `QuantityReturned` | `QuantityReturned` | integer |
| `ReturnAmount` | `ReturnAmount` | double |
| `ReturnStatus` | `ReturnStatus` | string |
| `ReturnReasonID` | `ReturnReasonID` | string |
| `RestockFlag` | `RestockFlag` | boolean |

### ReturnReason

| Setting | Value |
|---|---|
| Table | `sales.return_reason` |
| Entity type key | `ReasonID` |
| Display name property | `ReturnReasonName` |
| Description | One of eight reasons a customer can give for a return, grouped into five categories. |
| Synonyms | Reason |
| Additional metadata | None |
| Instances (committed snapshot) | 8 |

| Source column | Property name | Type |
|---|---|---|
| `ReturnReasonID` | **`ReasonID`** (rename) | string |
| `ReturnReasonName` | `ReturnReasonName` | string |
| `ReturnCategory` | `ReturnCategory` | string |

### StoreInventory

| Setting | Value |
|---|---|
| Table | `store.store_inventory` |
| Entity type key | `InventoryID` |
| Display name property | `InventoryID` (no name column, so the key) |
| Description | What the RFID stock count found on the shop floor and in the stockroom on the last day of the window, for every store and variant combination the store carries. A snapshot; InventoryBalance holds the months of movement behind it. |
| Synonyms | Shelf stock, Floor stock, Stock snapshot |
| Additional metadata | `grain` = `one store + one variant, current snapshot` |
| Instances (committed snapshot) | 11,773 |

| Source column | Property name | Type |
|---|---|---|
| `InventoryID` | `InventoryID` | string |
| `StoreID` | **`InventoryStoreID`** (rename) | string |
| `VariantID` | **`InventoryVariantID`** (rename) | string |
| `ProductID` | **`InventoryProductID`** (rename) | string |
| `SnapshotDate` | `SnapshotDate` | datetime |
| `FloorQty` | `FloorQty` | integer |
| `BackroomQty` | `BackroomQty` | integer |
| `OnHandQty` | `OnHandQty` | integer |
| `FloorMinQty` | `FloorMinQty` | integer |
| `ReorderPoint` | `ReorderPoint` | integer |

### InventoryBalance

| Setting | Value |
|---|---|
| Table | `store.inventory_balance` |
| Entity type key | `BalanceID` |
| Display name property | `BalanceID` (no name column, so the key) |
| Description | The monthly stock ledger for one store and variant. It balances exactly and closes on the count in StoreInventory: opening plus received minus sold plus returned plus adjusted equals closing. |
| Synonyms | Stock ledger, Stock movement |
| Additional metadata | `grain` = `one store + one variant + one month` |
| Instances (committed snapshot) | 235,460 |

| Source column | Property name | Type |
|---|---|---|
| `BalanceID` | `BalanceID` | string |
| `StoreID` | **`BalanceStoreID`** (rename) | string |
| `VariantID` | **`BalanceVariantID`** (rename) | string |
| `ProductID` | **`BalanceProductID`** (rename) | string |
| `BalanceMonth` | `BalanceMonth` | datetime |
| `OpeningQty` | `OpeningQty` | integer |
| `ReceivedQty` | `ReceivedQty` | integer |
| `SoldQty` | `SoldQty` | integer |
| `ReturnedQty` | `ReturnedQty` | integer |
| `AdjustedQty` | `AdjustedQty` | integer |
| `ClosingQty` | `ClosingQty` | integer |
| `DaysOutOfStock` | `DaysOutOfStock` | integer |
| `DaysBelowShelfMin` | `DaysBelowShelfMin` | integer |

### PurchaseOrder

| Setting | Value |
|---|---|
| Table | `supply.purchase_order` |
| Entity type key | `PurchaseOrderID` |
| Display name property | `PurchaseOrderID` (no name column, so the key) |
| Description | One order a store placed with a supplier. Stores reorder from each supplier roughly every two weeks. An order still in transit at the end of the window has no DeliveredDate. |
| Synonyms | Purchase order, PO |
| Additional metadata | None |
| Instances (committed snapshot) | 6,108 |

| Source column | Property name | Type |
|---|---|---|
| `PurchaseOrderID` | `PurchaseOrderID` | string |
| `SupplierID` | **`POSupplierID`** (rename) | string |
| `StoreID` | **`POStoreID`** (rename) | string |
| `PurchaseOrderDate` | `PurchaseOrderDate` | datetime |
| `ExpectedDeliveryDate` | `ExpectedDeliveryDate` | datetime |
| `DeliveredDate` | `DeliveredDate` | datetime |
| `POStatus` | `POStatus` | string |
| `POTotalCost` | `POTotalCost` | double |

### PurchaseOrderLine

| Setting | Value |
|---|---|
| Table | `supply.purchase_order_line` |
| Entity type key | `PurchaseOrderLineID` |
| Display name property | `PurchaseOrderLineID` (no name column, so the key) |
| Description | One variant on a purchase order. A short delivery shows QuantityReceived below QuantityOrdered. |
| Synonyms | PO line |
| Additional metadata | None |
| Instances (committed snapshot) | 81,170 |

| Source column | Property name | Type |
|---|---|---|
| `PurchaseOrderLineID` | `PurchaseOrderLineID` | string |
| `PurchaseOrderID` | **`POLineOrderID`** (rename) | string |
| `VariantID` | **`POLineVariantID`** (rename) | string |
| `ProductID` | **`POLineProductID`** (rename) | string |
| `QuantityOrdered` | `QuantityOrdered` | integer |
| `QuantityReceived` | `QuantityReceived` | integer |
| `POUnitCost` | `POUnitCost` | double |
| `POLineCost` | `POLineCost` | double |

### Promotion

| Setting | Value |
|---|---|
| Table | `sales.promotion` |
| Entity type key | `PromotionID` |
| Display name property | `PromotionName` |
| Description | A named markdown campaign: a clearance after the holidays or at the end of summer, or a smaller seasonal event in between. |
| Synonyms | Campaign, Sale event |
| Additional metadata | None |
| Instances (committed snapshot) | 8 |

| Source column | Property name | Type |
|---|---|---|
| `PromotionID` | `PromotionID` | string |
| `PromotionName` | `PromotionName` | string |
| `PromotionType` | `PromotionType` | string |
| `PromotionStartDate` | `PromotionStartDate` | datetime |
| `PromotionEndDate` | `PromotionEndDate` | datetime |
| `DiscountDepth` | `DiscountDepth` | string |

### SalesTarget

| Setting | Value |
|---|---|
| Table | `sales.sales_target` |
| Entity type key | `TargetID` |
| Display name property | `TargetID` (no name column, so the key) |
| Description | One store's net sales target for one month. Targets follow the store's normal trading pattern; the stores opened in 2023 and the online channel were set more ambitious growth targets. |
| Synonyms | Target, Plan, Quota |
| Additional metadata | None |
| Instances (committed snapshot) | 456 |

| Source column | Property name | Type |
|---|---|---|
| `TargetID` | `TargetID` | string |
| `StoreID` | **`TargetStoreID`** (rename) | string |
| `TargetMonth` | `TargetMonth` | datetime |
| `TargetNetSales` | `TargetNetSales` | double |
<!-- /generated:entities -->

**Checkpoint:** the Explorer lists 15 entity types, each with a key, a display name property, every
property bound, and a description.

## Step 3: relationships

For each row: **+ Add relationship** (Home toolbar, or **…** next to the origin entity type). In the **Add
new relationship** dialog: **Relationship type name**, **Origin entity type**, **Target entity type** →
**Create**. Select the new relationship on the canvas and fill in the middle panel:

- **Mapping table**: pick the table from the dropdown.
- **Matched *Origin*: *key*** (for example **Matched SalesOrder: OrderID**): the column in that table whose
  values match the origin entity type's key.
- **Matched *Target*: *key*** (for example **Matched Store: StoreID**): the column whose values match the
  target entity type's key.

If you pick origin and target the wrong way round, **Switch direction** swaps them.

Further down the same page: **Metadata** → **Edit** → paste the **Description** from the table below →
**Update**. Then **Save** at the bottom of the page, and **Cancel** to close it. The matched columns are **source column names**
from the table, not the renamed properties: `StoreID`, not `OrderStoreID`.

The dialog calls the mapping table *optional*. Every relationship here needs one: without it the
relationship type exists in the design but has no instances, so the graph has no edges for it.

<!-- generated:relationships -->
| # | Relationship type | Origin → Target | Mapping table | Matched origin column | Matched target column | Description | Edges in snapshot |
|---:|---|---|---|---|---|---|---:|
| 1 | `orderAtStore` | SalesOrder → Store | `sales.sales_order` | `OrderID` | `StoreID` | Which store, or the online channel, an order was placed at. | 33,757 |
| 2 | `orderByCustomer` | SalesOrder → Customer | `sales.sales_order` | `OrderID` | `CustomerID` | Which customer placed an order. | 33,757 |
| 3 | `lineInOrder` | SalesOrderLine → SalesOrder | `sales.sales_order_line` | `OrderLineID` | `OrderID` | Which order an order line belongs to. | 69,198 |
| 4 | `lineForVariant` | SalesOrderLine → ProductVariant | `sales.sales_order_line` | `OrderLineID` | `VariantID` | Which variant an order line is for. | 69,198 |
| 5 | `lineOfStyle` | SalesOrderLine → ProductStyle | `sales.sales_order_line` | `OrderLineID` | `ProductID` | Which style an order line is for, in one hop instead of going through the variant. | 69,198 |
| 6 | `variantOfStyle` | ProductVariant → ProductStyle | `product.product_variant` | `VariantID` | `ProductID` | Which style a variant belongs to. | 744 |
| 7 | `styleFromSupplier` | ProductStyle → Supplier | `product.product` | `ProductID` | `SupplierID` | Which supplier manufactures a style. | 52 |
| 8 | `returnOfLine` | SalesReturn → SalesOrderLine | `sales.sales_return` | `ReturnID` | `OrderLineID` | Which order line a return applies to. | 6,749 |
| 9 | `returnOfStyle` | SalesReturn → ProductStyle | `sales.sales_return` | `ReturnID` | `ProductID` | Which style a return applies to, in one hop instead of going through the order line and variant. | 6,749 |
| 10 | `returnHasReason` | SalesReturn → ReturnReason | `sales.sales_return` | `ReturnID` | `ReturnReasonID` | Why a return was made. | 6,749 |
| 11 | `returnTakenAtStore` | SalesReturn → Store | `sales.sales_return` | `ReturnID` | `ReturnStoreID` | Which store physically took a return back. Separate from orderAtStore, because a customer can return to a different store than the one that sold it. | 6,749 |
| 12 | `stockAtStore` | StoreInventory → Store | `store.store_inventory` | `InventoryID` | `StoreID` | Which store a shelf-stock position belongs to. | 11,773 |
| 13 | `stockOfVariant` | StoreInventory → ProductVariant | `store.store_inventory` | `InventoryID` | `VariantID` | Which variant a shelf-stock position is counting. | 11,773 |
| 14 | `balanceAtStore` | InventoryBalance → Store | `store.inventory_balance` | `BalanceID` | `StoreID` | Which store a month of stock movement belongs to. | 235,460 |
| 15 | `balanceOfVariant` | InventoryBalance → ProductVariant | `store.inventory_balance` | `BalanceID` | `VariantID` | Which variant a month of stock movement is for. | 235,460 |
| 16 | `poFromSupplier` | PurchaseOrder → Supplier | `supply.purchase_order` | `PurchaseOrderID` | `SupplierID` | Which supplier a purchase order was placed with. | 6,108 |
| 17 | `poForStore` | PurchaseOrder → Store | `supply.purchase_order` | `PurchaseOrderID` | `StoreID` | Which store a purchase order is being delivered to. | 6,108 |
| 18 | `poLineOnOrder` | PurchaseOrderLine → PurchaseOrder | `supply.purchase_order_line` | `PurchaseOrderLineID` | `PurchaseOrderID` | Which purchase order a line belongs to. | 81,170 |
| 19 | `poLineForVariant` | PurchaseOrderLine → ProductVariant | `supply.purchase_order_line` | `PurchaseOrderLineID` | `VariantID` | Which variant a purchase order line is for. | 81,170 |
| 20 | `poLineOfStyle` | PurchaseOrderLine → ProductStyle | `supply.purchase_order_line` | `PurchaseOrderLineID` | `ProductID` | Which style a purchase order line is for, in one hop instead of going through the variant. | 81,170 |
| 21 | `lineOnPromotion` | SalesOrderLine → Promotion | `sales.order_line_promotion` | `OrderLineID` | `PromotionID` | Which campaign a discounted order line was sold under. | 16,501 |
| 22 | `targetForStore` | SalesTarget → Store | `sales.sales_target` | `TargetID` | `StoreID` | Which store a monthly sales target belongs to. | 456 |
<!-- /generated:relationships -->

Every name is unique; Microsoft lists duplicate relationship names as a known issue that breaks
natural-language queries. Two are deliberate shortcuts: `lineOfStyle` and `returnOfStyle` reach
`ProductStyle` in one hop instead of going through `ProductVariant`, which keeps the return-rate question
to one hop per side.

`returnTakenAtStore` is what makes "which store takes back the most online returns?" answerable. A return
reaches a store two ways: through its order (`returnOfLine` → `lineInOrder` → `orderAtStore`, the store
that sold it) and directly (the store that took it back).

**Watch `returnHasReason`.** ReturnReason's key property is named `ReasonID`, but the column in
`sales_return` is `ReturnReasonID`. So **Matched ReturnReason: ReasonID** takes `ReturnReasonID`, not
`ReturnID` or `ReasonID`. Get it wrong and the relationship saves without complaint but links no return to
any reason: a data agent then reports that no return reasons exist.

**One special case, `lineOnPromotion`.** For the other 21, the mapping table is the origin entity type's own
table. `lineOnPromotion` uses `order_line_promotion` instead: a linking table with one row per discounted
order line and no entity type of its own. Pick it from the **Mapping table** dropdown like any other table.
Lines sold at full price have no row there, so they have no promotion edge.

If a **Matched** dropdown offers no keys, the entity type at that end has no key yet. Go back to step 2.

**Checkpoint:** the canvas shows 22 relationships, each with a mapping table, both matched columns and a
description.

## Step 4: refresh and verify the graph

Changing the ontology's design re-ingests the bound data by itself. New **rows** don't, so refresh after
every notebook run: workspace → the ontology's graph model (type **Graph model**) → **…** → **Refresh now**.
Each refresh rebuilds the whole graph and uses capacity, so batch your changes, and leave **Schedule** (the
recurring refresh, on the same menu) unset, on the trial or on a paid capacity.

Then select an entity type → **View entity type details** → **Instances**:

| Check | Expected |
|---|---|
| Each entity type's instance count | Its table's row count in the run's `manifest.json` |
| `ProductStyle` → *Cascade Ridge Hiking Boot* | Linked to supplier *Halden Footwear Group* through `styleFromSupplier` |
| A `SalesReturn` instance | One edge each for `returnOfLine`, `returnOfStyle`, `returnHasReason` and `returnTakenAtStore` |
| **Overview** → graph → **Expand** → **Query builder** → **Run query** | Returns results; switch to **Table** view to read IDs |

Zero instances or missing edges usually mean a missing key, a wrong matched column, or a table that isn't a
managed Delta table. The notebook's *Verify* cell already rules out the last one.

## Step 5: property descriptions

Each of the 127 properties gets a description, and money and sensitive-looking properties get additional
metadata. Do this after the relationships, once the ontology works.

For each property: select the **tag icon** next to it (in **Properties** on the binding page: **Configure**
→ **Manage property bindings** → **Manage bindings**, or in the **Add properties** dialog) → **Description**
and any **Additional metadata** → **Update**. Each description then shows in the **Description** column on
**Configure**.

Additional metadata keys only need to be unique within their own object, not across the ontology, so
`unit` repeats on every money property, and that's fine.

<!-- generated:property-metadata -->
### Store properties

| Property | Description | Additional metadata |
|---|---|---|
| `StoreID` | Unique store code. ST001-ST018 are physical shops; ST900 is the online channel. |  |
| `StoreName` | Public-facing name shown in reports and the graph, for example Yuktikara Bend Outlet. |  |
| `RegionName` | One of four physical regions, or Online for the e-commerce channel. |  |
| `City` | City the store trades in, used to place it on a map. |  |
| `StateCode` | Two-letter US state code. |  |
| `Latitude` | Map coordinate, decimal degrees. |  |
| `Longitude` | Map coordinate, decimal degrees. |  |
| `StoreFormat` | Flagship, Standard, Outlet or Ecommerce. Drives typical daily order volume. |  |
| `SquareFeet` | Physical retail floor area; 0 for the online channel. |  |
| `OpenedDate` | The day the store opened for trading. Stores opened partway through the period aren't comparable to older ones on raw totals. |  |

### Supplier properties

| Property | Description | Additional metadata |
|---|---|---|
| `SupplierID` | Unique supplier code, SUP01-SUP07. |  |
| `SupplierName` | The manufacturer's name. |  |
| `Country` | Country the goods are manufactured in. |  |
| `LeadTimeDays` | Days the supplier quotes between placing a purchase order and delivery. Compare against actual delivery dates to see who is reliable. |  |
| `QualityRating` | 1.0-5.0 quality score. The lowest-rated supplier also has the weakest on-time delivery record. | `unit` = `1-5 rating` |

### ProductStyle properties

| Property | Description | Additional metadata |
|---|---|---|
| `ProductID` | Unique style code, P0001-P0052. |  |
| `StyleCode` | Human-readable style code, for example YK-FOO-0001. |  |
| `ProductName` | The style's name, unique across the catalogue. |  |
| `DepartmentName` | Footwear, Apparel or Equipment. |  |
| `CategoryName` | Product category within the department, for example Hiking Boots or Rain Shells. |  |
| `StyleSupplierID` | The manufacturer of this style. |  |
| `SeasonCode` | The season the style was designed for, for example SS26 or AllSeason. |  |
| `StyleListPrice` | List price before any markdown, shared by every variant of the style. | `unit` = `USD` |
| `UnitCost` | What Yuktikara pays the supplier per unit, 38-52% of list price. | `unit` = `USD` |
| `LaunchDate` | The date this style went on sale. |  |
| `IsRfidTagged` | True for Footwear and Apparel, false for Equipment. Only RFID-tagged styles appear in the shop-floor stock data. |  |

### ProductVariant properties

| Property | Description | Additional metadata |
|---|---|---|
| `VariantID` | Unique SKU code, V00001-. |  |
| `VariantProductID` | The style this variant belongs to. |  |
| `SKU` | Human-readable SKU, also the display name for this entity type. |  |
| `ColorName` | One of two or three colourways offered for the style. |  |
| `SizeCode` | Footwear sizes 7-13 in half sizes, Apparel XS-XXL, Equipment One Size. |  |
| `SizeOrder` | Numeric sort order for SizeCode, because the text values don't sort correctly on their own (XS would sort after L). |  |
| `VariantListPrice` | Inherited from the style; the same for every variant of it. | `unit` = `USD` |

### Customer properties

| Property | Description | Additional metadata |
|---|---|---|
| `CustomerID` | Unique customer code, C00001-. |  |
| `CustomerName` | Invented first and last name. | `sensitivity` = `none - synthetic data` |
| `LoyaltyTier` | None, Trailhead, Summit or Alpine, in ascending order. |  |
| `JoinDate` | When the customer joined the loyalty programme; may be before the sales window starts. |  |
| `HomeCity` | Invented home city. | `sensitivity` = `none - synthetic data` |
| `HomeStateCode` | Invented home state. | `sensitivity` = `none - synthetic data` |
| `PreferredStoreID` | The physical store the customer nominated as their preference. They may buy anywhere, including online. |  |

### SalesOrder properties

| Property | Description | Additional metadata |
|---|---|---|
| `OrderID` | Unique order code, SO000001-. |  |
| `OrderNumber` | Customer-facing order reference, for example YK-2026-000123. |  |
| `OrderStoreID` | The store, or ST900 online, where the order was placed. |  |
| `OrderCustomerID` | The customer who placed the order. |  |
| `Channel` | Store or Online. |  |
| `OrderDate` | The day the order was placed. |  |
| `OrderStatus` | Completed, Shipped, Pending or Cancelled. Only Completed and Shipped orders count as sales. |  |
| `GrossAmount` | Quantity times unit price, before any markdown. | `unit` = `USD` |
| `OrderDiscountAmount` | Sum of the line-level markdowns on this order. | `unit` = `USD` |
| `SubTotal` | GrossAmount minus the order's discount. This is the sales-recognised amount net sales is built from. | `unit` = `USD` |
| `TaxAmount` | Sales tax, 8.25% of SubTotal. | `unit` = `USD` |
| `OrderTotal` | SubTotal plus TaxAmount, what the customer actually paid. Includes tax, so it is not a sales figure. | `unit` = `USD` |
| `PaymentMethod` | How the order was paid for. |  |

### SalesOrderLine properties

| Property | Description | Additional metadata |
|---|---|---|
| `OrderLineID` | Unique line code, &lt;OrderID&gt;-&lt;line number&gt;, for example SO000001-1. |  |
| `LineOrderID` | The order this line belongs to. |  |
| `OrderLineNumber` | Position of this line within its order, restarting at 1 for each order. |  |
| `LineVariantID` | The variant sold on this line. |  |
| `LineProductID` | The style the variant belongs to, denormalised so product questions need one hop fewer. |  |
| `Quantity` | Units sold on this line, 1-3. |  |
| `UnitPrice` | Price per unit before markdown. |  |
| `LineDiscountAmount` | Markdown applied to this line. | `unit` = `USD` |
| `LineTotal` | Quantity times UnitPrice minus the line's discount. | `unit` = `USD` |

### SalesReturn properties

| Property | Description | Additional metadata |
|---|---|---|
| `ReturnID` | Unique return code, RT000001-. |  |
| `ReturnOrderID` | The order the returned line belongs to. |  |
| `ReturnOrderLineNumber` | The line number within that order. |  |
| `ReturnOrderLineID` | The order line being returned. |  |
| `ReturnVariantID` | The variant being returned. |  |
| `ReturnProductID` | The style being returned, denormalised. |  |
| `ReturnDate` | The day the return was accepted, rejected or left pending. Net sales counts a return on this date, not the original order date, so a sale made in one quarter can reduce a later one. |  |
| `ReturnStoreID` | The store that physically took the return back. Not always the store that made the sale: a customer can return an online order to any physical store. |  |
| `QuantityReturned` | Units returned; may be fewer than the quantity originally sold on the line. |  |
| `ReturnAmount` | The share of the line's total being refunded. | `unit` = `USD` |
| `ReturnStatus` | Accepted, Pending or Rejected. Only Accepted reduces net sales. |  |
| `ReturnReasonID` | Why the customer returned it. |  |
| `RestockFlag` | True if the returned item can go back on sale; false when it's damaged or otherwise can't be restocked. |  |

### ReturnReason properties

| Property | Description | Additional metadata |
|---|---|---|
| `ReasonID` | Unique reason code, RR1-RR8. |  |
| `ReturnReasonName` | The reason text shown to the customer, for example Too small or Damaged or faulty. |  |
| `ReturnCategory` | Groups the eight reasons into Fit, Description, Quality, Logistics or Customer. |  |

### StoreInventory properties

| Property | Description | Additional metadata |
|---|---|---|
| `InventoryID` | Unique position code, &lt;StoreID&gt;-&lt;VariantID&gt;. |  |
| `InventoryStoreID` | Physical stores only; the online channel's stock isn't counted here. |  |
| `InventoryVariantID` | The variant being counted. |  |
| `InventoryProductID` | The style, denormalised. |  |
| `SnapshotDate` | The day this count was taken, the last day of the data window. |  |
| `FloorQty` | Units physically on the shop floor. |  |
| `BackroomQty` | Units in the stockroom, not yet on the floor. |  |
| `OnHandQty` | FloorQty plus BackroomQty. |  |
| `FloorMinQty` | The shelf minimum for this variant at this store, set from how fast it sells there. Below this, the floor should be refilled from the backroom, the trigger the operations agent watches for. |  |
| `ReorderPoint` | Below this level, the store places a new purchase order with the supplier. |  |

### InventoryBalance properties

| Property | Description | Additional metadata |
|---|---|---|
| `BalanceID` | Unique code, &lt;StoreID&gt;-&lt;VariantID&gt;-&lt;YYYYMM&gt;. |  |
| `BalanceStoreID` | The store this month's movement belongs to. |  |
| `BalanceVariantID` | The variant this month's movement belongs to. |  |
| `BalanceProductID` | The style, denormalised. |  |
| `BalanceMonth` | First day of the month this row covers. |  |
| `OpeningQty` | Units on hand at the start of the month, equal to the previous month's closing quantity. |  |
| `ReceivedQty` | Units delivered by the supplier during the month. |  |
| `SoldQty` | Units sold at this store on Completed or Shipped orders during the month. |  |
| `ReturnedQty` | Accepted returns put back on sale at this store during the month. |  |
| `AdjustedQty` | Stock-count corrections: negative for a loss found at count time, positive for stock sent in from another store to cover a shortfall. |  |
| `ClosingQty` | Units on hand at the end of the month. The last month's value equals the on-hand quantity in StoreInventory for this position. |  |
| `DaysOutOfStock` | Days during the month this position ended the day with zero stock. |  |
| `DaysBelowShelfMin` | Days during the month this position ended the day below its shelf minimum. |  |

### PurchaseOrder properties

| Property | Description | Additional metadata |
|---|---|---|
| `PurchaseOrderID` | Unique order code, PO000001-. |  |
| `POSupplierID` | The supplier this order was placed with. |  |
| `POStoreID` | The store the goods are being delivered to. |  |
| `PurchaseOrderDate` | The day the order was placed. |  |
| `ExpectedDeliveryDate` | The order date plus the supplier's quoted lead time. |  |
| `DeliveredDate` | The day the order actually arrived. Empty while the order is still open. Compare against ExpectedDeliveryDate to measure a supplier's on-time performance. |  |
| `POStatus` | Received, Partially received or Open. |  |
| `POTotalCost` | What Yuktikara is paying for everything ordered on this purchase order. | `unit` = `USD` |

### PurchaseOrderLine properties

| Property | Description | Additional metadata |
|---|---|---|
| `PurchaseOrderLineID` | Unique line code, &lt;PurchaseOrderID&gt;-&lt;line number&gt;. |  |
| `POLineOrderID` | The purchase order this line belongs to. |  |
| `POLineVariantID` | The variant being ordered. |  |
| `POLineProductID` | The style, denormalised. |  |
| `QuantityOrdered` | Units ordered on this line. |  |
| `QuantityReceived` | Units that actually arrived; zero while the order is still open. |  |
| `POUnitCost` | Cost per unit for this delivery. Some suppliers' unit costs rise partway through the current year. | `unit` = `USD` |
| `POLineCost` | QuantityOrdered times the unit cost. | `unit` = `USD` |

### Promotion properties

| Property | Description | Additional metadata |
|---|---|---|
| `PromotionID` | Unique campaign code, for example PR2026-1. |  |
| `PromotionName` | The campaign's display name, for example Summer Clearance 2026. |  |
| `PromotionType` | Clearance or Seasonal event. |  |
| `PromotionStartDate` | First day of the campaign. |  |
| `PromotionEndDate` | Last day of the campaign; may fall after the data window for a campaign still running. |  |
| `DiscountDepth` | How deep the campaign's discounts go, for example 15-40% off. |  |

### SalesTarget properties

| Property | Description | Additional metadata |
|---|---|---|
| `TargetID` | Unique code, &lt;StoreID&gt;-&lt;YYYYMM&gt;. |  |
| `TargetStoreID` | The store this target belongs to. |  |
| `TargetMonth` | First day of the month the target covers. |  |
| `TargetNetSales` | The store's net sales target for the month, rounded to the nearest thousand. | `unit` = `USD` |
<!-- /generated:property-metadata -->

## A note on descriptions and agents

The portal says entity and relationship metadata "helps AI agents better understand and work with your
data". Microsoft's semantic enrichment page, at the time of writing, says the data agent doesn't use these
fields. Episode 2 tests which is true. Either way, the net sales definition also goes into the data agent's
**instructions**, never only into a description.

## Sources

Microsoft Learn, checked 2026-09-23:

- [Create entity types](https://learn.microsoft.com/en-us/fabric/iq/ontology/how-to-create-entity-types): adding properties by hand, display name, supported types
- [Bind data](https://learn.microsoft.com/en-us/fabric/iq/ontology/how-to-bind-data): the binding page, naming, limitations
- [Add relationship types](https://learn.microsoft.com/en-us/fabric/iq/ontology/how-to-create-relationship-types)
- [GQL reserved words](https://learn.microsoft.com/en-us/fabric/graph/gql-reference-reserved-terms)
- [Refresh the graph model](https://learn.microsoft.com/en-us/fabric/iq/ontology/how-to-view-entity-type-details#refresh-the-graph-model)
- [Add semantic enrichment](https://learn.microsoft.com/en-us/fabric/iq/ontology/how-to-add-semantic-enrichment): descriptions, synonyms, additional metadata
