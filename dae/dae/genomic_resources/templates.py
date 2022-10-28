import math
from jinja2 import Template


def convert_size(size_bytes: int) -> str:
    """Convert an integer representing size in bytes to a human-readable string.
    Copied from https://stackoverflow.com/questions/5194057/better-way-to-convert-file-sizes-in-python
    """
    if size_bytes == 0:
        return "0B"
    suffix = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    exponent = int(math.floor(math.log(size_bytes, 1024)))
    size = round(size_bytes / math.pow(1024, exponent), 2)
    return f"{size} {suffix[exponent]}"


repository_template = Template("""
<html>
 <head>
    <style>
        th {
            background: lightgray;
        }
        td, th {
            border: 1px solid black;
            padding: 5px;
        }
        table {
            border: 3px inset;
            max-width: 60%;
        }
        table, td, th {
            border-collapse: collapse;
        }
        .meta-div {
            max-height: 250px;
            overflow: scroll;
        }
        .nowrap {
            white-space: nowrap
        }
    </style>
 </head>
 <body>
     <table>
        <thead>
            <tr>
                <th>Type</th>
                <th>ID</th>
                <th>Version</th>
                <th>Number of files</th>
                <th>Size in bytes (total)</th>
                <th>Meta</th>
            </tr>
        </thead>
        <tbody>
            {%- for key, value in data.items() recursive%}
            <tr>
                <td class="nowrap">{{value['type']}}</td>
                <td class="nowrap">
                    <a href='/{{key}}/'>{{key}}</a>
                </td>
                <td class="nowrap">{{value['res_version']}}</td>
                <td class="nowrap">{{value['res_files']}}</td>
                <td class="nowrap">{{value['res_size']}}</td>
                <td>
                    <div class="meta-div">
                        {{value.get('meta', 'N/A')}}
                    </div>
                </td>
            </tr>
            {%- endfor %}
        </tbody>
     </table>
 </body>
</html>
""")

resource_template = Template("""
<html>
<head>
<style>
h3,h4 {
    margin-top:0.5em;
    margin-bottom:0.5em;
}

{% block extra_styles %}{% endblock %}

</style>
</head>
<body>
<h1>{{ resource_id }}</h3>

{% block content %}
N/A
{% endblock %}

<div>
<span class="description">
{{ data["meta"] if data["meta"] else "N/A" }}
</span>
</div>


</body>
</html>
""")
