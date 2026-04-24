from typing import Any, List, Optional, Type
from sqlalchemy.orm import Session

class CRUDEngine:
    def __init__(self, model: Type[Any]):
        self.model = model

    def list(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100, 
        search: Optional[str] = None
    ) -> List[Any]:
        query = db.query(self.model)
        # TODO: Implement search logic
        return query.offset(skip).limit(limit).all()

    def get(self, db: Session, id: Any) -> Optional[Any]:
        return db.query(self.model).filter(self.model.id == id).first()

    def create(self, db: Session, data: dict) -> Any:
        obj = self.model(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update(self, db: Session, id: Any, data: dict) -> Optional[Any]:
        obj = self.get(db, id)
        if not obj:
            return None
        for key, value in data.items():
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
