from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..core.schema import generate_admin_schema
from ..core.crud import CRUDEngine

def create_admin_router(admin: Any) -> APIRouter:
    router = APIRouter()

    @router.get("/schema")
    async def get_schema():
        return generate_admin_schema(admin.registry)

    @router.get("/models")
    async def list_models():
        return list(admin.registry.get_models().keys())

    # Dynamically generate routes for each registered model
    for name, registration in admin.registry.get_models().items():
        crud = CRUDEngine(registration.model)
        
        def create_list_route(model_name: str, crud_engine: CRUDEngine, get_db_dep: Any):
            @router.get(f"/{model_name}", name=f"admin_list_{model_name}")
            async def list_records(
                skip: int = 0, 
                limit: int = 100, 
                search: str = None, 
                db: Session = Depends(get_db_dep)
            ):
                records = crud_engine.list(db, skip=skip, limit=limit, search=search)
                return {"data": records, "total": len(records)} # TODO: Fix total
            return list_records

        create_list_route(name, crud, registration.get_db)

        # TODO: Add GET, POST, PUT, DELETE routes for each model
        
    return router
