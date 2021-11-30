"""
A Wrapper for the Todoist API
"""

from cred_manage.bitwarden import make_bitwarden_container
import json
import requests 
import os

def make_todoist_api(config_file='config.json'):
    """
    A factory method to init a TodoistAPI object by reading the API key from a bitwarden vault.
    The GUID (Not to be confused with the API key itself) for the BW Vault item is read from 
    a config file

    Returns:
        [type]: [description]
    """

    # Read the config file, which contains the bitwarden GUID corresponding with the API key
    if not os.path.isfile(config_file):
        raise FileNotFoundError(f"Cannot read from config file '{config_file}' because it does not exist!")
    else:
        with open(config_file, 'r') as f:
            s = f.read()
    j = json.loads(s)
    bitwarden_todoist_api_guid = j['config']['todoistApiTokenGuid']  #This is a GUID that points to the API key in bitwarden

    # Retrieve the actual API key from bitwarden
    bw = make_bitwarden_container()
    todoist_api_key = bw.get_password_by_guid(bitwarden_todoist_api_guid)

    # Instantiate TodoistAPI object and return it 
    todoist = TodoistAPI(api_key=todoist_api_key)
    return todoist


class TodoistAPI():

    def __init__(self, api_key:str):
        """
        init method for the Todoist API wrapper

        Args:
            api_key (str): The API key used to interact with the Todoist API.  
                See:  https://developer.todoist.com/rest/v1/#javascript-sdk
        """
        
        
        # Pin the api key that we just read out of bitwarden to self
        self.api_key = api_key
        self.auth_header = {"Authorization": f"Bearer {self.api_key}"}

        # Handle the base URL
        self.base_url = "https://api.todoist.com/rest/v1/" # method endpoints get concatendated onto this

    def _do_get(self, url:str, headers:dict={}, params:dict={}):
        """
        Does a GET request to the API and returns the result.  That's it
        The caller should to subsequent processing on the status code

        Args:
            url ([string]): The URL to do the GET request on
            headers (dict, optional): Any headers that need to be passed along.  We'll update() in auth as needed. Defaults to {}.
            parameters (dict, optional):  A dictionary of URL parameters to be passed along
        """

        # Merge Authorization into headers object as needed
        if not headers:
            headers = self.auth_header
        else:
            if 'Authorization' not in headers.keys():
                headers.update(self.auth_header)

        result = requests.get(url=url, headers=headers, params=params)

        # Raise and exception if something bad happened
        if not requests.codes.ok:
            result.raise_for_status()

        return result
    
    def get_projects(self):
        """
        Returns the projects under the todoist account.  
        See:  https://developer.todoist.com/rest/v1/#get-a-user-39-s-projects
        """

        method = "projects"
        endpoint_url = f"{self.base_url}{method}"

        result = self._do_get(url=endpoint_url)
        
        projects = result.json()

        return projects





        print("!")

        
        



        

        print("!")


if __name__ == '__main__':
    td = make_todoist_api()
    print("!")