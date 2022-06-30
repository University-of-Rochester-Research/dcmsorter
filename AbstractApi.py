from abc import ABC, abstractmethod


class AbstractApi(ABC):
    @abstractmethod
    def study_path(self, tags: dict, patterns: dict):
        return patterns

    @abstractmethod
    def archive_path(self, tags: dict, patterns: dict):
        return patterns