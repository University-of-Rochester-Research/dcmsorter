import os

from requests_cache import install_cache

# Initiate a 1 hour cache
from requests import RequestException, get
from requests.auth import HTTPBasicAuth

from AbstractApi import AbstractApi
from common import error_print, debug_print, OUTGOING_DIR

install_cache('/app/config/dcmsorter_cache', expire_after=3600)


class CalpendoConfig(object):
    CALPENDO_USER = os.environ.get("CALPENDO_USER", "user")
    CALPENDO_PASS = os.environ.get("CALPENDO_PASS", "pass")
    CALPENDO_URL = os.environ.get("CALPENDO_URL", "https://calpendohost/webdav/")


class CalpendoApi(AbstractApi):
    def archive_path(self, clean_tags: dict, patterns: dict):
        # TODO: Implement archivePath in Calpendo
        return patterns

    # This function gets only the data path. Should ALWAYS return an os.path compatible path or an
    # URL (eg. rclone://config/targetdirectory) if you implemented the URL handler
    def study_path(self, clean_tags: dict, patterns: dict):
        study_name = clean_tags['StudyName']
        protocol_name = clean_tags['ProtocolName']
        # TODO: Implement Protocol + Study search
        # Get all the study info in cache
        data = self.study_info(study_name)

        # Path is not set, go to a default location
        if not data or not data['dataPath']:
            debug_print(f"Project {study_name} does not exist or has no dataPath")
            return patterns

        # Path is a Windows UNC, translate to a Unix Path
        if data['dataPath'].startswith(r"\\"):
            data['dataPath'] = data['dataPath'].replace("\\", "/")

        debug_print("Returned Path:")
        debug_print(data['dataPath'])

        # TODO: Implement custom path and file patterns in Calpendo
        patterns['sort_path_pattern'] = f"{data['dataPath']}/{protocol_name}/$SubjectName/$DateStamp/$SeriesNumber.$SeriesDescription"

        return patterns

    def get_calpendo_url(self, url, params=None):
        baseurl = CalpendoConfig.CALPENDO_URL

        try:
            resp = get(url=baseurl + url,
                       auth=HTTPBasicAuth(CalpendoConfig.CALPENDO_USER,
                                          CalpendoConfig.CALPENDO_PASS),
                       params=params)
            resp.raise_for_status()
            data = resp.json()
        except RequestException as e:
            error_print(e)
            return None

        debug_print("Returned URL Data:")
        debug_print(data)

        return data

    def study_info(self, study):
        # Search for the Project ID
        url = 'q/Calpendo.Project/projectCode/EQ/' + study + '/'
        res = self.get_calpendo_url(url)
        if not res or not res['biskits']:
            error_print(f"Error: Project {study} not found")
            return None

        project_biskit = res['biskits'][0]

        # Get the Project Properties
        url = '/b/Calpendo.Project/' + str(project_biskit['id'])
        res = self.get_calpendo_url(url)
        if not res or not res['properties']:
            error_print(f"Error: Project {study} has no properties")
            return None

        project = res["properties"]

        debug_print("Returned Project Data:")
        debug_print(project)

        return project
