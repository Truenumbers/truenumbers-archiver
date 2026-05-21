import requests

class TruenumbersTriggerApi:
    """
    High-level client for the Truenumbers Trigger API.

    This class wraps endpoints for managing trigger definitions. Methods raise
    ``ValueError`` when required arguments are missing and ``Exception`` when
    the underlying HTTP request returns a status code >= 400.

    Example::

        api = TruenumbersTriggerApi(
            base_url="https://api.example.com/truenumbers-trigger-api",
            shared_headers={"Authorization": "Bearer <token>"},
        )
        created = api.create_trigger(
            numberspace="my_space",
            name="on_create",
            tnql="* has *",
            execute_on=["CREATE"],
        )
    """
    base_url = ""
    shared_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    def __init__(self, *, base_url, shared_headers=None):
        """
        Initialize a new Truenumbers Trigger API client.

        Args:
            base_url (str): Base URL of the Trigger API, for example
                ``"https://api.truenumbers.com/truenumbers-trigger-api"``.
                Required.
            shared_headers (dict, optional): Extra HTTP headers to send with every
                request (for example authentication headers). Supplied keys
                override the defaults in ``shared_headers``.

        Raises:
            ValueError: If ``base_url`` is not provided.

        Example::

            api = TruenumbersTriggerApi(
                base_url="https://api.example.com/truenumbers-trigger-api",
            )
            api_auth = TruenumbersTriggerApi(
                base_url="https://api.example.com/truenumbers-trigger-api",
                shared_headers={"Authorization": "Bearer <token>"},
            )
        """
        if not base_url:
            raise ValueError('base_url is required')
        self.base_url = base_url
        if shared_headers:
            self.shared_headers.update(shared_headers)

    def create_trigger(self, *, numberspace, name, execute_on, description=None, tnql=None, status=None, tag_on_trigger=None, load_historic_data=None, destinations=None):
        """
        Create a trigger definition.

        This wraps ``POST /v1/trigger-definition``.

        Args:
            numberspace (str): Numberspace where the trigger will be created.
                Required.
            name (str): Trigger name. Required.
            execute_on (list[str]): When the trigger fires. Common values include
                ``"CREATE"``, ``"TAG"``, and ``"CRON"``. Required.
            description (str, optional): Human-readable description.
            tnql (str, optional): TNQL query that selects which Truenumbers should
                activate the trigger. Required when ``execute_on`` includes
                ``"CREATE"`` or ``"TAG"``.
            status (str, optional): Trigger status (for example enabled/disabled).
            tag_on_trigger (list[str], optional): Tags that should be applied to
                Truenumbers when the trigger executes (if supported by your server).
            load_historic_data (bool, optional): If ``True``, the server may backfill
                the trigger by evaluating historic matching Truenumbers.
            destinations (list[dict], optional): Where trigger events are delivered.
                Each destination is a JSON object; typical fields include ``"type"``
                and destination-specific configuration.

        Returns:
            dict: A JSON object representing the created trigger definition.
            Common fields include ``"guid"``/``"id"``, ``"numberspace"``, ``"name"``,
            ``"tnql"``, ``"executeOn"``, ``"status"``, ``"destinations"`` and timestamps.

        Raises:
            ValueError: If required arguments are missing or inconsistent.
            Exception: If the API response status code is >= 400.

        Example::

            created = api.create_trigger(
                numberspace="my_space",
                name="tagged_items",
                description="Fires when matching Truenumbers are tagged",
                tnql="* has *",
                execute_on=["TAG"],
                status="ENABLED",
                tag_on_trigger=["processed"],
                load_historic_data=True,
                destinations=[{"type": "WEB_SOCKET"}],
            )
        """
        if not numberspace:
            raise ValueError('numberspace is required')
        if not name:
            raise ValueError('name is required')
        if not execute_on:
            raise ValueError('execute_on is required')
        if ('CREATE' in execute_on or 'TAG' in execute_on) and (not tnql):
            raise ValueError('tnql is required for CREATE or TAG execute_on')
        params = {} if load_historic_data is None or load_historic_data is False else {'loadHistoricData': 'true'}
        dest = destinations if destinations else [{'type': 'WEB_SOCKET'}]
        payload = {'numberspace': numberspace, 'name': name, 'description': description, 'tnql': tnql, 'executeOn': execute_on, 'status': status, 'tagOnTrigger': tag_on_trigger, 'destinations': dest}
        url = f'{self.base_url}/v1/trigger-definition'
        response = requests.post(url, headers=self.shared_headers, json=payload, params=params)
        if response.status_code >= 400:
            raise Exception(f'Failed to create trigger: {response.text}')
        return response.json()

    def get_triggers(self, *, numberspace, name=None, status=None):
        """
        List trigger definitions for a numberspace.

        This wraps ``GET /v1/trigger-definitions``.

        Args:
            numberspace (str): Numberspace to list triggers for. Required.
            name (str, optional): If provided, filter results by trigger name.
            status (list[str], optional): If provided, filter results by one or more
                status values. The wrapper sends them as a comma-separated string.

        Returns:
            dict: A JSON object containing a list of trigger definitions, typically
            under a key like ``"items"`` or similar, plus optional paging metadata.

        Raises:
            ValueError: If ``numberspace`` is missing.
            Exception: If the API response status code is >= 400.

        Example::

            all_triggers = api.get_triggers(numberspace="my_space")
            filtered = api.get_triggers(
                numberspace="my_space",
                name="on_create",
                status=["ENABLED", "DISABLED"],
            )
        """
        if not numberspace:
            raise ValueError('numberspace is required')
        url = f'{self.base_url}/v1/trigger-definitions'
        status_delimiter = ','
        status_param = status_delimiter.join(status) if status else None
        response = requests.get(url, headers=self.shared_headers, params={'numberspace': numberspace, 'name': name, 'status': status_param})
        if response.status_code >= 400:
            raise Exception(f'Failed to get triggers: {response.text}')
        return response.json()

    def get_trigger_by_id(self, *, id):
        """
        Retrieve a single trigger definition by GUID.

        This wraps ``GET /v1/trigger-definitions/{guid}``.

        Args:
            id (str): GUID of the trigger definition. Required.

        Returns:
            dict: A JSON object representing the trigger definition, including
            fields such as ``"guid"``/``"id"``, ``"numberspace"``, ``"name"``,
            ``"tnql"``, ``"executeOn"``, ``"status"``, and ``"destinations"``.

        Raises:
            ValueError: If ``id`` is missing.
            Exception: If the API response status code is >= 400.

        Example::

            trigger = api.get_trigger_by_id(
                id="00000000-0000-0000-0000-000000000000",
            )
        """
        if not id:
            raise ValueError('id is required')
        url = f'{self.base_url}/v1/trigger-definitions/{id}'
        response = requests.get(url, headers=self.shared_headers)
        if response.status_code >= 400:
            raise Exception(f'Failed to get trigger by id: {response.text}')
        return response.json()

    def update_trigger(self, *, id, name=None, description=None, tnql=None, execute_on=None, status=None, tag_on_trigger=None, destinations=None):
        """
        Partially update a trigger definition by GUID.

        This wraps ``PATCH /v1/trigger-definitions/{guid}``.

        Args:
            id (str): GUID of the trigger definition to update. Required.
            name (str, optional): New trigger name.
            description (str, optional): New description.
            tnql (str, optional): New TNQL query string.
            execute_on (list[str], optional): New execute-on values, such as
                ``["CREATE", "TAG"]``.
            status (str, optional): New trigger status.
            tag_on_trigger (list[str], optional): New tag-on-trigger values.
            destinations (list[dict], optional): New destinations array.

        Returns:
            dict: A JSON object representing the updated trigger definition.

        Raises:
            ValueError: If ``id`` is missing.
            Exception: If the API response status code is >= 400.

        Example::

            updated = api.update_trigger(
                id="00000000-0000-0000-0000-000000000000",
                name="tagged_items_v2",
                tnql="* has *",
                execute_on=["TAG", "CREATE"],
                status="ENABLED",
            )
        """
        if not id:
            raise ValueError('id is required')
        payload = {'name': name, 'description': description, 'tnql': tnql, 'executeOn': execute_on, 'status': status, 'tagOnTrigger': tag_on_trigger, 'destinations': destinations}
        url = f'{self.base_url}/v1/trigger-definitions/{id}'
        response = requests.patch(url, headers=self.shared_headers, json=payload)
        if response.status_code >= 400:
            raise Exception(f'Failed to update trigger: {response.text}')
        return response.json()

    def delete_trigger(self, *, id):
        """
        Delete a trigger definition by GUID.

        This wraps ``DELETE /v1/trigger-definitions/{guid}``.

        Args:
            id (str): GUID of the trigger definition to delete. Required.

        Returns:
            dict: A JSON object confirming deletion and any status details.

        Raises:
            ValueError: If ``id`` is missing.
            Exception: If the API response status code is >= 400.

        Example::

            result = api.delete_trigger(
                id="00000000-0000-0000-0000-000000000000",
            )
        """
        if not id:
            raise ValueError('id is required')
        url = f'{self.base_url}/v1/trigger-definitions/{id}'
        response = requests.delete(url, headers=self.shared_headers)
        if response.status_code >= 400:
            raise Exception(f'Failed to delete trigger: {response.text}')
        return response.json()
