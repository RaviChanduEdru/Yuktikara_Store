# Building the Yuktikara ontology by hand

Every entity type, binding and relationship for the Yuktikara Store ontology, in the order you create them
in the Fabric portal. The ontology is built **from OneLake**: each entity type is bound directly to a
lakehouse table, so every mapping is visible and nothing is generated for you.

Everything on this page was checked against the data by script: property names are unique across the
ontology, all are 26 characters or fewer, none is a GQL reserved word, every key is unique, and every
relationship's matched columns resolve to real keys at both ends.

Ontology is a preview feature. The UI labels below come from the Microsoft Learn pages linked at the end
(checked 2026-09-22); if a label has changed, the concept hasn't.

## Before you start

| Check | How |
|---|---|
| Tenant setting **Ontology item (preview)** is on | Workspace → **+ New item** lists **Ontology (preview)** |
| Workspace is on a Fabric capacity | Workspace settings → License info. A 60-day trial capacity is enough for everything on this page; only Episode 2's data agents need a paid F2 or higher |
| Lakehouse `yuktikara_lh` created with **Lakehouse schemas**, OneLake security **off** | Tables show the schemas `customer`, `product`, `sales`, `shared`, `store`, `supply` (plus the empty default `dbo`) |
| The 17 tables are loaded | The load notebook's *Verify* cell ends in `PASS` |

## Three design decisions to understand first

**Every property name is unique across the whole ontology.** An ontology has one namespace for properties,
and Microsoft's binding page requires names to be unique across all entity types. `StoreID` appears in
seven tables, so only the `Store` entity type keeps that name; the order's copy becomes `OrderStoreID` and
the stock ledger's becomes `BalanceStoreID`. The rule used throughout is: an entity's own key keeps its
column name, and a reference to something else takes its owner's prefix. That gives 29 renames in total,
marked **(rename)** below. The one exception is `ReturnReason`, whose key becomes `ReasonID` so that a
return can keep the natural `ReturnReasonID`.

**`Product` can't be an entity type name.** `PRODUCT` is a GQL reserved word, as are `ORDER` and `RETURN`.
The style-level table becomes **`ProductStyle`**; the sellable size-and-colour item is **`ProductVariant`**.

**Every entity type has a single-column key.** Order lines, stock positions and monthly stock balances are
naturally identified by several columns, but relationships match one column per side, so the data carries
`OrderLineID` (`SO000001-1`), `InventoryID` (`ST001-V00002`) and `BalanceID` (`ST001-V00002-202501`).

Two tables get no entity type. `dim_date`, because dates are properties on the things that happen, and the
date table exists for the semantic model and the lakehouse-only comparison agent. And
`order_line_promotion`, which is only the mapping table behind the `lineOnPromotion` relationship.

## Step 1: create the ontology item

From the task flow's **Ontology** task: **+ New item** → **Ontology (preview)**. In the **New Ontology**
dialog, **Name** `Yuktikara_Ontology`, **Location** the `ontology` folder, **Assign to task** `Ontology` →
**Create**. See [workspace-setup.md](01-workspace-setup.md) for the folder layout.

Ontology names take letters, numbers and underscores only; no spaces or dashes. Fabric also creates a
**graph model** child item in the workspace. Leave it alone until step 4.

## Step 2: entity types and their data bindings

Build **all fifteen entity types and bindings before any relationship**: a relationship needs a key on both
ends.

### Walkthrough, using Store

1. On the configuration canvas, select **Add entity type** (ribbon or canvas centre) → name `Store` →
   **Add Entity Type**.
2. Select **…** next to `Store` → **Bind data** → **Add data binding** → choose the lakehouse source → your
   lakehouse → schema `store` → table `store`.
3. The binding page has four sections:
   - **Entity type key**: the property that identifies each row.
   - **Binding selection**: the source table.
   - **Entity type key mapping**: the source column that maps to the key (string or integer columns only).
   - **Properties**: **Source column** on the left, **Property name** on the right, defaulting to the
     column name.
4. In **Properties**, change only the names marked **(rename)** in the tables below. Leave the data types
   alone; they come from the table.
5. **Define entity type key** → `StoreID` → **Save**.
6. **Save** the binding, wait for *entity type updated successfully*, then **Cancel** to close it.
7. On the **Configure** page, confirm every property shows as bound, then set the **display name property**
   to `StoreName`, so the graph shows store names instead of IDs.
8. Select **Home** to return to the canvas.

A **Timeseries data** section may appear. Ignore it for now: every binding here is static, and each entity
type takes exactly one static binding. The live RFID feed arrives later as a time-series binding.

Repeat for the other fourteen, in this order. Instance counts are for the committed snapshot. After a notebook
regeneration, compare against the `manifest.json` you uploaded with the data instead.

<!-- generated:entities -->
### Store

Table `store.store` · key **`StoreID`** · display name **`StoreName`** · 19 instances in the committed snapshot

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

Table `product.supplier` · key **`SupplierID`** · display name **`SupplierName`** · 7 instances in the committed snapshot

| Source column | Property name | Type |
|---|---|---|
| `SupplierID` | `SupplierID` | string |
| `SupplierName` | `SupplierName` | string |
| `Country` | `Country` | string |
| `LeadTimeDays` | `LeadTimeDays` | integer |
| `QualityRating` | `QualityRating` | double |

### ProductStyle

Table `product.product` · key **`ProductID`** · display name **`ProductName`** · 52 instances in the committed snapshot

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

Table `product.product_variant` · key **`VariantID`** · display name **`SKU`** · 744 instances in the committed snapshot

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

Table `customer.customer` · key **`CustomerID`** · display name **`CustomerName`** · 6,200 instances in the committed snapshot

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

Table `sales.sales_order` · key **`OrderID`** · display name **`OrderNumber`** · 33,757 instances in the committed snapshot

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

Table `sales.sales_order_line` · key **`OrderLineID`** · display name **`OrderLineID`** · 69,198 instances in the committed snapshot

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

Table `sales.sales_return` · key **`ReturnID`** · display name **`ReturnID`** · 6,749 instances in the committed snapshot

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

Table `sales.return_reason` · key **`ReasonID`** · display name **`ReturnReasonName`** · 8 instances in the committed snapshot

| Source column | Property name | Type |
|---|---|---|
| `ReturnReasonID` | **`ReasonID`** (rename) | string |
| `ReturnReasonName` | `ReturnReasonName` | string |
| `ReturnCategory` | `ReturnCategory` | string |

### StoreInventory

Table `store.store_inventory` · key **`InventoryID`** · display name **`InventoryID`** · 11,773 instances in the committed snapshot

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

Table `store.inventory_balance` · key **`BalanceID`** · display name **`BalanceID`** · 235,460 instances in the committed snapshot

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

Table `supply.purchase_order` · key **`PurchaseOrderID`** · display name **`PurchaseOrderID`** · 6,108 instances in the committed snapshot

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

Table `supply.purchase_order_line` · key **`PurchaseOrderLineID`** · display name **`PurchaseOrderLineID`** · 81,170 instances in the committed snapshot

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

Table `sales.promotion` · key **`PromotionID`** · display name **`PromotionName`** · 8 instances in the committed snapshot

| Source column | Property name | Type |
|---|---|---|
| `PromotionID` | `PromotionID` | string |
| `PromotionName` | `PromotionName` | string |
| `PromotionType` | `PromotionType` | string |
| `PromotionStartDate` | `PromotionStartDate` | datetime |
| `PromotionEndDate` | `PromotionEndDate` | datetime |
| `DiscountDepth` | `DiscountDepth` | string |

### SalesTarget

Table `sales.sales_target` · key **`TargetID`** · display name **`TargetID`** · 456 instances in the committed snapshot

| Source column | Property name | Type |
|---|---|---|
| `TargetID` | `TargetID` | string |
| `StoreID` | **`TargetStoreID`** (rename) | string |
| `TargetMonth` | `TargetMonth` | datetime |
| `TargetNetSales` | `TargetNetSales` | double |
<!-- /generated:entities -->

**Checkpoint:** the Explorer lists 15 entity types, each with a key, a display name property and every
property bound.

## Step 3: relationships

For each row: **Add relationship** (ribbon, or **…** next to the origin entity type) → **Relationship type
name**, **Origin entity type**, **Target entity type** → **Create**. Select the new relationship on the
canvas and fill in the middle panel:

- **Mapping table**: **Browse available sources** → the table in the list.
- **Matched** (origin): the column in that table whose values match the origin entity type's key.
- **Matched** (target): the column whose values match the target entity type's key.

**Save**, confirm, **Cancel**. The matched columns are **source column names**, not the renamed properties.

<!-- generated:relationships -->
| # | Relationship type | Origin → Target | Mapping table | Matched origin column | Matched target column | Edges in snapshot |
|---:|---|---|---|---|---|---:|
| 1 | `orderAtStore` | SalesOrder → Store | `sales.sales_order` | `OrderID` | `StoreID` | 33,757 |
| 2 | `orderByCustomer` | SalesOrder → Customer | `sales.sales_order` | `OrderID` | `CustomerID` | 33,757 |
| 3 | `lineInOrder` | SalesOrderLine → SalesOrder | `sales.sales_order_line` | `OrderLineID` | `OrderID` | 69,198 |
| 4 | `lineForVariant` | SalesOrderLine → ProductVariant | `sales.sales_order_line` | `OrderLineID` | `VariantID` | 69,198 |
| 5 | `lineOfStyle` | SalesOrderLine → ProductStyle | `sales.sales_order_line` | `OrderLineID` | `ProductID` | 69,198 |
| 6 | `variantOfStyle` | ProductVariant → ProductStyle | `product.product_variant` | `VariantID` | `ProductID` | 744 |
| 7 | `styleFromSupplier` | ProductStyle → Supplier | `product.product` | `ProductID` | `SupplierID` | 52 |
| 8 | `returnOfLine` | SalesReturn → SalesOrderLine | `sales.sales_return` | `ReturnID` | `OrderLineID` | 6,749 |
| 9 | `returnOfStyle` | SalesReturn → ProductStyle | `sales.sales_return` | `ReturnID` | `ProductID` | 6,749 |
| 10 | `returnHasReason` | SalesReturn → ReturnReason | `sales.sales_return` | `ReturnID` | `ReturnReasonID` | 6,749 |
| 11 | `returnTakenAtStore` | SalesReturn → Store | `sales.sales_return` | `ReturnID` | `ReturnStoreID` | 6,749 |
| 12 | `stockAtStore` | StoreInventory → Store | `store.store_inventory` | `InventoryID` | `StoreID` | 11,773 |
| 13 | `stockOfVariant` | StoreInventory → ProductVariant | `store.store_inventory` | `InventoryID` | `VariantID` | 11,773 |
| 14 | `balanceAtStore` | InventoryBalance → Store | `store.inventory_balance` | `BalanceID` | `StoreID` | 235,460 |
| 15 | `balanceOfVariant` | InventoryBalance → ProductVariant | `store.inventory_balance` | `BalanceID` | `VariantID` | 235,460 |
| 16 | `poFromSupplier` | PurchaseOrder → Supplier | `supply.purchase_order` | `PurchaseOrderID` | `SupplierID` | 6,108 |
| 17 | `poForStore` | PurchaseOrder → Store | `supply.purchase_order` | `PurchaseOrderID` | `StoreID` | 6,108 |
| 18 | `poLineOnOrder` | PurchaseOrderLine → PurchaseOrder | `supply.purchase_order_line` | `PurchaseOrderLineID` | `PurchaseOrderID` | 81,170 |
| 19 | `poLineForVariant` | PurchaseOrderLine → ProductVariant | `supply.purchase_order_line` | `PurchaseOrderLineID` | `VariantID` | 81,170 |
| 20 | `poLineOfStyle` | PurchaseOrderLine → ProductStyle | `supply.purchase_order_line` | `PurchaseOrderLineID` | `ProductID` | 81,170 |
| 21 | `lineOnPromotion` | SalesOrderLine → Promotion | `sales.order_line_promotion` | `OrderLineID` | `PromotionID` | 16,501 |
| 22 | `targetForStore` | SalesTarget → Store | `sales.sales_target` | `TargetID` | `StoreID` | 456 |
<!-- /generated:relationships -->

Every name is unique. Microsoft lists duplicate relationship names as a known issue that breaks
natural-language queries. Two are deliberate shortcuts: `lineOfStyle` and `returnOfStyle` reach
`ProductStyle` in one hop instead of going through `ProductVariant`. That keeps the return-rate question to
a single hop per side while the preview's aggregation support is still rough.

`returnTakenAtStore` is what makes "which store takes back the most online returns?" answerable. A return
reaches a store two ways: through its order (`returnOfLine` → `lineInOrder` → `orderAtStore`, the store
that sold it) and directly (the store that took it back).

If a **Matched** dropdown offers no keys, the entity type at that end has no key yet. Go back to step 2.

**Checkpoint:** the canvas shows 22 relationships, each with a mapping table and both matched columns.

## Step 4: refresh and verify the graph

Changing the schema re-ingests bound data automatically. Changing the **rows** doesn't, so refresh after
every notebook run: workspace → the ontology's graph model → **…** → **Schedule** → **Refresh now**. Each
refresh rebuilds the whole graph and uses capacity, so batch your changes and don't set a recurring
schedule, whether you're on the trial or a paid capacity.

Then select an entity type → **View entity type details** → **Instances**:

| Check | Expected |
|---|---|
| Each entity type's instance count | Its table's row count in the run's `manifest.json` |
| `ProductStyle` → *Cascade Ridge Hiking Boot* | Linked to supplier *Halden Footwear Group* through `styleFromSupplier` |
| A `SalesReturn` instance | One edge each for `returnOfLine`, `returnOfStyle`, `returnHasReason` and `returnTakenAtStore` |
| **Overview** → graph → **Expand** → **Query builder** → **Run query** | Returns results; switch to **Table** view to read IDs |

Zero instances or missing edges usually mean a missing key, a wrong matched column, or a table that isn't a
managed Delta table. The notebook's *Verify* cell already rules out the last one.

## Step 5: semantic enrichment (optional, worth doing anyway)

Descriptions, synonyms and additional metadata make the model readable for people, not for agents:
Microsoft states plainly that **the data agent doesn't use the semantic enrichment fields**. The net
sales definition still goes only into a data agent's **instructions** in Episode 2, never into an entity
description. Do this step because the next person who opens the ontology — including you, in six months —
shouldn't have to reverse-engineer what `BalanceStoreID` means from the source data.

**Entity types** (description, synonyms, additional metadata): select the entity type → **View Entity
Type details** → in the **Metadata** section, **Edit** → fill in **Description**, **Synonyms** and
**Additional metadata** → **Update**.

**Properties** (description and additional metadata, no synonyms): from the entity type's **Configure**
tab, open its data binding → in **Properties**, select the **tag icon** next to the property → **Description**
and **Additional metadata** → **Update**.

**Relationships** (description and additional metadata, no synonyms): open the relationship type's
configuration → **Metadata** → **Edit** → **Description** and **Additional metadata** → **Update**.

**Additional metadata keys must be unique within their own object** (an entity type, a property or a
relationship), never unique across the whole ontology — unlike property names. `unit` is reused below on
every money property, which is fine.

<!-- generated:entity-metadata -->
### Store

**Description:** A Yuktikara selling location: one of 18 physical shops or the online channel ST900. Every order, return and stock position points back to a store.

**Synonyms:** Shop, Location, Branch

**Additional metadata:** `domain` = `Retail operations`

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

### Supplier

**Description:** A manufacturer Yuktikara buys finished styles from. Each style comes from exactly one supplier, and suppliers vary in lead time, delivery reliability and quality.

**Synonyms:** Vendor, Manufacturer

| Property | Description | Additional metadata |
|---|---|---|
| `SupplierID` | Unique supplier code, SUP01-SUP07. |  |
| `SupplierName` | The manufacturer's name. |  |
| `Country` | Country the goods are manufactured in. |  |
| `LeadTimeDays` | Days the supplier quotes between placing a purchase order and delivery. Compare against actual delivery dates to see who is reliable. |  |
| `QualityRating` | 1.0-5.0 quality score. The lowest-rated supplier also has the weakest on-time delivery record. | `unit`=`1-5 rating` |

### ProductStyle

**Description:** A product design, for example the Cascade Ridge Hiking Boot. A style isn't sellable on its own; a customer buys a ProductVariant, one size and colour of it.

**Synonyms:** Style, Product

| Property | Description | Additional metadata |
|---|---|---|
| `ProductID` | Unique style code, P0001-P0052. |  |
| `StyleCode` | Human-readable style code, for example YK-FOO-0001. |  |
| `ProductName` | The style's name, unique across the catalogue. |  |
| `DepartmentName` | Footwear, Apparel or Equipment. |  |
| `CategoryName` | Product category within the department, for example Hiking Boots or Rain Shells. |  |
| `StyleSupplierID` | The manufacturer of this style. |  |
| `SeasonCode` | The season the style was designed for, for example SS26 or AllSeason. |  |
| `StyleListPrice` | List price before any markdown, shared by every variant of the style. | `unit`=`USD` |
| `UnitCost` | What Yuktikara pays the supplier per unit, 38-52% of list price. | `unit`=`USD` |
| `LaunchDate` | The date this style went on sale. |  |
| `IsRfidTagged` | True for Footwear and Apparel, false for Equipment. Only RFID-tagged styles appear in the shop-floor stock data. |  |

### ProductVariant

**Description:** A single sellable item: one style, in one colour and one size. Order lines, returns and stock positions all point to a variant, never directly to a style.

**Synonyms:** SKU, Variant

| Property | Description | Additional metadata |
|---|---|---|
| `VariantID` | Unique SKU code, V00001-. |  |
| `VariantProductID` | The style this variant belongs to. |  |
| `SKU` | Human-readable SKU, also the display name for this entity type. |  |
| `ColorName` | One of two or three colourways offered for the style. |  |
| `SizeCode` | Footwear sizes 7-13 in half sizes, Apparel XS-XXL, Equipment One Size. |  |
| `SizeOrder` | Numeric sort order for SizeCode, because the text values don't sort correctly on their own (XS would sort after L). |  |
| `VariantListPrice` | Inherited from the style; the same for every variant of it. | `unit`=`USD` |

### Customer

**Description:** A synthetic shopper. No real names, emails or addresses exist anywhere in this dataset.

**Synonyms:** Shopper, Buyer

| Property | Description | Additional metadata |
|---|---|---|
| `CustomerID` | Unique customer code, C00001-. |  |
| `CustomerName` | Invented first and last name. | `sensitivity`=`none - synthetic data` |
| `LoyaltyTier` | None, Trailhead, Summit or Alpine, in ascending order. |  |
| `JoinDate` | When the customer joined the loyalty programme; may be before the sales window starts. |  |
| `HomeCity` | Invented home city. | `sensitivity`=`none - synthetic data` |
| `HomeStateCode` | Invented home state. | `sensitivity`=`none - synthetic data` |
| `PreferredStoreID` | The physical store the customer nominated as their preference. They may buy anywhere, including online. |  |

### SalesOrder

**Description:** One customer order, placed in a store or online. Carries five money columns; picking the wrong one is the most common way to misstate sales. Net sales is built from SubTotal, only on Completed or Shipped orders.

**Synonyms:** Order, Sale

| Property | Description | Additional metadata |
|---|---|---|
| `OrderID` | Unique order code, SO000001-. |  |
| `OrderNumber` | Customer-facing order reference, for example YK-2026-000123. |  |
| `OrderStoreID` | The store, or ST900 online, where the order was placed. |  |
| `OrderCustomerID` | The customer who placed the order. |  |
| `Channel` | Store or Online. |  |
| `OrderDate` | The day the order was placed. |  |
| `OrderStatus` | Completed, Shipped, Pending or Cancelled. Only Completed and Shipped orders count as sales. |  |
| `GrossAmount` | Quantity times unit price, before any markdown. | `unit`=`USD` |
| `OrderDiscountAmount` | Sum of the line-level markdowns on this order. | `unit`=`USD` |
| `SubTotal` | GrossAmount minus the order's discount. This is the sales-recognised amount net sales is built from. | `unit`=`USD` |
| `TaxAmount` | Sales tax, 8.25% of SubTotal. | `unit`=`USD` |
| `OrderTotal` | SubTotal plus TaxAmount, what the customer actually paid. Includes tax, so it is not a sales figure. | `unit`=`USD` |
| `PaymentMethod` | How the order was paid for. |  |

### SalesOrderLine

**Description:** One variant on one order. An order with three items has three lines.

**Synonyms:** Order line, Line item

| Property | Description | Additional metadata |
|---|---|---|
| `OrderLineID` | Unique line code, <OrderID>-<line number>, for example SO000001-1. |  |
| `LineOrderID` | The order this line belongs to. |  |
| `OrderLineNumber` | Position of this line within its order, restarting at 1 for each order. |  |
| `LineVariantID` | The variant sold on this line. |  |
| `LineProductID` | The style the variant belongs to, denormalised so product questions need one hop fewer. |  |
| `Quantity` | Units sold on this line, 1-3. |  |
| `UnitPrice` | Price per unit before markdown. |  |
| `LineDiscountAmount` | Markdown applied to this line. | `unit`=`USD` |
| `LineTotal` | Quantity times UnitPrice minus the line's discount. | `unit`=`USD` |

### SalesReturn

**Description:** A returned order line. Returns only exist against orders that were Completed or Shipped. Only Accepted returns, on their ReturnDate, reduce net sales.

**Synonyms:** Return, Refund

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
| `ReturnAmount` | The share of the line's total being refunded. | `unit`=`USD` |
| `ReturnStatus` | Accepted, Pending or Rejected. Only Accepted reduces net sales. |  |
| `ReturnReasonID` | Why the customer returned it. |  |
| `RestockFlag` | True if the returned item can go back on sale; false when it's damaged or otherwise can't be restocked. |  |

### ReturnReason

**Description:** One of eight reasons a customer can give for a return, grouped into five categories.

**Synonyms:** Reason

| Property | Description | Additional metadata |
|---|---|---|
| `ReasonID` | Unique reason code, RR1-RR8. |  |
| `ReturnReasonName` | The reason text shown to the customer, for example Too small or Damaged or faulty. |  |
| `ReturnCategory` | Groups the eight reasons into Fit, Description, Quality, Logistics or Customer. |  |

### StoreInventory

**Description:** What the RFID stock count found on the shop floor and in the stockroom on the last day of the window, for every store and variant combination the store carries. A snapshot; InventoryBalance holds the months of movement behind it.

**Synonyms:** Shelf stock, Floor stock, Stock snapshot

**Additional metadata:** `grain` = `one store + one variant, current snapshot`

| Property | Description | Additional metadata |
|---|---|---|
| `InventoryID` | Unique position code, <StoreID>-<VariantID>. |  |
| `InventoryStoreID` | Physical stores only; the online channel's stock isn't counted here. |  |
| `InventoryVariantID` | The variant being counted. |  |
| `InventoryProductID` | The style, denormalised. |  |
| `SnapshotDate` | The day this count was taken, the last day of the data window. |  |
| `FloorQty` | Units physically on the shop floor. |  |
| `BackroomQty` | Units in the stockroom, not yet on the floor. |  |
| `OnHandQty` | FloorQty plus BackroomQty. |  |
| `FloorMinQty` | The shelf minimum for this variant at this store, set from how fast it sells there. Below this, the floor should be refilled from the backroom, the trigger the operations agent watches for. |  |
| `ReorderPoint` | Below this level, the store places a new purchase order with the supplier. |  |

### InventoryBalance

**Description:** The monthly stock ledger for one store and variant. It balances exactly and closes on the count in StoreInventory: opening plus received minus sold plus returned plus adjusted equals closing.

**Synonyms:** Stock ledger, Stock movement

**Additional metadata:** `grain` = `one store + one variant + one month`

| Property | Description | Additional metadata |
|---|---|---|
| `BalanceID` | Unique code, <StoreID>-<VariantID>-<YYYYMM>. |  |
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

### PurchaseOrder

**Description:** One order a store placed with a supplier. Stores reorder from each supplier roughly every two weeks. An order still in transit at the end of the window has no DeliveredDate.

**Synonyms:** Purchase order, PO

| Property | Description | Additional metadata |
|---|---|---|
| `PurchaseOrderID` | Unique order code, PO000001-. |  |
| `POSupplierID` | The supplier this order was placed with. |  |
| `POStoreID` | The store the goods are being delivered to. |  |
| `PurchaseOrderDate` | The day the order was placed. |  |
| `ExpectedDeliveryDate` | The order date plus the supplier's quoted lead time. |  |
| `DeliveredDate` | The day the order actually arrived. Empty while the order is still open. Compare against ExpectedDeliveryDate to measure a supplier's on-time performance. |  |
| `POStatus` | Received, Partially received or Open. |  |
| `POTotalCost` | What Yuktikara is paying for everything ordered on this purchase order. | `unit`=`USD` |

### PurchaseOrderLine

**Description:** One variant on a purchase order. A short delivery shows QuantityReceived below QuantityOrdered.

**Synonyms:** PO line

| Property | Description | Additional metadata |
|---|---|---|
| `PurchaseOrderLineID` | Unique line code, <PurchaseOrderID>-<line number>. |  |
| `POLineOrderID` | The purchase order this line belongs to. |  |
| `POLineVariantID` | The variant being ordered. |  |
| `POLineProductID` | The style, denormalised. |  |
| `QuantityOrdered` | Units ordered on this line. |  |
| `QuantityReceived` | Units that actually arrived; zero while the order is still open. |  |
| `POUnitCost` | Cost per unit for this delivery. Some suppliers' unit costs rise partway through the current year. | `unit`=`USD` |
| `POLineCost` | QuantityOrdered times the unit cost. | `unit`=`USD` |

### Promotion

**Description:** A named markdown campaign: a clearance after the holidays or at the end of summer, or a smaller seasonal event in between.

**Synonyms:** Campaign, Sale event

| Property | Description | Additional metadata |
|---|---|---|
| `PromotionID` | Unique campaign code, for example PR2026-1. |  |
| `PromotionName` | The campaign's display name, for example Summer Clearance 2026. |  |
| `PromotionType` | Clearance or Seasonal event. |  |
| `PromotionStartDate` | First day of the campaign. |  |
| `PromotionEndDate` | Last day of the campaign; may fall after the data window for a campaign still running. |  |
| `DiscountDepth` | How deep the campaign's discounts go, for example 15-40% off. |  |

### SalesTarget

**Description:** One store's net sales target for one month. Targets follow the store's normal trading pattern; the stores opened in 2023 and the online channel were set more ambitious growth targets.

**Synonyms:** Target, Plan, Quota

| Property | Description | Additional metadata |
|---|---|---|
| `TargetID` | Unique code, <StoreID>-<YYYYMM>. |  |
| `TargetStoreID` | The store this target belongs to. |  |
| `TargetMonth` | First day of the month the target covers. |  |
| `TargetNetSales` | The store's net sales target for the month, rounded to the nearest thousand. | `unit`=`USD` |
<!-- /generated:entity-metadata -->

### Relationships

<!-- generated:relationship-metadata -->
| Relationship type | Description |
|---|---|
| `orderAtStore` | Which store, or the online channel, an order was placed at. |
| `orderByCustomer` | Which customer placed an order. |
| `lineInOrder` | Which order an order line belongs to. |
| `lineForVariant` | Which variant an order line is for. |
| `lineOfStyle` | Which style an order line is for, in one hop instead of going through the variant. |
| `variantOfStyle` | Which style a variant belongs to. |
| `styleFromSupplier` | Which supplier manufactures a style. |
| `returnOfLine` | Which order line a return applies to. |
| `returnOfStyle` | Which style a return applies to, in one hop instead of going through the order line and variant. |
| `returnHasReason` | Why a return was made. |
| `returnTakenAtStore` | Which store physically took a return back. Separate from orderAtStore, because a customer can return to a different store than the one that sold it. |
| `stockAtStore` | Which store a shelf-stock position belongs to. |
| `stockOfVariant` | Which variant a shelf-stock position is counting. |
| `balanceAtStore` | Which store a month of stock movement belongs to. |
| `balanceOfVariant` | Which variant a month of stock movement is for. |
| `poFromSupplier` | Which supplier a purchase order was placed with. |
| `poForStore` | Which store a purchase order is being delivered to. |
| `poLineOnOrder` | Which purchase order a line belongs to. |
| `poLineForVariant` | Which variant a purchase order line is for. |
| `poLineOfStyle` | Which style a purchase order line is for, in one hop instead of going through the variant. |
| `lineOnPromotion` | Which campaign a discounted order line was sold under. |
| `targetForStore` | Which store a monthly sales target belongs to. |
<!-- /generated:relationship-metadata -->

## Sources

- [Create entity types](https://learn.microsoft.com/en-us/fabric/iq/ontology/how-to-create-entity-types)
- [Bind data](https://learn.microsoft.com/en-us/fabric/iq/ontology/how-to-bind-data) (naming, supported types, limitations)
- [Add relationship types](https://learn.microsoft.com/en-us/fabric/iq/ontology/how-to-create-relationship-types)
- [GQL reserved words](https://learn.microsoft.com/en-us/fabric/graph/gql-reference-reserved-terms)
- [Refresh the graph model](https://learn.microsoft.com/en-us/fabric/iq/ontology/how-to-view-entity-type-details#refresh-the-graph-model)
- [Add semantic enrichment](https://learn.microsoft.com/en-us/fabric/iq/ontology/how-to-add-semantic-enrichment) (descriptions, synonyms, additional metadata; checked 2026-09-23)
