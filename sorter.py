#!python
# cython: language_level=3
import filecmp
import hashlib
import os
import re
import shutil
import tarfile
import unicodedata
from string import Template

from pydicom import filereader
from pydicom.errors import InvalidDicomError

from common import *

api_config = os.environ.get('API', 'FILE')
if api_config == "CALPENDO":
    from api_CALPENDO import CalpendoApi as API
else:
    from api_FILE import FileApi as API

api = API()
filenames = []


def get_valid_filename(s):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py

    Return the given string converted to a string that can be used for a clean
    filename. Remove leading and trailing spaces; convert other spaces to
    underscores; and remove anything that is not an alphanumeric, dash,
    underscore, or dot.
    >>> get_valid_filename("john's portrait in 2004.jpg")
    'johns_portrait_in_2004.jpg'
    """
    # Cast as string and Normalize Unicode characters to ASCII
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode('ascii')

    # strip leading and trailing whitespace; then replace spaces with _
    s = re.sub(r'\s+', '_', s.strip())

    # switch to ASCII mode, remove things that aren't dashes, words ([a-zA-Z0-9_]) or dots
    s = re.sub(r'(?a)[^-\w.]', '', s)

    return s


def get_header(tag, ds, validate=True):
    try:
        out = ds.data_element(tag).value
    except (AttributeError, KeyError) as err:
        # Simply print it as an error, but continue constructing the folder
        error_print(f"Missing tag: {tag}")

        # If its not okay for the key to be missing, exit
        return ""

    if validate:
        out = get_valid_filename(out)

    return out


# r=root, d=directories, f = files
series = {}
for entry in os.scandir(INCOMING_DIR):
    if entry.name.endswith(".dcm") and not entry.is_dir():
        # Get the Series UID from the file name
        seriesString = entry.name.split("#", 1)[0]
        # If this is the first image of the series, create new file list for the series
        if seriesString not in series.keys():
            series[seriesString] = []
        # Add the current file to the file list
        series[seriesString].append(entry.name)

debug_print(f"All Series:\n {series}")

if not series:
    print("No files found to be processed")
    sys.exit(ExitCodes.NOTHING_TO_DO)

# Keep track of duplicate files
dup_files = {}


def archive_file(file: str, tags: dict, patterns: dict, tars: dict):
    patterns = api.archive_path(tags=tags, patterns=patterns)

    try:
        path_template = Template(patterns['archive_path_pattern'])
        output_path = path_template.substitute(**tags)
        os.makedirs(output_path, exist_ok=True)
    except OSError:
        error_print(f"Error creating output directory {output_path}")
        exit(ExitCodes.OSERROR)

    try:
        archive_filename_template = Template(patterns['archive_file_pattern'])
        archive_filename = archive_filename_template.substitute(**tags)
        in_file = f"{INCOMING_DIR}/{file}"
        out_file = f"{output_path}/{archive_filename}"
        if out_file not in tars:
            # This will append duplicate files
            tars[out_file] = tarfile.open(out_file, "a:")
        with open(in_file, "rb") as f:
            file_mem = f.read()  # read entire file as bytes
            readable_hash = hashlib.sha256(file_mem).hexdigest()

        # If study has same file multiple times, don't keep adding to tar
        if readable_hash not in dup_files:
            tars[out_file].add(in_file, arcname=f"{readable_hash}.dcm")
            dup_files[readable_hash] = in_file

    except OSError:
        error_print(f"Error archiving {in_file} into {out_file}")
        exit(ExitCodes.OSERROR)


def sort_file(file: str, tags: dict, patterns: dict):
    patterns = api.study_path(tags=tags, patterns=patterns)

    try:
        path_template = Template(patterns['sort_path_pattern'])
        output_path = path_template.substitute(**tags)
        os.makedirs(output_path, exist_ok=True)
    except OSError:
        error_print(f"Error creating output directory {output_path}")
        exit(ExitCodes.OSERROR)

    try:
        file_template = Template(patterns['sort_file_pattern'])
        output_filename = file_template.substitute(**tags)
        output_location = f"{output_path}/{output_filename}"
        input_location = f"{INCOMING_DIR}/{file}"
        count = 0
        while os.path.exists(output_location) and not filecmp.cmp(input_location, output_location):
            count += 1
            output_location = output_location.replace(".dcm", f"-v{count}.dcm")
        shutil.copy(input_location, output_location)
    except OSError as e:
        error_print(f"Error copying {file} to {output_path}/{output_filename}")
        debug_print(e)
        exit(ExitCodes.OSERROR)


for seriesString in series:
    tar_files = {}
    debug_print(f"Series:\n {seriesString}")
    debug_print(f"List of Filenames:\n {series[seriesString]}")
    for filename in series[seriesString]:
        # Make sure we have a valid DICOM
        print(f"Processing {filename}")

        try:
            dataset = filereader.dcmread(f"{INCOMING_DIR}/{filename}")
        except InvalidDicomError:
            error_print(
                f"{filename} is missing DICOM File Meta Information header or the 'DICM' prefix is missing from the "
                f"header - skipping")
            continue

        # Find Station Name, each Station has different methods of encoding Study Names
        StationName = get_header("StationName", ds=dataset)
        print(f"Station Name: {StationName}")
        StationConfig = stations.get(StationName, stations.get("default"))

        StudyTag = StationConfig.get('TagForStudy', 'StudyDescription')
        StudyName = get_header(StudyTag, ds=dataset, validate=False)

        if not StudyName:
            error_print(f"Bad DICOM {filename}: {StudyTag} not present")
            continue

        # stations.json can define splitting a header
        if StationConfig.get('StudySplit', False):
            study_split_list = StudyName.split(StationConfig['StudySplit'])
            study_split_index = StationConfig.get('StudySplitIndex', 0)

            # If the index is misconfigured, we go out of bounds
            if len(study_split_list) <= study_split_index:
                error_print(f"Potentially bad configuration: {StudyName} does not conform to StudySplit config")
                study_split_index = len(study_split_list) - 1

            StudyName = study_split_list[study_split_index]

        # Get the Protocol Name
        ProtocolTag = StationConfig.get('TagForProtocol', 'StudyDescription')
        ProtocolName = get_header(ProtocolTag, ds=dataset, validate=False)

        if StationConfig.get('ProtocolSplit', False):
            protocol_split_list = ProtocolName.split(StationConfig['ProtocolSplit'])
            protocol_split_index = StationConfig.get('ProtocolSplitIndex', 0)
            # If the index is misconfigured, we go out of bounds
            debug_print(f"Protocol Split List: {protocol_split_list}")
            debug_print(f"Protocol Split Index {protocol_split_index}")
            if len(protocol_split_list) <= protocol_split_index:
                error_print(f"Potentially bad configuration: {StudyName} does not conform to ProtocolSplit config")
                protocol_split_index = len(protocol_split_list) - 1
                debug_print(f"Protocol Split Index {protocol_split_index}")

            ProtocolName = protocol_split_list[protocol_split_index]

        if not ProtocolName:
            error_print(f"Bad DICOM {filename}: {ProtocolTag} not present")
            continue

        print(f'Study from {StudyTag}: {StudyName}')
        print(f'Protocol from {ProtocolTag}: {ProtocolName}')

        ProtocolName = get_valid_filename(ProtocolName)
        StudyName = get_valid_filename(StudyName)

        if not ProtocolName or not StudyName:
            error_print(f"Bad DICOM {filename}: Cannot make valid filename from {StudyTag} or {ProtocolTag}")
            continue

        # Get the Relevant Information From DICOM
        CleanTags = {
            "ProtocolName": ProtocolName,
            "StudyName": StudyName,
            "SubjectName": get_header('PatientName', dataset),
            "DateStamp": get_header('SeriesDate', dataset),
            "TimeStamp": get_header('SeriesTime', dataset).split('.')[0],
            "SeriesNumber": get_header('SeriesNumber', dataset),
            "InstanceNumber": get_header("InstanceNumber", dataset).rjust(5, "0"),
            "SeriesDescription": get_header("SeriesDescription", dataset),
            "EchoNumbers": get_header("EchoNumbers", dataset),
            "SeriesInstanceUID": get_header("SeriesInstanceUID", dataset),
            "StudyInstanceUID": get_header("StudyInstanceUID", dataset),
            "SOPInstanceUID": get_header("SOPInstanceUID", dataset)
        }

        SortPathPattern = StationConfig.get("sort_path_pattern", DEFAULT_SORT_PATH_PATTERN)
        SortFilePattern = StationConfig.get("sort_file_pattern", DEFAULT_SORT_FILE_PATTERN)
        ArchivePathPattern = StationConfig.get("archive_path_pattern", DEFAULT_ARCHIVE_PATH_PATTERN)
        ArchiveFilePattern = StationConfig.get("archive_file_pattern", DEFAULT_ARCHIVE_FILE_PATTERN)

        Patterns = {
            "sort_path_pattern": SortPathPattern,
            "sort_file_pattern": SortFilePattern,
            "archive_path_pattern": ArchivePathPattern,
            "archive_file_pattern": ArchiveFilePattern
        }

        debug_print(f"Sorting Pattern (Config):\n {Patterns}")
        if StationConfig.get("sort", True):
            sort_file(filename, CleanTags, Patterns)

        if StationConfig.get("archive", True) and ARCHIVE_DIR and ARCHIVE_DIR != "None":
            archive_file(filename, CleanTags, Patterns, tar_files)

    for item in tar_files.values():
        item.close()
