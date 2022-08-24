#!/usr/bin/env python
import sys
import os
import argparse
import logging
import ast
import re

from glob import glob

from jinja2 import Template


logger = logging.getLogger("api_docs_generator")

HTTP_METHODS = [
    "get", "post", "put", "patch", "delete",
    "head", "options", "trace"
]


def no_parse(line):
    return line


def parse_parameter(line):
    if line == "":
        return None
    split = line.find(":")
    if split == -1:
        raise ValueError(f"Invalid parameter line format: {line}")
    return {
        "name": line[0:split].strip(),
        "desc": line[split + 1:].strip(),
    }


def parse_typed_parameter(line):
    """
    Return a dictionary representing a typed parameter parsed from a line.

    Example of a typed parameter line:
        parameter_name (type): description
    """
    if line == "":
        return None
    regex = r"(\w+).*\((\w+)\):\s*(.+)"
    match = re.match(regex, line)
    if match is None:
        logger.info("Failed to find type for parameter on line: %s", line)
        return parse_parameter(line)

    groups = match.groups()

    return {
        "name": groups[0],
        "type": groups[1],
        "desc": groups[2],
    }


DOC_SECTIONS_PARSERS = {
    "request": no_parse,
    "response": no_parse,
    "status codes": parse_parameter,
    "url parameters": parse_parameter,
    "query parameters": parse_typed_parameter,
    "request json parameters": parse_typed_parameter,
    "response json parameters": parse_typed_parameter,
}

DOC_SECTIONS = list(DOC_SECTIONS_PARSERS.keys())


def get_section_lines(lines, section_name):
    """Return list of lines contained in a given doc section."""
    start = -1
    end = 0
    for idx, line in enumerate(lines):
        if line.strip().lower() == f"{section_name}:":
            start = idx + 1
            break

    if start == -1:
        logger.warning("Section %s not found!", section_name)
        return None

    for idx, line in enumerate(lines[start:len(lines)], start=start):
        for section in DOC_SECTIONS:
            if line.strip().lower() == f"{section}:":
                end = idx - 1
                break
        if end != 0:
            break

    if end == 0:
        end = len(lines)

    base_whitespace_length = len(lines[start]) - len(lines[start].lstrip())

    def limited_strip(line):
        line = line.replace(base_whitespace_length * " ", "", 1)
        line = line.rstrip()
        return line

    output = map(limited_strip, lines[start:end])
    output = map(DOC_SECTIONS_PARSERS[section_name], output)
    output = filter(lambda line: line is not None, output)
    return list(output)


def get_wdae_root_dir():
    dirname = os.path.dirname(__file__)
    return os.path.abspath(os.path.join(dirname, "../"))


def get_doc_output_dir():
    dirname = os.path.dirname(__file__)
    return os.path.abspath(os.path.join(dirname, "routes"))


def collect_views(root_dir, urls_files=None):
    """Return a list of all dirnames containing a views.py and urls.py file."""
    if urls_files is None or len(urls_files) == 0:
        urls_files = glob(f"{root_dir}/**/urls.py")

    view_dir_list = []
    for filepath in urls_files:
        directory = os.path.dirname(filepath)
        if os.path.exists(os.path.join(directory, "views.py")):
            view_dir_list.append(directory)
    return view_dir_list


def find_urlpatterns(url_tree):
    """Find and return urlpatterns Assign node."""
    for node in ast.iter_child_nodes(url_tree):
        if not isinstance(node, ast.Assign):
            continue
        if node.targets[0].id == "urlpatterns":
            return node

    return None


def find_view_class(views_tree, class_name):
    """Find and return view by class name."""
    for node in ast.iter_child_nodes(views_tree):
        if not isinstance(node, ast.ClassDef):
            continue
        if node.name == class_name:
            return node

    return None


def find_view_function(views_tree, function_name):
    """Find and return view by function name."""
    for node in ast.iter_child_nodes(views_tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        if node.name == function_name:
            return node

    return None


def find_api_view_decorator(function_node):
    """Return api_view decorator of a given view function."""
    for decorator in function_node.decorator_list:
        if not isinstance(decorator, ast.Call):
            continue
        if decorator.func.id == "api_view":
            return decorator

    return None


def get_view_source(pattern):
    """Return name of node that this view uses in views.py."""
    view_node = pattern.args[1]
    if isinstance(view_node, ast.Call):
        source_node = view_node.func.value
    else:
        source_node = view_node

    if isinstance(source_node, ast.Attribute):
        return source_node.attr

    if isinstance(source_node, ast.Name):
        return source_node.id

    return None


def iter_routes(url_tree):
    """Iterate through urlpatterns in a given parsed urls.py file."""
    urlpatterns = find_urlpatterns(url_tree)
    if urlpatterns is None:
        raise ValueError("Could not find urlpatterns in urls.py")

    assign_value = urlpatterns.value

    if isinstance(assign_value, ast.BinOp):
        if isinstance(assign_value.left, ast.List):
            urlpatterns = assign_value.left
        elif isinstance(assign_value.right, ast.List):
            urlpatterns = assign_value.right
        else:
            raise ValueError("Couldn't parse urlpatterns in urls.py")
    elif isinstance(assign_value, ast.List):
        urlpatterns = assign_value
    else:
        raise ValueError("Couldn't parse urlpatterns in urls.py")

    for pattern in urlpatterns.elts:
        regex = pattern.args[0].value
        view_source = get_view_source(pattern)
        if view_source is None:
            raise ValueError(
                f"Couldn't parse urlpatterns in urls.py for {regex}"
            )
        yield (regex, view_source)


def find_method(class_tree, method_name):
    """Find and return a method in a class."""
    for node in ast.iter_child_nodes(class_tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        if node.name == method_name:
            return node

    return None


def parse_http_docstring(docstring):
    """Return a dictionary containing the sections of a given docstring."""
    lines = docstring.split("\n")
    summary = lines[0]
    lines = lines[1:len(lines)]
    section_lines = {}
    for section in DOC_SECTIONS:
        # pylint: disable=broad-except
        try:
            out_lines = get_section_lines(lines, section)
            section_lines[section] = out_lines
        except ValueError as err:
            logger.error("Failed to parse section %s!", section)
            logger.exception(err)
        except Exception as err:
            logger.error("Failed to parse section %s!", section)
            logger.exception(err)

    output = {"summary": summary}

    for doc_type, doc in section_lines.items():
        out_doc_type = doc_type.replace(" ", "_")
        output[f"{out_doc_type}_doc"] = doc

    return output


def collect_http_method_docstrings(method_node, method_name=None):
    """Return a complete doc dictionary for a node."""
    docstring = ast.get_docstring(method_node)
    if docstring is None:
        return None

    # pylint: disable=broad-except
    try:
        output = parse_http_docstring(docstring)

        if method_name is None:
            method_name = method_node.name

        output["method"] = method_name

        return output
    except Exception as err:
        logger.error("Failed to parse method %s!", method_node.name)
        logger.exception(err)
        return None


def transform_api_name(name):
    name = name.replace("_", " ")
    return name.capitalize()


def get_route_documentation(regex, views_tree, view_source):
    """Collect all docstrings from source in a node tree."""
    output = []
    view_class = find_view_class(views_tree, view_source)
    if view_class is not None:
        for method_name in HTTP_METHODS:
            method_node = find_method(view_class, method_name)
            if method_node is None:
                continue

            route_documentation = collect_http_method_docstrings(method_node)
            if route_documentation is not None:
                route_documentation["regex"] = regex
                output.append(route_documentation)
        return output

    logger.info(
        "Failed to find view class %s, searching for function", view_source
    )
    view_function = find_view_function(views_tree, view_source)
    if view_function is None:
        raise ValueError(f"Could not find {view_source}")
    logger.info(
        "Found function %s", view_source
    )

    api_decorator = find_api_view_decorator(view_function)

    if api_decorator is None:
        raise ValueError(f"Invalid view function found for {view_source}")

    for method in api_decorator.args[0].elts:
        method_name = method.n
        route_documentation = collect_http_method_docstrings(
            view_function, method_name
        )
        output.append(route_documentation)
    return output


def collect_docstrings(route):
    """Collect view docstrings from a given route."""
    urls_filepath = os.path.join(route, "urls.py")
    with open(urls_filepath) as file:
        url_tree = ast.parse(file.read())

    views_filepath = os.path.join(route, "views.py")
    with open(views_filepath) as file:
        views_tree = ast.parse(file.read())

    module_docstring = ast.get_docstring(views_tree)

    api_routes = []

    output = {
        "api_name": transform_api_name(os.path.basename(route)),
        "api_module_documentation": module_docstring,
        "api_routes": api_routes
    }

    for regex, view_source in iter_routes(url_tree):
        api_routes.extend(get_route_documentation(
            regex, views_tree, view_source
        ))

    return output


def main(argv=None):
    """Entrypoint for API documentation generation tool."""
    description = "Tool for generating WDAE API documentation"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--verbose", "-V", "-v", action="count", default=0)
    parser.add_argument(
        "--root_dir", type=str, default=None,
        help="Root directory containing all routes"
    )
    parser.add_argument(
        "--output_dir", type=str, default=None,
        help="Directory to write results in"
    )

    parser.add_argument(
        "routes", type=str, nargs="*", default=None,
        help="routes to document (only module folder, eg. users_api)"
    )

    args = parser.parse_args(argv)

    if args.verbose == 1:
        logging.basicConfig(level=logging.WARNING)
    elif args.verbose == 2:
        logging.basicConfig(level=logging.INFO)
    elif args.verbose >= 3:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    logger.info("Beginning to collect documentation")

    root_dir = args.root_dir
    if root_dir is None:
        root_dir = get_wdae_root_dir()
    logger.info("Documentation root directory: %s", root_dir)

    urls_files = None
    if args.routes is not None:
        urls_files = []
        for route in args.routes:
            filepath = f"{root_dir}/{route}/urls.py"
            assert os.path.exists(filepath), filepath
            urls_files.append(filepath)
        logger.info("Found urls files for given routes: %s", urls_files)

    view_dir_list = collect_views(root_dir, urls_files)

    logger.info("Found views to collect documentation: %s", view_dir_list)

    documentation_dict = {}
    for view_dir in view_dir_list:
        api_name = os.path.basename(view_dir)
        # pylint: disable=broad-except
        try:
            logger.info("Collecting docstrings from %s", api_name)
            documentation = collect_docstrings(view_dir)
        except Exception as err:
            logger.error("Failed to collect docstrings from %s", api_name)
            logger.exception(err)
        else:
            documentation_dict[api_name] = documentation

    logger.info("Collected all docstrings!")

    output_dir = args.output_dir
    if output_dir is None:
        output_dir = get_doc_output_dir()
    logger.info("Documentation output directory: %s", output_dir)

    for api_name, doc_dict in documentation_dict.items():
        out_path = os.path.join(output_dir, f"{api_name}.rst")
        logger.info("Writing documentation for %s to %s", api_name, out_path)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w") as outfile:
            outfile.write(API_DOCUMENTATION_TEMPLATE.render(doc_dict))


API_DOCUMENTATION_TEMPLATE = Template(
    """\
{{ "#" * api_name|length }}
{{ api_name }}
{{ "#" * api_name|length }}

{%- if api_documentation %}

{{ api_documentation }}

{%- endif %}

{%- for api_route in api_routes %}

.. http:{{ api_route.method }}:: {{ api_route.regex }}

  {{ api_route.summary }}
  {% if api_route.request_doc %}
  **Example request:**

  .. sourcecode:: http
  {% for line in api_route.request_doc %}
      {{ line }}
  {%- endfor %}
  {%- endif %}
  {% if api_route.response_doc %}
  **Example response:**

  .. sourcecode:: http
  {% for line in api_route.response_doc %}
      {{ line }}
  {%- endfor %}
  {% endif %}

  {%- if api_route.status_codes_doc %}
  {%- for code in api_route.status_codes_doc %}
  :statuscode {{ code.name }}: {{ code.desc }}
  {%- endfor %}
  {%- endif %}

  {%- if api_route.url_parameters_doc %}
  {%- for url_param in api_route.url_parameters_doc %}
  :param {{ url_param.name }}: {{ url_param.desc }}
  {%- endfor %}
  {%- endif %}

  {%- if api_route.query_parameters_doc %}
  {%- for param in api_route.query_parameters_doc %}
  :queryparam {{ param.type }} {{ param.name }}: {{ param.desc }}
  {%- endfor %}
  {%- endif %}

  {%- if api_route.request_json_parameters_doc %}
  {%- for json_param in api_route.request_json_parameters_doc %}
  :<json {{ json_param.type }} {{ json_param.name }}: {{ json_param.desc }}
  {%- endfor %}
  {%- endif %}

  {%- if api_route.response_json_parameters_doc %}
  {%- for json_param in api_route.response_json_parameters_doc %}
  :>json {{ json_param.type }} {{ json_param.name }}: {{ json_param.desc }}
  {%- endfor %}
  {%- endif %}

{%- endfor %}
"""
)


if __name__ == "__main__":
    main(sys.argv[1:])
