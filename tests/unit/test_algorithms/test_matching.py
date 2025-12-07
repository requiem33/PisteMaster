# tests/unit/test_algorithms/test_matching.py
import unittest
from datetime import datetime, timedelta
from core.algorithms.matching import MatchGenerationAlgorithm
from core.models.match import PoolMatch, DirectEliminationMatch, MatchStatus


class TestMatchGenerationAlgorithm(unittest.TestCase):
    """测试对阵生成算法"""

    def setUp(self):
        """准备测试数据"""
        self.test_pool = [101, 102, 103, 104]  # 4名选手的小组
        self.stage_id = 1
        self.start_time = datetime(2025, 12, 5, 9, 0)  # 测试开始时间

    def test_generate_pool_matches_basic(self):
        """测试为单个小组生成循环赛对阵表"""
        matches = MatchGenerationAlgorithm.generate_pool_matches(
            self.test_pool, self.stage_id
        )

        # 4人小组应产生 C(4,2)=6 场比赛
        self.assertEqual(len(matches), 6)

        # 每场比赛都应是 PoolMatch 实例
        for match in matches:
            self.assertIsInstance(match, PoolMatch)
            self.assertEqual(match.stage_id, self.stage_id)
            self.assertEqual(match.status, MatchStatus.SCHEDULED)

        # 检查是否包含所有可能的组合
        expected_pairs = [(101, 102), (101, 103), (101, 104),
                          (102, 103), (102, 104), (103, 104)]
        actual_pairs = [(m.fencer_a_id, m.fencer_b_id) for m in matches]
        self.assertEqual(set(actual_pairs), set(expected_pairs))

    def test_generate_pool_matches_with_time(self):
        """测试带时间安排的小组赛生成"""
        matches = MatchGenerationAlgorithm.generate_pool_matches(
            self.test_pool, self.stage_id, start_time=self.start_time
        )

        # 检查时间安排逻辑
        for i, match in enumerate(matches):
            expected_time = self.start_time + timedelta(minutes=i * 10)
            self.assertEqual(match.scheduled_time, expected_time)

    def test_generate_elimination_bracket_power_of_two(self):
        """测试选手数为2的幂次时淘汰赛生成（如4、8、16人）"""
        participants = [201, 202, 203, 204]  # 4人，正好是2^2
        matches = MatchGenerationAlgorithm.generate_elimination_bracket(
            participants, self.stage_id
        )

        # 4人单败淘汰应有3场比赛（半决赛2场 + 决赛1场）
        self.assertEqual(len(matches), 3)

        # 第一轮应是2场半决赛
        first_round_matches = [m for m in matches if m.round_number == 1]
        self.assertEqual(len(first_round_matches), 2)

        # 第二轮应是1场决赛
        second_round_matches = [m for m in matches if m.round_number == 2]
        self.assertEqual(len(second_round_matches), 1)

        # 检查淘汰赛类型
        for match in matches:
            self.assertIsInstance(match, DirectEliminationMatch)
            self.assertTrue(match.bracket_position.startswith('round'))

    def test_generate_elimination_bracket_with_byes(self):
        """测试选手数非2的幂次时淘汰赛生成（包含轮空）"""
        participants = [301, 302, 303, 304, 305]
        matches = MatchGenerationAlgorithm.generate_elimination_bracket(
            participants, self.stage_id
        )

        # 基础验证
        self.assertEqual(len(matches), 7)

        # 按轮次分组
        matches_by_round = {}
        for match in matches:
            matches_by_round.setdefault(match.round_number, []).append(match)

        # 验证轮次数量
        self.assertEqual(len(matches_by_round[1]), 4)
        self.assertEqual(len(matches_by_round[2]), 2)
        self.assertEqual(len(matches_by_round[3]), 1)

        # 验证轮空：5名选手需要3个轮空位置
        # 有3个轮空位置，它们可能分布在1场或2场比赛中
        # 计算第一轮中的轮空位置总数
        round1_bye_positions = 0
        for m in matches_by_round[1]:
            if m.fencer_a_id == -1:
                round1_bye_positions += 1
            if m.fencer_b_id == -1:
                round1_bye_positions += 1

        self.assertEqual(round1_bye_positions, 3, "第一轮应有3个轮空位置")

        # 验证所有实际选手都在第一轮出现
        round1_fencers = set()
        for match in matches_by_round[1]:
            if match.fencer_a_id != -1:
                round1_fencers.add(match.fencer_a_id)
            if match.fencer_b_id != -1:
                round1_fencers.add(match.fencer_b_id)

        self.assertEqual(round1_fencers, set(participants))

        # 验证后续轮次比赛等待胜者
        for round_num in [2, 3]:
            for match in matches_by_round.get(round_num, []):
                self.assertEqual(match.fencer_a_id, -1)
                self.assertEqual(match.fencer_b_id, -1)


if __name__ == '__main__':
    unittest.main()