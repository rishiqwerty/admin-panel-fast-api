from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
import inspect
from fastapi.responses import RedirectResponse
import shutil
import uuid
import os
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.schema import generate_admin_schema
from ..core.crud import CRUDEngine

def create_admin_router(admin: Any) -> APIRouter:
    router = APIRouter()

    @router.get("/schema")
    async def get_schema():
        return generate_admin_schema(admin.registry)

    @router.post("/upload", name="admin_upload_file")
    async def upload_file(
        file: UploadFile = File(...),
        field_path: Optional[str] = Query(default=None, description="Subdirectory path for field-specific uploads")
    ):
        if admin.upload_handler:
            try:
                # Pass field_path to custom handler if it accepts it
                handler_sig = inspect.signature(admin.upload_handler)
                handler_params = handler_sig.parameters
                
                kwargs = {}
                if 'field_path' in handler_params:
                    kwargs['field_path'] = field_path or ''
                
                if asyncio.iscoroutinefunction(admin.upload_handler):
                    url = await admin.upload_handler(file, **kwargs)
                else:
                    url = admin.upload_handler(file, **kwargs)
                return {"url": url}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Custom upload failed: {str(e)}")
        else:
            # Build target directory
            # field_path is the complete directory path (e.g. "media/profile_images")
            # When empty, falls back to the global upload_dir
            if field_path:
                target_dir = field_path
                url_prefix = f"/{field_path}"
            else:
                target_dir = admin.upload_dir
                url_prefix = admin.upload_url
            
            if not os.path.exists(target_dir):
                os.makedirs(target_dir, exist_ok=True)
            
            ext = os.path.splitext(file.filename)[1]
            filename = f"{uuid.uuid4()}{ext}"
            filepath = os.path.join(target_dir, filename)
            
            try:
                with open(filepath, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")
                
            return {"url": f"{url_prefix}/{filename}"}

    @router.get("/media", name="admin_resolve_media")
    async def resolve_media(path: str = Query(...)):
        if not path:
            raise HTTPException(status_code=400, detail="Path parameter is required")
        try:
            if asyncio.iscoroutinefunction(admin.url_resolver):
                resolved_url = await admin.url_resolver(path)
            else:
                resolved_url = admin.url_resolver(path)
            return RedirectResponse(url=resolved_url)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to resolve media URL: {str(e)}")

    @router.get("/models")
    async def list_models():
        return list(admin.registry.get_models().keys())

    # Dynamically generate routes for each registered model
    for name, registration in admin.registry.get_models().items():
        crud = CRUDEngine(registration.model)
        get_db_dep = registration.get_db
        
        def create_routes(model_name: str, crud_engine: CRUDEngine, db_dep: Any, reg: Any):
            @router.get(f"/{model_name}", name=f"admin_list_{model_name}")
            async def list_records(
                skip: int = 0, 
                limit: int = 100, 
                search: str = None, 
                order_by: str = None,
                order_dir: str = "asc",
                db: AsyncSession = Depends(db_dep)
            ):
                records = await crud_engine.list(
                    db, skip=skip, limit=limit, search=search, 
                    order_by=order_by, order_dir=order_dir
                )
                total = await crud_engine.count(db, search=search)
                return {"data": records, "total": total}

            @router.get(f"/{model_name}/{{id}}", name=f"admin_get_{model_name}")
            async def get_record(id: Any, db: AsyncSession = Depends(db_dep)):
                record = await crud_engine.get(db, id)
                if not record:
                    raise HTTPException(status_code=404, detail="Record not found")
                return record

            @router.post(f"/{model_name}", name=f"admin_create_{model_name}")
            async def create_record(data: Dict[str, Any], db: AsyncSession = Depends(db_dep)):
                # Remove readonly fields from incoming data
                readonly = reg.config.get("readonly_fields", [])
                for field in readonly:
                    if field in data:
                        del data[field]
                return await crud_engine.create(db, data)

            @router.put(f"/{model_name}/{{id}}", name=f"admin_update_{model_name}")
            async def update_record(id: Any, data: Dict[str, Any], db: AsyncSession = Depends(db_dep)):
                # Remove readonly fields from incoming data
                readonly = reg.config.get("readonly_fields", [])
                for field in readonly:
                    if field in data:
                        del data[field]
                record = await crud_engine.update(db, id, data)
                if not record:
                    raise HTTPException(status_code=404, detail="Record not found")
                return record

            @router.delete(f"/{model_name}/{{id}}", name=f"admin_delete_{model_name}")
            async def delete_record(id: Any, db: AsyncSession = Depends(db_dep)):
                success = await crud_engine.delete(db, id)
                if not success:
                    raise HTTPException(status_code=404, detail="Record not found")
                return {"success": True}

        create_routes(name, crud, get_db_dep, registration)
        
    return router
