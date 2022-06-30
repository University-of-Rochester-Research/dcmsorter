from abc import ABC, abstractmethod


class AbstractApi(ABC):
    @abstractmethod
    def study_path(self, clean_tags: dict, patterns: dict):
        return patterns

    @abstractmethod
    def archive_path(self, clean_tags: dict, patterns: dict):
        return patterns