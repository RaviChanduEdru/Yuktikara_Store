# Yuktikara Store

A synthetic retail dataset and build guide for learning **Microsoft Fabric** — ontology, data agents and
Real-Time Intelligence — by building every piece **by hand in the portal**, with no installer notebook and
no deployment script.

Yuktikara Store is a fictional apparel, footwear and outdoor gear chain: 18 stores across the Pacific
Northwest, Northern Rockies, Colorado Front Range and Great Basin, plus an online channel. Every row in
this repository is generated. No real customer, employee, supplier or company is represented.

## Why this exists

Most Fabric samples hand you a notebook that provisions everything at once. That is useful for a demo and
useless for learning: the interesting decisions all happen inside the black box. This repository takes the
opposite approach. The data is given; the lakehouse, semantic model, ontology, data agent and eventhouse
are all built manually, one field at a time.

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

Generated for **2025-01-01 to 2026-08-31**: 33,757 orders, 69,198 order lines and 6,749 returns.

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
| `StoreInventory.csv` | 6,916 | Floor and backroom stock, with the floor minimum per variant |

Column-by-column reference: [docs/data-model.md](docs/data-model.md).

Deliberately only eleven tables. Every one of them is a manual upload, so each has to earn its place.

## What is planted in the data

Two findings are seeded, both with a cause that is recoverable from the data rather than asserted:

**Cascade Ridge Hiking Boot returns at 19.20%**, against a 12.29% footwear average and a 12.81% runner-up.
The boot runs small, so 64% of its returns carry the reason *Too small*, and they concentrate in sizes
7.5 to 9.5 (22-34%) while sizes 10 and above sit at 5-9%. Finding the product needs one hop; explaining it
needs three.

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

Generation is deterministic: the same seed produces the same bytes. `data/manifest.json` carries a SHA-256
for every file, so you can confirm you are working from the dataset the documented figures describe.

## Repository layout

```
data/      the dataset, ready to upload to Fabric, plus ground truth and hashes
scripts/   the generator and the oracle
docs/      data model reference and the build guides
```

## Licence

MIT. See [LICENSE](LICENSE).

All data in this repository is synthetic. Store locations use real city coordinates so that map visuals
behave realistically; everything else — the company, its stores, products, suppliers and customers — is
invented.
