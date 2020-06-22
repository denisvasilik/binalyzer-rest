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
    SimpleTemplateProvider,
    BufferedIODataProvider,
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

    source_template = requests.get(source_template_url)
    _destination_template = requests.get(destination_template_url)

    data_blobs = []
    for data_url in data_urls:
        data_blob = requests.get(data_url).content
        data_blobs.append(data_blob)

    template = XMLTemplateParser(source_template.text).parse()
    template_provider = SimpleTemplateProvider(template)
    data_provider = BufferedIODataProvider(io.BytesIO(data_blobs[0]))
    binalyzer = Binalyzer(template_provider, data_provider)
    binalyzer.template = template_provider.template

    # Could be n files, should they be downloaded or uploaded to somewhere else?
    return send_file(io.BytesIO(binalyzer.template.value),
                     attachment_filename=binalyzer.template.id,
                     mimetype='application/octet-stream')


@flask_app.route('/download/<string:filename>')
@swag_from('resources/download.yml')
def download(filename):
    """Download a file for testing purposes.
    """
    filepath = os.path.join(os.getcwd(), 'tests', 'resources', filename)
    return send_file(filepath, attachment_filename=filename)


if __name__ == "__main__":
    flask_app.run(host='0.0.0.0', port=8888, debug=True)
