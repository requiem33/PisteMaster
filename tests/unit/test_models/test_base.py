"""
BaseModel 基类测试
"""

import pytest
from core.models.base import BaseModel


class ConcreteModel(BaseModel):
    """用于测试的具体模型实现"""

    def __init__(self, value):
        self.value = value

    def validate(self):
        if not self.value:
            raise ValueError("值不能为空")


class TestBaseModel:
    """BaseModel测试类"""

    def test_abstract_method(self):
        """测试抽象方法要求"""
        # 不能直接实例化抽象类
        with pytest.raises(TypeError):
            BaseModel()

    def test_concrete_model(self):
        """测试具体模型实现"""
        model = ConcreteModel("test")
        assert model.value == "test"

        # 测试验证
        model.validate()

        # 测试无效验证
        invalid_model = ConcreteModel("")
        with pytest.raises(ValueError, match="值不能为空"):
            invalid_model.validate()

    def test_to_dict_default(self):
        """测试默认的to_dict方法"""
        model = ConcreteModel("test")
        assert model.to_dict() == {}

    def test_str_representation(self):
        """测试字符串表示"""
        model = ConcreteModel("test")
        assert str(model) == "ConcreteModel"
        assert "ConcreteModel" in repr(model)
