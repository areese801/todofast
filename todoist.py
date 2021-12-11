"""
A Wrapper for the Todoist API
"""

from cred_manage.bitwarden import make_bitwarden_container
import json
import requests 
import os
import sys
import uuid

from requests import status_codes
from requests.api import head

# List of dicts below correspond with colors supported by todoist.  See:  https://developer.todoist.com/guides/#colors
TODOIST_COLORS = {
30: {"color_hex_code": "b8256f", "color_name": "berry_red"}, 
40: {"color_hex_code": "96c3eb", "color_name": "light_blue"}, 
31: {"color_hex_code": "db4035", "color_name": "red"}, 
41: {"color_hex_code": "4073ff", "color_name": "blue"}, 
32: {"color_hex_code": "ff9933", "color_name": "orange"}, 
42: {"color_hex_code": "884dff", "color_name": "grape"}, 
33: {"color_hex_code": "fad000", "color_name": "yellow"}, 
43: {"color_hex_code": "af38eb", "color_name": "violet"}, 
34: {"color_hex_code": "afb83b", "color_name": "olive_green"}, 
44: {"color_hex_code": "eb96eb", "color_name": "lavender"}, 
35: {"color_hex_code": "7ecc49", "color_name": "lime_green"}, 
45: {"color_hex_code": "e05194", "color_name": "magenta"}, 
36: {"color_hex_code": "299438", "color_name": "green"}, 
46: {"color_hex_code": "ff8d85", "color_name": "salmon"}, 
37: {"color_hex_code": "6accbc", "color_name": "mint_green"}, 
47: {"color_hex_code": "808080", "color_name": "charcoal"}, 
38: {"color_hex_code": "158fad", "color_name": "teal"}, 
48: {"color_hex_code": "b8b8b8", "color_name": "grey"}, 
39: {"color_hex_code": "14aaf5", "color_name": "sky_blue"}, 
49: {"color_hex_code": "ccac93", "color_name": "taupe"}
}

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
                See:  https://developer.todoist.com/rest/v1/?shell#authorization
        """
        
        
        # Pin the api key that we just read out of bitwarden to self
        self.api_key = api_key
        self.auth_header = {"Authorization": f"Bearer {self.api_key}"}

        # Handle the base URL
        self.base_url = "https://api.todoist.com/rest/v1/" # method endpoints get concatendated onto this

    def _do_get(self, url:str, headers:dict={}, params:dict={}, expected_status_code=200):
        """
        Does a GET request to the API and returns the result.  That's it.
        This function wraps _do_request
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

        result = self._do_request(http_method='GET', url=url, headers=headers, get_request_url_parameters=params, expected_status_code=expected_status_code)
        
        return result

    def _do_post(self, url:str, headers:dict={}, data:dict={}, expected_status_code=200):
        """
        Does a POST request to the API and returns the results.  That's it.
        The caller should do subsequent processing

        Args:
            url (str): The URL to do the POST request to
            headers (dict, optional): Any headers that need to be passed along.  We'll update() in auth as needed.  Defaults to {}.
            data (dict, optional): The dictionary payload to send in the POST request. Defaults to {}.
            expected_status_code (int, optional): An integer or list of integers corresponding with the http request code that we would expect to get back
                200 is the default which means ok
                204, might also be acceptable when updating a task, for example
                See:  https://en.wikipedia.org/wiki/List_of_HTTP_status_codes
                See:  https://developer.todoist.com/rest/v1/#overview
        """

        # Construct Headers as needed
        if 'Content-Type' not in headers.keys():
            headers['Content-Type'] = 'application/json'

        if 'X-Request-Id' not in headers.keys():
            headers['X-Request-Id'] = str(uuid.uuid1()).upper() # Todoist like a UUID to be passed in POSTS to avoid re-processing the same thing over and over
        
        result = self._do_request(http_method='POST', url=url, headers=headers, post_request_data=data, expected_status_code=expected_status_code)

        return result

    def _do_request(self, http_method:str, url:str, headers:dict={}, post_request_data:dict={}, get_request_url_parameters:dict={}, expected_status_code=200):
        """
        Does a request to the API with the corresponding 'verb' passed in the request_type argument

        Args:
            http_method (str): An HTTP method type.  GET, POST, etc.  
            url (str): The URL to do the GET request on
            headers (dict, optional): Any headers that need to be passed along.  We'll update() in auth as needed. Defaults to {}.
            post_request_data (dict, optional): The dictionary payload to send in the POST request. Defaults to {}.
            get_request_url_parameters (dict, optional): A dictionary of URL parameters to be passed along.  Used with GET requests
            expected_status_code (int, optional): An integer or list of integers corresponding with the http request code that we would expect to get back
                200 is the default which means ok
                204, might also be acceptable when updating a task, for example
                See:  https://en.wikipedia.org/wiki/List_of_HTTP_status_codes
                See:  https://developer.todoist.com/rest/v1/#overview
        """


        # Validate the method type
        http_method = http_method.upper()
        supported_http_methods = ['GET', 'POST']
        if http_method.upper() not in supported_http_methods:
            raise ValueError(f"{http_method} is not supported by this method.  Supported request types are: {supported_http_methods}")  

        #TODO:  If method is post validate that there is a payload here


        # Validate the expected response(s)
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

        # Make the API call
        if http_method == 'GET':
            result = requests.get(url=url, headers=headers, params=get_request_url_parameters)
        elif http_method == 'POST':
            result = requests.post(url=url, headers=headers, data=json.dumps(post_request_data))
        else:
            raise NotImplementedError(f"No handling is implemented for the HTTP method {http_method}")

        # Raise an exception if something bad happened
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


    def create_new_project(self, new_project_name:str, parent_project_id:int=None, color=None, is_favorite:bool=False):
        """
        Creates a new project
        See:  https://developer.todoist.com/rest/v1/#create-a-new-project

        Args:
            new_project_name (str): The project name
            parent_project_id (int, optional): The id of the parent project. Defaults to None.
            color: The color code for the project. Defaults to None.  See:  https://developer.todoist.com/guides/#colors
            favorite (bool, optional): Marks the new project as a favorite or not. Defaults to False.
        """

        # Validate the new project name.  We need a string
        if not type(new_project_name) is str:
            raise TypeError(f"The new project name must be a string.  Got {type(new_project_name)}")

        # Validate that the new project name doesn't already exist
        all_projects = self.get_all_projects()
        for p in all_projects:
            if p['name'].lower() == new_project_name.lower():
                raise IndexError(f"There is already a project named {p['name']}")

        # Validate the parent project id.  We need an int
        
        if parent_project_id is not None and type(parent_project_id) is not int:
            raise TypeError(f"The parent project id, if passed, should be an int.  Got {type(parent_project_id)}")

        # Validate that the parent project ID exists
        if parent_project_id is not None:
            parent_id_exists = False
            for p in all_projects:
                if p['id'] == parent_project_id:
                    parent_id_exists = True
                    break
            if parent_id_exists is False:
                raise IndexError(f"The specified parent project id, {parent_project_id}, does not exist.")

        # Validate the color
        if not color is None:
            color_found = False
            for c in TODOIST_COLORS.keys():
                o = TODOIST_COLORS[c]
                color_id = c
                color_hex_code = o.get('color_hex_code')
                color_name = o.get('color_name')

                if color == color_id or color.lower() == color_hex_code or color.lower() == color_name:
                    color_found = True
                    color = color_id  # We're interested in the ID, despite what the user passed into the function
                    break

            if color_found is False:
                raise ValueError(f"Could not resolve color value of {color} by id, nor by hex code, nor by name.  Got [{color}].  Possible values are: {json.dumps(TODOIST_COLORS, indent=4)}")

        # Validate the favorite flag
        if type(is_favorite) is not bool:
            raise ValueError(f"The type of is_favorite, if passed, should be boolean.  Got {type(is_favorite)}")

        # Construct the payload to pass to the api
        data = dict(name=new_project_name)
        
        if parent_project_id is not None:
            data['parent_id'] = parent_project_id

        if color is not None:
            data['color'] = color # We should have coerced to the int earlier, despite what was passed into this method

        if is_favorite is True:
            data['favorite'] = is_favorite # If not passed, defaults to False  

        # Validations have passed at this point.  Attempt to create the new project and leave the rest up to fate.
        method = "projects"
        endpoint_url = f"{self.base_url}{method}"
        result = self._do_post(url=endpoint_url, data=data, expected_status_code=200)

        return result.json()
        

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
    # active_tasks = td.get_active_tasks()
    # projects=td.get_all_projects()
    # print(json.dumps(projects, indent=4))
    # print(json.dumps(td.get_task_by_id(task_id=5374849640999), indent=4))
    # new_project = td.create_new_project(new_project_name="Test_Project_For_New_Creation4", color="taupe", is_favorite=True)
    
