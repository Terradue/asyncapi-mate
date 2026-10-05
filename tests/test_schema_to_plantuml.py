from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from asyncapi_mate import to_puml_name
from asyncapi_mate.schema_to_plantuml import (
    plantuml_application_channel_definitions,
    plantuml_operation_channel_definitions,
    schema_to_plantuml_model,
)


def _render_schema_diagram(model: object) -> str:
    templates_dir = Path(__file__).resolve().parents[1] / "src" / "asyncapi_mate" / "templates"
    environment = Environment(loader=FileSystemLoader(templates_dir))
    template = environment.get_template(
        "docs/diagrams/src/c4/components/EDA/schema_to_plantuml.puml.jinja"
    )
    return template.render(model=model)


def _render_eda_diagram(template_name: str, **context: object) -> str:
    templates_dir = Path(__file__).resolve().parents[1] / "src" / "asyncapi_mate" / "templates"
    environment = Environment(loader=FileSystemLoader(templates_dir))
    environment.filters.update(
        {
            "to_puml_name": to_puml_name,
            "get_operation_anchor_link": lambda operation: "operation-anchor",
            "plantuml_operation_channel_definitions": (plantuml_operation_channel_definitions),
            "plantuml_application_channel_definitions": (plantuml_application_channel_definitions),
        }
    )
    template = environment.get_template(template_name)
    return template.render(**context)


def _operation(
    action: str, address: str, message_name: str, examples: list[dict[str, object]]
) -> dict[str, object]:
    return {
        "action": action,
        "channel": {
            "address": address,
            "messages": {
                "defaultMessage": {
                    "name": message_name,
                    "examples": examples,
                }
            },
        },
    }


def _example(name: str, payload: object) -> dict[str, object]:
    return {"name": name, "payload": payload}


def test_plantuml_application_channel_definitions_deduplicate_writer_topics() -> None:
    applications = {
        "writer-a": {
            "operations": [
                _operation(
                    "send",
                    "events/orders.created",
                    "OrderCreated",
                    [_example("CreatedSample", {"id": "1"})],
                )
            ]
        },
        "writer-b": {
            "operations": [
                _operation(
                    "send",
                    "events/orders.created",
                    "OrderCreated",
                    [
                        _example("CreatedSample", {"id": "1"}),
                        _example("EnrichedSample", {"id": "2"}),
                    ],
                )
            ]
        },
        "reader": {
            "operations": [
                _operation(
                    "receive",
                    "events/orders.created",
                    "OrderCreated",
                    [_example("ReaderSample", {"id": "3"})],
                )
            ]
        },
    }

    channels = plantuml_application_channel_definitions(applications)

    assert len(channels) == 1
    assert channels[0].address == "events/orders.created"
    assert [example.name for example in channels[0].examples] == [
        "CreatedSample",
        "EnrichedSample",
    ]


def test_asyncapi_template_serializes_shared_writer_topic_once() -> None:
    asyncapi = {
        "x-applications": {
            "writer-a": {
                "operations": [
                    _operation(
                        "send",
                        "events/orders.created",
                        "OrderCreated",
                        [_example("CreatedSample", {"id": "1"})],
                    )
                ]
            },
            "writer-b": {
                "operations": [
                    _operation(
                        "send",
                        "events/orders.created",
                        "OrderCreated",
                        [
                            _example("CreatedSample", {"id": "1"}),
                            _example("EnrichedSample", {"id": "2"}),
                        ],
                    )
                ]
            },
        }
    }

    rendered = _render_eda_diagram(
        "docs/diagrams/src/c4/components/EDA/asyncapi.puml.jinja",
        asyncapi=asyncapi,
    )

    assert rendered.count('queue "events/orders.created" as events_orders_created') == 1
    assert rendered.count("json CreatedSample") == 1
    assert rendered.count("json EnrichedSample") == 1
    assert "writer_a -d-> events_orders_created" in rendered
    assert "writer_b -d-> events_orders_created" in rendered


def test_application_template_serializes_repeated_operation_topic_once() -> None:
    application = {
        "operations": [
            _operation(
                "send",
                "events/orders.created",
                "OrderCreated",
                [_example("CreatedSample", {"id": "1"})],
            ),
            _operation(
                "receive",
                "events/orders.created",
                "OrderCreated",
                [_example("CreatedSample", {"id": "1"})],
            ),
        ]
    }

    rendered = _render_eda_diagram(
        "docs/diagrams/src/c4/components/EDA/application.puml.jinja",
        application_name="worker",
        application=application,
    )

    assert rendered.count('queue "events/orders.created" as events_orders_created') == 1
    assert rendered.count("json CreatedSample") == 1
    assert "worker -D-> events_orders_created" in rendered
    assert "worker -U-> events_orders_created" in rendered


def test_schema_to_plantuml_model_tracks_typed_additional_properties() -> None:
    schema = {
        "title": "Metadata",
        "type": "object",
        "additionalProperties": {"$ref": "#/$defs/AttributeValue"},
        "$defs": {
            "AttributeValue": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                },
            }
        },
    }

    model = schema_to_plantuml_model(schema)
    classes = {cls["name"]: cls for cls in model["classes"]}

    assert "Mapping_str_Any" not in classes
    assert model["inheritances"] == []
    assert classes["Metadata"]["additional_properties"] == [
        {
            "name": "additionalProperties",
            "type": "Mapping[str, AttributeValue]",
            "required": False,
            "const": None,
        }
    ]
    assert {
        "src": "Metadata",
        "dst": "AttributeValue",
        "label": "additionalProperties",
        "mult_src": "1",
        "mult_dst": "0..*",
    } in model["links"]


def test_schema_to_plantuml_template_renders_typed_additional_properties() -> None:
    schema = {
        "title": "Metadata",
        "type": "object",
        "additionalProperties": {"$ref": "#/$defs/AttributeValue"},
        "$defs": {
            "AttributeValue": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                },
            }
        },
    }

    model = schema_to_plantuml_model(schema)
    rendered = _render_schema_diagram(model)

    assert "#additionalProperties: Mapping[str, AttributeValue]" in rendered
    assert 'Metadata "1" --> "0..*" AttributeValue : additionalProperties' in rendered


def test_schema_to_plantuml_model_tracks_untyped_additional_properties() -> None:
    schema = {
        "title": "Metadata",
        "type": "object",
        "additionalProperties": True,
    }

    model = schema_to_plantuml_model(schema)
    classes = {cls["name"]: cls for cls in model["classes"]}

    assert "Mapping_str_Any" not in classes
    assert model["inheritances"] == []
    assert classes["Metadata"]["additional_properties"] == [
        {
            "name": "additionalProperties",
            "type": "Mapping[str, Any]",
            "required": False,
            "const": None,
        }
    ]
    assert model["links"] == []


def test_schema_to_plantuml_template_renders_untyped_additional_properties() -> None:
    schema = {
        "title": "Metadata",
        "type": "object",
        "additionalProperties": True,
    }

    model = schema_to_plantuml_model(schema)
    rendered = _render_schema_diagram(model)

    assert "#additionalProperties: Mapping[str, Any]" in rendered
    assert "Mapping_str_Any" not in rendered


def test_schema_to_plantuml_flattens_inline_allof_and_map_properties() -> None:
    schema = {
        "title": "Event",
        "type": "object",
        "properties": {
            "data": {
                "title": "PipedData",
                "allOf": [
                    {"$ref": "#/$defs/BaseData"},
                    {
                        "type": "object",
                        "required": ["entries"],
                        "properties": {
                            "entries": {
                                "type": "object",
                                "additionalProperties": {
                                    "$ref": "#/$defs/GeoJSON_FeatureCollection"
                                },
                            }
                        },
                    },
                ],
            }
        },
        "$defs": {
            "BaseData": {
                "type": "object",
                "properties": {
                    "properties": {
                        "type": "object",
                        "additionalProperties": True,
                    }
                },
            },
            "GeoJSON_FeatureCollection": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["FeatureCollection"],
                    }
                },
            },
        },
    }

    model = schema_to_plantuml_model(schema)
    classes = {cls["name"]: cls for cls in model["classes"]}
    piped_data_attributes = {
        attr["name"]: attr["type"] for attr in classes["PipedData"]["attributes"]
    }
    base_data_attributes = {
        attr["name"]: attr["type"] for attr in classes["BaseData"]["attributes"]
    }

    assert "PipedData_AllOf_2" not in classes
    assert "PipedData_entries" not in classes
    assert piped_data_attributes["entries"] == "Mapping[str, GeoJSON_FeatureCollection]"
    assert base_data_attributes["properties"] == "Mapping[str, Any]"
    assert ("BaseData", "PipedData") in model["inheritances"]
    assert ("PipedData_AllOf_2", "PipedData") not in model["inheritances"]
    assert {
        "src": "PipedData",
        "dst": "GeoJSON_FeatureCollection",
        "label": "entries",
        "mult_src": "1",
        "mult_dst": "0..*",
    } in model["links"]


def test_schema_to_plantuml_template_avoids_synthetic_allof_map_classes() -> None:
    schema = {
        "title": "Event",
        "type": "object",
        "properties": {
            "data": {
                "title": "PipedData",
                "allOf": [
                    {"$ref": "#/$defs/BaseData"},
                    {
                        "type": "object",
                        "required": ["entries"],
                        "properties": {
                            "entries": {
                                "type": "object",
                                "additionalProperties": {
                                    "$ref": "#/$defs/GeoJSON_FeatureCollection"
                                },
                            }
                        },
                    },
                ],
            }
        },
        "$defs": {
            "BaseData": {
                "type": "object",
                "properties": {
                    "properties": {
                        "type": "object",
                        "additionalProperties": True,
                    }
                },
            },
            "GeoJSON_FeatureCollection": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["FeatureCollection"],
                    }
                },
            },
        },
    }

    rendered = _render_schema_diagram(schema_to_plantuml_model(schema))

    assert "class PipedData_AllOf_2" not in rendered
    assert "class PipedData_entries" not in rendered
    assert "+entries: Mapping[str, GeoJSON_FeatureCollection]" in rendered
    assert "#properties: Mapping[str, Any]" in rendered
    assert "PipedData_AllOf_2 <|-- PipedData" not in rendered
    assert 'PipedData "1" --> "0..*" GeoJSON_FeatureCollection : entries' in rendered


def test_schema_to_plantuml_detects_array_item_types() -> None:
    schema = {
        "title": "Batch",
        "type": "object",
        "properties": {
            "events": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                    },
                },
            },
            "states": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["pending", "done"],
                },
            },
            "by_name": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": {"$ref": "#/$defs/GeoJSON_FeatureCollection"},
                },
            },
        },
        "$defs": {
            "GeoJSON_FeatureCollection": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["FeatureCollection"],
                    }
                },
            }
        },
    }

    model = schema_to_plantuml_model(schema)
    classes = {cls["name"]: cls for cls in model["classes"]}
    batch_attributes = {attr["name"]: attr["type"] for attr in classes["Batch"]["attributes"]}

    assert batch_attributes["events"] == "List[Batch_events_Item]"
    assert batch_attributes["states"] == "List[Batch_states_Item_Enum]"
    assert batch_attributes["by_name"] == "List[Mapping[str, GeoJSON_FeatureCollection]]"
    assert "Batch_events_Item" in classes
    assert {
        "src": "Batch",
        "dst": "Batch_events_Item",
        "label": "events",
        "mult_src": "1",
        "mult_dst": "0..*",
    } in model["links"]
    assert {
        "src": "Batch",
        "dst": "Batch_states_Item_Enum",
        "label": "states",
        "mult_src": "1",
        "mult_dst": "0..*",
    } in model["links"]
    assert {
        "src": "Batch",
        "dst": "GeoJSON_FeatureCollection",
        "label": "by_name",
        "mult_src": "1",
        "mult_dst": "0..*",
    } in model["links"]


def test_schema_to_plantuml_template_renders_array_item_types() -> None:
    schema = {
        "title": "Batch",
        "type": "object",
        "properties": {
            "events": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                    },
                },
            },
            "states": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["pending", "done"],
                },
            },
            "by_name": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": {"$ref": "#/$defs/GeoJSON_FeatureCollection"},
                },
            },
        },
        "$defs": {
            "GeoJSON_FeatureCollection": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["FeatureCollection"],
                    }
                },
            }
        },
    }

    rendered = _render_schema_diagram(schema_to_plantuml_model(schema))

    assert "#events: List[Batch_events_Item]" in rendered
    assert "#states: List[Batch_states_Item_Enum]" in rendered
    assert "#by_name: List[Mapping[str, GeoJSON_FeatureCollection]]" in rendered
    assert 'Batch "1" --> "0..*" Batch_events_Item : events' in rendered
    assert 'Batch "1" --> "0..*" Batch_states_Item_Enum : states' in rendered
    assert 'Batch "1" --> "0..*" GeoJSON_FeatureCollection : by_name' in rendered
