# tests/unit/test_algorithms/test_promotion.py
import unittest
from core.algorithms.promotion import PromotionAlgorithm, PoolRanking
from core.models.match import PoolMatch, MatchStatus


class TestPromotionAlgorithm(unittest.TestCase):
    """测试晋级算法（击剑TIE-BREAK规则）"""

    def setUp(self):
        """准备测试数据：模拟一个4人小组的完整比赛结果"""
        # 创建一个小组的4名选手
        self.pool_fencers = [401, 402, 403, 404]
        self.stage_id = 1

        # 创建所有6场比赛并设置结果
        self.matches = []

        # 比赛1: 401 vs 402 (15-10)
        match1 = PoolMatch(401, 402, self.stage_id, status=MatchStatus.COMPLETED)
        match1.score_a, match1.score_b = 15, 10
        self.matches.append(match1)

        # 比赛2: 401 vs 403 (15-12)
        match2 = PoolMatch(401, 403, self.stage_id, status=MatchStatus.COMPLETED)
        match2.score_a, match2.score_b = 15, 12
        self.matches.append(match2)

        # 比赛3: 401 vs 404 (12-15) - 401输一场
        match3 = PoolMatch(401, 404, self.stage_id, status=MatchStatus.COMPLETED)
        match3.score_a, match3.score_b = 12, 15
        self.matches.append(match3)

        # 比赛4: 402 vs 403 (15-14)
        match4 = PoolMatch(402, 403, self.stage_id, status=MatchStatus.COMPLETED)
        match4.score_a, match4.score_b = 15, 14
        self.matches.append(match4)

        # 比赛5: 402 vs 404 (10-15)
        match5 = PoolMatch(402, 404, self.stage_id, status=MatchStatus.COMPLETED)
        match5.score_a, match5.score_b = 10, 15
        self.matches.append(match5)

        # 比赛6: 403 vs 404 (13-15)
        match6 = PoolMatch(403, 404, self.stage_id, status=MatchStatus.COMPLETED)
        match6.score_a, match6.score_b = 13, 15
        self.matches.append(match6)

        # 预期排名（基于上述结果计算）:
        # 404: 3胜0负，击中45，被击中35，净胜+10 → 第1名
        # 401: 2胜1负，击中42，被击中37，净胜+5 → 第2名
        # 402: 1胜2负，击中39，被击中44，净胜-5 → 第3名
        # 403: 0胜3负，击中39，被击中45，净胜-6 → 第4名

    def test_calculate_pool_ranking_basic(self):
        """测试基本的小组赛排名计算"""
        rankings = PromotionAlgorithm.calculate_pool_ranking(self.matches)

        # 应有4个排名结果
        self.assertEqual(len(rankings), 4)

        # 检查是否所有选手都在排名中
        ranked_fencer_ids = {r.fencer_id for r in rankings}
        self.assertEqual(ranked_fencer_ids, set(self.pool_fencers))

        # 验证每个排名对象的结构
        for ranking in rankings:
            self.assertIsInstance(ranking, PoolRanking)
            self.assertIsInstance(ranking.victories, int)
            self.assertIsInstance(ranking.indicator, int)
            self.assertIsInstance(ranking.rank, int)
            self.assertTrue(ranking.rank >= 1 and ranking.rank <= 4)

    def test_calculate_pool_ranking_order(self):
        """测试排名顺序是否符合TIE-BREAK规则"""
        rankings = PromotionAlgorithm.calculate_pool_ranking(self.matches)

        # 按排名获取选手ID
        ranked_ids = [r.fencer_id for r in sorted(rankings, key=lambda x: x.rank)]

        # 预期顺序: 404 (3胜) > 401 (2胜) > 402 (1胜) > 403 (0胜)
        expected_order = [404, 401, 402, 403]
        self.assertEqual(ranked_ids, expected_order,
                         f"排名顺序错误: 期望 {expected_order}, 实际 {ranked_ids}")

    def test_calculate_pool_ranking_stats(self):
        """测试排名统计数据的准确性"""
        rankings = PromotionAlgorithm.calculate_pool_ranking(self.matches)

        # 将结果转为字典便于查询
        ranking_dict = {r.fencer_id: r for r in rankings}

        # 验证404号选手（全胜）的数据
        fencer404 = ranking_dict[404]
        self.assertEqual(fencer404.victories, 3)
        self.assertEqual(fencer404.hits_scored, 45)  # 15+15+15
        self.assertEqual(fencer404.hits_received, 35)  # 12+10+13
        self.assertEqual(fencer404.indicator, 10)  # 45-35
        self.assertEqual(fencer404.rank, 1)

        # 验证401号选手的数据
        fencer401 = ranking_dict[401]
        self.assertEqual(fencer401.victories, 2)
        self.assertEqual(fencer401.hits_scored, 42)  # 15+15+12
        self.assertEqual(fencer401.hits_received, 37)  # 10+12+15
        self.assertEqual(fencer401.indicator, 5)
        self.assertEqual(fencer401.rank, 2)

    def test_calculate_pool_ranking_tie_breaker(self):
        """测试平局情况下的TIE-BREAK规则（直接对决）"""
        # 创建一个平局场景：两名选手胜负和净胜分相同
        # 选手501和502都战胜了503，且相互对战501胜
        tie_matches = [
            self._create_match(501, 502, 15, 10, MatchStatus.COMPLETED),  # 501胜502
            self._create_match(501, 503, 15, 5, MatchStatus.COMPLETED),  # 501胜503
            self._create_match(502, 503, 15, 5, MatchStatus.COMPLETED),  # 502胜503
        ]

        rankings = PromotionAlgorithm.calculate_pool_ranking(tie_matches)

        # 501应排第一（因直接战胜502）
        rank_dict = {r.fencer_id: r.rank for r in rankings}
        self.assertEqual(rank_dict[501], 1)
        self.assertEqual(rank_dict[502], 2)
        self.assertEqual(rank_dict[503], 3)

    def test_promote_from_pools(self):
        """测试从多个小组中选拔晋级选手"""
        # 创建两个小组的模拟排名
        pool1_rankings = [
            PoolRanking(601, 3, 45, 30, 15, 1),
            PoolRanking(602, 2, 42, 35, 7, 2),
            PoolRanking(603, 1, 38, 40, -2, 3),
            PoolRanking(604, 0, 30, 50, -20, 4),
        ]

        pool2_rankings = [
            PoolRanking(605, 3, 44, 31, 13, 1),
            PoolRanking(606, 2, 43, 36, 7, 2),
            PoolRanking(607, 1, 39, 41, -2, 3),
            PoolRanking(608, 0, 31, 49, -18, 4),
        ]

        # 每组取前2名晋级
        promoted = PromotionAlgorithm.promote_from_pools(
            [pool1_rankings, pool2_rankings], promotion_count=2
        )

        # 应晋级4名选手（2组×2人）
        self.assertEqual(len(promoted), 4)

        # 检查是否包含各组前两名
        expected_promoted = [601, 602, 605, 606]  # 各组第1、2名
        self.assertEqual(set(promoted), set(expected_promoted))

        # 测试只取前1名
        promoted_top1 = PromotionAlgorithm.promote_from_pools(
            [pool1_rankings, pool2_rankings], promotion_count=1
        )
        self.assertEqual(len(promoted_top1), 2)
        self.assertEqual(set(promoted_top1), {601, 605})

    def _create_match(self, fencer_a, fencer_b, score_a, score_b, status):
        """辅助方法：创建一场比赛"""
        match = PoolMatch(fencer_a, fencer_b, 1, status=status)
        match.score_a = score_a
        match.score_b = score_b
        return match


if __name__ == '__main__':
    unittest.main()