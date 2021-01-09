from flask import Blueprint, render_template

from project.api import test_method

frontend = Blueprint('frontend', __name__, template_folder='templates')


@frontend.route('/')
def index():
    return render_template('frontend/home.html')


@frontend.route('/test_api')
def test():
    return test_method()
