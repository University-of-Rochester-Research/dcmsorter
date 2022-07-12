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

DEBUG = environ.get("DEBUG", True)

INCOMING_DIR = environ.get("MERCURE_IN_DIR", "/in")
OUTGOING_DIR = environ.get("OUTGOING_DIR", "/out")
ARCHIVE_DIR = environ.get("ARCHIVE_DIR", "/archive")
CONFIG_PATH = environ.get("CONFIG_DIR", "/app/config")

if not Path(INCOMING_DIR).exists() or not Path(OUTGOING_DIR).exists():
    error_print("IN/OUT paths do not exist")
    sys.exit(ExitCodes.MISSING_CONFIG)

DEFAULT_SORT_FILE_PATTERN = environ.get("DEFAULT_SORT_FILE_PATTERN",
                                        f"$SubjectName.$DateStamp.$TimeStamp.$SeriesNumber.$SeriesDescription."
                                        f"Echo_$EchoNumbers.$InstanceNumber.dcm")
DEFAULT_SORT_PATH_PATTERN = environ.get("DEFAULT_SORT_PATH_PATTERN",
                                        "$OUTGOING_DIR/$StudyName/$ProtocolName/"
                                        "$SubjectName/$DateStamp/$SeriesNumber.$SeriesDescription")
DEFAULT_ARCHIVE_PATH_PATTERN = environ.get("DEFAULT_ARCHIVE_PATH_PATTERN", "$ARCHIVE_DIR/$StudyName/$ProtocolName")
DEFAULT_ARCHIVE_FILE_PATTERN = environ.get("DEFAULT_ARCHIVE_FILE_PATTERN",
                                           "$SubjectName.$DateStamp.$TimeStamp.$SeriesNumber.$SeriesDescription.tar")

settings: dict = {}
stations: dict = {}

try:
    # Open the stations.json file
    with open(os.path.join(CONFIG_PATH, 'stations.json'), 'r') as json_file:
        stations = json.load(json_file)
except FileNotFoundError:
    debug_print("No stations.json found, maybe it is in task.json")
except JSONDecodeError:
    error_print("Invalid JSON file stations.json")
    sys.exit(ExitCodes.MISSING_CONFIG)

try:
    # Check if we're in Mercure
    with open(os.path.join(INCOMING_DIR, "task.json"), "r") as json_file:
        task: dict = json.load(json_file)

    # Get the process
    if task.get("process", False):
        # Get the settings
        settings = task["process"].get("settings", {})
        if settings:
            # Overwrite any existing stations
            stations.update(settings.get("stations", {}))
except FileNotFoundError:
    debug_print("No task.json found, not in Mercure?")
except JSONDecodeError:
    error_print("Invalid JSON file task.json")
    sys.exit(ExitCodes.MISSING_CONFIG)

if not stations:
    error_print("No list of stations found")
    sys.exit(ExitCodes.MISSING_CONFIG)