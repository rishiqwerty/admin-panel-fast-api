from typing import Any, Dict, List, Type
from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeMeta

def introspect_sqlalchemy_model(model: Type[Any]) -> Dict[str, Any]:
    """
    Introspect a SQLAlchemy model to extract field information.
    """
    mapper = inspect(model)
    fields = []
    for column in mapper.columns:
        fields.append({
            "name": column.key,
            "type": str(column.type),
            "primary_key": column.primary_key,
            "nullable": column.nullable,
            "default": str(column.default) if column.default else None,
            "required": not column.nullable and column.default is None and not column.primary_key
        })
    return {
        "fields": fields
    }
