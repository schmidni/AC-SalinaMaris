import requests
from config import Config

_headers = {"Api-Token": Config.AC_KEY}
_url = Config.AC_URL


def _get_response(endpoint, params={}):
    """Send a GET request to the specified endpoint"""
    return requests.get(_url+endpoint, headers=_headers, params=params)


def _get_field_id(field_name):
    """Finds the internal id of the specified field."""

    # get all fields
    all_fields = _get_response("fields").json()["fields"]

    # of those fields, find te first one where title is equal to the name searched
    field = next((f for f in all_fields if f["title"] == field_name), None)

    return field["id"]


def test_method():
    response = _get_field_id("Sprache")

    return response
