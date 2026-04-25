from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi_admin_lite import Admin
from .database import engine, Base, get_db
from .models import User, Product

# 1. Define a security dependency
async def verify_admin_token(x_admin_token: str = Header(None)):
    return

# 2. Mock some log data
def get_system_logs():
    return [
        {"level": "info", "timestamp": "10:45 AM", "event": "User signup", "user": "alice@example.com"},
        {"level": "error", "timestamp": "11:20 AM", "event": "Payment failed", "user": "bob@example.com"},
        {"level": "warn", "timestamp": "12:05 PM", "event": "High CPU usage", "user": "system"},
    ]

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# 3. Pass everything to the Admin panel
admin = Admin(
    title="Secure Admin Panel",
    auth_dependency=verify_admin_token,
    get_logs=get_system_logs,
    logs_config={
        "title": "Recent Activity",
        "columns": ["level", "timestamp", "event", "user"]
    }
)

# Register models
admin.register(
    model=User,
    get_db=get_db,
    list_display=["id", "name", "email", "is_active", "created_at"],
    date_field="created_at",
    attention_filter=(User.is_active == False),
    readonly_fields=["created_at"],
    config={"display_name": "System Users"}
)

admin.register(
    model=Product,
    get_db=get_db,
    list_display=["id", "name", "price", "stock", "created_at"],
    date_field="created_at",
    attention_filter=(Product.price == 0),
    readonly_fields=["created_at"]
)

# Mount admin panel
admin.mount(app)

@app.get("/")
def read_root():
    return {"message": "Go to /admin to see the admin panel"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
