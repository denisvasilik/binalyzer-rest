"""
    binalyzer_rest.rest
    ~~~~~~~~~~~~~~~~~~~

    This module implements the Binalyzer REST API.
"""
import os
import io
import time
import requests
import antlr4

from . import utils

from threading import Thread

from flasgger import Swagger
from flasgger.utils import swag_from
from flask import (
    Flask,
    jsonify,
    request,
    redirect,
    url_for,
    send_file,
    Response
)
from werkzeug.wsgi import FileWrapper

from binalyzer import (
    Binalyzer,
    XMLTemplateParser,
    TemplateProvider,
    DataProvider,
    __version__,
)


flask_app = Flask(__name__)
swagger_config = Swagger.DEFAULT_CONFIG
swagger_config['specs'][0]['route'] = '/binalyzer_rest.json'
swagger_config['hide_top_bar'] = True
swagger_config['title'] = "Binalyzer REST API"
swagger_template = {
    "swagger": "2.0",
    "info": {
        "description": "",
        "version": __version__,
        "title": "Binalyzer REST API",
    },
    "schemes": [
        "http",
        "https",
    ],
    "tags": [
        {"name": "general"},
        {"name": "transformation"},
    ],
}


swagger = Swagger(
    flask_app,
    config=swagger_config,
    template=swagger_template
)


@flask_app.route('/')
def index():
    """Redirects base path to API documentation.
    """
    return redirect(url_for('flasgger.apidocs'))


@flask_app.route('/health', methods=['GET'])
@swag_from('resources/health.yml')
def health():
    return jsonify()


@flask_app.route('/transform', methods=['POST'])
@swag_from('resources/transform.yml')
def transform():
    params = request.get_json()

    source_template_url = params['source_template_url']
    source_binding = params['source_binding']
    destination_template_url = params['destination_template_url']
    destination_binding = params['destination_binding']
    deployment_url = params['deployment_url']

    source_template = utils.create_template(
        source_template_url,
        source_binding
    )

    destination_template = utils.create_template(
        destination_template_url,
        destination_binding
    )

    utils.bind_data_to_template(
        source_template,
        source_binding
    )

    Binalyzer().transform(
        source_template,
        destination_template,
    )

    utils.bind_data_to_template(
        destination_template,
        destination_binding
    )

    if deployment_url:
        requests.put(deployment_url,
                    data=io.BytesIO(destination_template.value),
                    headers={'Content-type': 'application/octet-stream'})
        return jsonify(), 200
    else:
        destination_data = io.BytesIO(destination_template.value)
        destination_file = FileWrapper(destination_data)
        return Response(destination_file, direct_passthrough=True)
