from typing import Any
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

# Get path to templates directory relative to this file
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

def create_ui_router(admin: Any) -> APIRouter:
    router = APIRouter()

    @router.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request):
        from datetime import datetime, timedelta
        from sqlalchemy import select, func
        models = admin.registry.get_models()
        
        # Collect real counts for each model
        stats = []
        for name, reg in models.items():
            if admin.dashboard_models and name not in admin.dashboard_models:
                continue
                
            db_gen = reg.get_db()
            # Handle both async and sync generators for maximum compatibility
            if hasattr(db_gen, "__anext__"):
                db = await db_gen.__anext__()
            else:
                db = next(db_gen)

            try:
                # 1. Get Total Count
                total_query = select(func.count()).select_from(reg.model)
                total_result = await db.execute(total_query)
                total_count = total_result.scalar()
                
                # 2. Get 24h Count
                recent_count = None
                date_field = reg.config.get("date_field")
                if date_field and hasattr(reg.model, date_field):
                    yesterday = datetime.now() - timedelta(hours=24)
                    recent_query = select(func.count()).select_from(reg.model).filter(
                        getattr(reg.model, date_field) >= yesterday
                    )
                    recent_result = await db.execute(recent_query)
                    recent_count = recent_result.scalar()

                stats.append({
                    "name": reg.config.get("display_name") or name.capitalize(),
                    "count": total_count,
                    "recent_count": recent_count,
                    "model_name": name,
                    "has_date_field": bool(date_field)
                })
            finally:
                if hasattr(db_gen, "aclose"):
                    await db_gen.aclose()
                elif hasattr(db_gen, "close"):
                    db_gen.close()

        # Handle logs
        recent_logs = []
        if admin.get_logs:
            try:
                if asyncio.iscoroutinefunction(admin.get_logs):
                    recent_logs = await admin.get_logs()
                else:
                    recent_logs = admin.get_logs()
            except Exception as e:
                print(f"Error fetching logs: {e}")

        return templates.TemplateResponse(
            request=request, 
            name="dashboard.html", 
            context={"stats": stats, "recent_logs": recent_logs, "models": list(models.keys())}
        )

    @router.get("/{model_name}", response_class=HTMLResponse)
    async def model_list(request: Request, model_name: str):
        from datetime import datetime, timedelta
        from sqlalchemy import select, func
        reg = admin.registry.get_model(model_name)
        if not reg:
            raise HTTPException(status_code=404, detail="Model not found")
            
        models = list(admin.registry.get_models().keys())
        
        # Calculate stats for this specific model
        recent_count = None
        attention_count = None
        date_field = reg.config.get("date_field")
        attn_filter = reg.config.get("attention_filter")
        
        db_gen = reg.get_db()
        if hasattr(db_gen, "__anext__"):
            db = await db_gen.__anext__()
        else:
            db = next(db_gen)

        try:
            if date_field and hasattr(reg.model, date_field):
                yesterday = datetime.now() - timedelta(hours=24)
                recent_query = select(func.count()).select_from(reg.model).filter(
                    getattr(reg.model, date_field) >= yesterday
                )
                recent_result = await db.execute(recent_query)
                recent_count = recent_result.scalar()
            
            if attn_filter is not None:
                attn_query = select(func.count()).select_from(reg.model).filter(attn_filter)
                attn_result = await db.execute(attn_query)
                attention_count = attn_result.scalar()
        finally:
            if hasattr(db_gen, "aclose"):
                await db_gen.aclose()
            elif hasattr(db_gen, "close"):
                db_gen.close()

        return templates.TemplateResponse(
            request=request, 
            name="model_list.html", 
            context={
                "model_name": model_name, 
                "models": models,
                "recent_count": recent_count,
                "attention_count": attention_count,
                "has_date_field": bool(date_field),
                "has_attention_filter": attn_filter is not None
            }
        )

    @router.get("/{model_name}/new", response_class=HTMLResponse)
    async def model_create(request: Request, model_name: str):
        models = list(admin.registry.get_models().keys())
        return templates.TemplateResponse(
            request=request, 
            name="model_form.html", 
            context={"model_name": model_name, "id": None, "models": models}
        )

    @router.get("/{model_name}/{id}", response_class=HTMLResponse)
    async def model_edit(request: Request, model_name: str, id: str):
        models = list(admin.registry.get_models().keys())
        return templates.TemplateResponse(
            request=request, 
            name="model_form.html", 
            context={"model_name": model_name, "id": id, "models": models}
        )
    
    @router.get("/{model_name}/{id}/detail", response_class=HTMLResponse)
    async def model_detail(request: Request, model_name: str, id: str):
        models = list(admin.registry.get_models().keys())
        return templates.TemplateResponse(
            request=request, 
            name="model_detail.html", 
            context={"model_name": model_name, "id": id, "models": models}
        )

    return router
