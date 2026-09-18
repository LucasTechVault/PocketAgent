"""Shared base model for PocketAgent runtime contracts.

M01 purpose:
--------------
Provides consistent validation semantics for typed contracts that form the boundaries between runtime components.

Grand scheme:
--------------
- ModelGateway
- Tool Runtime
- Control Loop
- Persistence Layer
- Observability System

will eventually exchange these models.
"""

from pydantic import BaseModel, ConfigDict

class ContractModel(BaseModel):
    """Base class for PocketAgent runtime contracts."""
    
    model_config = ConfigDict(
        extra="forbid", # prevents hallucinated key-value
        validate_assignment=True
    )