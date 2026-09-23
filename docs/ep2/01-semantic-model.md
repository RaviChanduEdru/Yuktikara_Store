# The Yuktikara Sales semantic model

A semantic model with the business's measures, built on the lakehouse from Episode 1. The data agent uses
it for every number (net sales, units sold, returns, return rate), and the ontology for how things connect
and why.

## Why the agent needs it

Episode 1's ontology answers *why* questions well. Asked "why do customers return the Cascade Ridge Hiking
Boot?", the ontology agent walked returns → reasons and matched the data exactly. Asked for a **return
rate**, it wrote a plausible graph query every time, and got a different wrong answer every time:

| Setup | Answer | What went wrong |
|---|---|---|
| Ontology, no instructions | Chinook Trekking Poles, 96.4% | Counted units sold only on lines that were returned |
| Ontology + definitions | 100% (1 of 1) | Grouped by each single return |
| Ontology + "compute the totals separately" | Chinook Trekking Poles, 95.44% | Joined every order line to every return of the same product |
| **Ontology + this model, routed by instructions** | **Cascade Ridge Hiking Boot, 19.20%** | Correct |

A rate needs two independent totals divided at the end. A measure computes that once, correctly, and the
agent only has to pick it.

## Before you start

| Check | How |
|---|---|
| Episode 1 is complete | The lakehouse has 17 tables in six schemas; the ontology's graph is refreshed |
| The workspace is on a paid F2 or higher | **Workspace settings** → workspace type. The model itself runs on a trial; the data agent in step 2 doesn't |

## Step 1: create the model

Open `yuktikara_lh`'s **SQL analytics endpoint** → **New semantic model**.

- **Name**: `Yuktikara Sales`
- **Location**: the `dashboards` folder, assigned to the **Sales model** task
- **Tables**:

| Table | What it's for |
|---|---|
| `sales.sales_order` | order status, order date, store |
| `sales.sales_order_line` | units sold and the value of each line |
| `sales.sales_return` | returned units, return status, return date, refund amount |
| `product.product` | product names |
| `product.supplier` | who makes each product |
| `store.store` | store names and regions |
| `shared.dim_date` | one calendar for both sales and returns |

The model opens in Direct Lake mode: it reads the lakehouse tables in place, with nothing copied.

## Step 2: relationships

In the model view, drag each column onto its match. All are many-to-one, filtering in a single direction.

| From (many) | To (one) |
|---|---|
| `sales_order_line[OrderID]` | `sales_order[OrderID]` |
| `sales_order_line[ProductID]` | `product[ProductID]` |
| `sales_return[ProductID]` | `product[ProductID]` |
| `product[SupplierID]` | `supplier[SupplierID]` |
| `sales_order[StoreID]` | `store[StoreID]` |
| `sales_order[OrderDate]` | `dim_date[Date]` |
| `sales_return[ReturnDate]` | `dim_date[Date]` |

`sales_order_line` has no date of its own: a date filter reaches it through its order (dim_date → order →
line). Returns are dated by their own `ReturnDate`, so a March sale returned in April reduces April.

## Step 3: measures

Select the home table, then **New measure**. The home table only decides where the measure is listed; it
doesn't change the result.

| Measure | Home table |
|---|---|
| `Units Sold` | `sales_order_line` |
| `Accepted Returned Units` | `sales_return` |
| `Return Rate` | `sales_order_line` |
| `Net Sales` | `sales_order` |

```dax
Units Sold =
CALCULATE ( SUM ( sales_order_line[Quantity] ),
    KEEPFILTERS ( sales_order[OrderStatus] IN { "Completed", "Shipped" } ) )
```

```dax
Accepted Returned Units =
CALCULATE ( SUM ( sales_return[QuantityReturned] ),
    KEEPFILTERS ( sales_return[ReturnStatus] = "Accepted" ) )
```

```dax
Return Rate = DIVIDE ( [Accepted Returned Units], [Units Sold] )
```

```dax
Net Sales =
VAR SoldSubtotal =
    CALCULATE ( SUM ( sales_order_line[LineTotal] ),
        KEEPFILTERS ( sales_order[OrderStatus] IN { "Completed", "Shipped" } ) )
VAR AcceptedReturns =
    CALCULATE ( SUM ( sales_return[ReturnAmount] ),
        KEEPFILTERS ( sales_return[ReturnStatus] = "Accepted" ) )
RETURN SoldSubtotal - AcceptedReturns
```

**Why Net Sales sums the lines, not the orders.** The lines' `LineTotal` adds up to each order's `SubTotal`
exactly, so the grand total is the same either way. But a product filter reaches the lines, never the
orders (it flows product → line, not line → order). Summing `sales_order[SubTotal]` gives almost the
whole company's sales on every product row.

## Step 4: check it before you trust it

Open **DAX query view**, paste each query and **Run**. The figures are for the committed snapshot. After
regenerating the data, compare against the `expected_answers.json` you uploaded with it.

```dax
EVALUATE
TOPN ( 3,
    SUMMARIZECOLUMNS ( product[ProductName], "Return Rate", [Return Rate] ),
    [Return Rate], DESC )
```

| ProductName | Return Rate |
|---|---:|
| Cascade Ridge Hiking Boot | 0.1920 |
| Chinook Approach Shoe | 0.1281 |
| Kestrel Insulated Boot | 0.1252 |

```dax
EVALUATE
SUMMARIZECOLUMNS ( dim_date[YearQuarter], "Net Sales", [Net Sales] )
```

The `2026-Q2` row reads **2,047,800.63**, the same as the SQL check in Episode 1.

A table visual by product should total **73,851** units sold, **5,999** accepted returned units, a return
rate of **0.08** and net sales of **11,060,075.41**. Cascade Ridge Hiking Boot's row: 1,547 sold, 297
returned, 0.19, net sales **322,288.01**.

If Return Rate is blank or the same for every product, check `sales_order_line[ProductID]` →
`product[ProductID]`. If Net Sales ignores the quarter, check the two relationships to `dim_date`.

## Step 5: promote it

**Settings** → **Endorsement** → **Promoted**, once every check in step 4 matches. Promotion marks it as the
trusted figure, which is the job it does for the agent.

## Not covered yet

**Don't slice Net Sales by store or region yet.** A store filter reaches the sales (store → order → line)
but not the returns, so every store's row subtracts the whole company's accepted returns. By product,
supplier and date it's correct. Fixing it needs each return linked to the store that made the original
sale, through its order, which is a later step.

## Next

[Add the model to the data agent and route questions to it](02-agent-instructions.md).
