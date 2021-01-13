import requests
import warnings
from config import Config

_headers = {"Api-Token": Config.AC_KEY}
_url = Config.AC_URL


def _get_response(endpoint: str, params: dict = {}):
    """Send a GET request to the specified endpoint"""
    return requests.get(_url+endpoint, headers=_headers, params=params)


def _post_object(endpoint: str, data: dict):
    """Send a POST request to the specified endpoint using data as body"""
    return requests.post(_url+endpoint, headers=_headers, json=data)


def _get_custom_field_id(field_name: str):
    """Finds the internal id of the specified field.

    Returns: id of field or None if field not found.
    """
    # https://developers.activecampaign.com/reference#retrieve-fields-1

    # query fields endpoint, only use the list of fields
    all_fields = _get_response("fields").json()["fields"]

    # of those fields, find the first one where title is equal to the name searched
    field = next(
        (f for f in all_fields if f["title"] == field_name), {"id": None})

    return field["id"]


def get_list_id(list_name: str):
    """ Finds the internal id of the specified list.

    Returns: id of list or None if list not found
    """
    # https://developers.activecampaign.com/reference#retrieve-all-lists

    # query all lists and filter by list name
    lists = _get_response("lists", params={"filters[name]": list_name}).json()

    # return None if no list by this name found
    if len(lists["lists"]) < 1:
        return None

    # else return id of first list found
    return lists["lists"][0]["id"]


def get_tag_id(tag_name: str):
    """ Finds the internal id of the specified tag.

    Returns: id of tag or None if tag not found
    """
    # https://developers.activecampaign.com/reference#retrieve-all-tags

    # query all tags and filter by tag name
    tags = _get_response("tags", params={"search": tag_name}).json()

    # return None if no tag by this name found
    if len(tags["tags"]) < 1:
        return None

    # else return id of first tag found
    return tags["tags"][0]["id"]


def _create_contact(contact: dict):
    """Create contact object which can be posted to the AC api

    Args: flat dictionary with all the information for the contact
      Field 'email' with a valid email address is required. 
    Returns: nested object which can directly be used for the AC api
    """
    # https://developers.activecampaign.com/reference#create-or-update-contact-new

    # init new object, fieldValues is a list of custom fields
    ac_contact = {"fieldValues": []}
    fields = ["email", "firstName", "lastName", "phone"]  # standard fields

    # write standard fields on first level, custom fields on second level into a list
    for k, v in contact.items():
        if k in fields:
            ac_contact[k] = v
        else:
            # get id of custom field
            id = _get_custom_field_id(k)
            if id:
                ac_contact["fieldValues"].append({"field": id, "value": v})
            else:
                warnings.warn(
                    "The field {} is unknown and was ignored.".format(k)
                )

    return {"contact": ac_contact}


def post_contact(contact: dict):
    """sends a new contact to AC using the 'create or update' contact endpoint

    Args: flat dictionary with all the information for the contact
      Field 'email' with a valid email address is required. 
    Returns: AC contact object or error description
    """
    # https://developers.activecampaign.com/reference#create-or-update-contact-new

    ac_contact = _create_contact(contact)
    response = _post_object("contact/sync", ac_contact)
    return response


def subscribe_contact_to_list(contact_id: int, list_id: int):
    """subscribes a contact to the specified list"""
    # https://developers.activecampaign.com/reference#update-list-status-for-contact

    data = {"contactList": {
        "list": list_id,
        "contact": contact_id,
        "status": 1,
    }}
    response = _post_object('contactLists', data)
    return response


def add_tag_to_contact(tag_id: int, contact_id: int):
    """adds a tag to the specified contact"""
    # https://developers.activecampaign.com/reference#contact-tags

    data = {"contactTag": {
        "contact": contact_id,
        "tag": tag_id,
    }}
    response = _post_object("contactTags", data)
    return response
