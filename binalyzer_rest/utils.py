import requests

from anytree import find_by_attr


def transform(source_template, destination_template, additional_data={}):
    transfer(source_template, destination_template)
    bind(diff(source_template, destination_template), additional_data)


def transfer(source_template, destination_template):
    existing_leaves = [(source_leave, destination_leave)
                       for source_leave in source_template.leaves
                       for destination_leave in destination_template.leaves
                       if source_leave.name == destination_leave.name]

    for (source_leave, destination_leave) in existing_leaves:
        extension_size = destination_leave.size - source_leave.size
        destination_leave.value = (source_leave.value +
                                   bytes([0] * extension_size))


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
            template.value = bytes([0] * template.size)


def retrieve_data_and_bind_to_template(root_template, bindings):
    for binding in bindings:
        (data_url, template_name) = binding.values()
        template = find_by_attr(root_template, template_name)
        if template:
            data = requests.get(data_url).content
            template.value = data
