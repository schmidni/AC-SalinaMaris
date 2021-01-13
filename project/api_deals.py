import requests
import warnings

from requests.models import HTTPError
from config import Config

_headers = {"Api-Token": Config.AC_KEY}
_url = Config.AC_URL


def _get_response(endpoint: str, params: dict = {}):
    """Send a GET request to the specified endpoint"""
    return requests.get(_url+endpoint, headers=_headers, params=params)


def _post_object(endpoint: str, data: dict):
    """Send a POST request to the specified endpoint using data as body"""
    return requests.post(_url+endpoint, headers=_headers, json=data)


def _put_object(endpoint: str, id: int, data: dict):
    """Send a PUT request to the specified endpoint using data as body"""
    return requests.put(f'{_url}{endpoint}/{id}', headers=_headers, json=data)


def _get_custom_deal_field_id(field_name: str):
    """Finds the internal id of the specified deal field.

    Returns: id of field or None if field not found.
    """
    # https://developers.activecampaign.com/reference#retrieve-all-dealcustomfielddata-resources

    # query deal fields endpoint, only use the list of fields
    all_fields = _get_response("dealCustomFieldMeta").json()[
        "dealCustomFieldMeta"]

    # for those fields, find the first one where fieldLabel is equal to the name searched
    field = next(
        (f for f in all_fields if f["fieldLabel"] == field_name), {"id": None}
    )

    return field["id"]


def _create_deal(deal: dict):
    """Create deal object which can be posted to the AC api

    Args: flat dictionary with all the informtion for the deal
      Required fiels are 'contact', 'title', 'value' if a new deal should be created
    Returns: nested object which can directly be used for the AC api
    """
    # https://developers.activecampaign.com/reference#create-a-deal-new

    # init new object, fields is a list of custom fields
    ac_deal = {"currency": "chf", "group": "1", "fields": []}
    fields = ["contact", "title", "value", "currency", "group", "id"]

    for k, v in deal.items():
        if k in fields:
            ac_deal[k] = v
        else:
            # get id of custom fields
            id = _get_custom_deal_field_id(k)
            if id:
                ac_deal["fields"].append(
                    {"customFieldId": id, "fieldValue": v})
            else:
                warnings.warn(
                    "The field {} is unknown and was ignored.".format(k)
                )

    return {"deal": ac_deal}


def post_deal(deal: dict):
    """sends a new deal to AC using the 'create' deal endpoint

    Args: flat dictionary with all the informtion for the deal
      Required fiels are 'contact', 'title', 'value.
    Returns: AC deal object or error description
    """
    # https://developers.activecampaign.com/reference#create-a-deal-new

    ac_deal = _create_deal(deal)
    response = _post_object("deals", ac_deal)

    return response


def _find_deal_id(reservationsnummer: int, status: int = 0, contact_email: str = None):
    """find deal by custom deal field 'Reservationsnummer'

    The method searches by default all open (status=0) deals for the one with the respective RN
    Args: 
      reservationsnummer: the deal's "Reservationsnummer'
      status: defaults to 0=open, can also be 1=won or 2=lost
      contact_email: the linked contact's email, makes the query more efficient
    Returns:
      The deal id or None if no deal found
    """
    # https://developers.activecampaign.com/reference#list-all-deals

    # filter by deal status, default all open deals
    search_params = {"filters[stage]": status}

    # sideload custom field data and meta information to search by "Reservationsnummer"
    search_params["include"] = "dealCustomFieldData"

    # if a email is provided, add filter, reduces the response to a reasonable size
    if contact_email:
        search_params["filters[search_field]"] = "email"
        search_params["filters[search]"] = contact_email

    # execute the query
    response = _get_response("deals", params=search_params)

    # get the field id for Reservationsnummer
    reservationsnummer_field_id = _get_custom_deal_field_id(
        "Reservationsnummer")

    try:
        # check if request was successful
        response.raise_for_status()
        # get all customFieldData from all returned deals
        ac_custom_fields = response.json()["dealCustomFieldData"]
        # find the field where custom_field_id is reservationsnummer_field_id and the number vaulue is the reservationsnummer
        ac_reservationsnummer_field = next(
            (f for f in ac_custom_fields if f["custom_field_id"] ==
             reservationsnummer_field_id and int(float(f["custom_field_number_value"])) == reservationsnummer), None
        )
        # return theid of the deal to which this fiel belongs
        ac_deal_id = ac_reservationsnummer_field["deal_id"]

    except Exception as err:
        return {"error": str(err)}

    return ac_deal_id


def put_deal(reservationsnummer: int, data: dict, email=None):
    """update deal with the respective 'Reservationsnummer'

    Args:
      reservationsnummer: custom field 'Reservationsnummer'
      data: new deal data which should update the existing deal
      email: contact's email, makes it more efficient to find the deal
    """
    # https://developers.activecampaign.com/reference#update-a-deal-new

    deal_id = _find_deal_id(reservationsnummer, contact_email=email)
    deal_object = _create_deal(data)
    response = _put_object("deals", deal_id, deal_object)

    return response
