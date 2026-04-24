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
        models = list(admin.registry.get_models().keys())
        return templates.TemplateResponse(
            request=request, 
            name="dashboard.html", 
            context={"models": models}
        )

    @router.get("/{model_name}", response_class=HTMLResponse)
    async def model_list(request: Request, model_name: str):
        return templates.TemplateResponse(
            request=request, 
            name="model_list.html", 
            context={"model_name": model_name}
        )
    
    return router
