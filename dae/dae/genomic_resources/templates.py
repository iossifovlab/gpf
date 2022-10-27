from jinja2 import Template

repository_template = Template("""
<html>
{%- for key, value in data.items() recursive%}
     {{key}}: {{value}}
{%- endfor %}
</html>
""")

resource_template = Template("""
<html>
{%- for key, value in data.items() recursive%}
     {{key}}: {{value}}
{%- endfor %}
</html>
""")
