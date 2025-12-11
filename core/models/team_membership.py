from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID


@dataclass
class TeamMembership:
    """3.3. Team_Membership（队伍成员）"""
    team_id: UUID = field(metadata={"foreign_key": "Team", "description": "所属队伍"})
    fencer_id: UUID = field(metadata={"foreign_key": "Fencer", "description": "队员"})
    role_id: UUID = field(metadata={"foreign_key": "Team_Role", "description": "角色"})

    order_number: Optional[int] = field(default=None, metadata={"description": "出场顺序"})
    is_captain: bool = field(default=False, metadata={"description": "是否为队长"})

    # 组合主键 (team_id, fencer_id) 必须在 ORM 层面处理
