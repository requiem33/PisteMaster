"""
Tournament 模型测试
"""

import pytest
from core.models.tournament import Tournament


class TestTournament:
    """Tournament模型测试类"""

    def test_create_valid_tournament(self):
        """测试创建有效的赛事"""
        tournament = Tournament(
            name="2024全国击剑锦标赛",
            location="北京国家会议中心"
        )

        assert tournament.name == "2024全国击剑锦标赛"
        assert tournament.location == "北京国家会议中心"

    def test_tournament_validation_empty_name(self):
        """测试空名称验证"""
        with pytest.raises(ValueError, match="赛事名称不能为空"):
            Tournament(name="", location="北京")

        with pytest.raises(ValueError, match="赛事名称不能为空"):
            Tournament(name="   ", location="北京")

    def test_tournament_validation_empty_location(self):
        """测试空地点验证"""
        with pytest.raises(ValueError, match="比赛地点不能为空"):
            Tournament(name="测试赛事", location="")

        with pytest.raises(ValueError, match="比赛地点不能为空"):
            Tournament(name="测试赛事", location="   ")

    def test_tournament_validation_name_length(self):
        """测试名称长度验证"""
        # 过短名称
        with pytest.raises(ValueError, match="赛事名称过短"):
            Tournament(name="A", location="北京")

        # 过长名称
        long_name = "A" * 201
        with pytest.raises(ValueError, match="赛事名称不能超过200个字符"):
            Tournament(name=long_name, location="北京")

    def test_tournament_validation_location_length(self):
        """测试地点长度验证"""
        # 过短地点
        with pytest.raises(ValueError, match="比赛地点过短"):
            Tournament(name="测试赛事", location="北")

        # 过⻓地点
        long_location = "A" * 101
        with pytest.raises(ValueError, match="比赛地点不能超过100个字符"):
            Tournament(name="测试赛事", location=long_location)

    def test_to_dict_method(self):
        """测试to_dict方法"""
        tournament = Tournament(
            name="测试赛事",
            location="测试地点"
        )

        result = tournament.to_dict()

        assert isinstance(result, dict)
        assert result["name"] == "测试赛事"
        assert result["location"] == "测试地点"
        assert len(result) == 2  # 只有两个字段

    def test_from_dict_method(self):
        """测试from_dict类方法"""
        data = {
            "name": "从字典创建的赛事",
            "location": "字典地点"
        }

        tournament = Tournament.from_dict(data)

        assert tournament.name == "从字典创建的赛事"
        assert tournament.location == "字典地点"

    def test_from_dict_missing_fields(self):
        """测试from_dict缺少字段"""
        # 缺少name
        with pytest.raises(ValueError, match="缺少必需字段: name"):
            Tournament.from_dict({"location": "北京"})

        # 缺少location
        with pytest.raises(ValueError, match="缺少必需字段: location"):
            Tournament.from_dict({"name": "测试赛事"})

    def test_str_representation(self):
        """测试字符串表示"""
        tournament = Tournament(
            name="测试赛事",
            location="测试地点"
        )

        assert str(tournament) == "赛事: 测试赛事 @ 测试地点"
        assert "Tournament" in repr(tournament)
        assert "测试赛事" in repr(tournament)
        assert "测试地点" in repr(tournament)

    def test_equality(self):
        """测试相等性判断"""
        tournament1 = Tournament("赛事A", "地点A")
        tournament2 = Tournament("赛事A", "地点A")
        tournament3 = Tournament("赛事B", "地点A")
        tournament4 = Tournament("赛事A", "地点B")

        # 相同名称和地点应该相等
        assert tournament1 == tournament2

        # 不同名称或地点应该不相等
        assert tournament1 != tournament3
        assert tournament1 != tournament4

        # 与非Tournament对象比较
        assert tournament1 != "not a tournament"
        assert tournament1 != None

    def test_hash(self):
        """测试哈希值"""
        tournament1 = Tournament("赛事A", "地点A")
        tournament2 = Tournament("赛事A", "地点A")
        tournament3 = Tournament("赛事B", "地点A")

        # 相同对象应该有相同哈希
        assert hash(tournament1) == hash(tournament2)

        # 不同对象应该有不同的哈希（大概率）
        assert hash(tournament1) != hash(tournament3)

        # 可以放入集合
        tournament_set = {tournament1, tournament2, tournament3}
        assert len(tournament_set) == 2  # tournament1和tournament2相同

    def test_immutability_after_creation(self):
        """测试创建后的不可变性（业务逻辑角度）"""
        tournament = Tournament("测试赛事", "测试地点")

        # 可以修改属性，但业务上不建议
        tournament.name = "新名称"
        tournament.location = "新地点"

        # 重新验证会失败，因为属性已改变
        # 注意：实际使用中应该避免直接修改属性
        assert tournament.name == "新名称"
        assert tournament.location == "新地点"
