# test_match_model.py
import os
import django
import sys

# 设置Django环境
sys.path.append('C:/Users/Tian/OneDrive/PisteMaster/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PisteMaster.settings')
django.setup()

from backend.apps.api.models import Match, Fencer, CompetitionItem, CompetitionRules


# 创建测试数据
def test_match_creation():
    print("测试 Match 模型...")

    # 1. 创建必要的依赖对象
    # 先检查是否有规则
    try:
        rule = CompetitionRules.objects.first()
        if not rule:
            rule = CompetitionRules.objects.create(
                name="测试规则",
                weapon_type="foil",
                is_default=True
            )
            print(f"创建规则: {rule}")
    except Exception as e:
        print(f"创建规则失败: {e}")
        return

    # 2. 创建比赛单项
    try:
        item = CompetitionItem.objects.create(
            name="测试比赛单项",
            weapon_type="foil",
            gender_category="men",
            age_group="senior",
            rules=rule,
            status="draft"
        )
        print(f"创建比赛单项: {item}")
    except Exception as e:
        print(f"创建比赛单项失败: {e}")
        return

    # 3. 获取或创建选手
    try:
        fencer1 = Fencer.objects.first()
        if not fencer1:
            fencer1 = Fencer.objects.create(
                first_name="张",
                last_name="三",
                country="CHN",
                weapon="Foil"
            )

        fencer2 = Fencer.objects.last()
        if not fencer2 or fencer2.id == fencer1.id:
            fencer2 = Fencer.objects.create(
                first_name="李",
                last_name="四",
                country="CHN",
                weapon="Foil"
            )

        print(f"选手1: {fencer1}, 选手2: {fencer2}")
    except Exception as e:
        print(f"创建选手失败: {e}")
        return

    # 4. 创建比赛
    try:
        match = Match.objects.create(
            competition_item=item,
            match_type=Match.MatchType.POOL,
            fencer_a=fencer1,
            fencer_b=fencer2,
            pool_number=1,
            pool_round=1,
            status=Match.MatchStatus.SCHEDULED,
            score_a=0,
            score_b=0
        )
        print(f"成功创建比赛: {match}")

        # 测试属性
        print(f"选手A ID: {match.fencer_a_id}")
        print(f"选手B ID: {match.fencer_b_id}")
        print(f"是否为轮空: {match.is_bye_match}")
        print(f"胜者: {match.winner}")

        # 测试状态更新
        match.score_a = 15
        match.score_b = 10
        match.status = Match.MatchStatus.COMPLETED
        match.save()
        print(f"更新比分后胜者: {match.winner}")

        # 测试轮空比赛
        bye_match = Match.objects.create(
            competition_item=item,
            match_type=Match.MatchType.DIRECT_ELIMINATION,
            fencer_a=fencer1,
            fencer_b=None,  # 轮空
            round_number=1,
            status=Match.MatchStatus.SCHEDULED
        )
        print(f"创建轮空比赛: {bye_match}")
        print(f"选手B ID（应为-1）: {bye_match.fencer_b_id}")
        print(f"是否为轮空: {bye_match.is_bye_match}")

    except Exception as e:
        print(f"创建比赛失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_match_creation()