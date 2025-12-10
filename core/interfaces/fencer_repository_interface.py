from abc import ABC, abstractmethod
from core.models.fencer import Fencer


class FencerRepositoryInterface(ABC):
    """Fencer 仓库的抽象定义。核心服务只依赖此接口。"""

    @abstractmethod
    def get_fencer_by_id(self, fencer_id: int) -> Fencer | None:
        pass

    @abstractmethod
    def save_fencer(self, fencer: Fencer) -> Fencer:
        pass
