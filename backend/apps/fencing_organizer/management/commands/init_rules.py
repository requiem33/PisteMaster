from django.core.management.base import BaseCommand
from backend.apps.fencing_organizer.services.rule_service import RuleService


class Command(BaseCommand):
    help = '初始化预定义赛制规则数据'

    def handle(self, *args, **options):
        service = RuleService()
        results = service.initialize_predefined_data()

        self.stdout.write(
            self.style.SUCCESS(
                f'成功初始化: {results["elimination_types"]} 个淘汰赛类型, '
                f'{results["ranking_types"]} 个排名类型, '
                f'{results["rules"]} 个规则'
            )
        )
