import asyncio
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi_admin_lite import Admin
from .database import engine, Base, get_db
from .models import User, Product
from contextlib import asynccontextmanager

# 1. Define a security dependency
async def verify_admin_token(x_admin_token: str = Header(None)):
    # Add your actual token verification logic here
    return

# 2. Mock some log data
async def get_system_logs():
    return [
        {"level": "info", "timestamp": "10:45 AM", "event": "User signup", "user": "alice@example.com"},
        {"level": "error", "timestamp": "11:20 AM", "event": "Payment failed", "user": "bob@example.com"},
        {"level": "warn", "timestamp": "12:05 PM", "event": "High CPU usage", "user": "system"},
    ]

# 3. Modern Lifespan handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)

# 4. Initialize Admin panel
admin = Admin(
    title="Secure Admin Panel",
    auth_dependency=verify_admin_token,
    get_logs=get_system_logs,
    logs_config={
        "title": "Recent Activity",
        "columns": ["level", "timestamp", "event", "user"]
    }
)

# 5. Register models
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

# 6. Mount admin panel
admin.mount(app)

@app.get("/")
def read_root():
    return {"message": "Go to /admin to see the admin panel"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
