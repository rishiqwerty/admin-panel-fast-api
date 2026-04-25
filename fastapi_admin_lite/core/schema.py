from typing import Any, Dict, List
from .registry import Registry
from ..integrations.sqlalchemy import introspect_sqlalchemy_model

def generate_admin_schema(registry: Registry) -> Dict[str, Any]:
    """
    Generate a JSON schema of all registered models for the UI.
    """
    models_info = []
    for name, reg in registry.get_models().items():
        introspection = introspect_sqlalchemy_model(reg.model)
        
        clean_config = reg.config.copy()
        if "attention_filter" in clean_config:
            del clean_config["attention_filter"]

        models_info.append({
            "name": name,
            "display_name": reg.config.get("display_name") or name.capitalize(),
            "fields": introspection["fields"],
            "list_display": reg.config.get("list_display"),
            "config": clean_config
        })
    
    return {
        "models": models_info
    }
