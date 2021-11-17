"""
A Wrapper for the Todoist API
"""

from cred_manage.bitwarden import BitwardenCredContainer

class Todoist():

    def __init__(self, api_key):
        """
        init method for the Todoist API wrapper
        """

        # Read the API key out of bitwarden
        todoist_api_key = 