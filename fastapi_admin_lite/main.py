from typing import Any, Dict, List, Optional, Type, Callable
from fastapi import FastAPI, APIRouter, Depends
from .core.registry import Registry
from .routers.admin import create_admin_router
from .ui.views import create_ui_router

class Admin:
    def __init__(
        self,
        title: str = "FastAPI Admin Lite",
        base_url: str = "/admin",
        enable_ui: bool = True,
        dependencies: Optional[List[Any]] = None,
        auth_dependency: Optional[Callable] = None,
        permission_checker: Optional[Callable] = None,
        dashboard_template: Optional[str] = None,
        dashboard_models: Optional[List[str]] = None,
        get_logs: Optional[Callable] = None,
        logs_config: Optional[Dict[str, Any]] = None
    ):
        self.title = title
        self.base_url = base_url
        self.enable_ui = enable_ui
        self.dependencies = dependencies or []
        self.registry = Registry()
        self.dashboard_template = dashboard_template
        self.dashboard_models = dashboard_models
        self.get_logs = get_logs
        self.logs_config = logs_config or {
            "columns": ["level", "timestamp", "message"],
            "title": "System Activity"
        }
        
        # Auth & Permissions
        self.auth_dependency = auth_dependency
        self.permission_checker = permission_checker or self.default_permission

        # Print warnings if not configured
        if not auth_dependency:
            print("\033[93m[WARNING] FastAPI Admin Lite: No auth_dependency provided. Admin panel is publicly accessible!\033[0m")
        if not permission_checker:
            print("\033[93m[WARNING] FastAPI Admin Lite: No permission_checker provided. Using default (allow all).\033[0m")

    async def default_permission(self, user: Any = None) -> bool:
        """Default permission checker that allows everything."""
        return True

    def register(
        self,
        model: Type[Any],
        get_db: Callable,
        list_display: Optional[List[str]] = None,
        date_field: Optional[str] = None,
        attention_filter: Optional[Any] = None,
        readonly_fields: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Register a model with the admin panel.
        """
        config = config or {}
        if list_display:
            # Only include fields that exist in the model
            valid_columns = {c.key for c in model.__table__.columns}
            sanitized_display = [f for f in list_display if f in valid_columns]
            config["list_display"] = sanitized_display
            
        if date_field:
            config["date_field"] = date_field
            
        if attention_filter is not None:
            config["attention_filter"] = attention_filter
            
        if readonly_fields:
            config["readonly_fields"] = readonly_fields
            
        self.registry.register(model, get_db, config)

    def mount(self, app: FastAPI):
        """
        Mount the admin router to the FastAPI application.
        """
        # Collect all dependencies
        all_deps = list(self.dependencies)
        if self.auth_dependency:
            all_deps.append(Depends(self.auth_dependency))

        router = create_admin_router(self)
        app.include_router(
            router, 
            prefix=self.base_url + "/api", 
            tags=["Admin"],
            dependencies=all_deps
        )

        if self.enable_ui:
            ui_router = create_ui_router(self)
            app.include_router(
                ui_router, 
                prefix=self.base_url, 
                include_in_schema=False,
                dependencies=all_deps
            )
