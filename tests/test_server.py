import os
import io
import pytest
import unittest

from unittest.mock import MagicMock

from binalyzer_rest import server
from binalyzer_rest.server import flask_app


TESTS_ABS_PATH = os.path.dirname(os.path.abspath(__file__))

TEST_SOURCE_DATA = None
TEST_SOURCE_TEMPLATE = None
TEST_DESTINATION_TEMPLATE = None
TEST_RESPONSE_DATA = None


def requests_get_mock(url):
    if 'source_data' in url:
        with open(os.path.join(TESTS_ABS_PATH, "resources/source_data.bin"), 'rb') as test_file:
            return MagicMock(content=TEST_SOURCE_DATA)

    if 'source_template' in url:
        with open(os.path.join(TESTS_ABS_PATH, "resources/source_template.xml")) as test_file:
            return MagicMock(text=TEST_SOURCE_TEMPLATE)

    if 'destination_template' in url:
        with open(os.path.join(TESTS_ABS_PATH, "resources/destination_template.xml")) as test_file:
            return MagicMock(text=TEST_DESTINATION_TEMPLATE)

    if 'additional_data' in url:
        with open(os.path.join(TESTS_ABS_PATH, "resources/additional_data.xml")) as test_file:
            return MagicMock(text=test_file.read())

    raise RuntimeError()


def send_file_mock(filename_or_fp, attachment_filename, mimetype):
    global TEST_RESPONSE_DATA
    filename_or_fp.seek(0)
    TEST_RESPONSE_DATA = filename_or_fp.read()
    return '{}', 200


@pytest.fixture
def test_client():
    return flask_app.test_client()


@pytest.fixture(scope="module")
def test_mock(request):
    requests_get_tmp = server.requests.get
    send_file_tmp = server.send_file
    server.requests.get = requests_get_mock
    server.send_file = send_file_mock

    def reset_mock():
        server.requests.get = requests_get_tmp
        server.send_file = send_file_tmp
    request.addfinalizer(reset_mock)


def test_route_health(test_client):
    response = test_client.get('/health')
    assert response.status_code == 200


def assertStreamEqual(first, second):
    zipped_data = zip(first, second)
    for (first_byte, second_byte) in zipped_data:
        assert first_byte == second_byte


def test_route_transform(test_client, test_mock):
    global TEST_SOURCE_TEMPLATE
    global TEST_DESTINATION_TEMPLATE
    global TEST_SOURCE_DATA

    TEST_SOURCE_DATA = (bytes([0x11] * 8) +
                        bytes([0x22] * 8) +
                        bytes([0x33] * 8) +
                        bytes([0x44] * 8))

    TEST_SOURCE_TEMPLATE = """
        <template name="a">
            <field name="b" size="8"></field>
            <field name="c" size="8"></field>
            <field name="d" size="8"></field>
            <field name="e" size="8"></field>
        </template>
    """

    TEST_DESTINATION_TEMPLATE = """
        <template name="a">
            <field name="c" size="8"></field>
            <field name="e" size="8"></field>
            <field name="i" size="8"></field>
            <field name="j" size="8"></field>
        </template>
    """

    expected_bytes = (bytes([0x22] * 8) +
                      bytes([0x44] * 8) +
                      bytes([0x00] * 8) +
                      bytes([0x00] * 8))

    response = test_client.post('/transform', json={
        'source_template_url': 'http://localhost:8000/download/source_template.xml',
        'destination_template_url': 'http://localhost:8000/download/destination_template.xml',
        'data_urls': ['http://localhost:8000/download/source_data.bin'],
        'additional_data_urls': ['http://localhost:8000/download/additional_data.bin'],
    })

    assertStreamEqual(TEST_RESPONSE_DATA, expected_bytes)
    assert response.status_code == 200


def test_transform_identity(test_client, test_mock):
    global TEST_SOURCE_TEMPLATE
    global TEST_DESTINATION_TEMPLATE
    global TEST_SOURCE_DATA

    TEST_SOURCE_DATA = (bytes([0x11] * 8) +
                        bytes([0x22] * 8) +
                        bytes([0x33] * 8) +
                        bytes([0x44] * 8))

    TEST_SOURCE_TEMPLATE = """
        <template name="a">
            <field name="b" size="8"></field>
            <field name="c" size="8"></field>
            <field name="d" size="8"></field>
            <field name="e" size="8"></field>
        </template>
    """

    TEST_DESTINATION_TEMPLATE = """
        <template name="a">
            <field name="b" size="8"></field>
            <field name="c" size="8"></field>
            <field name="d" size="8"></field>
            <field name="e" size="8"></field>
        </template>
    """

    response = test_client.post('/transform', json={
        'source_template_url': 'http://localhost:8000/download/source_template.xml',
        'destination_template_url': 'http://localhost:8000/download/destination_template.xml',
        'data_urls': ['http://localhost:8000/download/source_data.bin'],
        'additional_data_urls': ['http://localhost:8000/download/additional_data.bin'],
    })

    assertStreamEqual(TEST_RESPONSE_DATA, TEST_SOURCE_DATA)
    assert response.status_code == 200


def test_transform_add_template(test_client, test_mock):
    global TEST_SOURCE_TEMPLATE
    global TEST_DESTINATION_TEMPLATE
    global TEST_SOURCE_DATA

    TEST_SOURCE_DATA = (bytes([0x11] * 8) +
                        bytes([0x22] * 8) +
                        bytes([0x33] * 8) +
                        bytes([0x44] * 8))

    TEST_SOURCE_TEMPLATE = """
        <template name="a">
            <field name="b" size="8"></field>
            <field name="c" size="8"></field>
            <field name="d" size="8"></field>
            <field name="e" size="8"></field>
        </template>
    """

    TEST_DESTINATION_TEMPLATE = """
        <template name="a">
            <field name="b" size="8"></field>
            <field name="c" size="8"></field>
            <field name="d" size="8"></field>
            <field name="e" size="8"></field>
            <field name="f" size="8"></field>
        </template>
    """

    expected_bytes = (bytes([0x11] * 8) +
                      bytes([0x22] * 8) +
                      bytes([0x33] * 8) +
                      bytes([0x44] * 8) +
                      bytes([0x00] * 8))

    response = test_client.post('/transform', json={
        'source_template_url': 'http://localhost:8000/download/source_template.xml',
        'destination_template_url': 'http://localhost:8000/download/destination_template.xml',
        'data_urls': ['http://localhost:8000/download/source_data.bin'],
        'additional_data_urls': ['http://localhost:8000/download/additional_data.bin'],
    })

    assertStreamEqual(TEST_RESPONSE_DATA, expected_bytes)
    assert response.status_code == 200


def test_transform_remove_template(test_client, test_mock):
    global TEST_SOURCE_TEMPLATE
    global TEST_DESTINATION_TEMPLATE
    global TEST_SOURCE_DATA

    TEST_SOURCE_DATA = (bytes([0x11] * 8) +
                        bytes([0x22] * 8) +
                        bytes([0x33] * 8) +
                        bytes([0x44] * 8))

    TEST_SOURCE_TEMPLATE = """
        <template name="a">
            <field name="b" size="8"></field>
            <field name="c" size="8"></field>
            <field name="d" size="8"></field>
            <field name="e" size="8"></field>
        </template>
    """

    TEST_DESTINATION_TEMPLATE = """
        <template name="a">
            <field name="b" size="8"></field>
            <field name="c" size="8"></field>
            <field name="d" size="8"></field>
        </template>
    """

    expected_bytes = (bytes([0x11] * 8) +
                      bytes([0x22] * 8) +
                      bytes([0x33] * 8))

    response = test_client.post('/transform', json={
        'source_template_url': 'http://localhost:8000/download/source_template.xml',
        'destination_template_url': 'http://localhost:8000/download/destination_template.xml',
        'data_urls': ['http://localhost:8000/download/source_data.bin'],
        'additional_data_urls': ['http://localhost:8000/download/additional_data.bin'],
    })

    assertStreamEqual(TEST_RESPONSE_DATA, expected_bytes)
    assert response.status_code == 200


def test_transform_shrink_template(test_client, test_mock):
    global TEST_SOURCE_TEMPLATE
    global TEST_DESTINATION_TEMPLATE
    global TEST_SOURCE_DATA

    TEST_SOURCE_DATA = (bytes([0x11] * 8) +
                        bytes([0x22] * 8) +
                        bytes([0x33] * 8) +
                        bytes([0x44] * 8))

    TEST_SOURCE_TEMPLATE = """
        <template name="a">
            <field name="b" size="8"></field>
            <field name="c" size="8"></field>
            <field name="d" size="8"></field>
            <field name="e" size="8"></field>
        </template>
    """

    TEST_DESTINATION_TEMPLATE = """
        <template name="a">
            <field name="b" size="4"></field>
            <field name="c" size="5"></field>
            <field name="d" size="6"></field>
            <field name="e" size="7"></field>
        </template>
    """

    expected_bytes = (bytes([0x11] * 4) +
                      bytes([0x22] * 5) +
                      bytes([0x33] * 6) +
                      bytes([0x44] * 7))

    response = test_client.post('/transform', json={
        'source_template_url': 'http://localhost:8000/download/source_template.xml',
        'destination_template_url': 'http://localhost:8000/download/destination_template.xml',
        'data_urls': ['http://localhost:8000/download/source_data.bin'],
        'additional_data_urls': ['http://localhost:8000/download/additional_data.bin'],
    })

    assertStreamEqual(TEST_RESPONSE_DATA, expected_bytes)
    assert response.status_code == 200


def test_transform_grow_template(test_client, test_mock):
    global TEST_SOURCE_TEMPLATE
    global TEST_DESTINATION_TEMPLATE
    global TEST_SOURCE_DATA

    TEST_SOURCE_DATA = (bytes([0x11] * 8) +
                        bytes([0x22] * 8) +
                        bytes([0x33] * 8) +
                        bytes([0x44] * 8))

    TEST_SOURCE_TEMPLATE = """
        <template name="a">
            <field name="b" size="8"></field>
            <field name="c" size="8"></field>
            <field name="d" size="8"></field>
            <field name="e" size="8"></field>
        </template>
    """

    TEST_DESTINATION_TEMPLATE = """
        <template name="a">
            <field name="b" size="16"></field>
            <field name="c" size="15"></field>
            <field name="d" size="14"></field>
            <field name="e" size="13"></field>
        </template>
    """

    expected_bytes = (bytes([0x11] * 8) +
                      bytes([0x00] * 8) +
                      bytes([0x22] * 8) +
                      bytes([0x00] * 7) +
                      bytes([0x33] * 8) +
                      bytes([0x00] * 6) +
                      bytes([0x44] * 8) +
                      bytes([0x00] * 5))

    response = test_client.post('/transform', json={
        'source_template_url': 'http://localhost:8000/download/source_template.xml',
        'destination_template_url': 'http://localhost:8000/download/destination_template.xml',
        'data_urls': ['http://localhost:8000/download/source_data.bin'],
        'additional_data_urls': ['http://localhost:8000/download/additional_data.bin'],
    })

    assert len(TEST_RESPONSE_DATA) == len(expected_bytes)
    assertStreamEqual(TEST_RESPONSE_DATA, expected_bytes)
    assert response.status_code == 200


@pytest.mark.skip()
def test_transform_single_source_template_single_destination_template():
    pass


@pytest.mark.skip()
def test_transform_single_source_template_multiple_destination_templates():
    pass


@pytest.mark.skip()
def test_transform_multiple_source_templates_multiple_destination_templates():
    pass


@pytest.mark.skip()
def test_transform_multiple_source_templates_single_destination_templates():
    pass
