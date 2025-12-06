# core/models/tests/test_fencer.py
import unittest
from datetime import date
from ..fencer import Fencer  # 导入核心类


class TestFencer(unittest.TestCase):
    """测试核心 Fencer 业务对象"""

    def setUp(self):
        """在每个测试方法前运行，准备测试数据"""
        self.fencer = Fencer(
            first_name="小明",
            last_name="张",
            country="CHN",
            date_of_birth=date(2010, 5, 1),
            weapon="Foil",
        )

    def test_full_name(self):
        """测试 full_name 属性是否正确拼接"""
        self.assertEqual(self.fencer.full_name, "张 小明")

    def test_age_calculation(self):
        """测试年龄计算逻辑（基于当前日期）"""
        # 注意：这个测试依赖于当前日期，可能不稳定
        # 更严谨的做法是 mock date.today()
        self.assertIsInstance(self.fencer.age, int)
        self.assertGreater(self.fencer.age, 10)

    def test_age_group_assignment(self):
        """测试年龄组别分配逻辑"""
        # 给定2010年出生，假设当前是2025年，年龄是15岁
        # 应该属于 Cadet 或 U16 组（根据你的规则）
        self.assertEqual(self.fencer.age_group, "U16")  # 根据你的实际规则调整

    def test_is_eligible_for_tournament(self):
        """测试赛事资格验证逻辑"""
        # 测试一个允许的情况
        self.assertTrue(
            self.fencer.is_eligible_for_tournament(
                min_age=10,
                max_age=20,
                allowed_weapons=['Foil', 'Epee']
            )
        )
        # 测试一个不允许的情况（年龄不符）
        self.assertFalse(
            self.fencer.is_eligible_for_tournament(
                min_age=16,  # 最小年龄16岁，但选手15岁
                max_age=20,
                allowed_weapons=[]
            )
        )


if __name__ == '__main__':
    unittest.main()