# Copyright 2026 Terradue
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Build internal PlantUML diagram structures from JSON Schema and AsyncAPI data."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, field
from typing import Any

from . import to_puml_name

JsonDict = dict[str, Any]
MISSING = object()


def ref_name(ref: str) -> str:
    """Return the normalized final segment of a reference."""
    return to_puml_name(ref.split("/")[-1])


def schema_title(node: JsonDict, fallback: str) -> str:
    """Return a normalized schema title or the supplied fallback."""
    return to_puml_name(node.get("title", fallback))


def py_string_literal(value: str) -> str:
    """Quote a string for display as a Python literal."""
    return repr(value)


@dataclass
class Attribute:
    """A rendered class field and its display metadata."""

    name: str
    type: str
    required: bool = False
    const: Any | None = None


@dataclass
class ClassDef:
    """A class declaration in a PlantUML diagram."""

    name: str
    attributes: list[Attribute] = field(default_factory=list)
    additional_properties: list[Attribute] = field(default_factory=list)


@dataclass
class EnumDef:
    """An enumeration declaration in a PlantUML diagram."""

    name: str
    values: list[str]


@dataclass
class LinkDef:
    """An association between two diagram elements."""

    src: str
    dst: str
    label: str
    mult_src: str | None = None
    mult_dst: str | None = None


@dataclass
class DiagramModel:
    """Classes, enumerations, and relationships for template rendering."""

    classes: list[ClassDef] = field(default_factory=list)
    enums: list[EnumDef] = field(default_factory=list)
    inheritances: list[tuple[str, str]] = field(default_factory=list)  # (parent, child)
    links: list[LinkDef] = field(default_factory=list)


@dataclass
class ChannelExampleDef:
    """A named example displayed beside a diagram channel."""

    name: str
    payload: Any


@dataclass
class ChannelDef:
    """A diagram channel and its deduplicated examples."""

    address: str
    examples: list[ChannelExampleDef] = field(default_factory=list)


def _read_member(node: Any, key: str, default: Any = MISSING) -> Any:
    if isinstance(node, Mapping):
        return node.get(key, default)

    try:
        return node[key]
    except (AttributeError, IndexError, KeyError, TypeError):
        pass

    return getattr(node, key, default)


def _read_path(node: Any, *keys: str, default: Any = None) -> Any:
    current = node

    for key in keys:
        current = _read_member(current, key)
        if current is MISSING:
            return default

    return current


def _iter_application_operations(applications: Any) -> Iterable[Any]:
    application_values = (
        applications.values() if isinstance(applications, Mapping) else applications
    )

    for application in application_values or []:
        yield from _read_member(application, "operations", []) or []


def plantuml_operation_channel_definitions(
    operations: Iterable[Any],
    send_only: bool = False,
) -> list[ChannelDef]:
    """Collect channels and named examples, optionally limiting them to send operations."""
    channels_by_key: dict[str, ChannelDef] = {}
    seen_examples_by_channel: dict[str, set[str]] = {}

    for operation in operations or []:
        if send_only and _read_member(operation, "action") != "send":
            continue

        address = _read_path(operation, "channel", "address")
        if address is None:
            continue

        channel_key = to_puml_name(str(address))
        if channel_key not in channels_by_key:
            channels_by_key[channel_key] = ChannelDef(address=str(address))
            seen_examples_by_channel[channel_key] = set()

        channel = channels_by_key[channel_key]
        seen_examples = seen_examples_by_channel[channel_key]

        _append_channel_examples(channel, seen_examples, operation)

    return list(channels_by_key.values())


def _append_channel_examples(
    channel: ChannelDef, seen_examples: set[str], operation: object
) -> None:
    """Append named examples once per normalized name within a channel."""
    examples = _read_path(
        operation,
        "channel",
        "messages",
        "defaultMessage",
        "examples",
        default=[],
    )
    for example in examples or []:
        name = _read_member(example, "name", None)
        if name is None:
            continue

        example_name = to_puml_name(str(name))
        if example_name in seen_examples:
            continue

        seen_examples.add(example_name)
        channel.examples.append(
            ChannelExampleDef(
                name=example_name,
                payload=_read_member(example, "payload", {}),
            )
        )


def plantuml_application_channel_definitions(
    applications: Any,
    send_only: bool = True,
) -> list[ChannelDef]:
    """Collect channels and named examples, optionally limiting them to send operations."""
    return plantuml_operation_channel_definitions(
        _iter_application_operations(applications),
        send_only=send_only,
    )


class SchemaToPlantUMLModel:
    """Build diagram declarations and relationships from a JSON Schema."""

    def __init__(self, schema: JsonDict) -> None:
        self.schema = schema
        self.defs: JsonDict = schema.get("$defs", schema.get("definitions", {})) or {}

        self.model = DiagramModel()

        self._classes_by_name: dict[str, ClassDef] = {}
        self._enums_by_name: dict[str, EnumDef] = {}
        self._inheritance_seen: set[tuple[str, str]] = set()
        self._links_seen: set[tuple[str, str, str, str | None, str | None]] = set()
        self._rendered: set[str] = set()

    def build(self) -> DiagramModel:
        """Build the diagram, including reusable schema definitions."""
        root_name = schema_title(self.schema, "Root")
        self._render_object(root_name, self.schema)

        for def_name, def_schema in self.defs.items():
            self._render_object(to_puml_name(def_name), def_schema)

        self.model.classes = list(self._classes_by_name.values())
        self.model.enums = list(self._enums_by_name.values())
        return self.model

    def _ensure_class(self, name: str) -> ClassDef:
        if name not in self._classes_by_name:
            self._classes_by_name[name] = ClassDef(name=name)
        return self._classes_by_name[name]

    def _ensure_enum(self, name: str, values: list[Any]) -> None:
        if name not in self._enums_by_name:
            self._enums_by_name[name] = EnumDef(
                name=name,
                values=[to_puml_name(v) for v in values],
            )

    def _add_inheritance(self, parent: str, child: str) -> None:
        edge = (parent, child)
        if edge not in self._inheritance_seen:
            self._inheritance_seen.add(edge)
            self.model.inheritances.append(edge)

    def _add_link(
        self,
        src: str,
        dst: str,
        label: str,
        mult_src: str | None = None,
        mult_dst: str | None = None,
    ) -> None:
        edge = (src, dst, label, mult_src, mult_dst)
        if edge not in self._links_seen:
            self._links_seen.add(edge)
            self.model.links.append(
                LinkDef(
                    src=src,
                    dst=dst,
                    label=label,
                    mult_src=mult_src,
                    mult_dst=mult_dst,
                )
            )

    def _string_type(self, node: JsonDict) -> str:
        pattern = node.get("pattern")
        if pattern is not None:
            return f"re.compile({py_string_literal(pattern)})"
        return "string"

    def _scalar_type(self, node: JsonDict) -> str:
        scalar_type = node.get("type")
        if scalar_type == "string":
            return self._string_type(node)
        if isinstance(scalar_type, str) and scalar_type in {
            "integer",
            "number",
            "boolean",
            "null",
            "object",
            "array",
        }:
            return scalar_type
        if "$ref" in node:
            return ref_name(node["$ref"])
        return "any"

    def _inline_object_fragments(self, node: JsonDict) -> list[JsonDict]:
        fragments = [node]

        for parent in node.get("allOf", []):
            if "$ref" not in parent and self._is_object_like(parent):
                fragments.extend(self._inline_object_fragments(parent))

        return fragments

    def _flattened_properties(self, node: JsonDict) -> dict[str, JsonDict]:
        properties: dict[str, JsonDict] = {}

        for fragment in self._inline_object_fragments(node):
            properties.update(fragment.get("properties", {}))

        return properties

    def _flattened_required(self, node: JsonDict) -> set[str]:
        required: set[str] = set()

        for fragment in self._inline_object_fragments(node):
            required.update(fragment.get("required", []))

        return required

    def _raw_additional_properties_schema(self, node: JsonDict) -> Any:
        if not self._is_object_like(node):
            return MISSING

        if "additionalProperties" not in node:
            return MISSING

        return node["additionalProperties"]

    def _is_object_like(self, node: JsonDict) -> bool:
        return node.get("type") == "object" or "properties" in node or "allOf" in node

    def _inline_object_name(self, node: JsonDict, fallback: str) -> str:
        return schema_title(node, fallback)

    def _additional_properties_schema(self, node: JsonDict) -> Any | None:
        additional_properties: Any = MISSING

        for fragment in self._inline_object_fragments(node):
            candidate = self._raw_additional_properties_schema(fragment)
            if candidate is MISSING:
                continue
            if candidate is False:
                return None
            additional_properties = candidate

        if additional_properties is MISSING:
            return None

        return additional_properties

    def _mapping_value_type(
        self,
        owner_name: str,
        prop_name: str,
        node: JsonDict,
    ) -> str | None:
        additional_properties = self._additional_properties_schema(node)
        if additional_properties is None:
            return None

        if additional_properties is True:
            return "Any"

        value_type = self._field_type(owner_name, f"{prop_name}_Value", additional_properties)
        return "Any" if value_type == "any" else value_type

    def _is_pure_mapping_object(self, node: JsonDict) -> bool:
        if self._additional_properties_schema(node) is None:
            return False

        if self._flattened_properties(node):
            return False

        for fragment in self._inline_object_fragments(node):
            if any("$ref" in parent for parent in fragment.get("allOf", [])):
                return False

        return True

    def _mapping_type(
        self,
        owner_name: str,
        prop_name: str,
        node: JsonDict,
    ) -> str | None:
        if not self._is_pure_mapping_object(node):
            return None

        value_type = self._mapping_value_type(owner_name, prop_name, node)
        if value_type is None:
            return None

        return f"Mapping[str, {value_type}]"

    def _union_member_type(
        self,
        option: JsonDict,
        owner_name: str,
        prop_name: str,
        idx: int,
    ) -> str:
        if "$ref" in option:
            return ref_name(option["$ref"])

        if option.get("enum") and option.get("type") == "string":
            enum_name = to_puml_name(f"{owner_name}_{prop_name}_Option{idx}_Enum")
            self._ensure_enum(enum_name, option["enum"])
            return enum_name

        if self._is_object_like(option):
            fallback = f"{owner_name}_{prop_name}_Option{idx}"
            class_name = self._inline_object_name(option, fallback)
            self._render_object(class_name, option)
            return class_name

        return self._scalar_type(option)

    def _field_type(
        self,
        owner_name: str,
        prop_name: str,
        prop: JsonDict,
    ) -> str:
        if "oneOf" in prop:
            members = [
                self._union_member_type(option, owner_name, prop_name, i + 1)
                for i, option in enumerate(prop["oneOf"])
            ]
            return f"Union[{', '.join(members)}]"

        if prop.get("enum") and prop.get("type") == "string":
            enum_name = to_puml_name(f"{owner_name}_{prop_name}_Enum")
            self._ensure_enum(enum_name, prop["enum"])
            return enum_name

        if "$ref" in prop:
            return ref_name(prop["$ref"])

        return self._container_field_type(owner_name, prop_name, prop)

    def _container_field_type(self, owner_name: str, prop_name: str, prop: JsonDict) -> str:
        """Resolve arrays, mappings, inline objects, and scalar field types."""
        if prop.get("type") == "array":
            items = prop.get("items")
            if items is None:
                return "List[Any]"

            item_type = self._field_type(owner_name, f"{prop_name}_Item", items)
            if item_type == "any":
                item_type = "Any"
            return f"List[{item_type}]"

        mapping_type = self._mapping_type(owner_name, prop_name, prop)
        if mapping_type is not None:
            return mapping_type

        if self._is_object_like(prop):
            child_name = self._inline_object_name(prop, f"{owner_name}_{prop_name}")
            self._render_object(child_name, prop)
            return child_name

        return self._scalar_type(prop)

    def _render_member_links(
        self,
        owner_name: str,
        label: str,
        member: JsonDict,
        fallback: str,
        mult_src: str | None = None,
        mult_dst: str | None = None,
    ) -> None:
        mapping_type = self._mapping_type(owner_name, label, member)
        if mapping_type is not None:
            additional_properties = self._additional_properties_schema(member)
            if isinstance(additional_properties, dict):
                self._render_member_links(
                    owner_name,
                    label,
                    additional_properties,
                    f"{fallback}_Value",
                    mult_src or "1",
                    mult_dst or "0..*",
                )
            return

        if "$ref" in member or (member.get("enum") and member.get("type") == "string"):
            self._render_direct_link(owner_name, label, member, fallback, mult_src, mult_dst)
            return

        self._render_container_links(owner_name, label, member, fallback, mult_src, mult_dst)

    def _render_container_links(
        self,
        owner_name: str,
        label: str,
        member: JsonDict,
        fallback: str,
        mult_src: str | None,
        mult_dst: str | None,
    ) -> None:
        """Render union and array relationships with their display multiplicities."""
        if "oneOf" in member:
            for index, option in enumerate(member["oneOf"], start=1):
                self._render_direct_link(
                    owner_name, label, option, f"{fallback}_Option{index}", mult_src, mult_dst
                )
            return

        if member.get("type") == "array":
            items = member.get("items")
            if items is not None:
                self._render_member_links(
                    owner_name,
                    label,
                    items,
                    f"{fallback}_Item",
                    mult_src or "1",
                    mult_dst or "0..*",
                )
            return

        self._render_direct_link(owner_name, label, member, fallback, mult_src, mult_dst)

    def _render_direct_link(
        self,
        owner_name: str,
        label: str,
        member: JsonDict,
        fallback: str,
        mult_src: str | None,
        mult_dst: str | None,
    ) -> None:
        """Connect a field to its referenced class, inline class, or enum."""
        if member.get("enum") and member.get("type") == "string":
            enum_name = to_puml_name(f"{fallback}_Enum")
            self._ensure_enum(enum_name, member["enum"])
            self._add_link(owner_name, enum_name, label, mult_src, mult_dst)
            return

        if "$ref" in member:
            self._add_link(owner_name, ref_name(member["$ref"]), label, mult_src, mult_dst)
            return

        if self._is_object_like(member):
            target_name = self._inline_object_name(member, fallback)
            self._render_object(target_name, member)
            self._add_link(owner_name, target_name, label, mult_src, mult_dst)

    def _render_class(self, name: str, node: JsonDict) -> None:
        cls = self._ensure_class(name)
        if cls.attributes or cls.additional_properties:
            return

        required = self._flattened_required(node)
        for prop_name, prop in self._flattened_properties(node).items():
            cls.attributes.append(
                Attribute(
                    name=prop_name,
                    type=self._field_type(name, prop_name, prop),
                    required=prop_name in required,
                    const=prop.get("const"),
                )
            )

        additional_properties = self._additional_properties_schema(node)
        if additional_properties is not None:
            value_type = "Any"
            if isinstance(additional_properties, dict):
                value_type = self._field_type(name, "additionalProperties", additional_properties)
                if value_type == "any":
                    value_type = "Any"

            cls.additional_properties.append(
                Attribute(
                    name="additionalProperties",
                    type=f"Mapping[str, {value_type}]",
                )
            )

    def _render_object(self, name: str, node: JsonDict) -> None:
        if name in self._rendered:
            return
        self._rendered.add(name)

        self._render_class(name, node)

        if "allOf" in node:
            for parent in node["allOf"]:
                if "$ref" in parent:
                    parent_name = ref_name(parent["$ref"])
                    self._add_inheritance(parent_name, name)

        for prop_name, prop in self._flattened_properties(node).items():
            self._render_member_links(name, prop_name, prop, f"{name}_{prop_name}")

        additional_properties = self._additional_properties_schema(node)
        if isinstance(additional_properties, dict):
            self._render_member_links(
                name,
                "additionalProperties",
                additional_properties,
                f"{name}_additionalProperties",
                "1",
                "0..*",
            )


def schema_to_plantuml_model(schema: JsonDict) -> JsonDict:
    """Return the diagram as a mapping suitable for Jinja templates."""
    builder = SchemaToPlantUMLModel(schema)
    model = builder.build()
    return asdict(model)
