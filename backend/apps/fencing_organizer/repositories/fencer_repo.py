from uuid import UUID

from backend.apps.fencing_organizer.mappers.fencer_mapper import FencerMapper
from backend.apps.fencing_organizer.modules.fencer.models import DjangoFencer
from core.interfaces.interface import FencerRepositoryInterface
from core.models.fencer import Fencer
from django.db import IntegrityError


class DjangoFencerRepository(FencerRepositoryInterface):
    """Fencer 仓库接口在 Django 中的实现"""

    def get_fencer_by_id(self, fencer_id: UUID) -> Fencer | None:
        """通过 UUID 获取运动员"""
        try:
            django_fencer = DjangoFencer.objects.get(pk=fencer_id)
            return FencerMapper.to_domain(django_fencer)
        except DjangoFencer.DoesNotExist:
            return None

    def save_fencer(self, fencer: Fencer) -> Fencer:
        """保存或更新运动员信息"""
        orm_data = FencerMapper.to_orm_data(fencer)

        try:
            # update_or_create: 如果 id 存在则更新，否则创建
            django_fencer, created = DjangoFencer.objects.update_or_create(
                id=fencer.id,
                defaults=orm_data
            )
        except IntegrityError as e:
            # 捕获可能的 UNIQUE 约束错误 (如 fencing_id 重复)
            raise ValueError(f"保存 Fencer 时发生数据完整性错误: {e}")

            # 将最终保存的 ORM 对象转换回核心 Dataclass 对象返回
        return FencerMapper.to_domain(django_fencer)

    def get_fencers_by_country(self, country_code: str) -> list[Fencer]:
        """示例：获取某个国家的所有运动员，演示复杂查询"""
        django_fencers = DjangoFencer.objects.filter(country_code=country_code).order_by('last_name')

        # 列表推导式转换
        return [FencerMapper.to_domain(f) for f in django_fencers]
