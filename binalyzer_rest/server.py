"""
    binalyzer_rest.server
    ~~~~~~~~~~~~~~~~~~~~

    This module implements the Binalyzer REST API server.
"""
import os
import io
import time
import requests

import antlr4

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
)

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
        {"name": "test"},
    ],
}


swagger = Swagger(
    flask_app,
    config=swagger_config,
    template=swagger_template
)


def transform2(source_template, destination_template, additional_data={}):
    transfer(source_template, destination_template)
    bind(diff(source_template, destination_template), additional_data)


def transfer(source_template, destination_template):
    existing_leaves = ((source_leave, destination_leave)
                       for source_leave in source_template.leaves
                       for destination_leave in destination_template.leaves
                       if source_leave.name == destination_leave.name)

    for (source_leave, destination_leave) in existing_leaves:
        destination_leave.value = source_leave.value


def diff(source_template, destination_template):
    return (destination_leave
            for destination_leave in destination_template.leaves
            if destination_leave.name not in
            (source_leave.name for source_leave in source_template.leaves))


def bind(templates, data_template_map):
    for template in templates:
        if template.name in list(data_template_map.keys()):
            template.value = data_template_map[template.name]
        else:
            template.value = bytes([0] * template.size.value)


@flask_app.route('/')
def index():
    """Redirects base path to API documentation.
    """
    return redirect(url_for('flasgger.apidocs'))


@flask_app.route('/health', methods=['GET'])
@swag_from('resources/health.yml')
def health():
    """Health check
    """
    return jsonify()


@flask_app.route('/transform', methods=['POST'])
@swag_from('resources/transform.yml')
def transform():
    """Transforms data provided by `data_urls` from a source template description
    to a destination template description.
    """
    json_data = request.get_json()
    source_template_url = json_data['source_template_url']
    destination_template_url = json_data['destination_template_url']
    data_urls = json_data['data_urls']

    source_template_response = requests.get(source_template_url)
    destination_template_response = requests.get(destination_template_url)

    data_blobs = []
    for data_url in data_urls:
        data_blob = requests.get(data_url).content
        data_blobs.append(data_blob)

    source_template = XMLTemplateParser(source_template_response.text).parse()
    template_provider = TemplateProvider(source_template)
    data_provider = DataProvider(io.BytesIO(data_blobs[0]))
    binalyzer = Binalyzer(template_provider, data_provider)
    binalyzer.template = template_provider.template

    destination_template = XMLTemplateParser(
        destination_template_response.text).parse()

    transform2(source_template, destination_template)

    return send_file(io.BytesIO(destination_template.value),
                     attachment_filename=binalyzer.template.name,
                     mimetype='application/octet-stream')


if __name__ == "__main__":
    flask_app.run(host='0.0.0.0', port=8888, debug=True)
