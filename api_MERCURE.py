from AbstractApi import AbstractApi
from common import settings


class MercureApi(AbstractApi):
    def get_setting(self, study_name):
        studies_config = settings.get("studies", False)
        if not studies_config:
            return {}

        studies_default = studies_config.get("default", {})
        study_config = studies_config.get(study_name, {})

        return {**studies_default, **study_config}

    def get_config(self, clean_tags):
        StudyConfig = self.get_setting(f"studyname:{clean_tags['StudyName']}")
        ProtocolConfig =  self.get_setting(f"protocolname:{clean_tags['ProtocolName']}")
        return {**StudyConfig, **ProtocolConfig}

    def study_path(self, tags: dict, patterns: dict):
        Config = self.get_config(tags)
        patterns["sort_path_pattern"] = Config.get("sort_path_pattern", patterns["sort_path_pattern"])
        patterns["sort_file_pattern"] = Config.get("sort_file_pattern", patterns["sort_file_pattern"])

        return patterns

    def archive_path(self, tags: dict, patterns: dict):
        Config = self.get_config(tags)
        patterns["archive_path_pattern"] = Config.get("archive_path_pattern", patterns["archive_path_pattern"])
        patterns["archive_file_pattern"] = Config.get("archive_file_pattern", patterns["archive_file_pattern"])

        return patterns
