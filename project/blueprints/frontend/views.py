from flask import Blueprint, render_template

from project.api import post_contact, get_list_id, subscribe_contact_to_list

frontend = Blueprint('frontend', __name__, template_folder='templates')


@frontend.route('/')
def index():
    return render_template('frontend/home.html')


@frontend.route('/test_api')
def test():
    contact = {"email": "news@salinamaris.ch", "firstName": "Salina",
               "lastName": "Maris", "Sprache": "Deutsch"}

    response_contact = post_contact(contact)
    list_id = get_list_id("Marketing")
    contact_id = response_contact.json()["contact"]["id"]

    response_subscription = subscribe_contact_to_list(contact_id, list_id)
    return response_subscription.json()
