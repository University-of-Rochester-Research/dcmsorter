import os

from requests_cache import install_cache

# Initiate a 1 hour cache
from requests import RequestException, get
from requests.auth import HTTPBasicAuth

from AbstractApi import AbstractApi
from common import error_print, debug_print, CONFIG_PATH

install_cache(f'{CONFIG_PATH}/dcmsorter_cache', expire_after=3600)


class CalpendoConfig(object):
    CALPENDO_USER = os.environ.get("CALPENDO_USER", "user")
    CALPENDO_PASS = os.environ.get("CALPENDO_PASS", "pass")
    CALPENDO_URL = os.environ.get("CALPENDO_URL", "https://calpendohost/webdav/")


class CalpendoApi(AbstractApi):
    def archive_path(self, tags: dict, patterns: dict):
        # TODO: Implement archivePath in Calpendo
        return patterns

    # This function gets only the data path. Should ALWAYS return an os.path compatible path or an
    # URL (eg. rclone://config/targetdirectory) if you implemented the URL handler
    def study_path(self, tags: dict, patterns: dict):
        study_name = tags['StudyName']
        protocol_name = tags['ProtocolName']
        # TODO: Implement Protocol + Study search
        # Get all the study info in cache
        data = self.study_info(study_name)

        # Path is not set, go to a default location
        if not data or "dataPath" not in data:
            debug_print(f"Project {study_name} not found in Calpendo")
            return patterns

        # We already tested for the existence of data['dataPath']
        # Check if dataPath starts with a Windows-style path
        if data['dataPath'].startswith(r"\\"):
            # Path is a Windows UNC, translate to a Unix Path
            data['dataPath'] = data['dataPath'].replace("\\", "/")

        # There is a sorting pattern in the study and it has a value
        if data.get('pathPattern', False):
            patterns['sort_path_pattern'] = f"$OUTGOING_DIR/{data['pathPattern']}"

        # There is a file pattern in the study and it has a value
        if data.get('filePattern', False):
            patterns['sort_file_pattern'] = data['filePattern']

        # If data['dataPath'] is not an empty value (eg. '')
        # Replace the OUTGOING dir in the patterns
        if data['dataPath']:
            patterns['sort_path_pattern'] = patterns['sort_path_pattern'].replace("$OUTGOING_DIR", data['dataPath'])

        return patterns

    def get_calpendo_url(self, url, params=None):
        baseurl = CalpendoConfig.CALPENDO_URL

        try:
            resp = get(url=baseurl + url,
                       auth=HTTPBasicAuth(CalpendoConfig.CALPENDO_USER,
                                          CalpendoConfig.CALPENDO_PASS),
                       params=params)
            debug_print("Response:")
            debug_print(resp)
            resp.raise_for_status()
            data = resp.json()
        except RequestException as e:
            error_print(e)
            return None

        debug_print("Returned URL Data:")
        debug_print(data)

        return data

    def study_info(self, study_name: str):
        # Search for the Project ID
        url = 'q/Calpendo.Project/projectCode/EQ/' + study_name + '/'
        res = self.get_calpendo_url(url)
        if not res or not res['biskits']:
            debug_print(f"Project {study_name} not found")
            return None

        project_biskit = res['biskits'][0]

        # Get the Project Properties
        url = '/b/Calpendo.Project/' + str(project_biskit['id'])
        res = self.get_calpendo_url(url)
        if not res or not res['properties']:
            debug_print(f"Project {study_name} has no properties")
            return None

        project = res["properties"]

        debug_print("Returned Project Data:")
        debug_print(project)

        return project
