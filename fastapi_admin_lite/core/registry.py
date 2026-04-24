from typing import Any, Dict, Type, Callable, Optional
from dataclasses import dataclass, field

@dataclass
class ModelRegistration:
    model: Type[Any]
    get_db: Callable
    config: Dict[str, Any] = field(default_factory=dict)
    name: str = ""

class Registry:
    def __init__(self):
        self._models: Dict[str, ModelRegistration] = {}

    def register(
        self,
        model: Type[Any],
        get_db: Callable,
        config: Optional[Dict[str, Any]] = None
    ):
        config = config or {}
        name = config.get("name") or model.__name__.lower()
        
        if name in self._models:
            raise ValueError(f"Model with name '{name}' already registered.")
            
        registration = ModelRegistration(
            model=model,
            get_db=get_db,
            config=config,
            name=name
        )
        self._models[name] = registration

    def get_models(self) -> Dict[str, ModelRegistration]:
        return self._models

    def get_model(self, name: str) -> Optional[ModelRegistration]:
        return self._models.get(name)
