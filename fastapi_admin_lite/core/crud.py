from typing import Any, List, Optional, Type
from sqlalchemy.orm import Session
from sqlalchemy import Boolean, Integer, Float

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

    def count(self, db: Session, search: Optional[str] = None) -> int:
        query = db.query(self.model)
        # TODO: Implement search filtering in count
        return query.count()

    def list(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100, 
        search: Optional[str] = None,
        order_by: Optional[str] = None,
        order_dir: str = "asc"
    ) -> List[Any]:
        query = db.query(self.model)
        
        # Apply Search
        if search:
            # TODO: Implement generic search logic
            pass
            
        # Apply Sorting
        if order_by and hasattr(self.model, order_by):
            column = getattr(self.model, order_by)
            if order_dir.lower() == "desc":
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column.asc())
        
        return query.offset(skip).limit(limit).all()

    def _cast_id(self, id: Any) -> Any:
        """
        Cast ID to the correct type based on the model's primary key.
        """
        col = self.model.__table__.primary_key.columns[0]
        if isinstance(col.type, Integer):
            try:
                return int(id)
            except (ValueError, TypeError):
                return id
        return id

    def get(self, db: Session, id: Any) -> Optional[Any]:
        casted_id = self._cast_id(id)
        return db.query(self.model).filter(self.model.id == casted_id).first()

    def create(self, db: Session, data: dict) -> Any:
        prepared_data = self._prepare_data(data)
        obj = self.model(**prepared_data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update(self, db: Session, id: Any, data: dict) -> Optional[Any]:
        obj = self.get(db, id)
        if not obj:
            return None
        
        prepared_data = self._prepare_data(data)
        for key, value in prepared_data.items():
            setattr(obj, key, value)
        db.commit()
        db.refresh(obj)
        return obj

    def delete(self, db: Session, id: Any) -> bool:
        obj = self.get(db, id)
        if not obj:
            return False
        db.delete(obj)
        db.commit()
        return True
