import pytest
from django.urls import reverse
from rest_framework import status
from backend.apps.fencing_organizer.modules.tournament_status.models import DjangoTournamentStatus


@pytest.mark.django_db
class TestTournamentStatusAPI:

    def test_get_status_list(self, client):
        """测试获取状态列表"""
        url = reverse('tournament-status-list')
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data or isinstance(response.data, list)

    def test_create_status(self, client, admin_user):
        """测试创建状态"""
        url = reverse('tournament-status-list')
        client.force_login(admin_user)

        data = {
            "status_code": "TEST_STATUS",
            "display_name": "测试状态",
            "description": "这是一个测试状态"
        }

        response = client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status_code'] == "TEST_STATUS"

    def test_initialize_predefined_statuses(self, client, admin_user):
        """测试初始化预定义状态"""
        url = reverse('tournament-status-initialize')
        client.force_login(admin_user)

        response = client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
