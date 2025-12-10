# backend/apps/api/management/commands/reset_test_data.py
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q  # 导入 Q 对象用于复杂查询
from backend.apps.fencing_organizer.models import Tournament, TournamentEvent, CompetitionItem, CompetitionRules, Fencer
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '安全地重置所有测试数据（考虑外键约束）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制删除所有测试数据，即使关联了非测试数据',
        )

    def handle(self, *args, **options):
        force = options['force']

        # 定义测试数据的标识模式
        TEST_PATTERNS = ['测试', 'test', 'Test', 'TEST']

        with transaction.atomic():
            deleted_counts = {}

            # 第1步：解除多对多关联（最底层依赖）
            # 找到所有测试比赛单项，清空其参赛选手
            test_items = CompetitionItem.objects.filter(
                name__iregex=r'|'.join(TEST_PATTERNS)
            )
            for item in test_items:
                item.participants.clear()  # 解除 M2M 关系

            deleted_counts['participants_cleared'] = test_items.count()
            self.stdout.write(f"✅ 已清空 {test_items.count()} 个测试单项的选手关联")

            # 第2步：删除测试比赛单项（依赖 rules 和 event）
            items_deleted, _ = test_items.delete()
            deleted_counts['competition_items'] = items_deleted
            self.stdout.write(f"✅ 已删除 {items_deleted} 个测试比赛单项")

            # 第3步：删除测试赛事单元（依赖 tournament）
            test_events = TournamentEvent.objects.filter(
                name__iregex=r'|'.join(TEST_PATTERNS)
            )
            events_deleted, _ = test_events.delete()
            deleted_counts['tournament_events'] = events_deleted
            self.stdout.write(f"✅ 已删除 {events_deleted} 个测试赛事单元")

            # 第4步：删除测试主赛事
            test_tournaments = Tournament.objects.filter(
                name__iregex=r'|'.join(TEST_PATTERNS)
            )
            tournaments_deleted, _ = test_tournaments.delete()
            deleted_counts['tournaments'] = tournaments_deleted
            self.stdout.write(f"✅ 已删除 {tournaments_deleted} 个测试主赛事")

            # 第5步：最后删除测试规则（现在应该没有单项引用它们了）
            test_rules = CompetitionRules.objects.filter(
                name__iregex=r'|'.join(TEST_PATTERNS)
            )

            # 安全检查：确认没有比赛单项引用这些规则
            if not force:
                problematic_rules = []
                for rule in test_rules:
                    if rule.competition_items.exists():
                        problematic_rules.append(f"{rule.name}(ID:{rule.id})")

                if problematic_rules:
                    self.stderr.write(
                        self.style.ERROR(
                            f"❌ 以下规则仍被比赛单项引用，无法删除：{', '.join(problematic_rules)}\n"
                            "使用 --force 参数强制解除关联并删除。"
                        )
                    )
                    return

            rules_deleted, _ = test_rules.delete()
            deleted_counts['competition_rules'] = rules_deleted
            self.stdout.write(f"✅ 已删除 {rules_deleted} 个测试规则")

            # 第6步（可选）：清理测试选手数据
            if force:
                # 使用 Q 对象构建复杂查询条件
                # 查找姓名包含测试模式或俱乐部包含测试模式的选手
                test_fencers = Fencer.objects.filter(
                    Q(first_name__iregex=r'|'.join(TEST_PATTERNS)) |
                    Q(last_name__iregex=r'|'.join(TEST_PATTERNS)) |
                    Q(club__iregex=r'|'.join(TEST_PATTERNS))
                )

                fencers_deleted, _ = test_fencers.delete()
                deleted_counts['fencers'] = fencers_deleted
                self.stdout.write(f"✅ 已删除 {fencers_deleted} 个测试选手")

            # 汇总报告
            self.stdout.write("\n" + "=" * 50)
            self.stdout.write(self.style.SUCCESS("🏁 测试数据清理完成"))
            for model, count in deleted_counts.items():
                if count:
                    self.stdout.write(f"   {model}: {count} 条记录")

            total = sum(deleted_counts.values())
            self.stdout.write(self.style.SUCCESS(f"总计清理: {total} 条记录"))