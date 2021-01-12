from flask import Blueprint, render_template
from requests.models import HTTPError

from project.api_contacts import add_tag_to_contact, get_tag_id, post_contact, get_list_id, subscribe_contact_to_list
from project.api_deals import

frontend = Blueprint('frontend', __name__, template_folder='templates')


@frontend.route('/')
def index():
    return render_template('frontend/home.html')


@frontend.route('/create_contact')
def create_contact():

    # create contact object
    contact = {"email": "news@salinamaris.ch", "firstName": "Salina",
               "lastName": "Maris", "Sprache": "Deutsch"}

    # create or update contact
    response_contact = post_contact(contact)
    try:
        response_contact.raise_for_status()
    except HTTPError:
        return response_contact.json()

    contact_id = response_contact.json()["contact"]["id"]

    # add tag to contact
    tag_id = get_tag_id("Wellness")
    response_add_tag = add_tag_to_contact(tag_id, contact_id)
    try:
        response_add_tag.raise_for_status()
    except HTTPError:
        return response_add_tag.json()

    # add contact to list
    list_id = get_list_id("Marketing")
    response_subscription = subscribe_contact_to_list(contact_id, list_id)
    try:
        response_subscription.raise_for_status()
    except HTTPError:
        return response_subscription.json()

    return {"success": "contact created"}, 201


@frontend.route('/create_deal')
def create_deal():

    return "0"
