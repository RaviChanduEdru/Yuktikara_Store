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
| Workspace is on a Fabric capacity (F2 or above) | Workspace settings → License info |
| Lakehouse `yuktikara_lh` created with **Lakehouse schemas**, OneLake security **off** | Tables show the schemas `customer`, `product`, `sales`, `shared`, `store` (plus the empty default `dbo`) |
| The 11 tables are loaded | The refresh notebook's *Verify* cell ends in `PASS` |

## Three design decisions to understand first

**Every property name is unique across the whole ontology.** An ontology has one namespace for properties,
and Microsoft's binding page requires names to be unique across all entity types. `StoreID` appears in
three tables, so only the `Store` entity type keeps that name; the order's copy becomes `OrderStoreID` and
the inventory's becomes `InventoryStoreID`. The rule used throughout is: an entity's own key keeps its
column name, and a reference to something else takes its owner's prefix. That gives 20 renames in total,
marked **(rename)** below. The one exception is `ReturnReason`, whose key becomes `ReasonID` so that a
return can keep the natural `ReturnReasonID`.

**`Product` can't be an entity type name.** `PRODUCT` is a GQL reserved word, as are `ORDER` and `RETURN`.
The style-level table becomes **`ProductStyle`**; the sellable size-and-colour item is **`ProductVariant`**.

**Every entity type has a single-column key.** Order lines and inventory rows are naturally identified by
two columns, but relationships match one column per side, so the data carries `OrderLineID`
(`SO000001-1`) and `InventoryID` (`ST001-V00002`).

`dim_date` gets no entity type: dates are properties on the things that happen, and the date table exists
for the semantic model and the lakehouse-only comparison agent.

## Step 1: create the ontology item

Open the workspace folder **`ontology`**, then **+ New item** → search **Ontology (preview)** → **Name**
`Yuktikara_Ontology` → **Create**. Creating it from inside the folder puts it there; see
[workspace-setup.md](workspace-setup.md) for the folder layout and the task it belongs to.

Ontology names take letters, numbers and underscores only; no spaces or dashes. Fabric also creates a
**graph model** child item in the workspace. Leave it alone until step 4.

## Step 2: entity types and their data bindings

Build **all ten entity types and bindings before any relationship**: a relationship needs a key on both
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

Repeat for the other nine, in this order. Instance counts are for the committed snapshot. After a notebook
run, compare against that run's `Files/yuktikara/runs/<end date>/manifest.json` instead.

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

Table `store.store_inventory` · key **`InventoryID`** · display name **`InventoryID`** · 7,025 instances in the committed snapshot

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
<!-- /generated:entities -->

**Checkpoint:** the Explorer lists 10 entity types, each with a key, a display name property and every
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
| 12 | `stockAtStore` | StoreInventory → Store | `store.store_inventory` | `InventoryID` | `StoreID` | 7,025 |
| 13 | `stockOfVariant` | StoreInventory → ProductVariant | `store.store_inventory` | `InventoryID` | `VariantID` | 7,025 |
<!-- /generated:relationships -->

Every name is unique. Microsoft lists duplicate relationship names as a known issue that breaks
natural-language queries. Two are deliberate shortcuts: `lineOfStyle` and `returnOfStyle` reach
`ProductStyle` in one hop instead of going through `ProductVariant`. That keeps the return-rate question to
a single hop per side while the preview's aggregation support is still rough.

`returnTakenAtStore` is what makes "which store takes back the most online returns?" answerable. A return
reaches a store two ways: through its order (`returnOfLine` → `lineInOrder` → `orderAtStore`, the store
that sold it) and directly (the store that took it back).

If a **Matched** dropdown offers no keys, the entity type at that end has no key yet. Go back to step 2.

**Checkpoint:** the canvas shows 13 relationships, each with a mapping table and both matched columns.

## Step 4: refresh and verify the graph

Changing the schema re-ingests bound data automatically. Changing the **rows** doesn't, so refresh after
every notebook run: workspace → the ontology's graph model → **…** → **Schedule** → **Refresh now**. Each
refresh rebuilds the whole graph and uses capacity, so batch your changes and don't set a recurring
schedule on F2.

Then select an entity type → **View entity type details** → **Instances**:

| Check | Expected |
|---|---|
| Each entity type's instance count | Its table's row count in the run's `manifest.json` |
| `ProductStyle` → *Cascade Ridge Hiking Boot* | Linked to supplier *Halden Footwear Group* through `styleFromSupplier` |
| A `SalesReturn` instance | One edge each for `returnOfLine`, `returnOfStyle`, `returnHasReason` and `returnTakenAtStore` |
| **Overview** → graph → **Expand** → **Query builder** → **Run query** | Returns results; switch to **Table** view to read IDs |

Zero instances or missing edges usually mean a missing key, a wrong matched column, or a table that isn't a
managed Delta table. The notebook's *Verify* cell already rules out the last one.

## Not on this page

Descriptions, synonyms and metadata (semantic enrichment) come next, and they are worth adding for people
reading the model. Microsoft states that the data agent doesn't use those fields, so the net sales
definition goes into the **agent instructions**, not into an entity description.

## Sources

- [Create entity types](https://learn.microsoft.com/en-us/fabric/iq/ontology/how-to-create-entity-types)
- [Bind data](https://learn.microsoft.com/en-us/fabric/iq/ontology/how-to-bind-data) (naming, supported types, limitations)
- [Add relationship types](https://learn.microsoft.com/en-us/fabric/iq/ontology/how-to-create-relationship-types)
- [GQL reserved words](https://learn.microsoft.com/en-us/fabric/graph/gql-reference-reserved-terms)
- [Refresh the graph model](https://learn.microsoft.com/en-us/fabric/iq/ontology/how-to-view-entity-type-details#refresh-the-graph-model)
