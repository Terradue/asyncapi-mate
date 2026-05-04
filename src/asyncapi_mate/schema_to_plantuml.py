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

from __future__ import annotations

from . import to_puml_name
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Set, Tuple

JsonDict = Dict[str, Any]
MISSING = object()


def ref_name(ref: str) -> str:
    return to_puml_name(ref.split("/")[-1])


def schema_title(node: JsonDict, fallback: str) -> str:
    return to_puml_name(node.get("title", fallback))


def py_string_literal(value: str) -> str:
    return repr(value)


@dataclass
class Attribute:
    name: str
    type: str
    required: bool = False
    const: Optional[Any] = None


@dataclass
class ClassDef:
    name: str
    attributes: List[Attribute] = field(default_factory=list)
    additional_properties: List[Attribute] = field(default_factory=list)


@dataclass
class EnumDef:
    name: str
    values: List[str]


@dataclass
class LinkDef:
    src: str
    dst: str
    label: str
    mult_src: Optional[str] = None
    mult_dst: Optional[str] = None


@dataclass
class DiagramModel:
    classes: List[ClassDef] = field(default_factory=list)
    enums: List[EnumDef] = field(default_factory=list)
    inheritances: List[Tuple[str, str]] = field(default_factory=list)  # (parent, child)
    links: List[LinkDef] = field(default_factory=list)


class SchemaToPlantUMLModel:
    def __init__(self, schema: JsonDict):
        self.schema = schema
        self.defs: JsonDict = schema.get("$defs", schema.get("definitions", {}))

        self.model = DiagramModel()

        self._classes_by_name: Dict[str, ClassDef] = {}
        self._enums_by_name: Dict[str, EnumDef] = {}
        self._inheritance_seen: Set[Tuple[str, str]] = set()
        self._links_seen: Set[Tuple[str, str, str, Optional[str], Optional[str]]] = (
            set()
        )
        self._rendered: Set[str] = set()

    def build(self) -> DiagramModel:
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

    def _ensure_enum(self, name: str, values: List[Any]) -> None:
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
        mult_src: Optional[str] = None,
        mult_dst: Optional[str] = None,
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
        t = node.get("type")
        if t == "string":
            return self._string_type(node)
        if t in {"integer", "number", "boolean", "null", "object", "array"}:
            return t
        if "$ref" in node:
            return ref_name(node["$ref"])
        return "any"

    def _inline_object_fragments(self, node: JsonDict) -> List[JsonDict]:
        fragments = [node]

        for parent in node.get("allOf", []):
            if "$ref" not in parent and self._is_object_like(parent):
                fragments.extend(self._inline_object_fragments(parent))

        return fragments

    def _flattened_properties(self, node: JsonDict) -> Dict[str, JsonDict]:
        properties: Dict[str, JsonDict] = {}

        for fragment in self._inline_object_fragments(node):
            properties.update(fragment.get("properties", {}))

        return properties

    def _flattened_required(self, node: JsonDict) -> Set[str]:
        required: Set[str] = set()

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

    def _additional_properties_schema(self, node: JsonDict) -> Optional[Any]:
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
    ) -> Optional[str]:
        additional_properties = self._additional_properties_schema(node)
        if additional_properties is None:
            return None

        if additional_properties is True:
            return "Any"

        value_type = self._field_type(
            owner_name, f"{prop_name}_Value", additional_properties
        )
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
    ) -> Optional[str]:
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
        mult_src: Optional[str] = None,
        mult_dst: Optional[str] = None,
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

        if member.get("enum") and member.get("type") == "string":
            enum_name = to_puml_name(f"{fallback}_Enum")
            self._ensure_enum(enum_name, member["enum"])
            self._add_link(owner_name, enum_name, label, mult_src, mult_dst)
            return

        if "$ref" in member:
            self._add_link(
                owner_name, ref_name(member["$ref"]), label, mult_src, mult_dst
            )
            return

        if "oneOf" in member:
            for i, option in enumerate(member["oneOf"], start=1):
                if "$ref" in option:
                    self._add_link(
                        owner_name, ref_name(option["$ref"]), label, mult_src, mult_dst
                    )
                elif option.get("enum") and option.get("type") == "string":
                    enum_name = to_puml_name(f"{fallback}_Option{i}_Enum")
                    self._ensure_enum(enum_name, option["enum"])
                    self._add_link(owner_name, enum_name, label, mult_src, mult_dst)
                elif self._is_object_like(option):
                    target_name = self._inline_object_name(
                        option, f"{fallback}_Option{i}"
                    )
                    self._render_object(target_name, option)
                    self._add_link(owner_name, target_name, label, mult_src, mult_dst)
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
                value_type = self._field_type(
                    name, "additionalProperties", additional_properties
                )
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
    builder = SchemaToPlantUMLModel(schema)
    model = builder.build()
    return asdict(model)
