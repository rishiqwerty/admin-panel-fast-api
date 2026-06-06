from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
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
    async def upload_file(file: UploadFile = File(...)):
        if admin.upload_handler:
            try:
                if asyncio.iscoroutinefunction(admin.upload_handler):
                    url = await admin.upload_handler(file)
                else:
                    url = admin.upload_handler(file)
                return {"url": url}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Custom upload failed: {str(e)}")
        else:
            if not os.path.exists(admin.upload_dir):
                os.makedirs(admin.upload_dir)
            
            ext = os.path.splitext(file.filename)[1]
            filename = f"{uuid.uuid4()}{ext}"
            filepath = os.path.join(admin.upload_dir, filename)
            
            try:
                with open(filepath, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")
                
            return {"url": f"{admin.upload_url}/{filename}"}

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
