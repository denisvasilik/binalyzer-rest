import requests

from anytree import find_by_attr

from binalyzer import XMLTemplateParser


def create_template(template_url, bindings):
    root_template_response = requests.get(template_url)
    root_template_text = root_template_response.text
    root_template = XMLTemplateParser(root_template_text).parse()

    for binding in bindings:
        (data_url, template_name) = binding.values()
        if root_template.name == template_name:
            root_data = requests.get(data_url).content
            root_template = XMLTemplateParser(
                root_template_text, root_data).parse()

    return root_template


def bind_data_to_template(root_template, bindings):
    for binding in bindings:
        data_url = binding.get('data_url')
        template_name = binding.get('template_name')
        template = find_by_attr(root_template, template_name)
        if template:
            data = requests.get(data_url).content
            template.value = data
