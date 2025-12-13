from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend

from .models import DjangoRule
from .serializers import RuleSerializer, RuleCreateSerializer
from ...services.rule_service import RuleService
from ..elimination_type.models import DjangoEliminationType
from ..ranking_type.models import DjangoRankingType


class RuleViewSet(viewsets.ViewSet):
    """
    赛制规则 API

    list: 获取规则列表
    retrieve: 获取单个规则
    create: 创建规则
    update: 更新规则
    destroy: 删除规则
    initialize: 初始化预定义规则
    by_elimination_type: 按淘汰赛类型获取规则
    """

    serializer_class = RuleSerializer
    service = RuleService()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['elimination_type', 'final_ranking_type', 'pool_size']
    search_fields = ['rule_name', 'description', 'match_format']
    ordering_fields = ['rule_name', 'pool_size', 'total_qualified_count', 'created_at']
    ordering = ['rule_name']

    def get_permissions(self):
        """权限控制"""
        if self.action in ['create', 'update', 'destroy', 'initialize']:
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        """根据action选择序列化器"""
        if self.action == 'create':
            return RuleCreateSerializer
        return RuleSerializer

    def list(self, request):
        """获取规则列表"""
        # 获取过滤后的queryset
        queryset = DjangoRule.objects.select_related(
            'elimination_type', 'final_ranking_type'
        ).all()

        # 应用过滤、搜索、排序
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, self)

        # 分页
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """获取单个规则"""
        try:
            rule = self.service.get_rule_by_id(pk)
            if not rule:
                return Response(
                    {"detail": "规则不存在"},
                    status=status.HTTP_404_NOT_FOUND
                )

            django_rule = DjangoRule.objects.select_related(
                'elimination_type', 'final_ranking_type'
            ).get(id=rule.id)

            serializer = self.get_serializer(django_rule)
            return Response(serializer.data)

        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def create(self, request):
        """创建规则"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # 将serializer数据转换为service需要的格式
            rule_data = serializer.validated_data
            rule_data['elimination_type_id'] = rule_data.pop('elimination_type_id')
            rule_data['final_ranking_type_id'] = rule_data.pop('final_ranking_type_id')

            # 处理可选字段
            for field in ['match_format', 'pool_size', 'match_duration',
                          'match_score_pool', 'match_score_elimination',
                          'group_qualification_ratio', 'description']:
                if field in rule_data and rule_data[field] == '':
                    rule_data[field] = None

            rule = self.service.create_rule(rule_data)

            # 获取完整的Django对象用于序列化
            django_rule = DjangoRule.objects.select_related(
                'elimination_type', 'final_ranking_type'
            ).get(id=rule.id)

            response_serializer = self.serializer_class(django_rule)

            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )

        except RuleService.RuleServiceError as e:
            return Response(
                {"detail": e.message, "errors": e.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"detail": f"创建失败: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def update(self, request, pk=None):
        """更新规则"""
        # 使用通用序列化器
        serializer = self.serializer_class(data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)

        try:
            # 准备数据
            rule_data = serializer.validated_data

            # 转换外键
            if 'elimination_type' in rule_data:
                rule_data['elimination_type_id'] = rule_data.pop('elimination_type').id

            if 'final_ranking_type' in rule_data:
                rule_data['final_ranking_type_id'] = rule_data.pop('final_ranking_type').id

            # 处理可选字段
            for field in ['match_format', 'pool_size', 'match_duration',
                          'match_score_pool', 'match_score_elimination',
                          'group_qualification_ratio', 'description']:
                if field in rule_data and rule_data[field] == '':
                    rule_data[field] = None

            rule = self.service.update_rule(pk, rule_data)

            # 获取更新后的Django对象
            django_rule = DjangoRule.objects.select_related(
                'elimination_type', 'final_ranking_type'
            ).get(id=rule.id)

            response_serializer = self.serializer_class(django_rule)

            return Response(response_serializer.data)

        except RuleService.RuleServiceError as e:
            return Response(
                {"detail": e.message, "errors": e.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, pk=None):
        """删除规则"""
        try:
            success = self.service.delete_rule(pk)

            if not success:
                return Response(
                    {"detail": "规则不存在"},
                    status=status.HTTP_404_NOT_FOUND
                )

            return Response(status=status.HTTP_204_NO_CONTENT)

        except RuleService.RuleServiceError as e:
            return Response(
                {"detail": e.message},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def initialize(self, request):
        """初始化预定义规则"""
        try:
            results = self.service.initialize_predefined_data()

            return Response({
                "success": True,
                "message": "预定义数据初始化完成",
                "results": results
            })

        except Exception as e:
            return Response(
                {"detail": f"初始化失败: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def by_elimination_type(self, request):
        """按淘汰赛类型获取规则"""
        elimination_type_id = request.query_params.get('elimination_type_id')
        elimination_type_code = request.query_params.get('elimination_type_code')

        if not elimination_type_id and not elimination_type_code:
            return Response(
                {"detail": "必须提供elimination_type_id或elimination_type_code参数"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            if elimination_type_code:
                # 通过代码查找类型
                elimination_type = DjangoEliminationType.objects.get(
                    type_code=elimination_type_code
                )
                elimination_type_id = elimination_type.id

            rules = self.service.get_rules_by_elimination_type(elimination_type_id)

            # 转换为Django模型用于序列化
            rule_ids = [rule.id for rule in rules]
            django_rules = DjangoRule.objects.select_related(
                'elimination_type', 'final_ranking_type'
            ).filter(id__in=rule_ids)

            serializer = self.get_serializer(django_rules, many=True)
            return Response(serializer.data)

        except DjangoEliminationType.DoesNotExist:
            return Response(
                {"detail": "指定的淘汰赛类型不存在"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def types(self, request):
        """获取所有淘汰赛类型和排名类型"""
        try:
            elimination_types = DjangoEliminationType.objects.all()
            ranking_types = DjangoRankingType.objects.all()

            return Response({
                "elimination_types": [
                    {
                        "id": str(t.id),
                        "type_code": t.type_code,
                        "display_name": t.display_name
                    }
                    for t in elimination_types
                ],
                "ranking_types": [
                    {
                        "id": str(t.id),
                        "type_code": t.type_code,
                        "display_name": t.display_name
                    }
                    for t in ranking_types
                ]
            })

        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def search(self, request):
        """搜索规则"""
        filters = {}

        # 收集过滤条件
        if 'name' in request.query_params:
            filters['name'] = request.query_params['name']
        if 'elimination_type_code' in request.query_params:
            filters['elimination_type_code'] = request.query_params['elimination_type_code']
        if 'ranking_type_code' in request.query_params:
            filters['ranking_type_code'] = request.query_params['ranking_type_code']
        if 'min_pool_size' in request.query_params:
            filters['min_pool_size'] = int(request.query_params['min_pool_size'])
        if 'max_pool_size' in request.query_params:
            filters['max_pool_size'] = int(request.query_params['max_pool_size'])
        if 'ordering' in request.query_params:
            filters['ordering'] = request.query_params['ordering']

        # 调用Service层搜索
        rules = self.service.search_rules(**filters)

        # 转换为Django模型用于序列化
        rule_ids = [rule.id for rule in rules]
        django_rules = DjangoRule.objects.select_related(
            'elimination_type', 'final_ranking_type'
        ).filter(id__in=rule_ids)

        serializer = self.get_serializer(django_rules, many=True)
        return Response(serializer.data)
