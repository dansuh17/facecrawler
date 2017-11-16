from abc import ABCMeta
from abc import abstractmethod


class CrawlerEngine(metaclass=ABCMeta):
    """
    Defines abstract methods for a crawler engine.
    """
    @abstractmethod
    def download(self, img_src, folder_name):
        pass

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def close(self):
        pass

    @classmethod
    def __subclasshook__(cls, C):
        if cls is CrawlerEngine:
            if any('download' in B.__dict__ and 'start' in B.__dict__
                    and 'close' in B.__dict__
                    and '__call__' for B in C.__mro__):
                return True
        return NotImplemented

