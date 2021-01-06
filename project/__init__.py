from project.blueprints.frontend import frontend
from flask import Flask, render_template
from config import Config
import logging
import os

from project.extensions import csrf, assets
from project.bundles import bundles

from logging.handlers import RotatingFileHandler

app = Flask(__name__)
app.config.from_object(Config)

# Set up logger
if not app.debug:
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/project.log', maxBytes=10240,
                                       backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('project startup')

# import and register blueprints
app.register_blueprint(frontend)

# init extensions
csrf.init_app(app)
assets.init_app(app)

# register static bundles
assets.register('js_bundle', bundles['js_bundle'])
assets.register('css_bundle', bundles['css_bundle'])


@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404
