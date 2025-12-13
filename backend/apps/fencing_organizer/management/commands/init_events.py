from django.core.management.base import BaseCommand
from backend.apps.fencing_organizer.services.event_service import EventService


class Command(BaseCommand):
    help = '初始化预定义项目数据'

    def handle(self, *args, **options):
        service = EventService()
        results = service.initialize_predefined_data()

        self.stdout.write(
            self.style.SUCCESS(
                f'成功初始化: {results["event_statuses"]} 个项目状态, '
                f'{results["event_types"]} 个项目类型'
            )
        )
