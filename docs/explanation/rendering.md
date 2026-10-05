# How rendering connects applications and payloads

An event-driven system has both a communication structure and a data structure. AsyncAPI Mate presents them as separate diagram views: applications exchange messages through channels, while payload schemas describe the content of those messages.

## Applications provide the runtime view

The `x-applications` extension groups operations by the component that performs them. That grouping lets the renderer show an order service and a billing service as distinct actors even when they share a channel and a message definition.

The action determines the relationship shown in a diagram. A `send` operation publishes to a queue; other actions use the receiving branch. The tool draws these relationships from the document without inspecting a running broker or service.

## Overview and application diagrams answer different questions

The overview collects queue declarations and examples from sending operations across applications. Repeated channels are grouped by their normalized PlantUML identifier. Named examples are deduplicated within a channel by their normalized names; the first encountered example wins.

An application diagram collects channels for all of that application's operations. It can therefore show a receiving channel even when no publisher for it is documented. The overview still draws receiver relationships, but explicit queue declarations and examples depend on send operations.

Deduplicating a queue does not deduplicate the operations themselves. Each operation still contributes its own relationship.

## Payload diagrams are a structural projection

Payload diagrams turn schema properties into fields, object definitions into classes, and supported relationships into associations or inheritance. This makes the contract easier to inspect alongside the communication view.

A diagram cannot establish that a payload is valid. Many validation constraints are not displayed, and document reference resolution can affect whether a relationship reaches the converter as a reference or as an inline object. The [schema support reference](../reference/schema-support.md) describes the implemented subset.

## Source generation and publishing are separate

The CLI resolves the input, renders bundled templates, and writes Markdown and PlantUML sources. A publishing workflow then arranges the files, renders diagrams into SVG, and builds a site.

This separation allows the generated artifacts to be reviewed as text. It also means a successful CLI run alone does not ensure that images or diagram hyperlinks resolve in the published site. The [integration guide](../how-to/integrate-output.md) describes the required layout and link checks.
