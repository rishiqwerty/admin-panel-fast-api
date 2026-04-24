from fastapi import FastAPI
from fastapi_admin_lite import Admin
from .database import engine, Base, get_db
from .models import User, Product

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Initialize Admin
admin = Admin(title="My Awesome Admin")

# Register models
admin.register(
    model=User,
    get_db=get_db,
    config={"name": "users", "display_name": "Users List"}
)

admin.register(
    model=Product,
    get_db=get_db,
    config={"name": "products"}
)

# Mount admin panel
admin.mount(app)

@app.get("/")
def read_root():
    return {"message": "Go to /admin to see the admin panel"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
