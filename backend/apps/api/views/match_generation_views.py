# backend/apps/api/views/match_generation_views.py
"""
比赛生成API视图
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from ..models import CompetitionItem
from ..services.match_service import MatchGenerationService


class GenerateMatchesAPI(APIView):
    """
    生成比赛对阵API
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, item_id):
        """
        为比赛单项生成比赛

        POST /api/competition-items/{item_id}/generate-matches/
        请求体:
        {
            "match_type": "pool",  # 或 "elimination"
            "pool_size": 7,        # 可选，仅用于小组赛
            "bracket_type": "single_elimination"  # 可选，仅用于淘汰赛
        }
        """
        try:
            # 获取比赛单项
            competition_item = get_object_or_404(CompetitionItem, id=item_id)

            # 验证比赛状态
            if competition_item.status not in ['open', 'ongoing']:
                return Response(
                    {'error': '比赛必须处于报名中或进行中状态'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 获取请求参数
            match_type = request.data.get('match_type', 'pool')
            pool_size = request.data.get('pool_size', 7)
            bracket_type = request.data.get('bracket_type', 'single_elimination')

            # 调用服务生成比赛
            if match_type == 'pool':
                matches = MatchGenerationService.generate_pool_matches(
                    competition_item_id=item_id,
                    pool_size=pool_size
                )
            elif match_type == 'elimination':
                matches = MatchGenerationService.generate_elimination_bracket(
                    competition_item_id=item_id,
                    bracket_type=bracket_type
                )
            else:
                return Response(
                    {'error': f'不支持的比赛类型: {match_type}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 序列化返回结果
            from ..serializers import MatchSerializer
            serializer = MatchSerializer(matches, many=True)

            return Response({
                'message': f'成功生成 {len(matches)} 场比赛',
                'match_type': match_type,
                'competition_item_id': item_id,
                'matches': serializer.data
            }, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'生成失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ClearMatchesAPI(APIView):
    """
    清除比赛API
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, item_id):
        """
        清除比赛单项的所有比赛

        POST /api/competition-items/{item_id}/clear-matches/
        """
        try:
            competition_item = get_object_or_404(CompetitionItem, id=item_id)

            # 获取比赛数量
            match_count = competition_item.matches.count()

            # 删除所有比赛
            competition_item.matches.all().delete()

            return Response({
                'message': f'成功清除 {match_count} 场比赛',
                'competition_item_id': item_id,
                'cleared_count': match_count
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': f'清除失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RegenerateMatchesAPI(APIView):
    """
    重新生成比赛API（先清除再生成）
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, item_id):
        """
        重新生成比赛

        POST /api/competition-items/{item_id}/regenerate-matches/
        请求体与 generate-matches 相同
        """
        try:
            # 先清除现有比赛
            clear_view = ClearMatchesAPI()
            clear_response = clear_view.post(request, item_id)

            if clear_response.status_code != 200:
                return clear_response

            # 再生成新比赛
            generate_view = GenerateMatchesAPI()
            return generate_view.post(request, item_id)

        except Exception as e:
            return Response(
                {'error': f'重新生成失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )