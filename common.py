import json
import os
import sys
from json import JSONDecodeError
from pathlib import Path
from sys import stderr, stdout
from os import environ


def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, file=stdout, **kwargs)


def error_print(*args, **kwargs):
    print(*args, file=stderr, **kwargs)


# Exit codes:
# 0 - all good
# 1 - nothing to do (eg. missing filenames)
# 2 - issue making outside calls (eg. to API)
# 3 - missing configuration files (eg. stations.json)
# 4 - missing critical headers in filenames (eg. StudyName)
# 5 - error writing files or other OS error (read only filesystem etc)
class ExitCodes:
    OK = 0
    NOTHING_TO_DO = 1
    CONNECT_ERROR = 2
    MISSING_CONFIG = 3
    MISSING_HEADERS = 4
    OSERROR = 5


INCOMING_DIR = environ.get("MERCURE_IN_DIR", "/in")
MERCURE_OUT_DIR = environ.get("MERCURE_OUT_DIR", "/out")
OUTGOING_DIR = environ.get("OUTGOING_DIR", MERCURE_OUT_DIR)
ARCHIVE_DIR = environ.get("ARCHIVE_DIR", "/archive")
CONFIG_PATH = environ.get("CONFIG_DIR", "/app/config")
DEBUG = environ.get("DEBUG", False)
DEFAULT_SORT_FILE_PATTERN = environ.get("DEFAULT_SORT_FILE_PATTERN",
                                        f"$SubjectName.$DateStamp.$TimeStamp.$SeriesNumber.$SeriesDescription."
                                        f"Echo_$EchoNumbers.$InstanceNumber.dcm")
DEFAULT_SORT_PATH_PATTERN = environ.get("DEFAULT_SORT_PATH_PATTERN",
                                        f"{OUTGOING_DIR}/$StudyName/$ProtocolName/"
                                        f"$SubjectName/$DateStamp/$SeriesNumber.$SeriesDescription")
DEFAULT_ARCHIVE_PATH_PATTERN = environ.get("DEFAULT_ARCHIVE_PATH_PATTERN", f"{ARCHIVE_DIR}/$StudyName/$ProtocolName")
DEFAULT_ARCHIVE_FILE_PATTERN = environ.get("DEFAULT_ARCHIVE_FILE_PATTERN",
                                           f"$SubjectName.$DateStamp.$TimeStamp."
                                           f"$SeriesNumber.$SeriesDescription.tar")

try:
    with open(os.path.join(CONFIG_PATH, 'stations.json'), 'r') as json_file:
        stations: dict = json.load(json_file)

    with open(os.path.join(INCOMING_DIR, "task.json"), "r") as json_file:
        task: dict = json.load(json_file)

except FileNotFoundError:
    error_print("No stations.json and/or task.json found")
    sys.exit(ExitCodes.MISSING_CONFIG)
except JSONDecodeError:
    error_print("Invalid JSON file stations.json and/or task.json")
    sys.exit(ExitCodes.MISSING_CONFIG)

if task.get("process", False):
    settings = task["process"].get("settings", False)
    if settings:
        stations.update(settings.get("stations", {}))

if not Path(INCOMING_DIR).exists() or not Path(OUTGOING_DIR).exists():
    error_print("IN/OUT paths do not exist")
    sys.exit(ExitCodes.MISSING_CONFIG)
