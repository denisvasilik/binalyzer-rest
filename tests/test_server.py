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
    if 'source_data' in url:
        with open(os.path.join(TESTS_ABS_PATH, "resources/source_data.bin"), 'rb') as test_file:
            return MagicMock(content=test_file.read())

    if 'source_template' in url:
        with open(os.path.join(TESTS_ABS_PATH, "resources/source_template.xml")) as test_file:
            return MagicMock(text=test_file.read())

    if 'destination_template' in url:
        with open(os.path.join(TESTS_ABS_PATH, "resources/destination_template.xml")) as test_file:
            return MagicMock(text=test_file.read())

    if 'additional_data' in url:
        with open(os.path.join(TESTS_ABS_PATH, "resources/additional_data.xml")) as test_file:
            return MagicMock(text=test_file.read())

    raise RuntimeError()


def assertStreamEqual(first, second):
    zipped_data = zip(first, second)
    for (first_byte, second_byte) in zipped_data:
        assert first_byte == second_byte


RESPONSE_DATA = None


def send_file_mock(filename_or_fp, attachment_filename, mimetype):
    global RESPONSE_DATA
    filename_or_fp.seek(0)
    RESPONSE_DATA = filename_or_fp.read()
    return '{}', 200


def test_route_transform(test_client):
    expected_bytes = (bytes([0x22] * 8) +
                      bytes([0x44] * 8) +
                      bytes([0x00] * 8) +
                      bytes([0x00] * 8))

    requests_get_tmp = server.requests.get
    send_file_tmp = server.send_file
    server.requests.get = requests_get_mock
    server.send_file = send_file_mock

    response = test_client.post('/transform', json={
        'source_template_url': 'http://localhost:8000/download/source_template.xml',
        'destination_template_url': 'http://localhost:8000/download/destination_template.xml',
        'data_urls': ['http://localhost:8000/download/source_data.bin'],
        'additional_data_urls': ['http://localhost:8000/download/additional_data.bin'],
    })

    assertStreamEqual(RESPONSE_DATA, expected_bytes)
    assert response.status_code == 200

    server.requests.get = requests_get_tmp
    server.send_file = send_file_tmp
