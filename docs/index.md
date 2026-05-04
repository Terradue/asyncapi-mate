# AsyncAPI Mate

AsyncAPI Mate turns an AsyncAPI YAML document into Markdown documentation for an event-driven pipeline. It reads the AsyncAPI definition, follows resolved references, and renders a documentation page that describes the API metadata, servers, applications, operations, topics, payload schemas, and examples.

The generated Markdown page is backed by PlantUML diagrams. Together, those diagrams show the full asynchronous pipeline, each application participating in it, and the payload structure for every generated message schema.

## How It Models The Pipeline

AsyncAPI Mate relies on the `x-applications` extension to describe the actors in the pipeline. Each entry under `x-applications` represents an application, service, producer, consumer, or other runtime component that participates in the AsyncAPI system.

An application declares the operations it performs. Operations with the AsyncAPI action `send` are rendered as publishers: the application writes an event to a channel. Other operations are rendered as subscribers: the application reads an event from a channel.

The operation links the actor to the AsyncAPI channel, the channel address, the default message, the payload schema, and the examples. This lets the generated documentation describe both the business-level pipeline and the concrete event contracts that flow through it.

## What Gets Generated

For an input AsyncAPI document, the CLI renders these documentation artifacts into the selected output directory:

- `docs/c4/components/EDA/asyncapi.md`: the main generated Markdown page for the AsyncAPI document.
- `docs/diagrams/src/c4/components/EDA/asyncapi.puml`: a PlantUML overview of the whole pipeline, with applications connected to the queues they publish to or subscribe from.
- `docs/diagrams/src/c4/components/EDA/<application>.puml`: one PlantUML diagram per `x-applications` entry, focused on that application and its operations.
- `docs/diagrams/src/c4/components/EDA/<message>.puml`: one PlantUML class diagram per operation payload, named from the operation's default message.

The generated Markdown page embeds the rendered diagram images and organizes the AsyncAPI content into sections for project metadata, license, servers, pipeline, applications, operations, payload schemas, and examples.

## Diagram Content

The pipeline diagrams render each `x-applications` entry as a PlantUML component. Channels are rendered as queues, and operation direction is derived from the AsyncAPI action:

- `send` operations draw the application as publishing down to the queue.
- Non-`send` operations draw the application as subscribing from the queue.

The application-specific diagrams repeat the same relationship for a single actor and include JSON examples from the default message inside the queue representation.

Payload diagrams are generated from each operation's default message payload schema. The schema converter produces a PlantUML class model with:

- classes for object schemas and inline object properties;
- attributes for schema properties, with required fields marked separately from optional fields;
- enums for string enum values;
- inheritance links for `$ref` entries inside `allOf`;
- associations for `$ref`, object, array, enum, and `oneOf` relationships;
- `List[...]`, `Union[...]`, and `Mapping[str, ...]` types for arrays, unions, and `additionalProperties`.

This gives each generated operation page both the communication view of the pipeline and the structural view of the event payload that travels through it.
