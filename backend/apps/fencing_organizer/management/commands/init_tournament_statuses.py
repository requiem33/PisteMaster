from django.core.management.base import BaseCommand
from backend.apps.fencing_organizer.services.tournament_status_service import TournamentStatusService


class Command(BaseCommand):
    help = '初始化预定义赛事状态'

    def handle(self, *args, **options):
        service = TournamentStatusService()
        created_statuses = service.initialize_predefined_statuses()

        self.stdout.write(
            self.style.SUCCESS(f'成功初始化 {len(created_statuses)} 个赛事状态')
        )
