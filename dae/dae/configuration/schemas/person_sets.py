person_set = {
    "id": {"type": "string"},
    "name": {"type": "string"},
    "value": {"type": "string"},
    "color": {"type": "string"},
}

person_set_collection = {
    "id": {"type": "string"},
    "name": {"type": "string"},
    "source": {
        "type": "dict",
        "schema": {
            "phenotype": {
                "type": "dict",
                "schema": {
                    "instrument": {"type": "string"},
                    "measure": {"type": "string"},
                },
                "excludes": "pedigree",
            },
            "pedigree": {
                "type": "dict",
                "schema": {"column": {"type": "string"}},
                "excludes": "phenotype",
            },
        },
    },
    "domain": {
        "type": "list",
        "schema": {"type": "dict", "schema": person_set},
    },
}

person_set_collections_schema = {
    "type": "dict",
    "valuesrules": {
        "oneof": [
            {"type": "list", "schema": {"type": "string"}},
            {"type": "dict", "schema": person_set_collection},
        ]
    },
}
