from typing import List, Optional
from pydantic import BaseModel, Field

class ModelConfig(BaseModel):
    name: str
    display_name: Optional[str] = None
    fields: List[str] = Field(default_factory=list)
    readonly_fields: List[str] = Field(default_factory=list)
    searchable_fields: List[str] = Field(default_factory=list)
    hidden_fields: List[str] = Field(default_factory=list)

    @property
    def label(self) -> str:
        return self.display_name or self.name.capitalize()
