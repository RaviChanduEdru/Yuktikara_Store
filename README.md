# Yuktikara Store

A synthetic retail dataset for learning **Microsoft Fabric** — ontology, data agents and Real-Time
Intelligence — by building every piece **by hand in the portal**. One notebook refreshes the data so its
dates are always current; everything built on top of it is done manually.

Yuktikara Store is a fictional apparel, footwear and outdoor gear chain: 18 stores across the Pacific
Northwest, Northern Rockies, Colorado Front Range and Great Basin, plus an online channel. Every row in
this repository is generated. No real customer, employee, supplier or company is represented.

New here? Start with **[About Yuktikara Store](docs/company.md)**: what the company sells, how a sale and a
return work, what it measures, and which table records each part of the business.

## Why this exists

Most Fabric samples hand you a notebook that provisions everything at once. That is useful for a demo and
useless for learning: the interesting decisions all happen inside the black box. This repository takes the
opposite approach. The data is given — as files, or refreshed by one notebook that does nothing but load
data — and the ontology, data agents and eventhouse are all built manually, one field at a time.

The dataset is designed around a single question that is harder than it looks:

> **What were our sales last quarter?**

## The definition everything hangs on

> **Net sales** is the `SubTotal` of orders whose `OrderStatus` is `Completed` or `Shipped`, minus the
> `ReturnAmount` of returns whose `ReturnStatus` is `Accepted`, counted on the `ReturnDate`.
> Cancelled and Pending orders are not sales. Tax is not sales.

Four defensible-looking numbers sit in the data, and only one is right:

| Figure | Value | Why it is wrong |
|---|---:|---|
| `GrossAmount`, every status | 13,876,486.40 | Counts cancelled and pending orders, ignores markdowns and returns |
| `OrderTotal`, sales statuses | 13,022,622.19 | Includes sales tax |
| `SubTotal`, sales statuses | 12,030,127.17 | Ignores returns |
| **Net sales** | **11,060,075.41** | — |

The gap between the first row and the last is **20.3%**. An agent that cannot see the definition will
usually land on one of the first three, and will not tell you which one it picked.

## The dataset

The committed snapshot covers **2025-01-01 to 2026-08-31**: 33,757 orders, 69,198 order lines and 6,749
returns. Every figure in this README describes that snapshot. To work with current dates instead, see
[Keeping the dates current](#keeping-the-dates-current).

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
| `StoreInventory.csv` | 7,025 | Floor and backroom stock, with the floor minimum per variant |

The business behind the tables: [docs/company.md](docs/company.md). Column-by-column reference:
[docs/data-model.md](docs/data-model.md). How the Fabric pieces fit together, and the order to build them in:
[docs/architecture.md](docs/architecture.md). The ontology, entity by entity:
[docs/ontology-bindings.md](docs/ontology-bindings.md).

Deliberately only eleven tables. Every one of them is a manual upload, so each has to earn its place.

## What is planted in the data

Two findings are seeded, both with a cause that is recoverable from the data rather than asserted:

**Cascade Ridge Hiking Boot returns at 19.20%**, against a 12.29% footwear average and a 12.81% runner-up.
The boot runs small, so 67% of its accepted returns carry the reason *Too small*, and they concentrate in
sizes 7.5 to 9.5, which return at 28.7% together (22-34% per size) against 10.1% for sizes 10 and above.
Finding the product needs one hop; explaining it needs three.

**Yuktikara Bend Outlet absorbs 29,172.44 of online returns**, roughly double any other store. Returns are
recorded against the store that took them back, not the one that made the sale.

Markdowns are real, concentrated in the January-February and July-August clearance windows, so discount is
a live part of the net sales calculation rather than a column of zeroes.

## Ground truth

`data/expected_answers.json` holds the verified answers: totals, net sales by year, quarter and month,
return rates by product and department, the size and reason breakdown behind the planted signal, and
per-store figures.

It is produced by `scripts/oracle_yuktikara.py`, which reads **only the generated CSVs** — the same files
that get uploaded to Fabric. Nothing is copied out of the generator's internals, so every number in it is
one an agent could in principle derive. Use it to mark answers; never paste it into an agent.

## Regenerating the data

Python 3.11 or later. No packages to install — both scripts are standard library only.

```bash
python scripts/generate_yuktikara.py    # writes the CSVs into data/
python scripts/oracle_yuktikara.py      # recomputes data/expected_answers.json
```

Generation is deterministic: the same seed and end date produce the same bytes. `data/manifest.json`
carries a SHA-256 for every file, so you can confirm you are working from the dataset the documented figures
describe.

For a window ending on another day, pass `--end` with a date, `yesterday` or `today`. The window always
runs from 1 January of the previous year to that day, so a complete "last year" always exists:

```bash
python scripts/generate_yuktikara.py --end yesterday --out current
python scripts/oracle_yuktikara.py --data current
```

## Keeping the dates current

A fixed snapshot goes stale: "last month" and "last quarter" drift away from the data as the calendar moves.
[`fabric/refresh_yuktikara_data.ipynb`](fabric/refresh_yuktikara_data.ipynb) fixes that inside Fabric. Each
run regenerates the dataset for a window ending yesterday (or any date you set), writes the 11 lakehouse
tables and verifies them.

It regenerates rather than shifting old dates forward. Shifting by an arbitrary number of days would put
the holiday peak and the clearance markdowns in the wrong months and move weekend trade onto weekdays. A
fresh window keeps the calendar honest. The planted findings don't depend on dates, and they hold for any
window: tested from October 2026 to November 2027, Cascade Ridge stayed first on returns and Bend Outlet
stayed first on online returns.

It also settles column types. Dates are written as `date` and money as `double`, the types ontology binding
needs, and the notebook fails loudly if a table comes out any other way.

To use it:

1. Set up the workspace, its folders and its task flow as in [docs/workspace-setup.md](docs/workspace-setup.md).
2. Create the lakehouse `yuktikara_lh` with **Lakehouse schemas** checked, and leave OneLake security off.
3. Upload `scripts/generate_yuktikara.py` and `scripts/oracle_yuktikara.py` to `Files/yuktikara/scripts/`.
4. Import the notebook into the workspace, attach the lakehouse as its default, and **Run all**.
5. Refresh the ontology's graph model afterwards, if one exists. It doesn't see new rows until you do.

Each run keeps its CSVs, manifest and answer key under `Files/yuktikara/runs/<end date>/`. The numbers
change from run to run, so mark agent answers against **that run's** `expected_answers.json`, not the
figures in this README. Never load the answer key into a table: an agent pointed at the lakehouse could
find it.

The tables are grouped into schemas by business area, the way Microsoft's IQ solution accelerator lays out
its lakehouse:

| Schema | Tables |
|---|---|
| `sales` | `sales_order`, `sales_order_line`, `sales_return`, `return_reason` |
| `product` | `product`, `product_variant`, `supplier` |
| `store` | `store`, `store_inventory` |
| `customer` | `customer` |
| `shared` | `dim_date` |

## Repository layout

```
data/      the committed snapshot, ready to upload to Fabric, plus ground truth and hashes
scripts/   the generator, the oracle, the ontology design checker and the notebook builder
fabric/    the notebook that refreshes the data to current dates
docs/      the company, data model, architecture, workspace setup, ontology bindings and the rehearsal log template
```

## Licence

MIT. See [LICENSE](LICENSE).

All data in this repository is synthetic. Store locations use real city coordinates so that map visuals
behave realistically; everything else — the company, its stores, products, suppliers and customers — is
invented.
