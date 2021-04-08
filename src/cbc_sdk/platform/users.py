#!/usr/bin/env python3

# *******************************************************
# Copyright (c) VMware, Inc. 2020. All Rights Reserved.
# SPDX-License-Identifier: MIT
# *******************************************************
# *
# * DISCLAIMER. THIS PROGRAM IS PROVIDED TO YOU "AS IS" WITHOUT
# * WARRANTIES OR CONDITIONS OF ANY KIND, WHETHER ORAL OR WRITTEN,
# * EXPRESS OR IMPLIED. THE AUTHOR SPECIFICALLY DISCLAIMS ANY IMPLIED
# * WARRANTIES OR CONDITIONS OF MERCHANTABILITY, SATISFACTORY QUALITY,
# * NON-INFRINGEMENT AND FITNESS FOR A PARTICULAR PURPOSE.

"""Model and Query Classes for Users"""
from cbc_sdk.base import MutableBaseModel, BaseQuery, IterableQueryMixin, AsyncQueryMixin
from cbc_sdk.errors import ApiError, ServerError
import time
import copy


"""User Models"""


class User(MutableBaseModel):
    """Represents a user in the Carbon Black Cloud."""
    urlobject = "/appservices/v6/orgs/{0}/users"
    urlobject_single = "/appservices/v6/orgs/{0}/users{1}"
    primary_key = "login_id"
    swagger_meta_file = "platform/models/user.yaml"

    def __init__(self, cb, model_unique_id, initial_data=None):
        """
        Initialize the User object.

        Args:
            cb (BaseAPI): Reference to API object used to communicate with the server.
            model_unique_id (int): Login ID of this user.
            initial_data (dict): Initial data used to populate the user.
        """
        super(User, self).__init__(cb, model_unique_id, initial_data)
        if model_unique_id is not None and initial_data is None:
            self._refresh()

    class UserBuilder:
        """Auxiliary object used to construct a new User."""
        def __init__(self, cb):
            """
            Create the empty UserBuilder object.

            Args:
                cb (BaseAPI): Reference to API object used to communicate with the server.
            """
            self._cb = cb
            self._criteria = {'org_id': 0, 'role': 'DEPRECATED', 'auth_method': 'PASSWORD',
                              'add_without_invite': False}

        def set_email(self, email):
            """
            Sets the E-mail address for the new user.

            Args:
                email (str): The E-mail address for the new user.

            Returns:
                UserBuilder: This object.
            """
            self._criteria['email'] = email
            return self

        def set_first_name(self, first_name):
            """
            Sets the first name for the new user.

            Args:
                first_name (str): The first name for the new user.

            Returns:
                UserBuilder: This object.
            """
            self._criteria['first_name'] = first_name
            return self

        def set_last_name(self, last_name):
            """
            Sets the last name for the new user.

            Args:
                last_name (str): The last name for the new user.

            Returns:
                UserBuilder: This object.
            """
            self._criteria['last_name'] = last_name
            return self

        def set_auth_method(self, method):
            """
            Sets the authentication method for the new user.  The default is 'PASSWORD'.

            Args:
                method (str): The authentication method for the new user.

            Returns:
                UserBuilder: This object.
            """
            self._criteria['auth_method'] = method
            return self

        def set_send_invitation(self, invite):
            """
            Sets whether or not an invitation will be sent to the new user via E-mail.

            Args:
                invite (bool): True to have an invitation sent, False to not have one sent.

            Returns:
                UserBuilder: This object.
            """
            self._criteria['add_without_invite'] = False if invite else True
            return self

        def build(self):
            """
            Builds the new user and returns it.

            Returns:
                User: The new user object from the server.  First element in returned tuple.
                str: The temporary password set for the user.  Second element in returned tuple.
            """
            return User._create_user(self._cb, self._criteria)

    @classmethod
    def _query_implementation(cls, cb, **kwargs):
        """
        Returns the appropriate query object for Users.

        Args:
            cb (BaseAPI): Reference to API object used to communicate with the server.
            **kwargs (dict): Not used, retained for compatibility.

        Returns:
            UserQuery: The query object for users.
        """
        return UserQuery(cls, cb)

    @classmethod
    def _create_user(cls, cb, user_data):
        """
        Creates a new user from template data.

        Args:
            cb (BaseAPI): Reference to API object used to communicate with the server.
            user_data (dict): The user data to be used to create the new user.

        Returns:
            User: The new user object from the server.  First element in returned tuple.
            str: The temporary password set for the user.  Second element in returned tuple.

        Raises:
            ServerError: If the user registration was unsuccessful.
        """
        url = User.urlobject.format(cb.credentials.org_key)
        result = cb.post_object(url, user_data)
        resp = result.json()
        if resp['registration_type'] == 'SUCCESS':
            new_user = User(cb, int(resp['login_id']))
            return new_user, resp['password']
        raise ServerError(f"registration return was unsuccessful: {resp['registration_type']}")

    def _refresh(self):
        """
        Rereads the user data from the server.

        Returns:
            bool: True if refresh was successful, False if not.
        """
        userdata = self._cb.get_object(self.urlobject.format(self._cb.credentials.org_key))
        rawdata = [user for user in userdata.get('users', []) if user.get('login_id', 0) == self._model_unique_id]
        if len(rawdata) == 0:
            return False
        self._info = rawdata[0]
        self._last_refresh_time = time.time()
        return True

    def _update_object(self):
        """
        Updates the user data on the server.

        Returns:
            int: The user ID for this user.
        """
        if 'login_id' not in self._info:
            raise ApiError("user should have already been created")
        url = self.urlobject_single.format(self._cb.credentials.org_key, self._model_unique_id)
        self._cb.put_object(url, self._info)
        return self._model_unique_id

    def _delete_object(self):
        """Deletes the user."""
        url = self.urlobject_single.format(self._cb.credentials.org_key, self._model_unique_id)
        self._cb.delete_object(url)
        return self._model_unique_id

    @classmethod
    def create(cls, cb, template=None):
        """
        Creates a new user.

        Args:
            cb (CBCloudAPI): A reference to the CBCloudAPI object.
            template (dict): Optional template data for creating the new user.

        Returns:
            User: New user created, if template is specified.  First element in returned tuple.
            str: Temporary password for new user, if template is specified. Second element in returned tuple.
            UserBuilder: If template is None, returns an instance of this object. Call methods on the object to set
                         the values associated with the new user, and then call build() to create it.
        """
        if template:
            my_templ = copy.deepcopy(template)
            my_templ['org_id'] = 0
            my_templ['role'] = 'DEPRECATED'
            if 'auth_method' not in my_templ:
                my_templ['auth_method'] = 'PASSWORD'
            if 'add_without_invite' not in my_templ:
                my_templ['add_without_invite'] = False
            return User._create_user(cb, my_templ)
        return User.UserBuilder(cb)

    def reset_google_authenticator_registration(self):
        """Forces Google Authenticator registration to be reset for this user."""
        url = self.urlobject_single.format(self._cb.credentials.org_key, self._model_unique_id) + "/googleauth"
        self._cb.delete_object(url)


"""User Queries"""


class UserQuery(BaseQuery, IterableQueryMixin, AsyncQueryMixin):
    """Query for retrieving users in bulk."""
    def __init__(self, doc_class, cb):
        """
        Initialize the Query object.

        Args:
            doc_class (class): The class of the model this query returns.
            cb (CBCloudAPI): A reference to the CBCloudAPI object.
        """
        super(UserQuery, self).__init__(None)
        self._doc_class = doc_class
        self._cb = cb
        self._count_valid = False
        self._total_results = 0

    def _execute(self):
        """
        Executes the query and returns the list of raw results.

        Returns:
            list: The raw results of the query, as a list of dicts.
        """
        rawdata = self._cb.get_object("/appservices/v6/orgs/{0}/users".format(self._cb.credentials.org_key))
        return rawdata.get('users', [])

    def _count(self):
        """
        Returns the number of results from the run of this query.

        Returns:
            int: The number of results from the run of this query.
        """
        if not self._count_valid:
            return_data = self._execute()
            self._total_results = len(return_data)
            self._count_valid = True
        return self._total_results

    def _perform_query(self, from_row=0, max_rows=-1):
        """
        Performs the query and returns the results of the query in an iterable fashion.

        Args:
            from_row (int): Unused in this implementation, always 0.
            max_rows (int): Unused in this implementation, always -1.

        Returns:
            Iterable: The iterated query.
        """
        return_data = self._execute()
        self._total_results = len(return_data)
        self._count_valid = True
        for item in return_data:
            yield User(self._cb, item['login_id'], item)

    def _run_async_query(self, context):
        """
        Executed in the background to run an asynchronous query.

        Args:
            context (object): Not used; always None.

        Returns:
            list: Result of the async query, as a list of User objects.
        """
        return_data = self._execute()
        self._total_results = len(return_data)
        self._count_valid = True
        return [User(self._cb, item['login_id'], item) for item in return_data]
