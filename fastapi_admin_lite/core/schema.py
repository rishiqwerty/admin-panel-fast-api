from typing import Any, Dict, List
from .registry import Registry

def generate_admin_schema(registry: Registry) -> Dict[str, Any]:
    """
    Generate a JSON schema of all registered models for the UI.
    """
    models_info = []
    for name, reg in registry.get_models().items():
        models_info.append({
            "name": name,
            "display_name": reg.config.get("display_name") or name.capitalize(),
            "fields": reg.config.get("fields", []),
            # In a real implementation, we would introspect the model here
        })
    
    return {
        "models": models_info
    }
