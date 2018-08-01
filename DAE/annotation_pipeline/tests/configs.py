BASE_CONFIG = """
[Add location]

options.columns=location

columns.location=loc
"""

REANNOTATE_CONFIG = """
[Reannotate location]

options.columns=location

columns.location=location
"""

DEFAULT_ARGUMENTS_CONFIG = """
[Add location]

options.columns=location

columns.location=location
options.default=True
"""

VIRTUALS_CONFIG = """
[Add location]

options.columns=location,variant

columns.location=loc
columns.variant=var

virtuals=variant
"""
