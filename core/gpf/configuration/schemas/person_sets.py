person_set = {
    "id": {"type": "string"},
    "name": {"type": "string"},
    "values": {"type": "list", "schema": {"type": "string"}},
    "color": {"type": "string"},
}

person_set_collection = {
    "id": {"type": "string"},
    "name": {"type": "string"},
    "sources": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "from": {
                    "type": "string", "allowed": ["pedigree", "phenodb"],
                },
                "source": {"type": "string"},
            },
        },
    },
    "domain": {
        "type": "list",
        "schema": {"type": "dict", "schema": person_set},
    },
    "default": {"type": "dict", "schema": person_set},
}

person_set_collections_schema = {
    "type": "dict",
    "valuesrules": {
        "oneof": [
            {"type": "list", "schema": {"type": "string"}},
            {"type": "dict", "schema": person_set_collection},
        ],
    },
}
