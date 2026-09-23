# The Yuktikara data agent: sources and instructions

One data agent with two sources: the **Yuktikara Sales** semantic model for every number, and the
**Yuktikara_Ontology** for how things connect and why. The instructions tell it which to use when. Without
them it computes rates in the graph and gets them wrong (see
[01-semantic-model.md](01-semantic-model.md#why-the-agent-needs-it)).

## Before you start

| Check | How |
|---|---|
| The workspace is on a paid F2 or higher | Data agents don't run on a Fabric trial capacity |
| `Yuktikara Sales` passes every check in [step 4](01-semantic-model.md#step-4-check-it-before-you-trust-it) | DAX query view |
| The ontology's graph is refreshed | Graph model → **…** → **Refresh now** |

## Step 1: add both sources

In the data agent: **Add data** → the `Yuktikara Sales` semantic model, then **Add data** → the
`Yuktikara_Ontology` ontology.

In the **Explorer**, expand **Yuktikara Sales** and make sure these tables are selected: `sales_order`,
`sales_order_line`, `sales_return`, `product`, `supplier`, `store`, `dim_date`. The agent only sees the
tables you select.

Microsoft doesn't support example questions on a semantic model source, so the measure names have to speak
for themselves. `Net Sales`, `Units Sold`, `Accepted Returned Units` and `Return Rate` do.

## Step 2: the instructions

**Agent instructions** → paste this → save.

```text
You answer questions about Yuktikara Store, a fictional outdoor retailer. You have two data sources.

1. Yuktikara Sales (semantic model). Use it for every number: net sales, units sold, returned units,
   return rate, by product, supplier or period. Always use its measures and never recompute them:
   [Net Sales], [Units Sold], [Accepted Returned Units], [Return Rate].

2. Yuktikara_Ontology. Use it for how things connect and why: why customers return a product
   (return reasons), which store took a return back, what a purchase order contains, stock on the shelf.

If a question needs both, for example "which product has the highest return rate, and why do customers
return it", get the number from Yuktikara Sales first, then look up the reasons in the ontology.

Definitions (already built into the measures):
- Net sales: sold value of Completed and Shipped orders, minus Accepted returns, counted on the return date.
  Tax is not sales.
- Return rate: Accepted returned units / units sold on Completed and Shipped orders.
- "Last quarter" means the last complete calendar quarter before the latest order date.

In every answer, say which measure and which period you used.
Always show the actual values (the number and the units behind it), not just the name.
```

The first paragraph does the real work: it sends every number to the measures. Instructions written as
recipes for the graph ("sum this property where that status…") made the agent keep computing in the graph,
and it kept getting rates wrong.

## Step 3: test it

**Clear chat** before each question, so earlier answers don't steer the next one. Open **"… steps
completed"** under each answer to see which source it used: a **DAX** query means the semantic model, a
**GQL** query means the ontology.

| Ask | Expected | Source it should use |
|---|---|---|
| Which product has the highest return rate, and who makes it? | Cascade Ridge Hiking Boot, 19.20% (297 of 1,547 units), Halden Footwear Group | Semantic model, then the supplier from either |
| What were our sales last quarter? | 2,047,800.63 net sales, 2026-Q2 | Semantic model |
| Why do customers return the Cascade Ridge Hiking Boot? | Mostly **Too small** (234 of its 355 returned units; 220 of its 337 returns) | Ontology |

Figures are for the committed snapshot. After regenerating the data, mark answers against the
`expected_answers.json` you uploaded with it, and never give that file to the agent.

If an answer is wrong, read its query before changing the instructions. Every wrong answer so far came from
the query's shape (which rows it joined, what it grouped by), not from a misunderstood definition, and more
wording didn't fix those.
