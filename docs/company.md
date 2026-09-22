# About Yuktikara Store

Yuktikara Store is a **fictional** outdoor retailer. It sells footwear, clothing and camping equipment for
people who hike, climb and camp, through 18 shops across the western United States and an online store.
Everything about it — the company, its shops, products, suppliers and customers — is invented, and every row
of its data is generated.

This page describes the business the way a new analyst would want it explained on their first day: what
Yuktikara sells, where and to whom, how a sale and a return work, what the company worries about, and which
table records each part. Read it before modelling anything; an ontology is only as good as its understanding
of the business.

Figures marked *snapshot* come from the committed dataset (2025-01-01 to 2026-08-31). A run of the refresh
notebook moves the calendar window, but the business keeps the same shape.

## At a glance

| | |
|---|---|
| What it sells | Outdoor footwear, apparel and equipment: 52 styles, 744 sellable size-and-colour variants |
| Where | 18 physical stores in four western US regions, plus Yuktikara Online |
| Store formats | 3 flagships, 13 standard stores, 2 outlets |
| Customers | 6,200; 62% belong to the three-tier loyalty programme |
| Suppliers | 7 manufacturers in six countries |
| Stock tracking | RFID tags on every footwear and apparel item, counted on the shop floor and in the stockroom |
| Buying | Every store reorders from each supplier every two weeks; suppliers take 16 to 55 days to deliver |
| Scale (*snapshot*) | 33,757 orders, 69,198 order lines, 6,749 returns; net sales 11,060,075.41 |
| Also in the data (*snapshot*) | 6,108 purchase orders, 11,773 stock positions with 20 months of stock history, 8 promotions, monthly targets per store |

## How it grew

Yuktikara started as an online shop in **April 2017** and opened its first physical store, **Portland Pearl**,
in October 2018. Flagships followed in Seattle (2019) and Denver (2019). The chain then spread into smaller
mountain towns, about one store a quarter, until **Fort Collins** opened in September 2023.

| Region | Stores (year opened) |
|---|---|
| **Pacific Northwest** | Portland Pearl, flagship (2018) · Seattle Flagship (2019) · Tacoma (2020) · Spokane (2021) · Bend Outlet (2021) · Eugene (2022) |
| **Colorado Front Range** | Denver LoDo, flagship (2019) · Boulder (2020) · Fort Collins (2023) |
| **Northern Rockies** | Boise (2020) · Bozeman (2021) · Missoula (2022) · Coeur d'Alene (2023) |
| **Great Basin** | Salt Lake City (2020) · Reno (2021) · Sacramento (2022) · Park City Outlet (2022) · Flagstaff (2023) |
| **Online** | Yuktikara Online (2017), store `ST900` |

Flagships are 22,100-24,500 square feet and do the most trade of any physical store. Standard stores are
8,700-13,100 square feet, and the two outlets, in Bend and Park City, are 14,300 and 13,600. The online store
is recorded as a store of its own, so every order has one, however it was placed. Online is also the
biggest single "store" by sales.

## What it sells

Three departments, sixteen categories. A **style** is a product design (the *Cascade Ridge Hiking Boot*); a
**variant** is one size in one colour of it (the Cascade Ridge in Moss, size 9). Customers buy variants,
stores stock variants, and RFID counts variants. Styles are how the business plans, prices and reports.

| Department | Categories | List prices | Sizes |
|---|---|---|---|
| **Footwear** · 16 styles, 384 variants | Hiking boots, trail runners, approach shoes, insulated boots | 108.95-271.95 | US 7-13 in half sizes, two colours |
| **Apparel** · 18 styles, 324 variants | Rain shells, insulated jackets, fleece, base layers, hiking trousers, technical tees | 39.95-439.95 | XS-XXL, three colours |
| **Equipment** · 18 styles, 36 variants | Backpacks, tents, sleeping bags, trekking poles, headlamps, camp stoves | 51.95-476.95 | One size, two colours |

Footwear and apparel carry RFID tags; equipment doesn't. Each style has one list price for the whole period.
Prices only ever go down, through markdowns.

## Who it buys from

| Supplier | Country | Lead time | Quality rating |
|---|---|---:|---:|
| Granite Peak Manufacturing | United States | 16 days | 4.7 |
| Northaven Textiles | Portugal | 28 days | 4.8 |
| Selkirk Down Company | Canada | 34 days | 4.5 |
| Juniper Mills | India | 39 days | 4.3 |
| Kestrel Technical Works | Vietnam | 42 days | 4.6 |
| Talus Hardgoods | China | 48 days | 4.1 |
| **Halden Footwear Group** | Vietnam | **55 days** | **3.4** |

Every style comes from exactly one supplier, and each supplier makes seven or eight styles. Halden has the
longest lead time and the weakest quality rating, and it makes the Cascade Ridge Hiking Boot — keep that in
mind when you reach returns.

## Who buys

6,200 customers. Each has a home city and a preferred store, but they shop wherever they like, in person or
online.

| Loyalty tier | Share of customers |
|---|---:|
| None (not a member) | 38% |
| Trailhead (entry tier) | 34% |
| Summit | 21% |
| Alpine (top tier) | 7% |

Payment (*snapshot*): credit card 46%, debit card 21%, the Yuktikara Rewards Card 14%, mobile wallet 14%,
gift card 5%.

## How a sale works

A customer places an **order** at a store or online. An order has one or more **order lines**, one per variant
bought, about two lines per order on average. Every order moves through a status:

| Status | Meaning | Share (*snapshot*) | Counts as a sale? |
|---|---|---:|---|
| Completed | Paid for and handed over or delivered | 83.7% | Yes |
| Shipped | Paid for and on its way | 7.6% | Yes |
| Pending | Placed but not yet fulfilled | 3.8% | No |
| Cancelled | Never fulfilled | 4.9% | No |

Pending orders cluster in the last week before the data ends, because those orders haven't shipped yet.

The money on an order builds up in steps, and each step has its own column:

```
GrossAmount     quantity x list price, before any markdown
- DiscountAmount  markdowns on the lines
= SubTotal        what the goods actually sold for        <- the sales figure
+ TaxAmount       sales tax, 8.25% of SubTotal
= OrderTotal      what the customer paid                  <- not sales: includes tax
```

Stores take most orders (84.7% *snapshot*); online takes 15.3%. A typical fulfilled order is worth about
390.18 before tax.

## Markdowns

Two clearance windows a year: **January-February** (after the holidays) and **July-August** (end of the
summer season). In those months a large share of lines sell at 15-40% off. The rest of the year, a smaller
share carry a 10-20% promotion. Across the *snapshot*, 23.8% of order lines were discounted, and markdowns
took 5.1% off gross sales.

## The seasons

Outdoor retail has two peaks, and so does Yuktikara:

- **Early summer (May-July)**, when hiking and camping start: footwear and equipment sell most.
- **Autumn into the holidays (September-December)**, driven by jackets and fleece: apparel's strongest
  months, with the overall peak in December.

February is the quietest month. Physical stores are busier at weekends; the online store isn't. In the
*snapshot*, 2025 net sales ran from 270,329.92 in February to 745,188.84 in June, with a second peak of
736,604.19 in December.

## Returns

Returns are a large part of the story, as they are in real outdoor and apparel retail.

- **How often:** footwear comes back most (12.29% of units sold, *snapshot*), then apparel (9.01%), then
  equipment (3.18%). Online orders come back far more often than store orders (12.6% of units against 7.3%),
  because the customer couldn't try them on first.
- **When:** usually one to seven weeks after purchase. A return is counted **on the day it's accepted**, so a
  March sale returned in April reduces April.
- **Where:** a store customer usually brings it back to the same store (88% of the time). An online customer
  returns to a physical store of their choice, and a disproportionate share end up at **Yuktikara Bend Outlet**, which takes in about twice the
  online returns of any other store (29,172.44, *snapshot*).
- **Outcome:** each return is **Accepted**, **Pending** or **Rejected**. Only accepted returns give money
  back, so only they reduce sales.
- **Why:** customers choose one of eight reasons, grouped into five categories: *Fit* (too small, too
  large), *Quality* (damaged or faulty), *Description* (not as described), *Logistics* (wrong item shipped,
  arrived too late) and *Customer* (changed mind, found a better price).

**The Cascade Ridge Hiking Boot** is the problem product. It comes back at 19.20% (*snapshot*), far above
any other style, and most of its returns say *Too small*: the boot runs small, so buyers of the common
smaller sizes send it back. It's made by Halden Footwear Group. Finding the boot is easy; explaining it
means connecting returns, reasons, sizes and suppliers — exactly the kind of question an ontology is for.

## Stock on the shop floor

Every footwear and apparel variant a store carries has an RFID count in two places: on the **shop floor**
and in the **stockroom**. Each variant also has two thresholds:

- **Floor minimum:** below this, a customer may not find their size, so staff should refill the floor from
  the stockroom.
- **Reorder point:** three times the floor minimum; below this, the store needs more stock from a supplier.

At the end of the *snapshot*, 1,243 of the 11,773 store-variant positions (10.6%) were below their floor
minimum, and 1,231 shelves were empty with stock still in the stockroom. Watching for exactly that, as it
happens, is the job of the live RFID feed and the operations agent later in the series.

Stock levels follow how fast each size sells in each store: 45,828 units on hand across the chain, a
typical position holding a handful. `InventoryBalance` holds the months behind that count, and it balances:
opening stock, plus deliveries and returns put back on sale, minus what sold, plus or minus stock
corrections, equals closing stock. The last month closes on exactly the counted snapshot.

## Buying from suppliers

Every store reorders from each supplier every two weeks, and only for the sizes that have fallen to their
reorder point. The supplier then takes its lead time to deliver: 16 days from Granite Peak in the United
States, 55 from Halden in Vietnam. `PurchaseOrder` records what was ordered and when it was expected;
`DeliveredDate` records when it actually turned up, and is empty for the 372 orders still in transit at the
end of the *snapshot*.

Suppliers differ, and that is the point:

| Supplier | Promised lead time | Delivered on time | Late by, when late | Of units ordered, delivered |
|---|---:|---:|---:|---:|
| Granite Peak Manufacturing | 16 days | 95.7% | 2.0 days | 98.8% |
| Northaven Textiles | 28 days | 92.3% | 3.5 days | 98.6% |
| Selkirk Down Company | 34 days | 90.7% | 4.2 days | 97.8% |
| Kestrel Technical Works | 42 days | 86.6% | 5.5 days | 98.2% |
| Juniper Mills | 39 days | 81.3% | 6.4 days | 96.9% |
| Talus Hardgoods | 48 days | 76.9% | 8.1 days | 95.8% |
| **Halden Footwear Group** | **55 days** | **56.0%** | **14.2 days** | **85.5%** |

Halden has the longest lead time, the weakest quality rating, the worst record for turning up on time, and
the habit of shipping less than was ordered. They also make the Cascade Ridge Hiking Boot. Their positions
run out of stock more often than anyone else's, and it shows in the stock history rather than in the sales,
because a shelf that is empty makes no sale to lose.

Costs rise too: Halden's prices went up 4% and Talus's 6% at the start of the current year, which shows in
`POUnitCost` against the standing `Product.UnitCost`.

## Promotions

Discounts aren't loose: every discounted sale line belongs to a campaign, through `OrderLinePromotion`.

| Campaign | When | Type |
|---|---|---|
| Winter Clearance | January to February | Clearance, 15-40% off |
| Spring Trail Days | March to June | Seasonal event, 10-20% off selected lines |
| Summer Clearance | July to August | Clearance, 15-40% off |
| Autumn Layers Event | September to October | Seasonal event |
| Holiday Gift Event | November to December | Seasonal event |

The two clearances do the heavy lifting: Summer Clearance 2025 alone moved 4,141 units and gave away
176,625.90 in markdown (*snapshot*).

## Plans and targets

Each store has a net sales target for every month, in `SalesTarget`, set from its trading pattern. The
stores that opened in 2023 and the online store were given growth plans, and they are the ones behind: over
the *snapshot*'s complete months, Coeur d'Alene reached 76% of plan and Fort Collins 78%, while Seattle
Flagship and Portland Pearl passed 108%. Fourteen of the nineteen stores were behind plan.

## How the business measures itself

| Measure | Definition |
|---|---|
| **Net sales** | `SubTotal` of Completed and Shipped orders, minus the `ReturnAmount` of Accepted returns, counted on the return date. Cancelled and Pending orders aren't sales; tax isn't sales |
| **Net sales by store** | The same, attributed to the store that sold the goods, not the store that took the return back |
| **Gross margin** | Net sales minus `Product.UnitCost` × units sold |
| **Return rate** | Accepted returned units ÷ units sold on Completed and Shipped orders, over the same period |
| **Markdown share** | `DiscountAmount` ÷ `GrossAmount` |
| **Floor availability** | Share of store-variant positions at or above their floor minimum |
| **Stockout days** | Days a position ended with nothing, from `InventoryBalance` |
| **On-time delivery** | Purchase orders delivered on or before `ExpectedDeliveryDate` ÷ orders delivered |
| **Fill rate** | `QuantityReceived` ÷ `QuantityOrdered` on delivered orders |
| **Plan attainment** | Net sales by store ÷ `SalesTarget.TargetNetSales`, over the same months |

**Net sales is the number everyone asks for and the one most often answered wrongly.** The data holds at
least four plausible candidates: gross, order total with tax, subtotal before returns, and true net sales.
Only the definition above is right. In the *snapshot* the gap between the first and the last is 20.3%.

## The tables, by part of the business

| Part of the business | Table | One row is |
|---|---|---|
| Where we sell | `Store` | A store, including the online store |
| What we sell | `Product` | A style |
| | `ProductVariant` | A sellable size and colour of a style |
| Who we buy from | `Supplier` | A manufacturer |
| Who buys | `Customer` | A customer |
| Selling | `SalesOrder` | An order, with its status and money |
| | `SalesOrderLine` | One variant on an order |
| Taking things back | `SalesReturn` | A returned order line |
| | `ReturnReason` | One of the eight return reasons |
| Stock on the floor | `StoreInventory` | One variant in one store: floor and stockroom counts |
| | `InventoryBalance` | One variant in one store for one month: opening, movements, closing |
| Buying | `PurchaseOrder` | An order to a supplier for one store |
| | `PurchaseOrderLine` | One variant on that order, ordered and received |
| Promoting | `Promotion` | A campaign |
| | `OrderLinePromotion` | The campaign a discounted sale line was sold under |
| Planning | `SalesTarget` | One store's target for one month |
| The calendar | `DimDate` | One day |

```
Supplier ── makes ──> Product ── comes in ──> ProductVariant
                                                   ^
Customer ── places ──> SalesOrder ── has ──> SalesOrderLine ── is for ──┘
                          │                        ^
                          └── at ──> Store         │
                                       ^           │
SalesReturn ── returns ────────────────┼───────────┘
     ├── taken back at ────────────────┘
     └── because ──> ReturnReason

StoreInventory ── counts a ProductVariant ── in a Store
```

Column by column: [data-model.md](data-model.md). The same business as an ontology, with every entity type,
property and relationship: [ontology-bindings.md](ontology-bindings.md).

## What's simplified

It's a teaching dataset, so some real-world complexity is deliberately left out:

- **One sales tax rate (8.25%) everywhere.** Real US sales tax varies by state and city.
- **Prices never rise.** Each style keeps its list price for the whole period; only markdowns change it.
- **No staff.** Who served the customer, and who refills the shelf, isn't modelled yet.
- **Stock never lost a sale.** The sales came first and the stock history was built to support them, so
  an empty shelf costs availability in the data, never revenue.
- **Customers shop anywhere.** Their preferred store doesn't influence where they buy.
- **Stores never close,** and none opens during the period covered.
- **One inventory snapshot**, taken on the last day. The live RFID feed arrives in a later episode.
