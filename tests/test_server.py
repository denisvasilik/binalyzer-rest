import os
import io
import pytest
import unittest

from unittest.mock import MagicMock

from binalyzer_rest import server
from binalyzer_rest.server import flask_app


TESTS_ABS_PATH = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def test_client():
    return flask_app.test_client()


def test_route_health(test_client):
    response = test_client.get('/health')
    assert response.status_code == 200


def requests_get_mock(url):
    if 'wasm_blob' in url:
        with open(os.path.join(TESTS_ABS_PATH, "resources/wasm_blob.bin"), 'rb') as test_file:
            return MagicMock(content=test_file.read())

    if 'wasm_source_template' in url:
        with open(os.path.join(TESTS_ABS_PATH, "resources/wasm_source_template.xml")) as test_file:
            return MagicMock(text=test_file.read())

    if 'wasm_destination_template' in url:
        with open(os.path.join(TESTS_ABS_PATH, "resources/wasm_destination_template.xml")) as test_file:
            return MagicMock(text=test_file.read())

    raise RuntimeError()


def send_file_mock(filename_or_fp, attachment_filename, mimetype):
    return '{}', 200


def test_route_transform(test_client):
    requests_get_tmp = server.requests.get
    send_file_tmp = server.send_file
    server.requests.get = requests_get_mock
    server.send_file = send_file_mock

    response = test_client.post('/transform', json={
        'source_template_url': 'http://localhost:8000/download/wasm_source_template.xml',
        'destination_template_url': 'http://localhost:8000/download/wasm_destination_template.xml',
        'data_urls': ['http://localhost:8000/download/wasm_blob.bin'],
    })

    assert response.status_code == 200

    server.requests.get = requests_get_tmp
    server.send_file = send_file_tmp

