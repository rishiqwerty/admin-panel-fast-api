from typing import Any, Dict, List, Optional, Type, Callable, Union
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
        logs_config: Optional[Dict[str, Any]] = None,
        upload_dir: str = "uploads",
        upload_url: str = "/uploads",
        upload_handler: Optional[Callable[[Any], Any]] = None,
        url_resolver: Optional[Callable[[str], Any]] = None
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
        self.upload_dir = upload_dir
        self.upload_url = upload_url
        self.upload_handler = upload_handler
        
        # Auth & Permissions
        self.auth_dependency = auth_dependency
        self.permission_checker = permission_checker or self.default_permission
        
        # Media resolver
        self.url_resolver = url_resolver or self.default_url_resolver

        # Print warnings if not configured
        if not auth_dependency:
            print("\033[93m[WARNING] FastAPI Admin Lite: No auth_dependency provided. Admin panel is publicly accessible!\033[0m")
        if not permission_checker:
            print("\033[93m[WARNING] FastAPI Admin Lite: No permission_checker provided. Using default (allow all).\033[0m")

    async def default_permission(self, user: Any = None) -> bool:
        """Default permission checker that allows everything."""
        return True

    def default_url_resolver(self, path: str) -> str:
        """Default URL resolver that resolves relative paths to the local static uploads URL."""
        if not path:
            return ""
        if path.startswith("http://") or path.startswith("https://") or path.startswith("data:"):
            return path
        
        clean_path = path.lstrip("/")
        clean_prefix = self.upload_url.strip("/")
        
        if clean_path.startswith(clean_prefix):
            return f"/{clean_path}"
            
        return f"{self.upload_url}/{clean_path}"

    def register(
        self,
        model: Type[Any],
        get_db: Callable,
        list_display: Optional[List[str]] = None,
        date_field: Optional[str] = None,
        attention_filter: Optional[Any] = None,
        readonly_fields: Optional[List[str]] = None,
        file_fields: Optional[Union[List[str], Dict[str, str]]] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Register a model with the admin panel.
        
        Args:
            file_fields: Fields that accept file uploads. Can be:
                - A list of field names (uploads go to the root upload_dir)
                - A dict mapping field names to subdirectory paths
                  e.g. {"profile_image": "profile_images", "cover_image": "cover_images"}
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

        if file_fields:
            # Normalize: list → dict with empty string values (root upload dir)
            if isinstance(file_fields, list):
                config["file_fields"] = {field: "" for field in file_fields}
            else:
                config["file_fields"] = file_fields
            
        self.registry.register(model, get_db, config)

    def mount(self, app: FastAPI):
        """
        Mount the admin router to the FastAPI application.
        """
        # Mount upload directory for static access if using default storage
        if not self.upload_handler:
            import os
            from fastapi.staticfiles import StaticFiles
            if not os.path.exists(self.upload_dir):
                os.makedirs(self.upload_dir)
            app.mount(self.upload_url, StaticFiles(directory=self.upload_dir), name="admin_uploads")
            
            # Auto-mount unique base directories from file_fields configs
            # e.g. file_fields={"profile_image": "media/profile_images"} → mount "media" at "/media"
            mounted_dirs = {os.path.abspath(self.upload_dir)}
            for name, reg in self.registry.get_models().items():
                file_fields = reg.config.get("file_fields", {})
                for field_name, field_path in file_fields.items():
                    if not field_path:
                        continue
                    # Extract the root directory (first path component)
                    base_dir = field_path.split("/")[0]
                    abs_base = os.path.abspath(base_dir)
                    if abs_base not in mounted_dirs:
                        if not os.path.exists(base_dir):
                            os.makedirs(base_dir, exist_ok=True)
                        app.mount(f"/{base_dir}", StaticFiles(directory=base_dir), name=f"admin_uploads_{base_dir}")
                        mounted_dirs.add(abs_base)

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
