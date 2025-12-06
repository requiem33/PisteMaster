from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Fencer(models.Model):
    """Django 数据库模型，对应 core.models.Fencer 核心业务对象。"""
    # ========== 核心身份信息 ==========
    first_name = models.CharField(max_length=50, verbose_name='名')
    last_name = models.CharField(max_length=50, verbose_name='姓')
    country = models.CharField(max_length=3, default='CHN', verbose_name='国家/地区代码')
    region = models.CharField(max_length=100, blank=True, null=True, verbose_name='地区/省份')
    club = models.CharField(max_length=150, blank=True, null=True, verbose_name='俱乐部')

    # ========== 个人特征信息 ==========
    date_of_birth = models.DateField(blank=True, null=True, verbose_name='出生日期')

    # 性别选择，使用明确选项
    class Gender(models.TextChoices):
        MALE = 'M', '男'
        FEMALE = 'F', '女'
        OTHER = 'O', '其他'
        NOT_SPECIFIED = 'N', '未指定'

    gender = models.CharField(
        max_length=1,
        choices=Gender.choices,
        default=Gender.NOT_SPECIFIED,
        verbose_name='性别'
    )

    # ========== 业务属性 ==========
    # 武器种类选择
    class WeaponType(models.TextChoices):
        FOIL = 'Foil', '花剑'
        EPEE = 'Epee', '重剑'
        SABRE = 'Sabre', '佩剑'
        UNSPECIFIED = '', '未指定'

    weapon = models.CharField(
        max_length=10,
        choices=WeaponType.choices,
        blank=True,
        default=WeaponType.UNSPECIFIED,
        verbose_name='主项武器'
    )

    rating = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='积分'
    )

    seed = models.PositiveIntegerField(blank=True, null=True, verbose_name='种子排位')

    # ========== 状态与元数据 ==========
    # 状态选择
    class Status(models.TextChoices):
        ACTIVE = 'active', '活跃'
        RETIRED = 'retired', '退役'
        SUSPENDED = 'suspended', '禁赛'
        INJURED = 'injured', '伤病'

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name='状态'
    )

    # 系统字段
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    # 唯一关联引用 (可选，用于快速反向查找)
    core_object_hash = models.CharField(max_length=64, blank=True, editable=False)

    class Meta:
        verbose_name = '击剑运动员'
        verbose_name_plural = '击剑运动员'
        # 姓名+国家可能作为简易唯一约束，实际项目可能需要更严谨方案
        unique_together = [['first_name', 'last_name', 'country']]
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.last_name} {self.first_name} ({self.country})'

    @property
    def full_name(self):
        """获取全名，与 core.Fencer 保持一致。"""
        return f'{self.last_name} {self.first_name}'

    @property
    def age(self):
        """计算年龄，与 core.Fencer 逻辑一致。"""
        if not self.date_of_birth:
            return None
        from datetime import date
        today = date.today()
        age = today.year - self.date_of_birth.year
        if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
            age -= 1
        return age

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


class CompetitionRules(models.Model):
    """
    比赛规则配置模型。
    对应 core.models.competition.CompetitionRules 核心类。
    """
    # ========== 基础信息 ==========
    name = models.CharField(
        max_length=100,
        verbose_name='规则名称',
        help_text='例如：国际剑联标准规则、青少年特殊规则'
    )

    # 武器类型选择（映射 core.enums.WeaponType）
    class WeaponType(models.TextChoices):
        FOIL = 'foil', '花剑'
        EPEE = 'epee', '重剑'
        SABRE = 'sabre', '佩剑'

    weapon_type = models.CharField(
        max_length=10,
        choices=WeaponType.choices,
        verbose_name='适用武器'
    )

    is_default = models.BooleanField(
        default=False,
        verbose_name='是否为默认规则',
        help_text='设为默认后，创建新比赛项目时会优先推荐此规则'
    )

    # ========== 规则配置存储方案 ==========
    # 【方案一：推荐】使用 JSONField (Django 4.2+ 内置，强大灵活)
    config = models.JSONField(
        default=dict,  # 默认值为空字典
        verbose_name='规则配置(JSON)',
        help_text='存储规则的各项可配置参数'
    )

    # 【方案二：备用】使用 TextField 存储 JSON 字符串（兼容性更好）
    # config_json = models.TextField(
    #     default='{}',  # 默认空JSON对象
    #     verbose_name='规则配置(JSON字符串)',
    #     help_text='请勿直接修改，应通过程序读写'
    # )
    #
    # @property
    # def config(self):
    #     """将 JSON 字符串转为 Python 字典"""
    #     import json
    #     try:
    #         return json.loads(self.config_json)
    #     except json.JSONDecodeError:
    #         return {}
    #
    # @config.setter
    # def config(self, value):
    #     """将 Python 字典转为 JSON 字符串存储"""
    #     import json
    #     self.config_json = json.dumps(value, ensure_ascii=False)

    # ========== 系统字段 ==========
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    created_by = models.ForeignKey(
        'auth.User',  # 关联 Django 内置用户模型
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='创建者'
    )

    class Meta:
        verbose_name = '比赛规则'
        verbose_name_plural = '比赛规则'
        # 同一武器类型下规则名称应唯一
        unique_together = ['weapon_type', 'name']
        ordering = ['weapon_type', '-is_default', 'name']
        indexes = [
            models.Index(fields=['weapon_type', 'is_default']),
        ]

    def __str__(self):
        default_flag = '（默认）' if self.is_default else ''
        return f'{self.get_weapon_type_display()}{self.name}{default_flag}'

    # ========== 业务逻辑方法 ==========
    def get_pool_settings(self):
        """便捷方法：获取小组赛设置"""
        return {
            'pool_size': self.config.get('pool_size', 7),
            'promotion_count': self.config.get('promotion_count', 4)
        }

    def update_config(self, key, value):
        """安全更新配置项"""
        current_config = self.config.copy()
        current_config[key] = value
        self.config = current_config
        # 注意：需要调用 save() 才会存入数据库

    def validate_rule(self) -> bool:
        """验证规则配置是否有效（示例）"""
        required_keys = ['pool_size', 'required_hits']
        return all(key in self.config for key in required_keys)

    @classmethod
    def get_default_for_weapon(cls, weapon_type: str):
        """类方法：获取某武器的默认规则（对应core层方法）"""
        try:
            return cls.objects.filter(
                weapon_type=weapon_type,
                is_default=True
            ).first()
        except cls.DoesNotExist:
            return None

    # ========== 与core模型的转换方法 ==========
    def to_core(self) -> 'core.models.competition.CompetitionRules':
        """转换为核心业务对象"""
        from core.models.competition import CompetitionRules as CoreRules
        from core.models.enums import WeaponType as CoreWeaponType

        # 将字符串转换为 core 层的 Enum
        weapon_enum = CoreWeaponType(self.weapon_type)

        # 创建core对象 - 注意：不传递 id 参数
        return CoreRules(
            name=self.name,
            weapon_type=weapon_enum,
            is_default=self.is_default,
            config=self.config  # JSONField 直接返回字典
        )

    @classmethod
    def from_core(cls, core_rules, save=False):
        """从核心业务对象创建或更新 Django 模型"""
        # 查找或创建实例
        instance, created = cls.objects.get_or_create(
            id=core_rules.id,
            defaults={
                'name': core_rules.name,
                'weapon_type': core_rules.weapon_type.value,
                'is_default': core_rules.is_default,
                'config': core_rules.config
            }
        )

        # 如果不是新建，则更新字段
        if not created:
            instance.name = core_rules.name
            instance.weapon_type = core_rules.weapon_type.value
            instance.is_default = core_rules.is_default
            instance.config = core_rules.config

            if save:
                instance.save()

        return instance


# backend/apps/api/models.py - 在 CompetitionRules 模型下方添加
class CompetitionItem(models.Model):
    """
    比赛单项模型。
    对应 core.models.competition.CompetitionItem。
    例如：'男子花剑个人（成年组）'
    """
    # ========== 基础信息 ==========
    name = models.CharField(
        max_length=200,
        verbose_name='单项名称',
        help_text='例如：男子花剑个人（成年组）'
    )

    # 武器类型选择（复用 CompetitionRules 中的枚举，确保一致）
    weapon_type = models.CharField(
        max_length=10,
        choices=CompetitionRules.WeaponType.choices,
        verbose_name='武器类型'
    )

    # 性别分组
    class GenderCategory(models.TextChoices):
        MEN = 'men', '男子'
        WOMEN = 'women', '女子'
        MIXED = 'mixed', '混合'
        OPEN = 'open', '公开组'

    gender_category = models.CharField(
        max_length=10,
        choices=GenderCategory.choices,
        verbose_name='性别分组'
    )

    # 年龄组别
    class AgeGroup(models.TextChoices):
        U14 = 'u14', 'U14'
        U16 = 'u16', 'U16'
        CADET = 'cadet', '青年组 (U18)'
        JUNIOR = 'junior', '少年组 (U20)'
        SENIOR = 'senior', '成年组'
        VETERAN = 'veteran', '老将组'

    age_group = models.CharField(
        max_length=10,
        choices=AgeGroup.choices,
        verbose_name='年龄组别'
    )

    # ========== 核心关联 ==========
    # 【关键关联1】每个单项必须使用一套规则
    rules = models.ForeignKey(
        CompetitionRules,
        on_delete=models.PROTECT,  # 防止误删关联的规则
        related_name='competition_items',
        verbose_name='比赛规则'
    )

    # 【关键关联2】一个单项属于一个赛事单元 (TournamentEvent)
    event = models.ForeignKey(
        'TournamentEvent',  # 【关键修改】使用字符串引用，而不是直接类名
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='所属赛事单元',
        null=True,  # 暂时允许为空
        blank=True
    )

    # 【关键关联3】参赛选手（个人赛）
    participants = models.ManyToManyField(
        Fencer,
        related_name='individual_competitions',
        blank=True,
        verbose_name='参赛选手',
        help_text='个人赛的参赛选手'
    )

    # 【预留关联4】参赛队伍（团体赛）- 未来扩展
    # teams = models.ManyToManyField(
    #     'Team',  # 未来的Team模型
    #     related_name='team_competitions',
    #     blank=True,
    #     verbose_name='参赛队伍'
    # )

    # ========== 状态与元数据 ==========
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', '草稿'),
            ('open', '报名中'),
            ('closed', '报名截止'),
            ('ongoing', '进行中'),
            ('completed', '已结束')
        ],
        default='draft',
        verbose_name='单项状态'
    )

    max_participants = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='最大报名人数',
        help_text='留空表示不限制'
    )

    current_participants = models.PositiveIntegerField(
        default=0,
        editable=False,  # 该字段由程序自动维护，不在后台直接修改
        verbose_name='当前报名人数'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '比赛单项'
        verbose_name_plural = '比赛单项'
        # 同一赛事单元下，单项名称应唯一
        # unique_together = ['event', 'name']  # 待event字段启用后取消注释
        ordering = ['weapon_type', 'gender_category', 'age_group']
        indexes = [
            models.Index(fields=['weapon_type', 'gender_category', 'status']),
            # models.Index(fields=['event', 'status']),  # 待event字段启用后取消注释
        ]

    def __str__(self):
        return f'{self.name} ({self.get_status_display()})'

    # ========== 业务逻辑方法 ==========
    @property
    def is_individual(self) -> bool:
        """判断是否为个人赛（目前版本均为个人赛）"""
        return True  # 当前版本只支持个人赛

    @property
    def is_full(self) -> bool:
        """检查报名是否已满"""
        if self.max_participants is None:
            return False
        return self.current_participants >= self.max_participants

    def can_add_participant(self, fencer: Fencer) -> tuple[bool, str]:
        """
        检查是否可以添加选手，返回(是否允许, 原因)。
        集中业务规则验证逻辑。
        """
        if self.status != 'open':
            return False, '当前不在报名期'
        if self.is_full:
            return False, '报名人数已满'
        if self.participants.filter(id=fencer.id).exists():
            return False, '选手已报名'
        # 未来可添加更多规则：如年龄、性别、武器类型匹配等
        return True, ''

    def add_participant(self, fencer: Fencer) -> bool:
        """添加选手到本单项（包含业务规则验证）"""
        can_add, reason = self.can_add_participant(fencer)
        if not can_add:
            # 在实际应用中，可以记录日志或抛出特定异常
            return False

        self.participants.add(fencer)
        self.current_participants = self.participants.count()
        self.save(update_fields=['current_participants'])
        return True

    def remove_participant(self, fencer: Fencer) -> bool:
        """从本单项移除选手"""
        if self.participants.filter(id=fencer.id).exists():
            self.participants.remove(fencer)
            self.current_participants = self.participants.count()
            self.save(update_fields=['current_participants'])
            return True
        return False

    def get_participant_ids(self) -> list[int]:
        """获取所有参赛选手ID列表（对应core层接口）"""
        return list(self.participants.values_list('id', flat=True))

    # ========== 与core模型的转换方法 ==========
    def to_core(self) -> 'core.models.competition.CompetitionItem':
        """转换为核心业务对象时，正确传递状态枚举"""
        from core.models.competition import CompetitionItem as CoreItem
        from core.models.enums import WeaponType, GenderCategory, AgeGroup
        from core.models.competition import CompetitionStatus as CoreStatus

        # 转换所有Enum字段
        weapon_enum = WeaponType(self.weapon_type)
        gender_enum = GenderCategory(self.gender_category)
        age_enum = AgeGroup(self.age_group)
        status_enum = CoreStatus(self.status)  # 字符串 → 核心层枚举

        return CoreItem(
            name=self.name,
            weapon_type=weapon_enum,
            gender_category=gender_enum,
            age_group=age_enum,
            rules=self.rules.to_core(),
            status=status_enum,  # 传递枚举，而非字符串
            participant_ids=self.get_participant_ids(),
        )

    def change_status(self, new_status_value: str) -> tuple[bool, str]:
        """
        Django层的方法：变更状态。
        委托给core对象执行业务逻辑，然后同步回数据库。
        """
        # 1. 转换为core对象
        core_item = self.to_core()

        # 2. 获取目标状态枚举
        from core.models.competition import CompetitionStatus as CoreStatus
        try:
            new_status_enum = CoreStatus(new_status_value)
        except ValueError:
            return False, f"无效的状态值: {new_status_value}"

        # 3. 调用核心层业务逻辑
        success = core_item.change_status(new_status_enum)
        if not success:
            return False, "状态变更被业务规则拒绝"

        # 4. 同步回Django模型
        self.status = core_item.status.value  # 枚举 → 字符串
        self.save(update_fields=['status'])
        return True, "状态变更成功"

    # 修改 can_add_participant 方法，也委托给core层
    def can_add_participant(self, fencer: Fencer) -> tuple[bool, str]:
        """Django层：检查是否可以添加选手"""
        core_item = self.to_core()
        return core_item.can_add_participant(fencer.id)

    @classmethod
    def from_core(cls, core_item, save=False):
        """从核心业务对象创建或更新 Django 模型"""
        # 注意：此方法需要 core_item.rules 已有对应的Django实例
        # 查找或创建实例
        instance, created = cls.objects.get_or_create(
            id=core_item.id,
            defaults={
                'name': core_item.name,
                'weapon_type': core_item.weapon_type.value,
                'gender_category': core_item.gender_category.value,
                'age_group': core_item.age_group.value,
                'rules_id': core_item.rules.id if core_item.rules.id else None,
                # 'event_id': ...  # 需要core_item提供event_id
            }
        )

        if not created and save:
            instance.name = core_item.name
            # ... 更新其他字段
            instance.save()

        # 同步参赛选手（比较ID列表差异，增量更新）
        if save:
            current_ids = set(instance.get_participant_ids())
            new_ids = set(core_item.participant_ids)

            # 添加新的
            to_add = new_ids - current_ids
            if to_add:
                instance.participants.add(*to_add)

            # 移除旧的
            to_remove = current_ids - new_ids
            if to_remove:
                instance.participants.remove(*to_add)

            instance.current_participants = instance.participants.count()
            instance.save(update_fields=['current_participants'])

        return instance


# backend/apps/api/models.py - 在 CompetitionItem 模型下方添加
class TournamentEvent(models.Model):
    """
    赛事单元模型。
    对应 core.models.competition.TournamentEvent。
    例如：'个人赛'、'团体赛'。
    """
    # ========== 基础信息 ==========
    name = models.CharField(
        max_length=100,
        verbose_name='单元名称',
        help_text='例如：个人赛、团体赛、U14组比赛'
    )

    # 事件类型
    class EventType(models.TextChoices):
        INDIVIDUAL = 'individual', '个人赛'
        TEAM = 'team', '团体赛'

    event_type = models.CharField(
        max_length=20,
        choices=EventType.choices,
        verbose_name='赛事类型'
    )

    description = models.TextField(
        blank=True,
        verbose_name='单元描述',
        help_text='可选的详细说明'
    )

    # ========== 核心关联 ==========
    # 【关键关联1】一个赛事单元属于一个主赛事
    tournament = models.ForeignKey(
        'Tournament',  # 使用字符串引用，Tournament模型稍后创建
        on_delete=models.CASCADE,
        related_name='events',
        verbose_name='所属主赛事'
    )

    # 【关键关联2】一个赛事单元包含多个比赛单项
    # 通过 CompetitionItem 模型中的反向关联实现
    # items = 反向关联，由 CompetitionItem.event 定义

    # ========== 顺序与调度 ==========
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='显示顺序',
        help_text='数字越小排序越靠前'
    )

    start_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='单元开始日期',
        help_text='留空则使用主赛事的开始日期'
    )

    end_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='单元结束日期',
        help_text='留空则使用主赛事的结束日期'
    )

    # ========== 状态与元数据 ==========
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', '草稿'),
            ('published', '已发布'),
            ('ongoing', '进行中'),
            ('completed', '已结束'),
            ('cancelled', '已取消')
        ],
        default='draft',
        verbose_name='单元状态'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '赛事单元'
        verbose_name_plural = '赛事单元'
        # 同一赛事下，单元名称应唯一（考虑到可能有多个'个人赛'但类型不同）
        unique_together = ['tournament', 'name', 'event_type']
        ordering = ['tournament', 'order', 'start_date']
        indexes = [
            models.Index(fields=['tournament', 'status']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self):
        return f'{self.tournament.name} - {self.name}' if hasattr(self, 'tournament') else self.name

    # ========== 便捷属性与方法 ==========
    @property
    def actual_start_date(self):
        """获取实际开始日期（优先使用单元日期，否则用赛事日期）"""
        return self.start_date or (self.tournament.start_date if self.tournament else None)

    @property
    def actual_end_date(self):
        """获取实际结束日期"""
        return self.end_date or (self.tournament.end_date if self.tournament else None)

    @property
    def duration_days(self):
        """计算单元持续天数"""
        start = self.actual_start_date
        end = self.actual_end_date
        if start and end:
            return (end - start).days + 1
        return 0

    def get_items_by_status(self, status: str = None):
        """获取本单元下的比赛单项（可筛选状态）"""
        # 使用反向关联查询
        items = self.items.all()  # 依赖于 CompetitionItem.event 的反向关联名称
        if status:
            items = items.filter(status=status)
        return items

    def get_participant_count(self) -> int:
        """获取本单元所有单项的总参赛选手数（去重）"""
        from django.db.models import Count
        # 通过 CompetitionItem 的 participants 多对多关系统计
        return self.items.aggregate(
            total_participants=Count('participants', distinct=True)
        )['total_participants'] or 0

    # ========== 与core模型的转换方法 ==========
    def to_core(self) -> 'core.models.competition.TournamentEvent':
        """转换为核心业务对象"""
        from core.models.competition import TournamentEvent as CoreEvent
        from core.models.enums import EventType as CoreEventType

        # 转换Enum字段
        event_type_enum = CoreEventType(self.event_type)

        # 获取关联的单项核心对象列表
        core_items = [item.to_core() for item in self.items.all()]

        return CoreEvent(
            name=self.name,
            type=event_type_enum,
            items=core_items
        )

    @classmethod
    def from_core(cls, core_event, tournament_id=None, save=False):
        """
        从核心业务对象创建或更新 Django 模型。
        注意：需要 tournament_id 来关联主赛事。
        """
        # 查找或创建实例（需要唯一性约束字段）
        # 注意：core_event 没有id，我们使用业务字段匹配
        defaults = {
            'event_type': core_event.type.value,
            'description': '',
            'tournament_id': tournament_id,  # 必须提供
        }

        instance, created = cls.objects.get_or_create(
            tournament_id=tournament_id,
            name=core_event.name,
            event_type=core_event.type.value,
            defaults=defaults
        )

        if not created:
            # 更新基本信息
            instance.description = defaults['description']
            # 其他字段...

        # 处理关联的单项
        if save:
            instance.save()
            # 清空现有关联，重新建立（根据需求调整此策略）
            instance.items.clear()
            for core_item in core_event.items:
                # 为每个core_item找到或创建对应的Django模型
                # 注意：这里需要 CompetitionItem.from_core 能处理无event_id的情况
                item_instance = CompetitionItem.from_core(core_item, save=False)
                item_instance.event = instance
                item_instance.save()

        return instance


# backend/apps/api/models.py - 在文件末尾添加
class Tournament(models.Model):
    """
    主赛事模型。
    对应 core.models.tournament.Tournament。
    是整个赛事结构的根容器。
    """
    # ========== 基础信息 ==========
    name = models.CharField(
        max_length=200,
        verbose_name='赛事名称',
        help_text='例如：2025年全国击剑锦标赛'
    )

    # 使用与core层一致的枚举
    class TournamentStatus(models.TextChoices):
        DRAFT = 'draft', '草稿'
        PUBLISHED = 'published', '已发布'
        REGISTRATION_CLOSED = 'registration_closed', '报名截止'
        ONGOING = 'ongoing', '进行中'
        COMPLETED = 'completed', '已结束'
        CANCELLED = 'cancelled', '已取消'

    status = models.CharField(
        max_length=30,
        choices=TournamentStatus.choices,
        default=TournamentStatus.DRAFT,
        verbose_name='赛事状态'
    )

    start_date = models.DateField(verbose_name='开始日期')
    end_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='结束日期',
        help_text='留空则表示单日赛事'
    )

    location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='举办地点'
    )

    description = models.TextField(blank=True, verbose_name='赛事描述')

    # ========== 配置规则 ==========
    default_weapon_type = models.CharField(
        max_length=10,
        choices=CompetitionRules.WeaponType.choices,  # 复用规则中的枚举
        blank=True,
        verbose_name='默认武器类型',
        help_text='为赛事中的所有单项设置默认武器类型（可覆盖）'
    )

    # ========== 系统字段 ==========
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='创建者'
    )

    class Meta:
        verbose_name = '主赛事'
        verbose_name_plural = '主赛事'
        ordering = ['-start_date', 'name']
        indexes = [
            models.Index(fields=['status', 'start_date']),
            models.Index(fields=['location']),
        ]

    def __str__(self):
        return f'{self.name} ({self.get_status_display()})'

    # ========== 便捷属性和方法 ==========
    @property
    def duration_days(self) -> int:
        """计算赛事持续天数"""
        if not self.start_date:
            return 0
        end = self.end_date or self.start_date
        return (end - self.start_date).days + 1

    @property
    def event_count(self) -> int:
        """获取包含的赛事单元数量"""
        return self.events.count()  # 使用 TournamentEvent.tournament 的反向关联

    @property
    def competition_item_count(self) -> int:
        """获取所有比赛单项的总数"""
        from django.db.models import Count
        return self.events.aggregate(
            total_items=Count('items', distinct=True)  # 通过 TournamentEvent.items 反向关联
        )['total_items'] or 0

    @property
    def participant_count(self) -> int:
        """获取所有参赛选手总数（去重）"""
        # 通过 TournamentEvent → CompetitionItem → participants 多级关联查询
        from django.db.models import Count
        return self.events.aggregate(
            total_participants=Count('items__participants', distinct=True)
        )['total_participants'] or 0

    def get_events_by_type(self, event_type: str):
        """按类型筛选赛事单元"""
        return self.events.filter(event_type=event_type)

    def publish(self) -> bool:
        """发布赛事（状态变更为已发布）"""
        if self.status == self.TournamentStatus.DRAFT:
            self.status = self.TournamentStatus.PUBLISHED
            self.save(update_fields=['status'])
            return True
        return False

    # ========== 与core模型的转换方法 ==========
    def to_core(self) -> 'core.models.tournament.Tournament':
        """转换为核心业务对象"""
        from core.models.tournament import Tournament as CoreTournament
        from core.models.enums import TournamentStatus as CoreStatus

        # 转换状态枚举
        status_enum = CoreStatus(self.status)

        # 获取关联的单元核心对象列表
        core_events = [event.to_core() for event in self.events.all()]

        return CoreTournament(
            name=self.name,
            start_date=self.start_date,
            end_date=self.end_date,
            location=self.location,
            status=status_enum,
            events=core_events
        )

    @classmethod
    def from_core(cls, core_tournament, save=False):
        """从核心业务对象创建或更新 Django 模型"""
        # 查找或创建实例
        instance, created = cls.objects.get_or_create(
            name=core_tournament.name,
            start_date=core_tournament.start_date,
            defaults={
                'end_date': core_tournament.end_date,
                'location': core_tournament.location,
                'status': core_tournament.status.value,
            }
        )

        if not created and save:
            instance.end_date = core_tournament.end_date
            instance.location = core_tournament.location
            instance.status = core_tournament.status.value
            instance.save()

        # 处理关联的赛事单元
        if save and core_tournament.events:
            # 注意：这里需要 TournamentEvent.from_core 方法支持
            for core_event in core_tournament.events:
                TournamentEvent.from_core(core_event, tournament_id=instance.id, save=True)

        return instance