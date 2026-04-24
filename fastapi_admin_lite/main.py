from typing import Any, Dict, List, Optional, Type, Callable
from fastapi import FastAPI, APIRouter
from .core.registry import Registry
from .routers.admin import create_admin_router
from .ui.views import create_ui_router

class Admin:
    def __init__(
        self,
        title: str = "FastAPI Admin Lite",
        base_url: str = "/admin",
        enable_ui: bool = True
    ):
        self.title = title
        self.base_url = base_url
        self.enable_ui = enable_ui
        self.registry = Registry()

    def register(
        self,
        model: Type[Any],
        get_db: Callable,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Register a model with the admin panel.
        """
        self.registry.register(model, get_db, config)

    def mount(self, app: FastAPI):
        """
        Mount the admin router to the FastAPI application.
        """
        router = create_admin_router(self)
        app.include_router(router, prefix=self.base_url, tags=["Admin"])

        if self.enable_ui:
            ui_router = create_ui_router(self)
            app.include_router(ui_router, prefix=self.base_url, include_in_schema=False)
