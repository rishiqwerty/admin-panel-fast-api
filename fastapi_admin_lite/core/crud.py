from typing import Any, List, Optional, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, Boolean, Integer, Float


class CRUDEngine:
    def __init__(self, model: Type[Any]):
        self.model = model

    def _prepare_data(self, data: dict) -> dict:
        """
        Cast string values from form data to correct types based on SQLAlchemy model.
        """
        prepared = {}
        columns = self.model.__table__.columns
        
        for key, value in data.items():
            if key not in columns:
                continue
            
            col = columns[key]
            
            if isinstance(col.type, Boolean):
                if isinstance(value, str):
                    prepared[key] = value.lower() in ('true', '1', 'yes', 'on')
                else:
                    prepared[key] = bool(value)
            elif isinstance(col.type, Integer):
                try:
                    prepared[key] = int(value)
                except (ValueError, TypeError):
                    prepared[key] = value
            elif isinstance(col.type, Float):
                try:
                    prepared[key] = float(value)
                except (ValueError, TypeError):
                    prepared[key] = value
            else:
                prepared[key] = value
        
        return prepared

    async def count(self, db: AsyncSession, search: Optional[str] = None) -> int:
        query = select(func.count()).select_from(self.model)
        if search:
            for column in self.model.__table__.columns:
                if hasattr(column.type, "python_type") and column.type.python_type == str:
                    query = query.filter(column.contains(search))
                    break
        result = await db.execute(query)
        return result.scalar()

    async def list(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100, 
        search: Optional[str] = None,
        order_by: Optional[str] = None,
        order_dir: str = "asc"
    ) -> List[Any]:
        query = select(self.model).offset(skip).limit(limit)
        
        # Apply Search
        if search:
            for column in self.model.__table__.columns:
                if hasattr(column.type, "python_type") and column.type.python_type == str:
                    query = query.filter(column.contains(search))
                    break
            
        # Apply Sorting
        if order_by and hasattr(self.model, order_by):
            column = getattr(self.model, order_by)
            if order_dir.lower() == "desc":
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column.asc())
        
        result = await db.execute(query)
        return result.scalars().all()

    async def get(self, db: AsyncSession, id: Any) -> Optional[Any]:
        return await db.get(self.model, id)

    async def create(self, db: AsyncSession, data: dict) -> Any:
        prepared_data = self._prepare_data(data)
        obj = self.model(**prepared_data)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    async def update(self, db: AsyncSession, id: Any, data: dict) -> Optional[Any]:
        obj = await self.get(db, id)
        if not obj:
            return None
        
        prepared_data = self._prepare_data(data)
        for key, value in prepared_data.items():
            setattr(obj, key, value)
        await db.commit()
        await db.refresh(obj)
        return obj

    async def delete(self, db: AsyncSession, id: Any) -> bool:
        obj = await self.get(db, id)
        if not obj:
            return False
        await db.delete(obj)
        await db.commit()
        return True
