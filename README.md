# Mozart ERP

**Open-source RAD platform for 3-tier client–server applications on Linux.**

Python 3 · PySide6 (Qt 6) · PostgreSQL 14+ · Ubuntu

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![Platform: Linux](https://img.shields.io/badge/platform-Ubuntu-orange.svg)](https://ubuntu.com/)

---

## The problem

When Microsoft discontinued Visual FoxPro, an entire class of tooling disappeared:
**fast, native, database-centric RAD** for business applications. Delphi stagnated.
The remaining options are either heavyweight enterprise suites, or web stacks where
every single form costs weeks of hand-written markup, API endpoints and state glue.

For internal business software — reference tables, document entry, registries,
reports — that trade-off is absurd. A form with a grid, three lookups and a save
button should take minutes, not a sprint.

Mozart ERP restores minute-scale form development on a modern, fully open stack.

---

## What it is

A visual configurator (IDE) plus a runtime, backed by a metadata-driven PostgreSQL
schema. You draw a form on a WYSIWYG canvas, declare its properties and methods,
and the platform generates the working application — no hand-written glue code
between the UI and the database.

### Core concepts

| Concept | Meaning |
|---|---|
| **Class / Version** | Every form, control and container is a versioned class. Editing never mutates history. |
| **Bloodline (lineage)** | Classes inherit from ERP ancestors *and* from a native Qt base class. Resolution happens inside PostgreSQL via recursive functions. |
| **Time machine** | Every class, property, method and signal carries `dt_start` / `dt_end`. Set the session date and the whole system renders as it existed on that day. |
| **Property bridge** | Declarative mapping between a metadata property and a native Qt call (`setStyleSheet`, `setFont`, …). No imperative adapters. |
| **Method resolution** | Strict priority: own/ancestor class method → SuperLibre fallback. Never the reverse. |
| **idCol identity** | Every object in a scene collection — element, property, method, signal — has one immutable integer key. All navigation goes through it. |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1 — Qt client (PySide6)                              │
│  Configurator IDE · WYSIWYG scene · Property Inspector      │
│  Runtime forms rendered from metadata                       │
└───────────────────────────┬─────────────────────────────────┘
                            │  TCP/IP (JSON protocol)
┌───────────────────────────▼─────────────────────────────────┐
│  Layer 2 — Application server                               │
│  Session state · method dispatch · transaction boundary     │
└───────────────────────────┬─────────────────────────────────┘
                            │  libpq
┌───────────────────────────▼─────────────────────────────────┐
│  Layer 3 — PostgreSQL                                       │
│  Schema mozart        — entities, fields, data              │
│  Schema class_erp     — classes, versions, properties,      │
│                         methods, signals, bridges           │
│  Stored functions     — lineage, inheritance, time travel   │
└─────────────────────────────────────────────────────────────┘
```

Business logic lives in stored procedures, not in scattered inline SQL.
The client asks for a data slice; the database decides how to build it.

---

## Features

**Configurator**
- Drag-and-drop form designer with snap-to-grid, move/resize handles
- Class palette grouped by category (input, display, containers, system)
- Live property table with per-type editors: color picker, font dialog,
  entity reference, field reference, form reference, image/BLOB upload
- Debug Collection Inspector — full tree of elements, properties, methods
  and signals with dirty/inherited/deleted flags and SQL preview
- Change log of every model mutation with source attribution

**Inheritance & versioning**
- Multiple inheritance paths: ERP ancestor chain + donor objects + Qt base
- Property overrides resolved nearest-ancestor-first, with `COALESCE` defaults
- Immutable version snapshots: saving a published class creates a new version
  and closes the previous one; in-development versions update in place
- Three explicit save scenarios: new class / update current / new version

**Runtime**
- Forms instantiated from metadata, no generated Python to maintain
- Method bodies stored in the database, compiled and cached per version
- Signals bound to methods declaratively
- Session date selector — inspect the system at any point in its history

**Internationalisation**
- SQLite-backed translation store, per-language columns
- Raw values kept separate from display values

---

## Tech stack

| Layer | Technology |
|---|---|
| UI | PySide6 / Qt 6 |
| Language | Python 3.12 |
| Database | PostgreSQL 14+ (plpgsql, recursive CTEs, temporal tables) |
| Translation store | SQLite 3 |
| Transport | TCP/IP sockets, JSON messages |
| OS | Linux (developed and tested on Ubuntu) |

---

## Getting started

### Prerequisites

```bash
sudo apt install python3.12 python3.12-venv postgresql-14
```

### Installation

```bash
git clone https://github.com/pankratovsn1973-stack/mozart.git
cd mozart

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Database

```bash
createdb mozart_erp
psql -d mozart_erp -f sql/schema_mozart.sql
psql -d mozart_erp -f sql/schema_class_erp.sql
psql -d mozart_erp -f sql/functions.sql
```

### Configuration

Connection settings live in a project manifest (`*.mzt`) or environment variables:

```bash
export MOZART_DB_HOST=localhost
export MOZART_DB_PORT=5432
export MOZART_DB_NAME=mozart_erp
export MOZART_DB_USER=postgres
export MOZART_DB_PASS=your_password
```

### Run

```bash
python ide_main.py
```

---

## Repository layout

```
core/           Object model, collections, registry, bridge resolver
controls/       Mozart widget classes (Qt subclasses)
dialogs/        Configurator dialogs, collection manager, inspectors
tabs/           IDE tabs: entities, classes, import, translations
widgets/        Reusable UI components
services/       Application services
layer2_server/  Application server
layer3_client/  Thin client
sql/            Schema and stored functions
lang_data/      Translation store
architecture/   Design notes and diagrams
docs/           Documentation
utils/          Helpers
```

---

## Roadmap

- [ ] Qwen-Max / Qwen-Coder integration into the configurator:
      method body generation, SQL logic analysis, metadata assistance
- [ ] Web renderer for the same metadata (optional deployment target)
- [ ] Report designer
- [ ] Migration tooling for FoxPro / DBF legacy projects
- [ ] Plugin API for third-party controls and bridges

---

## Why open source

This project is and will remain open. Closed tooling is exactly what killed
FoxPro — a vendor decided the product was no longer strategic, and an entire
ecosystem of business applications lost its foundation.

A RAD platform only makes sense if developers can trust it will outlive any
single company's roadmap.

---

## Contributing

Issues and pull requests are welcome. Please read `CONTRIBUTING.md` before
submitting larger changes — the object model has strict invariants around
identity (idCol), inheritance flags and version immutability.

---

## License

MIT — see [LICENSE](LICENSE).

---

## Author

**Sergey Pankratov** — [@pankratovsn1973-stack](https://github.com/pankratovsn1973-stack)
