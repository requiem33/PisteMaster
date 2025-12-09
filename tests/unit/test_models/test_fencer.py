"""
Fencer 模型测试
"""

import pytest
from datetime import date, datetime
from core.models.fencer import Fencer


class TestFencer:
    """Fencer模型测试类"""

    def test_create_valid_fencer(self):
        """测试创建有效的选手"""
        fencer = Fencer(
            last_name="张",
            first_name="三",
            nationality="CHN",
            birth_date=date(2000, 1, 1)
        )

        assert fencer.last_name == "张"
        assert fencer.first_name == "三"
        assert fencer.nationality == "CHN"
        assert fencer.birth_date == date(2000, 1, 1)

    def test_create_fencer_western_name(self):
        """测试创建西方名字选手"""
        fencer = Fencer(
            last_name="Doe",
            first_name="John",
            nationality="USA",
            birth_date=date(1995, 5, 15)
        )

        assert fencer.get_full_name() == "Doe John"
        assert fencer.get_full_name(western_order=True) == "John Doe"

    def test_fencer_validation_empty_name(self):
        """测试空姓名验证"""
        # 空姓氏
        with pytest.raises(ValueError, match="姓氏不能为空"):
            Fencer(
                last_name="",
                first_name="三",
                nationality="CHN",
                birth_date=date(2000, 1, 1)
            )

        # 空名字
        with pytest.raises(ValueError, match="名字不能为空"):
            Fencer(
                last_name="张",
                first_name="",
                nationality="CHN",
                birth_date=date(2000, 1, 1)
            )

    def test_fencer_validation_name_length(self):
        """测试姓名长度验证"""
        # 过长姓氏
        long_last_name = "张" * 51
        with pytest.raises(ValueError, match="姓氏不能超过50个字符"):
            Fencer(
                last_name=long_last_name,
                first_name="三",
                nationality="CHN",
                birth_date=date(2000, 1, 1)
            )

    def test_fencer_validation_nationality(self):
        """测试国籍验证"""
        # 空国籍
        with pytest.raises(ValueError, match="国籍不能为空"):
            Fencer(
                last_name="张",
                first_name="三",
                nationality="",
                birth_date=date(2000, 1, 1)
            )

        # 长度不对
        with pytest.raises(ValueError, match="国籍必须是3个字母的ISO代码"):
            Fencer(
                last_name="张",
                first_name="三",
                nationality="CH",
                birth_date=date(2000, 1, 1)
            )

        # 包含数字
        with pytest.raises(ValueError, match="国籍代码只能包含字母"):
            Fencer(
                last_name="张",
                first_name="三",
                nationality="CH1",
                birth_date=date(2000, 1, 1)
            )

        # 小写字母（会被自动转大写）
        fencer = Fencer(
            last_name="张",
            first_name="三",
            nationality="chn",  # 小写
            birth_date=date(2000, 1, 1)
        )
        assert fencer.nationality == "CHN"  # 自动转大写

    def test_fencer_validation_birth_date(self):
        """测试出生日期验证"""
        # 非date对象
        with pytest.raises(ValueError, match="出生日期必须是date对象"):
            Fencer(
                last_name="张",
                first_name="三",
                nationality="CHN",
                birth_date="2000-01-01"  # 字符串，不是date
            )

        # 未来日期
        future_date = date.today().replace(year=date.today().year + 1)
        with pytest.raises(ValueError, match="出生日期不能晚于今天"):
            Fencer(
                last_name="张",
                first_name="三",
                nationality="CHN",
                birth_date=future_date
            )

        # 太早的日期
        with pytest.raises(ValueError, match="出生日期不能早于1900年"):
            Fencer(
                last_name="张",
                first_name="三",
                nationality="CHN",
                birth_date=date(1899, 12, 31)
            )

        # 年龄太小
        today = date.today()
        child_date = today.replace(year=today.year - 3)  # 3岁
        with pytest.raises(ValueError, match="选手年龄太小，不符合击剑比赛要求"):
            Fencer(
                last_name="张",
                first_name="三",
                nationality="CHN",
                birth_date=child_date
            )

    def test_get_age(self):
        """测试年龄计算"""
        # 创建测试日期
        test_date = date(2024, 6, 1)

        # 生日在测试日期之前
        fencer1 = Fencer(
            last_name="张",
            first_name="三",
            nationality="CHN",
            birth_date=date(2000, 1, 1)
        )
        assert fencer1.get_age(test_date) == 24

        # 生日在测试日期之后（同一年）
        fencer2 = Fencer(
            last_name="李",
            first_name="四",
            nationality="CHN",
            birth_date=date(2000, 12, 1)
        )
        assert fencer2.get_age(test_date) == 23

        # 测试默认使用今天
        fencer3 = Fencer(
            last_name="王",
            first_name="五",
            nationality="CHN",
            birth_date=date(2000, 1, 1)
        )
        expected_age = date.today().year - 2000
        if (date.today().month, date.today().day) < (1, 1):
            expected_age -= 1
        assert fencer3.get_age() == expected_age

    def test_get_age_group(self):
        """测试年龄组计算"""
        # 使用固定参考日期以便测试
        reference_date = date(2024, 6, 1)

        # U10组
        fencer_u10 = Fencer(
            last_name="张",
            first_name="三",
            nationality="CHN",
            birth_date=date(2015, 6, 2)  # 8岁（参考日期时）
        )
        assert fencer_u10.get_age_group(reference_date) == "U10"

        # U12组
        fencer_u12 = Fencer(
            last_name="李",
            first_name="四",
            nationality="CHN",
            birth_date=date(2012, 6, 2)  # 11岁
        )
        assert fencer_u12.get_age_group(reference_date) == "U12"

        # Senior组
        fencer_senior = Fencer(
            last_name="王",
            first_name="五",
            nationality="CHN",
            birth_date=date(1990, 1, 1)  # 34岁
        )
        assert fencer_senior.get_age_group(reference_date) == "Senior"

        # Veteran组
        fencer_veteran = Fencer(
            last_name="赵",
            first_name="六",
            nationality="CHN",
            birth_date=date(1960, 1, 1)  # 64岁
        )
        assert fencer_veteran.get_age_group(reference_date) == "Veteran"

    def test_get_full_name(self):
        """测试获取全名"""
        fencer = Fencer(
            last_name="Smith",
            first_name="John",
            nationality="USA",
            birth_date=date(1990, 1, 1)
        )

        # 默认顺序（姓在前）
        assert fencer.get_full_name() == "Smith John"

        # 西方顺序（名在前）
        assert fencer.get_full_name(western_order=True) == "John Smith"

        # 中文名字
        chinese_fencer = Fencer(
            last_name="张",
            first_name="三",
            nationality="CHN",
            birth_date=date(2000, 1, 1)
        )
        assert chinese_fencer.get_full_name() == "张 三"

    def test_to_dict(self):
        """测试转换为字典"""
        fencer = Fencer(
            last_name="张",
            first_name="三",
            nationality="CHN",
            birth_date=date(2000, 1, 1)
        )

        result = fencer.to_dict()

        assert isinstance(result, dict)
        assert result["last_name"] == "张"
        assert result["first_name"] == "三"
        assert result["nationality"] == "CHN"
        assert result["birth_date"] == "2000-01-01"
        assert "age" in result
        assert "age_group" in result
        assert "full_name" in result

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "last_name": "张",
            "first_name": "三",
            "nationality": "CHN",
            "birth_date": "2000-01-01"
        }

        fencer = Fencer.from_dict(data)

        assert fencer.last_name == "张"
        assert fencer.first_name == "三"
        assert fencer.nationality == "CHN"
        assert fencer.birth_date == date(2000, 1, 1)

    def test_from_dict_with_different_date_formats(self):
        """测试不同日期格式"""
        # ISO格式
        data1 = {
            "last_name": "张",
            "first_name": "三",
            "nationality": "CHN",
            "birth_date": "2000-01-01"
        }
        fencer1 = Fencer.from_dict(data1)
        assert fencer1.birth_date == date(2000, 1, 1)

        # 斜杠格式
        data2 = {
            "last_name": "李",
            "first_name": "四",
            "nationality": "CHN",
            "birth_date": "2000/01/01"
        }
        fencer2 = Fencer.from_dict(data2)
        assert fencer2.birth_date == date(2000, 1, 1)

        # 欧洲格式
        data3 = {
            "last_name": "王",
            "first_name": "五",
            "nationality": "CHN",
            "birth_date": "01/01/2000"
        }
        fencer3 = Fencer.from_dict(data3)
        assert fencer3.birth_date == date(2000, 1, 1)

    def test_from_dict_missing_fields(self):
        """测试从字典创建时缺少字段"""
        # 缺少姓氏
        with pytest.raises(ValueError, match="缺少必需字段: last_name"):
            Fencer.from_dict({
                "first_name": "三",
                "nationality": "CHN",
                "birth_date": "2000-01-01"
            })

        # 缺少名字
        with pytest.raises(ValueError, match="缺少必需字段: first_name"):
            Fencer.from_dict({
                "last_name": "张",
                "nationality": "CHN",
                "birth_date": "2000-01-01"
            })

    def test_str_representation(self):
        """测试字符串表示"""
        fencer = Fencer(
            last_name="张",
            first_name="三",
            nationality="CHN",
            birth_date=date(2000, 1, 1)
        )

        assert str(fencer) == "张 三 (CHN)"
        assert "Fencer" in repr(fencer)
        assert "张" in repr(fencer)
        assert "三" in repr(fencer)
        assert "CHN" in repr(fencer)

    def test_equality(self):
        """测试相等性判断"""
        fencer1 = Fencer(
            last_name="张",
            first_name="三",
            nationality="CHN",
            birth_date=date(2000, 1, 1)
        )

        fencer2 = Fencer(
            last_name="张",
            first_name="三",
            nationality="CHN",
            birth_date=date(2000, 1, 1)
        )

        fencer3 = Fencer(
            last_name="李",
            first_name="四",
            nationality="CHN",
            birth_date=date(2000, 1, 1)
        )

        # 相同选手应该相等
        assert fencer1 == fencer2

        # 不同选手应该不相等
        assert fencer1 != fencer3

        # 与非Fencer对象比较
        assert fencer1 != "not a fencer"
        assert fencer1 is not None

    def test_hash(self):
        """测试哈希值"""
        fencer1 = Fencer(
            last_name="张",
            first_name="三",
            nationality="CHN",
            birth_date=date(2000, 1, 1)
        )

        fencer2 = Fencer(
            last_name="张",
            first_name="三",
            nationality="CHN",
            birth_date=date(2000, 1, 1)
        )

        fencer3 = Fencer(
            last_name="李",
            first_name="四",
            nationality="CHN",
            birth_date=date(2000, 1, 1)
        )

        # 相同选手应该有相同哈希
        assert hash(fencer1) == hash(fencer2)

        # 不同选手应该有不同的哈希
        assert hash(fencer1) != hash(fencer3)

        # 可以放入集合
        fencer_set = {fencer1, fencer2, fencer3}
        assert len(fencer_set) == 2  # fencer1和fencer2相同