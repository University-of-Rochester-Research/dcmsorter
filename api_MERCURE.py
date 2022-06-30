import json
import os
import sys
from json import JSONDecodeError

from AbstractApi import AbstractApi
from common import stations, INCOMING_DIR, error_print, ExitCodes

try:
    with open(os.path.join(INCOMING_DIR, "task.json"), "r") as json_file:
        task: dict = json.load(json_file)
except FileNotFoundError:
    error_print("No task.json found")
    sys.exit(ExitCodes.MISSING_CONFIG)
except JSONDecodeError:
    error_print("Invalid JSON file task.json")
    sys.exit(ExitCodes.MISSING_CONFIG)

settings = {}
if task.get("process", False):
    settings = task["process"].get("settings", {})
    if settings:
        stations.update(settings.get("stations", {}))


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
