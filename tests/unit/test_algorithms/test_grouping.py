# core/tests/algorithms/test_grouping.py
import unittest
from core.algorithms.grouping import GroupingAlgorithm


class TestGroupingAlgorithm(unittest.TestCase):
    def test_snake_seeding(self):
        participants = list(range(1, 25))  # 1-24号选手
        pools = GroupingAlgorithm.snake_seeding(participants, 4)

        # 验证每组6人
        self.assertEqual(len(pools), 4)
        for pool in pools:
            self.assertEqual(len(pool), 6)

        # 验证蛇形分布：1号种子在第1组，2号种子在第2组，3号种子在第3组，4号种子在第4组
        self.assertIn(1, pools[0])
        self.assertIn(2, pools[1])
        self.assertIn(3, pools[2])
        self.assertIn(4, pools[3])