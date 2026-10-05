# Input document reference

AsyncAPI Mate loads YAML or JSON, requires a mapping at the document root, and resolves JSON references with `jsonref`. It does not run an AsyncAPI schema validator. The following expectations come from the bundled templates and renderer; they are not a complete AsyncAPI specification.

## Fields consumed by the renderer

| Field | Use |
| --- | --- |
| `asyncapi` | Specification version displayed in the Markdown page. |
| `info.title`, `info.version`, `info.description` | Page title and introduction. |
| `info.contact.name`, `info.contact.email` | Project team link. |
| `info.license.name`, `info.license.url`, `info.termsOfService` | Licensing and terms links. |
| `servers` | Mapping iterated by the Markdown template. Use `{}` when there are no servers to describe. |
| `servers.<key>` | Displays `title`, `summary`, `description`, `host`, `protocol`, `protocolVersion`, and `externalDocs.description` / `externalDocs.url`. |
| `defaultContentType` | Message format label. |
| `x-applications` | Mapping of application names to their descriptions and operations. Required by the CLI. |
| `x-applications.<name>.summary` | Application description in Markdown. |
| `x-applications.<name>.operations` | List of inline operations or references to operations. |
| `operation.action` | `send` produces publisher arrows. Every other value follows the subscriber branch; use `receive` for receiving operations. |
| `operation.channel.address` | Queue label and normalized diagram identifier. |
| `operation.channel.parameters` | Optional parameter descriptions and enum values. |
| `operation.channel.messages.defaultMessage` | The specific message entry selected by the templates and CLI. Other message keys are not iterated. |
| `defaultMessage.name` | Message label and payload diagram filename. |
| `defaultMessage.payload` | Schema mapping passed to the payload diagram converter. |
| `defaultMessage.examples` | Examples with `name` and `payload`. Use `[]` for no examples. |

Missing descriptive values can render as empty text; missing nested objects or mappings can fail rendering. Start with the [complete example](../examples/orders.yaml) to supply the structure used by the templates.

## References

The example uses local fragment references such as `#/operations/publishOrder` and `#/channels/orders`. Reference proxies retain reference metadata used by the operation-anchor filter. Inline operations have no reference-derived anchor.

Remote references invoke an HTTP loader with a 30-second request timeout and HTTP status checking. Resolving references can therefore require network access. The implementation passes the source path directly as the reference base; relative external file references are not a documented portable workflow. Prefer a single document with local fragment references for the workflow shown here.

## Names

Use simple, distinct application keys and message names suitable for filenames. Their original values are used in output paths. Avoid path separators and collisions between application names and message names.

PlantUML identifiers replace spaces, hyphens, slashes, dots, and colons with underscores, and remove braces and square brackets. Distinct names can consequently produce the same diagram identifier. For example, `orders.created` and `orders-created` both become `orders_created`.
