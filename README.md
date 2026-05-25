# FastAPI Lite Admin

A premium, lightweight, pluggable admin panel for FastAPI and SQLAlchemy.

## Screenshots

### 🖥️ Dashboard / System Overview
![Dashboard](https://raw.githubusercontent.com/rishiqwerty/admin-panel-fast-api/add-docs-for-setting-up-admin-panel/docs/images/dashboard.png)

### 📊 Model List View
![Model List](https://raw.githubusercontent.com/rishiqwerty/admin-panel-fast-api/add-docs-for-setting-up-admin-panel/docs/images/model_list.png)

### 📝 Edit/Create Record Form
![Model Form](https://raw.githubusercontent.com/rishiqwerty/admin-panel-fast-api/add-docs-for-setting-up-admin-panel/docs/images/model_form.png)

## Features

- **Zero-config CRUD**: Automatically generate admin interfaces for your models.
- **ORM Agnostic**: Initial support for SQLAlchemy, designed to support others.
- **API First**: All admin actions are available via a clean, RESTful API.
- **Lightweight UI**: Fast, responsive, Jinja2 templates with server-side pagination, sorting, and search.
- **Attention Filters**: Highlight critical records (e.g. low stock, inactive users) requiring moderation attention.
- **Live Activity Badges**: "24h Activity" badges in headers and footers for real-time monitoring.
- **Custom System Logs**: Display a customizable activity feed on the main dashboard.

---

## Installation

Install the package directly into your project:

```bash
pip install fastapi-lite-admin
```

For development/local setup, clone the repository and run:

```bash
pip install -e ".[dev]"
```

---

## Quick Start & Usage

Using `FastAPI Lite Admin` is designed to be highly explicit, simple, and require minimal boilerplate. Here is how you can set it up in your application.

### 1. Initialize the Admin Panel

Instantiate the `Admin` class and mount it to your `FastAPI` instance.

```python
from fastapi import FastAPI
from fastapi_admin_lite import Admin

app = FastAPI()

admin = Admin(
    title="Secure Control Panel",  # Dashboard title
    base_url="/admin",             # URL prefix for the admin panel
    enable_ui=True                 # Enable/disable Jinja-based UI
)

# Mount the admin router and views to your FastAPI app
admin.mount(app)
```

This will automatically create and serve:
- The UI dashboard at `http://localhost:8000/admin`

---

## Registering Models (Adding Tables)

To add database tables to your admin panel, register your models using `admin.register()`.

```python
from database import get_db  # Your SQLAlchemy session dependency
from models import User

admin.register(
    model=User,
    get_db=get_db,
    list_display=["id", "email", "is_active", "created_at"],
    date_field="created_at",
    attention_filter=(User.is_active == False),
    readonly_fields=["created_at"],
    config={"display_name": "System Users"}
)
```

### Registration Configuration Parameters

When calling `admin.register()`, you can configure how each model is represented:

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| **`model`** | `Type[Any]` | **Yes** | The SQLAlchemy Declarative model class to generate CRUD operations for. |
| **`get_db`** | `Callable` | **Yes** | An async/sync generator yielding an active SQLAlchemy database session (`AsyncSession` or `Session`). |
| **`list_display`** | `List[str]` | No | List of field/column names to display as columns in the UI model list view. Defaults to all fields. |
| **`date_field`** | `str` | No | Name of the datetime field (e.g. `created_at`). Required to show the "24h Activity" count cards on the dashboard and lists. |
| **`attention_filter`** | `SQLAlchemy Expression` | No | A SQLAlchemy binary filter expression (e.g., `User.is_active == False` or `Product.stock < 10`) used to calculate and flag rows that require moderator attention. |
| **`readonly_fields`** | `List[str]` | No | List of columns that cannot be modified or set via creation or updates (e.g., auto-generated columns or timestamps like `id`, `created_at`). |
| **`config`** | `Dict[str, Any]` | No | Dictionary containing extra settings. Supports `"display_name"` to override the sidebar label. |

---

## Initialization Configurations

The `Admin` class constructor supports the following parameters for customization:

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| **`title`** | `str` | `"FastAPI Admin Lite"` | Customized title displayed in the UI header and dashboard. |
| **`base_url`** | `str` | `"/admin"` | URL prefix where the admin UI is served. |
| **`enable_ui`** | `bool` | `True` | Whether to serve the Jinja2 templates UI. If `False`, only the API routes are registered. |
| **`dependencies`** | `List[Any]` | `[]` | General list of FastAPI dependencies to apply to all admin routes. |
| **`auth_dependency`** | `Callable` | `None` | Dependency function for custom security gating (e.g., checking tokens or cookies). |
| **`permission_checker`**| `Callable` | `allow all` | Custom callable to restrict user roles. |
| **`dashboard_models`** | `List[str]` | `None` | List of registered model names to display on the dashboard (if you want to restrict which registered models show on the home dashboard). |
| **`get_logs`** | `Callable` | `None` | An optional callable (async or sync) returning system logs to display on the dashboard activity log feed. |
| **`logs_config`** | `Dict[str, Any]` | `{"title": "System Activity", "columns": ["level", "timestamp", "message"]}` | Config dictionary to customize dashboard log columns and activity title. |

---

## Gating Access & Security

By default, the admin panel warns if no authentication is configured. You can gate the admin panel and its APIs using standard FastAPI dependencies:

### 1. `auth_dependency`

Pass a dependency to `Admin` constructor that handles authentication.

```python
from fastapi import Header, HTTPException

async def verify_admin_token(x_admin_token: str = Header(None)):
    if x_admin_token != "super-secret-admin-token":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return x_admin_token

admin = Admin(
    title="Secure Admin",
    auth_dependency=verify_admin_token
)
```

### 2. `permission_checker`

Restrict granular user roles with a custom callable:

```python
async def check_permissions(user: Any = Depends(get_current_user)) -> bool:
    return user.is_superuser

admin = Admin(
    title="Staff Portal",
    permission_checker=check_permissions
)
```

---

## Custom Dashboard Activity Logs

Configure a live activity log feed on the dashboard homepage:

```python
async def fetch_system_logs():
    # Fetch logs from a database table, file, or third-party service
    return [
        {"level": "info", "timestamp": "10:45 AM", "event": "User signup", "user": "alice@example.com"},
        {"level": "error", "timestamp": "11:20 AM", "event": "Payment failed", "user": "bob@example.com"}
    ]

admin = Admin(
    title="Command Center",
    get_logs=fetch_system_logs,
    logs_config={
        "title": "Recent Activity Feed",
        "columns": ["level", "timestamp", "event", "user"]
    }
)
```

---

## Running the Example Application

We package a complete working example inside the `/example` directory. To run it:

```bash
# 1. Install dependencies with dev options
pip install -e ".[dev]"

# 2. Run the example application
python -m example.main
```

Then visit `http://localhost:8001/admin` in your web browser. You'll be able to view logs, add/update users, search database entries, and filter elements dynamically.

