from dataclasses import dataclass, field
from datetime import date
from typing import Optional, List


@dataclass
class Fencer:
    """
    击剑运动员核心业务对象。
    """
    # ========== 核心身份信息 ==========
    first_name: str  # 名
    last_name: str  # 姓
    country: str  # 国家 (建议使用标准国家代码，如 'CHN')
    region: Optional[str] = None  # 地区/省 (可选)
    club: Optional[str] = None  # 俱乐部 (可选)

    # ========== 个人特征信息 ==========
    date_of_birth: Optional[date] = None  # 出生日期
    gender: Optional[str] = None  # 性别 ('M', 'F', 'Other')

    # ========== 业务属性（对编排和计分至关重要）==========
    # 国际/国内排名积分
    rating: int = 0
    # 种子排位 (在具体赛事中)
    seed: Optional[int] = None
    # 所属武器种类 (可选，但建议区分：'Foil', 'Epee', 'Sabre')
    weapon: Optional[str] = None

    # ========== 唯一标识与状态 ==========
    # 内部唯一标识符 (例如数据库ID或UUID，初始化时通常为空)
    id: Optional[int] = field(default=None, compare=False)
    # 运动员状态 (如 'active', 'retired', 'suspended')
    status: str = 'active'

    # ========== 关联信息（可后期补充）==========
    # 历史参赛记录 (赛事ID列表)
    tournament_ids: List[str] = field(default_factory=list)
    # 关联的Django模型引用 (用于框架适配层)
    _django_instance: Optional[object] = field(default=None, repr=False, compare=False)

    # ========== 核心业务方法 ==========
    @property
    def full_name(self) -> str:
        """获取运动员全名（姓在前，名在后，符合中文习惯）。"""
        return f"{self.last_name} {self.first_name}"

    @property
    def age(self) -> Optional[int]:
        """根据出生日期计算年龄（截至当前日期）。"""
        if not self.date_of_birth:
            return None
        today = date.today()
        age = today.year - self.date_of_birth.year
        # 调整尚未过生日的年龄
        if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
            age -= 1
        return age

    @property
    def age_group(self) -> Optional[str]:
        """根据年龄计算所属组别（例如 U14, U16, Cadet, Junior, Senior）。"""
        # 这是一个业务规则示例，具体规则可根据击剑联合会规定实现
        age = self.age
        if age is None:
            return None
        if age < 14:
            return "U14"
        elif age < 16:
            return "U16"
        elif age < 18:
            return "Cadet"
        elif age < 20:
            return "Junior"
        else:
            return "Senior"

    def is_eligible_for_tournament(self, min_age: int, max_age: int, allowed_weapons: List[str]) -> bool:
        """
        检查运动员是否有资格参加特定赛事。
        这是一个核心业务逻辑方法的示例。
        """
        if self.status != 'active':
            return False
        current_age = self.age
        if current_age is None or not (min_age <= current_age <= max_age):
            return False
        if allowed_weapons and self.weapon not in allowed_weapons:
            return False
        return True

    def promote_seed(self, positions: int = 1) -> None:
        """提升种子排位（例如因其他选手退赛）。"""
        if self.seed is not None:
            self.seed = max(1, self.seed - positions)  # 种子数字越小，排位越高

    def update_rating(self, points: int) -> None:
        """更新运动员积分（正数为加分，负数为减分）。"""
        self.rating += points

    # 在 Fencer 类定义内部添加
    def to_core(self) -> 'core.models.Fencer':
        """将 Django 模型实例转换为核心业务对象。"""
        from core.models import Fencer as CoreFencer
        from datetime import date

        return CoreFencer(
            id=self.id,
            first_name=self.first_name,
            last_name=self.last_name,
            country=self.country,
            region=self.region,
            club=self.club,
            date_of_birth=self.date_of_birth,
            gender=self.gender if self.gender != 'N' else None,
            weapon=self.weapon if self.weapon else None,
            rating=self.rating,
            seed=self.seed,
            status=self.status,
            # 注意：无法在此直接传递 _django_instance，会造成循环导入
        )

    @classmethod
    def from_core(cls, core_fencer: 'core.models.Fencer', save=False):
        """从核心业务对象创建或更新 Django 模型实例。"""
        # 如果核心对象有ID，尝试查找现有记录
        if core_fencer.id is not None:
            instance = cls.objects.filter(id=core_fencer.id).first()
        else:
            instance = None

        # 如果找不到，创建新实例
        if instance is None:
            instance = cls()
            if core_fencer.id is not None:
                instance.id = core_fencer.id  # 注意：直接设置ID需谨慎

        # 更新字段
        instance.first_name = core_fencer.first_name
        instance.last_name = core_fencer.last_name
        instance.country = core_fencer.country
        instance.region = core_fencer.region
        instance.club = core_fencer.club
        instance.date_of_birth = core_fencer.date_of_birth
        instance.gender = core_fencer.gender if core_fencer.gender else 'N'
        instance.weapon = core_fencer.weapon if core_fencer.weapon else ''
        instance.rating = core_fencer.rating
        instance.seed = core_fencer.seed
        instance.status = core_fencer.status

        # 保存（如果要求）
        if save:
            instance.save()
            # 保存后，将生成的ID同步回核心对象
            core_fencer.id = instance.id

        return instance
