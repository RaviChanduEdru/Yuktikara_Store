# Setting up the Yuktikara workspace

How the Fabric workspace is organised before anything is built in it: its settings, folders, item names,
lakehouse layout and task flow. Do this once, at the start of Episode 1. Every later episode adds items into
the structure set up here.

## Before you start

Two things to confirm before you create anything, because both are awkward to fix once you've built on
top of them.

**The capacity's region supports Graph.** The ontology's graph model only runs in
[certain regions](https://learn.microsoft.com/en-us/fabric/graph/overview#region-availability) (checked
2026-09-23) — Central India is one of roughly 35, alongside East US, West Europe and UK South. **Admin
portal → Capacity settings →** your capacity, and check its region against that list. Everything for this
series — workspace, lakehouse, ontology and, later, the data agents — has to sit on this one capacity, so
settle this now rather than after Step 4.

**Install the Microsoft Fabric Capacity Metrics app**, so it's recording usage from your first item, not
from whenever you remember to add it. You need to be a capacity admin.
[AppSource → Microsoft Fabric Capacity Metrics](https://go.microsoft.com/fwlink/?linkid=2219875) → **Get it
now** → sign in → **Install**. On first run it asks for your UTC offset (`5.5` for India) and a capacity to
report on.

The tenant settings that let you create an ontology at all — **Ontology item (preview)** and Graph — are
checked separately, right before you need them, in
[ontology-bindings.md](ontology-bindings.md#before-you-start).

## 1. The workspace

**Workspaces → + New workspace**, then set these in **Workspace settings**:

| Setting | Value | Why |
|---|---|---|
| **Name** | `Yuktikara Retail - Demo` | See the naming note below |
| **Description** | The text below | A workspace should say what it is for and who owns it |
| **License mode** | Fabric capacity, on the F2 | Data agents need a paid F-SKU, and a trial capacity expires along with everything in it |
| **Workspace image** | [`docs/assets/workspace-image.png`](assets/workspace-image.png) | Learn: a consistent image helps people spot the workspace in a list |
| **Contacts** | Leave the default (the workspace admins) | Learn: change it only when someone else answers questions |
| **Domain** (optional) | A `Retail` domain, if you're a Fabric admin | Learn: domains group workspaces by business area and make ownership clear |

**Why the name ends in "- Demo".** It marks the environment, which is what tells anyone reading a list of
workspaces, or any tool that sorts them, that this one isn't production. Use a separator rather than
brackets: tooling that classifies workspaces by name typically looks for `dev`, `test`, `demo` or `sandbox`
with a space, hyphen, underscore or full stop on either side, so `[Demo]` in brackets is easily missed, while
`- Demo` is read either way.

**Description** (the field takes up to 4,000 characters; Learn suggests covering purpose, audience, content,
governance, environment and contact):

```text
Yuktikara Store (demo). A Microsoft Fabric build for a fictional outdoor retailer, made for a public video
series. Every item is built by hand in the portal, one episode at a time.

Audience: people following the series, and anyone learning Fabric IQ (ontology, graph and data agents).
Content: a lakehouse of synthetic retail data (orders, returns and store stock), the notebook that refreshes
it, a semantic model and an ontology. Data agents, a live RFID floor feed and a store app follow in later
episodes.
Status: demo environment, not production and not governed. All data is synthetic; there are no real
customers or people in it.
Questions: open an issue at github.com/RaviChanduEdru/Yuktikara_Store
```

## 2. Folders

Folders group items by **type**; the task flow in section 5 groups the same items by **purpose**. Learn
presents folders and task flows as alternatives that can also be combined, and here each answers a different
question: what is this, and what is it for.

| Folder | Holds | Episode |
|---|---|---|
| `lakehouses` | `yuktikara_lh` | 1 |
| `notebooks` | `load_yuktikara_data` | 1 |
| `dashboards` | the `Yuktikara Sales` semantic model; the net sales report later | 1, 2 |
| `ontology` | `Yuktikara_Ontology` and its graph model | 1 |
| `data_agent` | the lakehouse agent and the ontology agent | 2 |
| `realtime` | the RFID eventstream, eventhouse and KQL database, and the operations agent that watches them | 3, 4 |
| `apps` | the store app | 5 |

Create a folder only when its first item arrives: Episode 1 needs the first four. An empty folder shows
viewers a plan as if it were progress, and Git doesn't copy empty folders anyway.

How folders behave (Microsoft Learn):

- **New folder** in the workspace creates one. Names can't contain `~ " # . & * : < > ? / { | }` or start
  or end with a space. They can be up to 255 characters, and folders nest up to 10 levels.
- Open a folder, then **+ New item**: the item is created in that folder. Items created from the Fabric
  home page or the **Create** hub land in the workspace root. Move them with **… → Move to**.
- Admins, members and contributors can create, rename, move and delete folders. Viewers only see them.
  Only empty folders can be deleted.
- Two Learn pages disagree about Git. The folders page (updated May 2026) says Git doesn't support
  folders. The newer Git integration page (updated September 2026) says Git mirrors the folder structure
  up to 10 levels deep. The newer page is correct.

The ontology creates a graph model item alongside it. Check where it appears. If it lands in the workspace
root, move it into `ontology`. If Fabric won't move it, leave it where it is.

## 3. Item names

Every item starts with `Yuktikara` or `yuktikara`, so a search of the OneLake catalog finds all of them.
Items with restricted names use underscores; items people read in Power BI or chat use plain words.

| Item | Name | Rule it follows |
|---|---|---|
| Workspace | `Yuktikara Retail - Demo` | Section 1 |
| Lakehouse | `yuktikara_lh` | Letters, numbers and underscores only; the `_lh` suffix says what the item is |
| Notebook | `load_yuktikara_data` | Same as the file in [`fabric/`](../fabric/load_yuktikara_data.ipynb), so the repo and the workspace match |
| Semantic model | `Yuktikara Sales` | Business users see this name in Power BI |
| Ontology | `Yuktikara_Ontology` | Letters, numbers and underscores only; no spaces or dashes |
| Graph model | Named by Fabric | Created with the ontology |
| Data agents (Episode 2, planned) | `Yuktikara Lakehouse Agent`, `Yuktikara Ontology Agent` | Plain words, because orchestrators read the name |

## 4. Inside the lakehouse

Create the lakehouse inside the `lakehouses` folder: **+ New item → Lakehouse**, name `yuktikara_lh`.
Keep **Lakehouse schemas** checked, and leave OneLake security off, because an ontology can't bind to a
lakehouse with OneLake security.

**Files** hold the raw material:

```text
Files/yuktikara/data/                 the repo's data folder: 17 CSVs, manifest.json, expected_answers.json
```

**Tables** go into six schemas, one per business area. The load notebook creates them if they're missing.
You can also create them by hand first: **Tables → … → New schema**.

| Schema | Tables |
|---|---|
| `sales` | `sales_order`, `sales_order_line`, `sales_return`, `return_reason`, `promotion`, `order_line_promotion`, `sales_target` |
| `product` | `product`, `product_variant`, `supplier` |
| `store` | `store`, `store_inventory`, `inventory_balance` |
| `supply` | `purchase_order`, `purchase_order_line` |
| `customer` | `customer` |
| `shared` | `dim_date` |

The default `dbo` schema stays empty. Every schema-enabled lakehouse has one, and it can't be removed.
Schemas make the lakehouse browsable by business area. They also mean the ontology's binding dialog and
the Episode 2 lakehouse agent see `sales.sales_order` rather than a flat list of tables.

**Medallion layers, and why there's one lakehouse.** Microsoft Learn calls the medallion architecture the
recommended design for Fabric. It recommends one lakehouse per layer, ideally each in its own workspace.
Yuktikara uses one lakehouse instead, with the layers inside it:

- **Bronze:** raw files, kept per run.
- **Silver:** typed, verified tables.
- **Gold:** the semantic model and the ontology on top.

Separate layers pay off when separate teams own raw and curated data, or when messy sources need
preserving. Here there is one author and one synthetic source, on an F2. Revisit this if a real second
source arrives.

## 5. The task flow

A task flow is a diagram at the top of the workspace. It shows how the items work together, and selecting a
task filters the item list to that task's items. Build it once, in Episode 1, **with a task for every
episode**. Future tasks stay empty until their episode fills them, so the canvas doubles as the roadmap.
Episode 6 (Copilot Studio and MCP) runs outside the workspace, so it gets no task.

Building it (Microsoft Learn, *Set up a task flow* and *Work with task flows*):

1. Open the workspace in **List view**. In the empty task flow area, select **Add a task** and pick the
   first task type. Starting from **Select a predesigned task flow** also works, but you would rename and
   rearrange most of it.
2. Select the task, then **Edit**, and set its name and description from the table below. **Save**.
3. Add the remaining tasks from the **Add** dropdown on the canvas. Drag them into place.
4. **Connect as you go.** Drag from the edge of one task to the next, or use **Add → Connector**. A known
   issue moves any *unconnected* task back to its default position when you add a new task.
5. Assign items: select the task's clip icon, then **Assign item**, tick the items, then **Select**. An
   item belongs to one task at most. Create items inside their folder first, then assign them, so each
   item has both a folder and a task. **Do this the moment each item exists**, not as a batch at the end —
   assign the lakehouse right after you create it, the notebook right after you import it, and so on. The
   item list then stays organised through the whole build instead of needing a tidy-up pass afterward.
6. Select a blank area of the canvas, then **Edit**, and name the flow `Yuktikara Store platform`, with
   the description *One retailer's data platform, built by hand one episode at a time. Select a task to
   see its items.*

| # | Task name | Task type | Items | Episode |
|---:|---|---|---|---|
| 1 | Load data | Get data | `load_yuktikara_data` | 1 |
| 2 | Lakehouse | Store data | `yuktikara_lh` | 1 |
| 3 | Sales model | Visualize data | `Yuktikara Sales`; the net sales report in Episode 2 | 1, 2 |
| 4 | Ontology | General | `Yuktikara_Ontology` and its graph model | 1 |
| 5 | Data agents | Analyze and train data | The two agents | 2 |
| 6 | RFID floor feed | Track data | Eventstream, eventhouse, KQL database | 3 |
| 7 | Floor watch | Track data | The operations agent | 4 |
| 8 | Store app | Develop data | The store app | 5 |

Connectors: **1 → 2**, **2 → 3**, **2 → 4**, **4 → 5**, **6 → 4** (the live feed binds to the ontology as a
time series), **4 → 7**, **7 → 8**. Connectors are drawings only. They don't move data or create
connections.

Task descriptions to paste:

| Task | Description |
|---|---|
| Load data | Writes the uploaded CSVs as lakehouse tables with explicit column types, then checks them. The one notebook in an otherwise hand-built series, and it only loads. |
| Lakehouse | Raw CSVs per run under Files; typed Delta tables in the sales, product, store, customer and shared schemas. |
| Sales model | Direct Lake semantic model with the Net Sales measure: the figure people already trust. |
| Ontology | Entity types, relationships and bindings that describe the business, and the graph built from them. |
| Data agents | Two agents asked the same questions: one on lakehouse tables, one on the ontology. |
| RFID floor feed | Live floor stock readings from RFID-tagged items in the 18 physical stores. |
| Floor watch | An operations agent that spots floor stock below its minimum and asks the store to refill. |
| Store app | Where store managers work through replenishment tasks. |

The task type sets the item types Fabric suggests under **+ New item** on that task. It doesn't limit what
you can assign: under **Display**, switch from *Recommended items* to *All items* to see every type.

**Save the flow to the repo.** Select the canvas, then the **Import and export task flow** icon, then
**Export**, and commit the file as `fabric/task-flow.json`. The export keeps the names, descriptions and
connectors but not the item assignments, so anyone can import the same flow and assign their own items.

## 6. Endorsement and labels

- **Promote the semantic model** (**Settings → Endorsement → Promoted**) once its Net Sales measure matches
  the run's `expected_answers.json`. Promotion marks it as the trusted figure, which is its job in the series.
- **Sensitivity labels** need Microsoft Purview Information Protection in the tenant. Skip them if the tenant
  has none: all the data is synthetic.

## 7. What this setup follows, and what it skips

Followed:

| Practice | How Yuktikara meets it |
|---|---|
| Every workspace sits on a Fabric capacity | On the F2 |
| Every workspace has a description | Section 1 |
| Names follow a convention, with the environment in them | `Yuktikara Retail - Demo` |
| Capacity use is visible | The Capacity Metrics app, installed in *Before you start*: it's the only ongoing view of what the graph and Spark cost on an F2 |
| Trusted content is endorsed | The semantic model is promoted |
| Non-production capacity is paused when idle | Pause the F2 after every session |
| No secrets in notebooks | The load notebook holds none |
| No inline `%pip install` | The notebook and scripts use only the Python standard library and Spark |
| No hard-coded `abfss://` paths or GUIDs | Paths are relative to the default lakehouse |
| Write Delta, not Parquet or CSV | Every table is written as Delta |

Skipped on purpose:

| Practice | Why not here |
|---|---|
| A workspace per medallion layer | One author, one synthetic source; see section 4 |
| Git integration | Item definitions carry the workspace's and lakehouse's IDs, and this repo is public. For version history, connect a separate **private** repo |
| Deployment pipelines, from dev to test to prod | A second stage would need a second ontology, and each graph uses capacity while it runs, which an F2 can't spare |
| At least two workspace admins | This is a one-person demo, not production |

## Sources

Microsoft Learn, checked 2026-09-22 unless noted:

- [Graph overview](https://learn.microsoft.com/fabric/graph/overview#region-availability): region availability and pricing (checked 2026-09-23)
- [Install the Capacity Metrics app](https://learn.microsoft.com/fabric/enterprise/metrics-app-install) (checked 2026-09-23)
- [Workspace-level planning](https://learn.microsoft.com/power-bi/guidance/powerbi-implementation-planning-workspaces-workspace-level-planning): intra-workspace organisation, description, contacts, image, domains
- [Create folders in workspaces](https://learn.microsoft.com/fabric/fundamentals/workspaces-folders)
- [Task flows overview](https://learn.microsoft.com/fabric/fundamentals/task-flow-overview), [Set up a task flow](https://learn.microsoft.com/fabric/fundamentals/task-flow-create), [Work with task flows](https://learn.microsoft.com/fabric/fundamentals/task-flow-work-with)
- [Git integration process](https://learn.microsoft.com/fabric/cicd/git-integration/git-integration-process): folders in Git; [supported items](https://learn.microsoft.com/fabric/cicd/git-integration/intro-to-git-integration)
- [Lakehouse schemas](https://learn.microsoft.com/fabric/data-engineering/lakehouse-schemas)
- [Medallion lakehouse architecture](https://learn.microsoft.com/fabric/onelake/onelake-medallion-lakehouse-architecture)
- [Bind data to an ontology](https://learn.microsoft.com/fabric/iq/ontology/how-to-bind-data): OneLake security and column mapping limits
