# Setting up the Yuktikara workspace

How the Fabric workspace is organised before anything is built in it: its settings, folders, item names and
lakehouse layout. Do this once, at the start of Episode 1. Every later episode adds items into the structure
set up here. The task flow, which spans every episode, is in [architecture.md](../architecture.md#task-flow).

## Before you start

Two things to confirm before you create anything, because both are awkward to fix once you've built on
top of them.

**The capacity's region supports Graph.** The ontology's graph model only runs in
[certain regions](https://learn.microsoft.com/en-us/fabric/graph/overview#region-availability) (checked
2026-09-23) — Central India is one of roughly 35, alongside East US, West Europe and UK South. **Admin
portal → Capacity settings →** your capacity, and check its region against that list. Everything for this
series — workspace, lakehouse, ontology and, later, the data agents — has to run in this one region, so
settle this now rather than after Step 4. This applies the same way whether you start on a trial capacity
or a paid one: moving a workspace's items to a different region later means deleting them first.

**Install the Microsoft Fabric Capacity Metrics app**, so it's recording usage from your first item, not
from whenever you remember to add it. You need to be a capacity admin.
[AppSource → Microsoft Fabric Capacity Metrics](https://go.microsoft.com/fwlink/?linkid=2219875) → **Get it
now** → sign in → **Install**. On first run it asks for your UTC offset (`5.5` for India) and a capacity to
report on.

The tenant settings that let you create an ontology at all — **Ontology item (preview)** and Graph — are
checked separately, right before you need them, in
[ontology-bindings.md](03-ontology-bindings.md#before-you-start).

## 1. The workspace

**Workspaces → + New workspace**, then fill in the **Create a workspace** panel:

| Setting | Value | Why |
|---|---|---|
| **Name** | `Yuktikara Retail - Demo` | See the naming note below |
| **Description** | The text below | A workspace should say what it is for and who owns it |
| **Domain** (optional) | A `Retail` domain, if you're a Fabric admin | Learn: domains group workspaces by business area and make ownership clear |
| **Workspace image** | [`docs/assets/workspace-image.png`](../assets/workspace-image.png) | Learn: a consistent image helps people spot the workspace in a list |
| **Advanced → Contact list** | Leave the default (you) | Learn: change it only when someone else answers questions |
| **Advanced → Workspace type** | **Fabric Trial**, and your trial capacity under **Details** | The lakehouse, notebook, ontology and graph all run on a trial the same as on a paid capacity. Only Episode 2's data agents need a paid F2 or higher, so there's nothing to gain by paying before then |

**Why the name ends in "- Demo".** It marks the environment, which is what tells anyone reading a list of
workspaces, or any tool that sorts them, that this one isn't production. Use a separator rather than
brackets: tooling that classifies workspaces by name typically looks for `dev`, `test`, `demo` or `sandbox`
with a space, hyphen, underscore or full stop on either side, so `[Demo]` in brackets is easily missed, while
`- Demo` is read either way.

**Description:**

```text
Yuktikara Store (demo). A Microsoft Fabric build for a fictional outdoor retailer, made for a public video
series, built by hand in the portal, one episode at a time. All data is synthetic. Questions: open an issue
at github.com/RaviChanduEdru/Yuktikara_Store
```

## 2. Folders

Folders group items by **type**; the [task flow](../architecture.md#task-flow) groups the same items by
**purpose**. Learn presents folders and task flows as alternatives that can also be combined, and here each
answers a different question: what is this, and what is it for.

Four folders for this episode:

| Folder | Holds |
|---|---|
| `lakehouses` | `yuktikara_lh` |
| `notebooks` | `load_yuktikara_data` |
| `dashboards` | Empty for now: the `Yuktikara Sales` semantic model arrives in Episode 2 |
| `ontology` | `Yuktikara_Ontology` and its graph model |

`dashboards` is created now, empty, so the workspace is ready for Episode 2. The folders for agents,
real-time data and the app (`data_agent`, `realtime`, `apps`) come in their own episodes.

**Workspaces → + New folder**, then open it and **+ New item** to create directly inside it. Names can't
contain `~ " # . & * : < > ? / { | }` or start or end with a space. Items created elsewhere (the Fabric
home page, the **Create** hub) land in the workspace root instead; move them in with **… → Move to**.

The ontology creates a graph model item alongside it. Check where it appears. If it lands in the workspace
root, move it into `ontology`. If Fabric won't move it, leave it where it is.

## 3. Item names

Every item starts with `Yuktikara` or `yuktikara`, so a search of the OneLake catalog finds all of them.
Items with restricted names use underscores; items people read in Power BI or chat use plain words.

| Item | Name | Rule it follows |
|---|---|---|
| Workspace | `Yuktikara Retail - Demo` | Section 1 |
| Lakehouse | `yuktikara_lh` | Letters, numbers and underscores only; the `_lh` suffix says what the item is |
| Notebook | `load_yuktikara_data` | Same as the file in [`fabric/`](../../fabric/load_yuktikara_data.ipynb), so the repo and the workspace match |
| Semantic model (Episode 2) | `Yuktikara Sales` | Business users see this name in Power BI |
| Ontology | `Yuktikara_Ontology` | Letters, numbers and underscores only; no spaces or dashes |
| Graph model | Named by Fabric | Created with the ontology |
| Data agents (Episode 2, planned) | `Yuktikara Lakehouse Agent`, `Yuktikara Ontology Agent` | Plain words, because orchestrators read the name |

## 4. Inside the lakehouse

From the task flow's **Lakehouse** task: **+ New item → Lakehouse**. In the **New Lakehouse** dialog, name it
`yuktikara_lh`, set **Location** to the `lakehouses` folder, check that **Assign to task** says `Lakehouse`,
and keep **Lakehouse schemas** checked. OneLake security isn't in this dialog; don't turn it on later,
because an ontology can't bind to a lakehouse with OneLake security.

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
preserving. Here there is one author and one synthetic source, on a trial capacity for this episode (a
paid F2 from Episode 2). Revisit this if a real second source arrives.

## Sources

Microsoft Learn, checked 2026-09-22 unless noted:

- [Graph overview](https://learn.microsoft.com/fabric/graph/overview#region-availability): region availability and pricing (checked 2026-09-23)
- [Install the Capacity Metrics app](https://learn.microsoft.com/fabric/enterprise/metrics-app-install) (checked 2026-09-23)
- [Fabric trial capacity](https://learn.microsoft.com/fabric/fundamentals/fabric-trial): what's included, what's not (Copilot and AI Experiences, including data agents), and what happens when it expires (checked 2026-09-23)
- [Understand Microsoft Fabric licenses and capacity](https://learn.microsoft.com/fabric/enterprise/licenses): trial and F-SKU workspace types both support "all Fabric experiences" for non-Power BI items (checked 2026-09-23)
- [Fabric data agent creation](https://learn.microsoft.com/fabric/data-science/concept-data-agent#prerequisites): "a paid F2 or higher Fabric capacity" is a stated prerequisite (checked 2026-09-23)
- [Workspace-level planning](https://learn.microsoft.com/power-bi/guidance/powerbi-implementation-planning-workspaces-workspace-level-planning): intra-workspace organisation, description, contacts, image, domains
- [Create folders in workspaces](https://learn.microsoft.com/fabric/fundamentals/workspaces-folders)
- [Lakehouse schemas](https://learn.microsoft.com/fabric/data-engineering/lakehouse-schemas)
- [Medallion lakehouse architecture](https://learn.microsoft.com/fabric/onelake/onelake-medallion-lakehouse-architecture)
- [Bind data to an ontology](https://learn.microsoft.com/fabric/iq/ontology/how-to-bind-data): OneLake security and column mapping limits

The task flow (built now, but planned across every episode) and a checklist of which Well-Architected
practices this setup follows are in [architecture.md](../architecture.md#task-flow).
