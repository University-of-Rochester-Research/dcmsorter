import json
import os

from AbstractApi import AbstractApi
from common import CONFIG_PATH, ExitCodes, error_print

try:
    with open(os.path.join(CONFIG_PATH,"studies.json")) as json_file:
        StudiesConfig = json.load(json_file)
except FileNotFoundError:
    error_print(f"{CONFIG_PATH}/studies.json not found")
    exit(ExitCodes.MISSING_CONFIG)


class FileApi(AbstractApi):
    def archive_path(self, tags: dict, patterns: dict):
        return self.study_path(tags, patterns)

    def study_path(self, tags: dict, patterns: dict):
        ProtocolConfig = StudiesConfig.get(f"protocol:{tags['ProtocolName']}", {})
        StudyConfig = StudiesConfig.get(f"studyname:{tags['StudyName']}", {})

        Config = {**StudyConfig, **ProtocolConfig}

        patterns["sort_path_pattern"] = Config.get("sort_path_pattern",patterns["sort_path_pattern"])
        patterns["sort_file_pattern"] = Config.get("sort_file_pattern",patterns["sort_file_pattern"])
        patterns["archive_path_pattern"] = Config.get("archive_path_pattern",patterns["archive_path_pattern"])
        patterns["archive_file_pattern"] = Config.get("archive_file_pattern",patterns["archive_file_pattern"])

        return patterns