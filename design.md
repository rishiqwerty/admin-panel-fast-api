# FastAPI Admin Lite — Design Document

## 🎯 Goal

Build a **reusable, pluggable admin package** for FastAPI applications that enables:

* Viewing data (tables)
* Creating records
* Updating records
* Deleting records

The package must be:

* Framework-agnostic (within FastAPI ecosystem)
* ORM-agnostic (initial support: SQLAlchemy)
* UI-optional but bundled (Jinja-based)
* Highly configurable but not over-engineered
* Safe for production use

---

## 🧠 Design Principles

### 1. Explicit over implicit

Avoid heavy introspection. Require developers to define:

* fields
* configurations
* permissions (later)

---

### 2. API-first design

All functionality must be exposed via `/admin/*` APIs.

UI is a thin layer on top.

---

### 3. Loose coupling

* No direct DB access from external systems
* No dependency on project structure
* No assumptions about app architecture

---

### 4. Extensibility

Design for:

* multiple ORMs
* custom actions
* future RBAC
* external UI integration

---

### 5. Minimal viable abstraction

Support 80% of use cases with minimal complexity.

---

## 🏗️ High-Level Architecture

```
FastAPI App
   │
   ├── Admin Package (this project)
   │     ├── Registry
   │     ├── CRUD Engine
   │     ├── Schema Generator
   │     ├── Router (/admin/*)
   │     └── Jinja UI (optional)
   │
   └── User Models / DB
```

---

## 📦 Package Structure

```
fastapi_admin_lite/
│
├── core/
│   ├── registry.py        # model registration
│   ├── config.py          # model config schema
│   ├── schema.py          # admin schema generation
│   ├── crud.py            # generic CRUD logic
│
├── routers/
│   ├── admin.py           # API routes
│
├── ui/
│   ├── templates/
│   ├── views.py           # UI rendering logic
│
├── integrations/
│   ├── sqlalchemy.py      # ORM adapter
│
├── dependencies/
│   ├── db.py              # DB session handling
│
└── main.py                # Admin class (entry point)
```

---

## 🔌 Public API (Developer Usage)

```python
from fastapi_admin_lite import Admin

admin = Admin(enable_ui=True)

admin.register(
    model=User,
    get_db=get_db,
    config={
        "name": "users",
        "display_name": "Users",
        "fields": ["id", "email", "is_active"],
        "readonly_fields": ["id"],
        "searchable_fields": ["email"]
    }
)

admin.mount(app)
```

---

## 🧩 Core Components

### 1. Admin Class

Responsibilities:

* manage registry
* initialize routes
* mount UI

---

### 2. Model Registry

Stores:

* model reference
* DB dependency
* config

```python
registry = {
    "users": ModelConfig(...)
}
```

---

### 3. ModelConfig Schema

```python
{
  "name": "users",
  "display_name": "Users",
  "fields": ["id", "email", "is_active"],
  "readonly_fields": ["id"],
  "searchable_fields": ["email"],
  "hidden_fields": []
}
```

---

### 4. CRUD Engine

Generic operations:

* list()
* get()
* create()
* update()
* delete()

Must:

* use dependency-injected DB session
* support pagination
* support basic filtering

---

### 5. Schema Generator

Endpoint:

```
GET /admin/schema
```

Returns:

```json
{
  "models": [
    {
      "name": "users",
      "display_name": "Users",
      "fields": [...]
    }
  ]
}
```

---

## 🌐 API Design

### Base Route

```
/admin
```

---

### Endpoints

#### List Models

```
GET /admin/models
```

---

#### Get Schema

```
GET /admin/schema
```

---

#### List Records

```
GET /admin/{model}
```

Query params:

* `limit`
* `offset`
* `search`

---

#### Get Record

```
GET /admin/{model}/{id}
```

---

#### Create Record

```
POST /admin/{model}
```

---

#### Update Record

```
PUT /admin/{model}/{id}
```

---

#### Delete Record

```
DELETE /admin/{model}/{id}
```

---

### Standard Response Format

```json
{
  "data": [...],
  "total": 100
}
```

---

## 🎨 UI Design (Jinja आधारित)

### Goals

* zero setup
* simple and functional
* schema-driven rendering

---

### Routes

```
/admin                → dashboard
/admin/{model}        → table view
/admin/{model}/new    → create form
/admin/{model}/{id}   → edit form
```

---

### Components

#### 1. Dashboard

* list of registered models

---

#### 2. Table View

* columns from schema
* pagination
* search bar

---

#### 3. Form View

* dynamic inputs based on field type

| Type    | Input      |
| ------- | ---------- |
| string  | text input |
| int     | number     |
| boolean | checkbox   |

---

### Optional Enhancement

Use HTMX for:

* inline updates
* partial reloads
* better UX without SPA

---

## ⚙️ Configuration & Extensibility

### Field-level config (future)

```python
{
  "fields": [
    {"name": "email", "type": "string", "searchable": True},
    {"name": "is_active", "type": "boolean"}
  ]
}
```

---

### Custom Actions (future)

```python
admin.register_action(
    name="deactivate_users",
    handler=func
)
```

---

### RBAC (future)

* role-based access
* per-model permissions
* per-field permissions

---

## 🔐 Security Considerations

### MUST HAVE

* authentication layer (token or session)
* CSRF protection (for forms)
* input validation (via Pydantic)
* restricted access to `/admin/*`

---

### SHOULD HAVE

* audit logs
* rate limiting (optional)

---

## ⚠️ Constraints & Non-Goals

### Non-goals (for MVP)

* full Django Admin parity
* automatic DB schema introspection
* multi-ORM support
* advanced relationships UI

---

### Constraints

* FastAPI-based apps only
* Python 3.9+
* SQLAlchemy first-class support

---

## 🚀 MVP Scope

### Phase 1

* model registration
* CRUD endpoints
* schema endpoint
* basic Jinja UI

---

### Phase 2

* pagination + search
* multi-model support UI
* better forms

---

### Phase 3

* auth system
* filtering
* UI improvements

---

### Phase 4

* RBAC
* audit logs
* plugin system

---

## 🧪 Testing Strategy

* unit tests for CRUD engine
* integration tests with FastAPI app
* UI smoke tests

---

## 📦 Packaging & Distribution

* pip-installable
* semantic versioning
* minimal dependencies

---

## 🧠 Final Notes

This package is:

* not a Django Admin replacement
* not a full framework

It is:

> a lightweight, extensible admin layer for FastAPI systems

Focus on:

* simplicity
* reliability
* developer experience

Avoid:

* magic
* over-abstraction
* premature generalization
