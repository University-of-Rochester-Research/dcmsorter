import json

from AbstractApi import AbstractApi
from common import CONFIG_DIR, ExitCodes, error_print


class FileApi(AbstractApi):
    def archive_path(self, tags: dict, patterns: dict):
        return self.study_path(tags, patterns)

    def study_path(self, tags: dict, patterns: dict):
        try:
            with open(f'{CONFIG_DIR}/studies.json') as json_file:
                StudiesConfig = json.load(json_file)
        except FileNotFoundError:
            error_print(f"{CONFIG_DIR}/studies.json not found")
            exit(ExitCodes.MISSING_CONFIG)

        DefaultConfig = StudiesConfig.get("default", {})
        ProtocolConfig = StudiesConfig.get(tags['ProtocolName'], {})
        StudyConfig = StudiesConfig.get(tags['StudyName'], {})

        Config = {**DefaultConfig, **ProtocolConfig, **StudyConfig}

        patterns["sort_path_pattern"] = Config.get("sort_path_pattern",patterns["sort_path_pattern"])
        patterns["sort_file_pattern"] = Config.get("sort_file_pattern",patterns["sort_file_pattern"])
        patterns["archive_path_pattern"] = Config.get("archive_path_pattern",patterns["archive_path_pattern"])
        patterns["archive_file_pattern"] = Config.get("archive_file_pattern",patterns["archive_file_pattern"])

        return patterns

