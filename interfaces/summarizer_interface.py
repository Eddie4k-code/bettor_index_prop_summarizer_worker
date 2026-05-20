from abc import ABC, abstractmethod


class ISummarizerInterface(ABC):
    @abstractmethod
    def summarize(self, market_key: str) -> None:
        pass