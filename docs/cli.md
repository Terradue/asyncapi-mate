# Command Line

AsyncAPI Mate exposes one console command, `asyncapi_mate`, defined by the package entry point in `pyproject.toml`.

```bash
asyncapi_mate [OPTIONS] SOURCE
```

`SOURCE` is the AsyncAPI YAML document to process. In the current command definition it must be a local file that exists, is readable, and can be resolved to an absolute path.

## Options

```text
--output PATH   Output directory path. Required.
-h, --help      Show command help.
--version       Show the package version.
```

## Example

```bash
asyncapi_mate ./asyncapi.yaml --output ./site
```

This reads `./asyncapi.yaml`, resolves references, renders the documentation templates, and writes the generated documentation files under `./site`.

## Generated Directory Tree

For an AsyncAPI document with two applications named `order-service` and `billing-service`, and two default messages named `OrderCreated` and `InvoiceIssued`, the generated files have this shape:

```text
site/
└── docs/
    ├── c4/
    │   └── components/
    │       └── EDA/
    │           └── asyncapi.md
    └── diagrams/
        └── src/
            └── c4/
                └── components/
                    └── EDA/
                        ├── asyncapi.puml
                        ├── order-service.puml
                        ├── billing-service.puml
                        ├── OrderCreated.puml
                        └── InvoiceIssued.puml
```

The exact application and message file names come from the input document:

- `<application>.puml` is generated from each key under `x-applications`.
- `<message>.puml` is generated from `operation.channel.messages.defaultMessage.name`.

If more than one operation uses the same default message name, the first schema diagram is written and later operations with the same target file are skipped.

## Generated Files

`docs/c4/components/EDA/asyncapi.md` is the generated Markdown page. It includes the AsyncAPI title, version, description, project contact, license, terms of service, servers, pipeline section, application sections, operation details, payload schema images, and message examples.

`docs/diagrams/src/c4/components/EDA/asyncapi.puml` is the overall PlantUML pipeline diagram. It renders every `x-applications` entry as a component, channels as queues, and operation links from each application to the related channel.

`docs/diagrams/src/c4/components/EDA/<application>.puml` is the PlantUML diagram for one application. It shows that application, the queues used by its operations, the direction of each operation, and JSON examples from the operation's default message.

`docs/diagrams/src/c4/components/EDA/<message>.puml` is the PlantUML class diagram for an operation payload schema. It is built from the default message payload and can contain classes, attributes, enums, inheritance, associations, arrays, unions, and mappings.

The CLI writes PlantUML source files under `docs/diagrams/src/...`. The generated Markdown page references rendered SVG images under `docs/diagrams/out/...`, for example:

```text
docs/diagrams/out/c4/components/EDA/asyncapi.svg
docs/diagrams/out/c4/components/EDA/<application>.svg
docs/diagrams/out/c4/components/EDA/<message>.svg
```

Those SVG files are related generated artifacts produced by a PlantUML rendering step after the CLI has written the `.puml` sources.
