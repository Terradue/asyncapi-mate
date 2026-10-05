# Payload diagram reference

The payload converter builds a display model from a schema mapping. This is a diagram projection, not a JSON Schema validator or a complete representation of every constraint.

| Schema feature | Diagram representation |
| --- | --- |
| `title` | Normalized class name; the root falls back to `Root`. |
| `properties` | Class attributes, including classes for inline object properties. |
| `required` | Required attributes use `+`; other attributes use `#`. |
| Scalar `type` | `string`, `integer`, `number`, `boolean`, or `null`; unrecognized types fall back to `any`. |
| String `pattern` | Displayed as `re.compile(...)`; the renderer does not execute the expression. |
| String `enum` | Named enum and association. |
| `const` | Displayed alongside an attribute when its value is not null. |
| `$defs` / `definitions` | Reusable definitions rendered as classes; `$defs` takes precedence when present. |
| `$ref` | Named type and association when the reference remains in the schema passed to the converter. |
| `allOf` | Referenced parents produce inheritance; inline object fragments contribute properties and required fields. |
| `oneOf` | `Union[...]` display type, with links to referenced objects, inline objects, and enums. |
| Array `items` | `List[...]`, with links for supported item types. Missing item schemas display as `List[Any]`. |
| `additionalProperties: true` | `Mapping[str, Any]`. |
| Schema-valued `additionalProperties` | `Mapping[str, <value type>]`, with a value association when applicable. |
| `additionalProperties: false` | No additional-properties attribute. |

An object with only additional properties can appear directly as a mapping field. Objects with named properties can display a separate `additionalProperties` attribute. Collection associations use `1` and `0..*` multiplicities.

## Limits

Constraints such as numeric bounds, string length, and `anyOf` are not fully represented. The `+` and `#` symbols indicate requiredness by this project's convention, rather than language-level visibility.

The CLI resolves document references before conversion. The converter's support for raw `$ref` relationships does not mean those references will always remain intact after loading; resolved schemas can instead appear as inline structures. Circular reference graphs are not covered by the documented workflow.

For an overview of how these structures complement pipeline diagrams, read [How rendering works](../explanation/rendering.md).
