# backend/apps/fencing_organizer/management/commands/create_sample_tournaments.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from backend.apps.fencing_organizer.modules.tournament.models import DjangoTournament
from backend.apps.fencing_organizer.modules.tournament_status.models import DjangoTournamentStatus


class Command(BaseCommand):
    help = '创建示例赛事数据'

    def handle(self, *args, **options):
        # 获取状态
        try:
            planning_status = DjangoTournamentStatus.objects.get(status_code='PLANNING')
            registration_open = DjangoTournamentStatus.objects.get(status_code='REGISTRATION_OPEN')
            ongoing_status = DjangoTournamentStatus.objects.get(status_code='ONGOING')
            completed_status = DjangoTournamentStatus.objects.get(status_code='COMPLETED')
        except DjangoTournamentStatus.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('请先初始化赛事状态数据 (python manage.py init_tournament_statuses)')
            )
            return

        # 示例赛事数据
        sample_tournaments = [
            {
                'tournament_name': '2024全国击剑锦标赛',
                'organizer': '中国击剑协会',
                'location': '北京国家体育中心',
                'start_date': date(2024, 6, 1),
                'end_date': date(2024, 6, 5),
                'status': completed_status
            },
            {
                'tournament_name': '2024亚洲击剑锦标赛',
                'organizer': '亚洲击剑联合会',
                'location': '上海体育中心',
                'start_date': date(2024, 8, 15),
                'end_date': date(2024, 8, 20),
                'status': ongoing_status
            },
            {
                'tournament_name': '2025世界击剑锦标赛',
                'organizer': '国际击剑联合会',
                'location': '巴黎贝尔西体育馆',
                'start_date': date(2025, 7, 10),
                'end_date': date(2025, 7, 18),
                'status': registration_open
            },
            {
                'tournament_name': '2024全国青少年击剑比赛',
                'organizer': '中国击剑协会',
                'location': '广州体育中心',
                'start_date': date(2024, 10, 5),
                'end_date': date(2024, 10, 7),
                'status': planning_status
            },
        ]

        created_count = 0
        for tournament_data in sample_tournaments:
            # 检查是否已存在
            if not DjangoTournament.objects.filter(
                    tournament_name=tournament_data['tournament_name'],
                    start_date=tournament_data['start_date']
            ).exists():
                tournament = DjangoTournament(**tournament_data)
                tournament.save()
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"创建赛事: {tournament.tournament_name}")
                )

        self.stdout.write(
            self.style.SUCCESS(f'成功创建 {created_count} 个示例赛事')
        )
