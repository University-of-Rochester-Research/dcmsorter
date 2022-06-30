from sys import stderr, stdout
from os import environ

INCOMING_DIR = environ.get("MERCURE_IN_DIR", "/in")
MERCURE_OUT_DIR = environ.get("MERCURE_OUT_DIR", "/out")
OUTGOING_DIR = environ.get("OUTGOING_DIR", MERCURE_OUT_DIR)
ARCHIVE_DIR = environ.get("ARCHIVE_DIR", "/archive")
CONFIG_DIR = environ.get("CONFIG_DIR", "/app/config")
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
