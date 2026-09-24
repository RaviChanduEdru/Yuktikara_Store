# Yuktikara Store

[![Data checks](https://github.com/RaviChanduEdru/Yuktikara_Store/actions/workflows/data-checks.yml/badge.svg)](https://github.com/RaviChanduEdru/Yuktikara_Store/actions/workflows/data-checks.yml)
[![Licence: MIT](https://img.shields.io/badge/licence-MIT-informational)](LICENSE)

The data and build guides for **Yuktikara Store: Microsoft Fabric, End to End**, a series that builds a
retailer's whole data platform in **Microsoft Fabric**: lakehouse, ontology, data agents and Real-Time
Intelligence, every piece **by hand in the portal**.

Yuktikara Store is a fictional apparel, footwear and outdoor gear retailer: 18 stores across the Pacific
Northwest, Northern Rockies, Colorado Front Range and Great Basin, plus an online channel. The data covers
what such a business actually runs on — selling and returns, products and suppliers, buying and deliveries,
stock month by month, promotions and each store's plan — so the questions you can ask of it aren't limited
to one scenario.

Every row is generated. No real customer, employee, supplier or company is represented.

**New here?** Read **[About Yuktikara Store](docs/company.md)** first: what the company sells, how a sale and
a return work, what it measures, and which table records each part of the business.

## What's in here

| | |
|---|---|
| [`data/`](data) | 17 CSV tables, the answer key and a SHA-256 manifest |
| [`scripts/`](scripts) | The generator, the answer key (oracle) and the ontology design check. Standard library only |
| [`fabric/`](fabric/load_yuktikara_data.ipynb) | One notebook, which loads the CSVs into Fabric as typed tables |
| [`docs/`](docs) | The company, the data model, the architecture, the workspace setup and the ontology, entity by entity |

## Load it into Fabric

Python 3.11 or later; nothing to install. For your first build, skip straight to step 1 and upload the
committed `data/` folder as it is — the numbers throughout this README and the guides describe that exact
snapshot. Come back to this command only when you're ready to record, so the dates are current:

```bash
python scripts/generate_yuktikara.py --end yesterday   # dates that end yesterday
python scripts/oracle_yuktikara.py                     # recompute the answer key
```

1. Set up the workspace and its folders: [docs/ep1/01-workspace-setup.md](docs/ep1/01-workspace-setup.md),
   whose *Before you start* section covers your capacity's region and the Capacity Metrics app.
2. Create the lakehouse `yuktikara_lh` with **Lakehouse schemas** checked, and leave OneLake security off.
3. Upload `data/` to `Files/yuktikara/data/`: the 17 CSVs, `manifest.json` and `expected_answers.json`. (Just
   the data and the notebook, without cloning: the [ep1-data release](https://github.com/RaviChanduEdru/Yuktikara_Store/releases/tag/ep1-data).) Use
   the committed snapshot as it is for your first build, so every number you see in Fabric matches this
   README and the guides; regenerate only once you're ready to record (see below).
4. Import [`fabric/load_yuktikara_data.ipynb`](fabric/load_yuktikara_data.ipynb), attach the lakehouse as its
   default, and **Run all**. It writes every table with explicit column types, then verifies row counts,
   types and that no table has column mapping. Fabric runs no other code in this build.
5. Build the ontology by hand: [docs/ep1/03-ontology-bindings.md](docs/ep1/03-ontology-bindings.md).

Build the task flow too, alongside these steps rather than after them: [docs/architecture.md#task-flow](docs/architecture.md#task-flow).

Regenerate before you build, because a fixed snapshot goes stale: "last quarter" drifts away from the data as
the calendar moves. The generator rebuilds the window rather than shifting old dates forward, which keeps the
holiday peak in December, the clearance markdowns in January and July, and weekend trade at weekends. The
planted findings hold for any window (tested from October 2026 to November 2027).

The numbers move when you regenerate, so mark agent answers against the `expected_answers.json` you uploaded,
not the figures below. Never load the answer key into a table: an agent pointed at the lakehouse could find it.

## The dataset

The committed snapshot covers **2025-01-01 to 2026-08-31**: 33,757 orders, 69,198 order lines, 6,749 returns,
6,108 purchase orders and 20 months of stock history. Every figure in this README describes that snapshot.

| File | Rows | What it holds |
|---|---:|---|
| `Store.csv` | 19 | 18 stores plus the online channel, with coordinates for map visuals |
| `Supplier.csv` | 7 | Suppliers, lead times and a quality rating |
| `Product.csv` | 52 | Styles, with department, category, supplier and RFID flag |
| `ProductVariant.csv` | 744 | Sellable SKUs: style x colour x size |
| `Customer.csv` | 6,200 | Synthetic customers and loyalty tiers |
| `DimDate.csv` | 608 | One row per day, with quarter and month keys |
| `SalesOrder.csv` | 33,757 | Order header, status and money columns |
| `SalesOrderLine.csv` | 69,198 | Line-level quantity, price and discount |
| `SalesReturn.csv` | 6,749 | Returns, with reason, status and the store that absorbed them |
| `ReturnReason.csv` | 8 | Reason lookup, grouped into categories |
| `StoreInventory.csv` | 11,773 | Floor and backroom stock counted on the last day, with the shelf minimum per variant |
| `InventoryBalance.csv` | 235,460 | The stock ledger behind that count: one store, variant and month, and it balances |
| `PurchaseOrder.csv` | 6,108 | What each store ordered from each supplier, when it was due and when it arrived |
| `PurchaseOrderLine.csv` | 81,170 | Units ordered and units received, per variant |
| `Promotion.csv` | 8 | Clearances and seasonal events |
| `OrderLinePromotion.csv` | 16,501 | The campaign each discounted sale line was sold under |
| `SalesTarget.csv` | 456 | A monthly net sales target per store |

In the lakehouse they sit in six schemas, one per business area:

| Schema | Tables |
|---|---|
| `sales` | `sales_order`, `sales_order_line`, `sales_return`, `return_reason`, `promotion`, `order_line_promotion`, `sales_target` |
| `product` | `product`, `product_variant`, `supplier` |
| `store` | `store`, `store_inventory`, `inventory_balance` |
| `supply` | `purchase_order`, `purchase_order_line` |
| `customer` | `customer` |
| `shared` | `dim_date` |

Column by column: [docs/ep1/02-data-model.md](docs/ep1/02-data-model.md).

## Definitions, the thing a foundation writes down

> **Net sales** is the `SubTotal` of orders whose `OrderStatus` is `Completed` or `Shipped`, minus the
> `ReturnAmount` of returns whose `ReturnStatus` is `Accepted`, counted on the `ReturnDate`.
> Cancelled and Pending orders are not sales. Tax is not sales.

Ask "what were our sales?" and four defensible-looking numbers sit in the data. Only one is right:

| Figure | Value | Why it's wrong |
|---|---:|---|
| `GrossAmount`, every status | 13,876,486.40 | Counts cancelled and pending orders, ignores markdowns and returns |
| `OrderTotal`, sales statuses | 13,022,622.19 | Includes sales tax |
| `SubTotal`, sales statuses | 12,030,127.17 | Ignores returns |
| **Net sales** | **11,060,075.41** | — |

The gap between the first row and the last is **20.3%**. An agent that can't see the definition usually lands
on one of the first three, and won't tell you which it picked.

Sales is only the most familiar example. A return rate needs a numerator and denominator that agree, "on
time" needs to know which date you judge a delivery against, and availability needs a definition of an empty
shelf. [docs/company.md](docs/company.md) writes all of them down once.

## What is planted in the data

Three findings are seeded, each with a cause that is recoverable from the data rather than asserted:

**Cascade Ridge Hiking Boot returns at 19.20%**, against a 12.29% footwear average and a 12.81% runner-up.
The boot runs small, so 67% of its accepted returns carry the reason *Too small*, and they concentrate in
sizes 7.5 to 9.5, which return at 28.7% together against 10.1% for sizes 10 and above. Finding the product
needs one hop; explaining it needs three.

**Halden Footwear Group, who make that boot, are the weakest supplier.** They deliver on time 56.0% of the
time against Granite Peak's 95.7%, arrive 14.2 days late when late, ship 85.5% of the units ordered, and
their shelves run out more often than anyone else's.

**Yuktikara Bend Outlet absorbs 29,172.44 of online returns**, roughly double any other store. Returns are
recorded against the store that took them back, not the one that made the sale.

Markdowns are real, concentrated in the January-February and July-August clearance windows, so discount is a
live part of the net sales calculation rather than a column of zeroes. The stores that opened in 2023 sit at
76-80% of plan while the flagships pass 108%.

## Ground truth, and how the data is checked

`data/expected_answers.json` holds the verified answers: totals, net sales by year, quarter and month, return
rates, the size and reason breakdown behind the planted signal, supplier delivery performance, stock
availability, promotion results and plan attainment per store.

It's produced by `scripts/oracle_yuktikara.py`, which reads **only the generated CSVs**, the same files that
get uploaded to Fabric. Nothing is copied out of the generator's internals, so every number in it is one an
agent could in principle derive.

The oracle also asserts that the data hangs together: the stock ledger balances every month, each month opens
where the last closed, the final month closes on the counted snapshot, its receipts equal the delivered
purchase order lines, and its sales equal the order lines. [A GitHub Actions
workflow](.github/workflows/data-checks.yml) runs all of that on every push, along with a byte-for-byte
comparison of the committed data against a fresh run, and the ontology design check.

Generation is deterministic: the same seed and end date produce the same bytes. `data/manifest.json` carries a
SHA-256 for every file, so you can confirm you're working from the dataset these figures describe.

## The series

**Yuktikara Store: Microsoft Fabric, End to End.** Each episode adds to the same workspace; nothing built
earlier is thrown away. Episode 1's step-by-step article:
[Build a retail ontology in Microsoft Fabric, step by step](https://ravichanduedru.me/articles/fabric-iq/build-yuktikara-retail-foundation-fabric-iq).

| Episode | What it builds | Status |
|---|---|---|
| 1 | Workspace, lakehouse, ontology and graph | Data and guides ready |
| 2 | Two data agents, one on the tables and one on the ontology, put to six scenarios | Planned |
| 3 | RFID floor readings streamed through an eventstream into an eventhouse | Planned |
| 4 | An operations agent watching for shelves below their minimum | Planned |
| 5 | A store app for replenishment tasks | Planned |
| 6 | One assistant over Copilot Studio, Microsoft 365 and MCP | Planned |

The build order and what each piece reads from: [docs/architecture.md](docs/architecture.md). The log used to
record agent answers: [docs/rehearsal-template.csv](docs/rehearsal-template.csv).

## Licence

MIT. See [LICENSE](LICENSE).

All data in this repository is synthetic. Store locations use real city coordinates so that map visuals behave
realistically; everything else — the company, its stores, products, suppliers and customers — is invented.
