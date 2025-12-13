# tests/backend/test_tournament_api.py
import pytest
from django.urls import reverse
from rest_framework import status
from datetime import date, timedelta
from backend.apps.fencing_organizer.modules.tournament.models import DjangoTournament
from backend.apps.fencing_organizer.modules.tournament_status.models import DjangoTournamentStatus


@pytest.mark.django_db
class TestTournamentAPI:

    def test_get_tournament_list(self, client, sample_tournament):
        """测试获取赛事列表"""
        url = reverse('tournament-list')
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, dict) or isinstance(response.data, list)

    def test_create_tournament(self, client, admin_user, planning_status):
        """测试创建赛事"""
        url = reverse('tournament-list')
        client.force_login(admin_user)

        data = {
            "tournament_name": "测试赛事",
            "organizer": "测试组织",
            "location": "测试地点",
            "start_date": "2024-12-01",
            "end_date": "2024-12-05",
            "status_id": str(planning_status.id)
        }

        response = client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['tournament_name'] == "测试赛事"
        assert response.data['status_code'] == "PLANNING"

    def test_update_tournament_status(self, client, admin_user, sample_tournament, ongoing_status):
        """测试更新赛事状态"""
        url = reverse('tournament-update-status', kwargs={'pk': str(sample_tournament.id)})
        client.force_login(admin_user)

        data = {
            "status_id": str(ongoing_status.id)
        }

        response = client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status_code'] == "ONGOING"

    def test_get_upcoming_tournaments(self, client):
        """测试获取即将到来的赛事"""
        url = reverse('tournament-upcoming')
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK

    @pytest.fixture
    def planning_status(self):
        """计划中状态fixture"""
        status, created = DjangoTournamentStatus.objects.get_or_create(
            status_code='PLANNING',
            defaults={
                'display_name': '计划中',
                'description': '赛事正在计划阶段'
            }
        )
        return status

    @pytest.fixture
    def ongoing_status(self):
        """进行中状态fixture"""
        status, created = DjangoTournamentStatus.objects.get_or_create(
            status_code='ONGOING',
            defaults={
                'display_name': '进行中',
                'description': '赛事正在进行中'
            }
        )
        return status

    @pytest.fixture
    def sample_tournament(self, planning_status):
        """示例赛事fixture"""
        tournament = DjangoTournament.objects.create(
            tournament_name="示例赛事",
            organizer="示例组织",
            location="示例地点",
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=35),
            status=planning_status
        )
        return tournament
