from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional


@dataclass
class User:
    id: UUID
    username: str
    email: Optional[str] = None
    role: str = "SCHEDULER"
    first_name: str = ""
    last_name: str = ""
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def is_admin(self) -> bool:
        return self.role == "ADMIN"

    @property
    def is_scheduler(self) -> bool:
        return self.role == "SCHEDULER"

    @classmethod
    def create(cls, username: str, email: Optional[str] = None, role: str = "SCHEDULER", **kwargs) -> "User":
        return cls(
            id=uuid4(), username=username, email=email, role=role, created_at=datetime.utcnow(), updated_at=datetime.utcnow(), **kwargs
        )
