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
        models = admin.registry.get_models()
        model_names = list(models.keys())
        
        # Collect real counts for each model
        stats = []
        for name, reg in models.items():
            # Skip if user has specified a subset of models for the dashboard
            if admin.dashboard_models and name not in admin.dashboard_models:
                continue
                
            db_gen = reg.get_db()
            db = next(db_gen)
            try:
                # 1. Get Total Count
                total_count = db.query(reg.model).count()
                
                # 2. Get 24h Count if date_field is set
                recent_count = None
                date_field = reg.config.get("date_field")
                
                if date_field and hasattr(reg.model, date_field):
                    yesterday = datetime.now() - timedelta(hours=24)
                    recent_count = db.query(reg.model).filter(
                        getattr(reg.model, date_field) >= yesterday
                    ).count()

                stats.append({
                    "name": reg.config.get("display_name") or name.capitalize(),
                    "count": total_count,
                    "recent_count": recent_count,
                    "model_name": name,
                    "has_date_field": bool(date_field)
                })
            finally:
                # Handle generators properly
                try:
                    next(db_gen)
                except StopIteration:
                    pass
                    
        # Fetch Logs
        logs = []
        if admin.get_logs:
            try:
                logs = admin.get_logs()
            except Exception as e:
                print(f"Error fetching logs: {e}")

        return templates.TemplateResponse(
            request=request, 
            name=admin.dashboard_template or "dashboard.html", 
            context={
                "models": model_names, 
                "stats": stats,
                "admin_title": admin.title,
                "logs": logs,
                "logs_config": admin.logs_config
            }
        )

    @router.get("/{model_name}", response_class=HTMLResponse)
    async def model_list(request: Request, model_name: str):
        from datetime import datetime, timedelta
        reg = admin.registry.get_model(model_name)
        if not reg:
            raise HTTPException(status_code=404, detail="Model not found")
            
        models = list(admin.registry.get_models().keys())
        
        # Calculate 24h stats for this specific model
        recent_count = None
        date_field = reg.config.get("date_field")
        
        if date_field and hasattr(reg.model, date_field):
            db_gen = reg.get_db()
            db = next(db_gen)
            try:
                yesterday = datetime.now() - timedelta(hours=24)
                recent_count = db.query(reg.model).filter(
                    getattr(reg.model, date_field) >= yesterday
                ).count()
            finally:
                try: next(db_gen)
                except StopIteration: pass
        
        # Calculate Attention count
        attention_count = None
        attn_filter = reg.config.get("attention_filter")
        if attn_filter is not None:
            db_gen = reg.get_db()
            db = next(db_gen)
            try:
                attention_count = db.query(reg.model).filter(attn_filter).count()
            finally:
                try: next(db_gen)
                except StopIteration: pass

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
