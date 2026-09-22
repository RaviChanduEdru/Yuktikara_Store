# Setting up the Yuktikara workspace

How the Fabric workspace is organised before anything is built in it: its settings, folders, item names,
lakehouse layout and task flow. Do this once, at the start of Episode 1. Every later episode adds items into
the structure set up here.

Each convention comes from one of three Microsoft sources, checked on 2026-09-22 and linked at the end:

- **Microsoft Learn**, mainly the workspace-level planning guide. For organising content inside a workspace
  it recommends clear names, task flows, folders, and endorsement and sensitivity labels. It also covers the
  workspace's description, contacts and image.
- **[microsoft/microsoft-iq-solution-accelerator](https://github.com/microsoft/microsoft-iq-solution-accelerator)**,
  Microsoft's retail ontology and data agent solution. It is the closest match to this project. Its installer
  sorts items into folders by type, and its lakehouse groups tables into schemas by business area.
- **[microsoft/fabric-architecture-review](https://github.com/microsoft/fabric-architecture-review)**,
  Microsoft's tenant review accelerator. Its `config/review-checklist.yaml` is a list of numbered
  best-practice rules. This page cites the rule IDs it follows and names the ones it deliberately doesn't.

## 1. The workspace

**Workspaces → + New workspace**, then set these in **Workspace settings**:

| Setting | Value | Why |
|---|---|---|
| **Name** | `Yuktikara Retail - Demo` | See the naming note below |
| **Description** | The text below | Rule ARCH-006: every workspace documents its purpose and ownership |
| **License mode** | Fabric capacity, on the F2 | Rule ARCH-002. Data agents need a paid F-SKU, and rule COST-006 warns against trial capacities for real work |
| **Workspace image** | [`docs/assets/workspace-image.png`](assets/workspace-image.png) | Learn: a consistent image helps people spot the workspace in a list |
| **Contacts** | Leave the default (the workspace admins) | Learn: change it only when someone else answers questions |
| **Domain** (optional) | A `Retail` domain, if you're a Fabric admin | Learn: domains group workspaces by business area and make ownership clear |

**Why the name ends in "- Demo".** It marks the environment. Microsoft's review accelerator reads
environment markers from workspace names. A marker counts only if a space, hyphen, underscore or full stop
separates it from the rest of the name. `demo`, `dev`, `test` and `sandbox` count as non-production; `prod`
and `live` count as production. Learn's examples put the stage in brackets, as in `[Dev]`, but the
accelerator doesn't recognise a marker inside brackets. `- Demo` works for both. Naming the stage is rule
GOV-004, and the marker exempts the workspace from the production-only rules listed in section 7.

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

Folders group items by **type**, using the folder names from Microsoft's IQ accelerator, so anyone who has
deployed it will recognise the layout. The task flow in section 5 groups the same items by **purpose**.
Learn presents folders and task flows as alternatives that can also be combined; here each answers a
different question.

| Folder | Holds | Episode |
|---|---|---|
| `lakehouses` | `yuktikara_lh` | 1 |
| `notebooks` | `refresh_yuktikara_data` | 1 |
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
| Lakehouse | `yuktikara_lh` | Letters, numbers and underscores only. The `_lh` suffix follows the review accelerator's `fabric_arch_review_lh` |
| Notebook | `refresh_yuktikara_data` | Same as the file in [`fabric/`](../fabric/refresh_yuktikara_data.ipynb), so the repo and the workspace match |
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
Files/yuktikara/scripts/              the generator and oracle, uploaded by hand
Files/yuktikara/runs/<end date>/      one folder per notebook run: 11 CSVs, manifest.json, expected_answers.json
```

**Tables** go into five schemas by business area, the same layout as the IQ accelerator's lakehouse
(`sales`, `product`, `customer`, `shared` and others). The refresh notebook creates the schemas if they're
missing. You can also create them by hand first: **Tables → … → New schema**.

| Schema | Tables |
|---|---|
| `sales` | `sales_order`, `sales_order_line`, `sales_return`, `return_reason` |
| `product` | `product`, `product_variant`, `supplier` |
| `store` | `store`, `store_inventory` |
| `customer` | `customer` |
| `shared` | `dim_date` |

The default `dbo` schema stays empty. Every schema-enabled lakehouse has one, and it can't be removed.
Schemas make the lakehouse browsable by business area. They also mean the ontology's binding dialog and
the Episode 2 lakehouse agent see `sales.sales_order` rather than a flat list of tables.

**Medallion layers, and why there's one lakehouse.** Microsoft Learn calls the medallion architecture the
recommended design for Fabric. It recommends one lakehouse per layer, ideally each in its own workspace.
Yuktikara follows the IQ accelerator instead and uses one lakehouse, with the layers inside it:

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
   item has both a folder and a task.
6. Select a blank area of the canvas, then **Edit**, and name the flow `Yuktikara Store platform`, with
   the description *One retailer's data platform, built by hand one episode at a time. Select a task to
   see its items.*

| # | Task name | Task type | Items | Episode |
|---:|---|---|---|---|
| 1 | Generate data | Get data | `refresh_yuktikara_data` | 1 |
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
| Generate data | Regenerates the synthetic dataset for a window ending yesterday and loads typed tables. The one notebook in an otherwise hand-built series. |
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
  the run's `expected_answers.json`. Promotion marks it as the trusted figure, which is its job in the
  series. This follows rules GOV-008 and GOV-009.
- **Sensitivity labels** (rule GOV-003) need Microsoft Purview Information Protection in the tenant. Skip
  them if the tenant has none: all the data is synthetic.

## 7. Rules from Microsoft's review accelerator

Rules this setup follows:

| Rule | What it asks | How Yuktikara meets it |
|---|---|---|
| ARCH-002 | Every workspace on a Fabric capacity | On the F2 |
| ARCH-006 | Every workspace has a description | Section 1 |
| GOV-004 | Workspace names follow a convention with an environment marker | `Yuktikara Retail - Demo` |
| GOV-007 | The Capacity Metrics app is installed | Install it; it's the only ongoing view of what the graph and Spark cost on an F2 |
| GOV-008, GOV-009 | Trusted content is endorsed | The semantic model is promoted |
| COST-002, COST-003 | Non-production capacities are paused when idle | Pause the F2 after every session |
| NBCODE-001 | No secrets in notebooks | The refresh notebook holds none |
| NBCODE-002 | No inline `%pip install` | The notebook and scripts use only the Python standard library and Spark |
| NBCODE-005 | No hard-coded `abfss://` paths or GUIDs | Paths are relative to the default lakehouse |
| NBCODE-006 | Write Delta, not Parquet or CSV | Every table is written as Delta |

Rules left out on purpose, and why:

| Rule | What it asks | Why not here |
|---|---|---|
| ARCH-001 | Separate workspaces per medallion layer | One author, one synthetic source; see section 4 |
| ARCH-004, OPS-002 | Git integration for production workspaces | Production-only, and syncing would commit item definitions that carry the workspace's and lakehouse's IDs into a public repo. The IQ accelerator handles that with `parameter.yml` placeholders and deployment scripts, which this hand-built series avoids. For version history, connect a separate **private** repo |
| ARCH-009, OPS-001, OPS-003 | Deployment pipelines from dev to test to prod | Production-only. A second stage would need a second ontology, and each graph uses capacity while it runs, which an F2 can't spare |
| GOV-001 | At least two workspace admins | Production-only; this is a one-person demo |

## Sources

Microsoft Learn, checked 2026-09-22:

- [Workspace-level planning](https://learn.microsoft.com/power-bi/guidance/powerbi-implementation-planning-workspaces-workspace-level-planning): intra-workspace organisation, description, contacts, image, domains
- [Create folders in workspaces](https://learn.microsoft.com/fabric/fundamentals/workspaces-folders)
- [Task flows overview](https://learn.microsoft.com/fabric/fundamentals/task-flow-overview), [Set up a task flow](https://learn.microsoft.com/fabric/fundamentals/task-flow-create), [Work with task flows](https://learn.microsoft.com/fabric/fundamentals/task-flow-work-with)
- [Git integration process](https://learn.microsoft.com/fabric/cicd/git-integration/git-integration-process): folders in Git; [supported items](https://learn.microsoft.com/fabric/cicd/git-integration/intro-to-git-integration)
- [Lakehouse schemas](https://learn.microsoft.com/fabric/data-engineering/lakehouse-schemas)
- [Medallion lakehouse architecture](https://learn.microsoft.com/fabric/onelake/onelake-medallion-lakehouse-architecture)
- [Bind data to an ontology](https://learn.microsoft.com/fabric/iq/ontology/how-to-bind-data): OneLake security and column mapping limits

Microsoft repos:

- microsoft-iq-solution-accelerator: `docs/fabric/DeploymentGuideFabricManual.md` (the folder layout),
  `.github/instructions/fabric-workspace.instructions.md` (item conventions), and the ontology's data
  bindings, which read tables such as `supplychain.suppliers`
- fabric-architecture-review: `config/review-checklist.yaml` (the rules), `analyzers/applicability.py`
  (environment markers in workspace names), `fabric/README.md` (the workspace logo)
