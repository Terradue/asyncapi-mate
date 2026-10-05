# AsyncAPI Mate

AsyncAPI Mate generates Markdown documentation and PlantUML source diagrams from an AsyncAPI document. Its `x-applications` extension connects applications to their operations, channels, messages, and payloads.

The command produces an overview of the pipeline, a diagram for each application, and class diagrams for message payloads. Rendering the PlantUML sources into images is a separate step.

## Find what you need

This documentation follows [Diátaxis](https://diataxis.fr/), separating learning, practical tasks, technical facts, and conceptual understanding.

| Your goal | Start here |
| --- | --- |
| Learn by generating a small event pipeline | [Tutorial: your first pipeline](tutorials/first-pipeline.md) |
| Connect applications to operations in your document | [How to describe applications](how-to/describe-applications.md) |
| Refresh documentation after changing a schema | [How to regenerate documentation](how-to/regenerate.md) |
| Put the generated page and diagrams into a documentation site | [How to integrate the output](how-to/integrate-output.md) |
| Look up arguments, input expectations, or generated paths | [CLI](cli.md), [input](reference/input.md), and [output](reference/output.md) reference |
| Understand the pipeline and payload views | [Explanation: how rendering works](explanation/rendering.md) |

## Scope

The CLI accepts a readable local YAML or JSON file and requires an output directory. The package requires Python 3.10 or later. It resolves references and renders bundled templates; it does not validate a document against the AsyncAPI specification, contact a message broker, or generate SVG images.

The reference pages describe the current implementation, including its expected `defaultMessage` key, file overwrite behavior, and diagram-link limitations.
