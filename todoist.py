"""
A Wrapper for the Todoist API
"""

from cred_manage.bitwarden import make_bitwarden_container
import json
import requests 
import os
import sys

def make_todoist_api(config_file='config.json'):
    """
    A factory function to init a TodoistAPI object by reading the API key from a bitwarden vault.
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

    def _do_get(self, url:str, headers:dict={}, params:dict={}, expected_status_code=200):
        """
        Does a GET request to the API and returns the result.  That's it.
        The caller should to subsequent processing.

        Args:
            url ([string]): The URL to do the GET request on
            headers (dict, optional): Any headers that need to be passed along.  We'll update() in auth as needed. Defaults to {}.
            parameters (dict, optional):  A dictionary of URL parameters to be passed along
            expected_status_code (int or list of int, optional): An integer or list of integers corresponding with the http request code that we would expect to get back
                200 is the default which means ok
                204, might also be acceptable when updating a task, for example
                See:  https://en.wikipedia.org/wiki/List_of_HTTP_status_codes
                See:  https://developer.todoist.com/rest/v1/#overview
        """

        # Handle the expected response(s)
        err_msg = f"The expected_response argument should be an integer or list of integers corresponding with http status codes.  \nSee:  https://en.wikipedia.org/wiki/List_of_HTTP_status_codes\nSee:  https://developer.todoist.com/rest/v1/#overview"
        if type(expected_status_code) not in [int, list]:
            raise ValueError(err_msg)
        if type(expected_status_code) is not list:
            expected_status_code = [expected_status_code]
        for c in expected_status_code:
            if type(c) is not int:
                raise ValueError(err_msg)

        # Merge Authorization into headers object as needed
        if not headers:
            headers = self.auth_header
        else:
            if 'Authorization' not in headers.keys():
                headers.update(self.auth_header)

        result = requests.get(url=url, headers=headers, params=params)

        # Raise and exception if something bad happened
        status_code = result.status_code
        if status_code not in expected_status_code:
            result.raise_for_status()

        return result
    
    def get_all_projects(self):
        """
        Returns the projects under the todoist account.  
        See:  https://developer.todoist.com/rest/v1/#get-a-user-39-s-projects
        """

        method = "projects"
        endpoint_url = f"{self.base_url}{method}"

        result = self._do_get(url=endpoint_url)
        
        projects = result.json()

        return projects

    def get_active_tasks(self, project_id:int=None, section_id:int=None, label_id:int=None, filter:str=None, lang:str=None, ids:list=None):
        """
        Returns tasks, which may be filtered using one or more of the parameters as documented here: 
            https://developer.todoist.com/rest/v1/?shell#get-active-tasks

        Args:
            project_id (int, optional): Filters Tasks by Project ID. Defaults to None.
            section_id (int, optional): Filters Tasks by section ID. Defaults to None.
            label_id (int, optional): Filters Tasks by Label ID. Defaults to None.
            filter (str, optional): Filters tasks by any supported filter. Defaults to None.  
                See:  https://todoist.com/help/articles/introduction-to-filters
            lang (str, optional): IETF language tag defining what language filter is written in, if differs from default English. Defaults to None.
            ids (list, optional): 	A list of the task IDs to retrieve, this should be a comma separated list. Defaults to None.
        """

        # Validate Project ID
        if project_id is not None and type(project_id) is not int:
            raise ValueError(f"project_id, if supplied must be an integer.  Got {type(project_id)}.  See:  https://developer.todoist.com/rest/v1/?shell#get-active-tasks")

        # Validate Section ID
        if section_id is not None and type(section_id) is not int:
            raise ValueError(f"section_id, if supplied must be an integer.  Got {type(section_id)}.  See:  https://developer.todoist.com/rest/v1/?shell#get-active-tasks")

        # Validate Label ID
        if label_id is not None and type(label_id) is not int:
            raise ValueError(f"label_id, if supplied must be an integer.  Got {type(label_id)}.  See:  https://developer.todoist.com/rest/v1/?shell#get-active-tasks")

        # Validate Filter.  We'll leave most of the rest of the validation up to the API.
        if filter is not None and type(filter) is not str:
            raise ValueError(f"filter, if supplied must be a string.  Got {type(filter)}.  See:  https://developer.todoist.com/rest/v1/?shell#get-active-tasks")

        # Validate Lang.  We'll leave most of the rest of the validation up to the API.
        if lang is not None and type(lang) is not str:
            raise ValueError(f"lang, if supplied must be a string.  Got {type(lang)}.  See:  https://developer.todoist.com/rest/v1/?shell#get-active-tasks")

        # Validate IDs
        if ids is not None and type(ids) is not list:
            raise ValueError(f"ids, if supplied but be a list of integers.  Got {type(ids)}.  See:  https://developer.todoist.com/rest/v1/?shell#get-active-tasks")
        if type(ids) is list:
            if len(ids) >=1:
                for i in ids:
                    if type(i) is not int:
                        raise ValueError(f"ids, if supplied must be a list of integers.  Encountered the value {i} which is type {type(i)}.  See:  https://developer.todoist.com/rest/v1/?shell#get-active-tasks")
            else:
                print(f"Warning:  An empty list was passed in for the 'ids' argument.  Coercing to None.", file=sys.stderr)
                ids = None

        # Construct a dict of truthy arguments
        params = {}
        if project_id is not None:
            params['project_id'] = project_id
        if section_id is not None:
            params['section_id'] = section_id
        if label_id is not None:
            params['label_id'] = label_id
        if filter is not None:
            params['filter'] = filter
        if lang is not None:
            params['lang'] = lang
        if ids is not None:
            params['ids'] = ids

        # Prepare the request
        method = "tasks"
        endpoint_url = f"{self.base_url}{method}"

        # Submit the request
        result = self._do_get(url=endpoint_url, params=params)

        # Return the results.
        tasks = result.json()
        return tasks

    def get_all_tasks(self):
        """
        A wrapper method, for convenience around get_active_tasks(), and provides no arguments.  
        The returned payload then, will simply be all active tasks
        """

        all_tasks = self.get_active_tasks() # No args means no filtering will take place
        return all_tasks

    def get_task_by_id(self, task_id:int):
        """
        Returns a single task based on the ID of that task.

        Args:
            task_id (int): [description]
        """

        # Validate the data type of the task ID
        if type(task_id) is not int:
            raise ValueError(f"task_id argument should be an integer.  Got {type(task_id)}")

        method = "tasks"
        endpoint_url = f"{self.base_url}{method}/{task_id}"  # Here, we simply suffix the task ID in question

        result = self._do_get(url=endpoint_url)
        task = result.json()

        return task


if __name__ == '__main__':
    td = make_todoist_api()
    projects=td.get_all_projects()
    # print(json.dumps(projects, indent=4))
    print(json.dumps(td.get_task_by_id(task_id=5374849640999), indent=4))
