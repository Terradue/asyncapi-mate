# Integrate generated output into a documentation site

This guide places generated Markdown and diagrams in the directory layout expected by the bundled image links. You need a successful generation, a separate documentation project with a `docs` directory, and a PlantUML renderer capable of producing SVG.

## Arrange the generated artifacts

For output generated into `build/orders`, run the following from the directory containing that output. Replace `documentation-site` with your destination project:

```bash
mkdir -p documentation-site/docs/c4/components/EDA
mkdir -p documentation-site/docs/diagrams/src/c4/components/EDA
cp build/orders/asyncapi.md documentation-site/docs/c4/components/EDA/asyncapi.md
cp build/orders/asyncapi.puml documentation-site/docs/diagrams/src/c4/components/EDA/asyncapi.puml
cp build/orders/docs/diagrams/src/c4/components/EDA/*.puml documentation-site/docs/diagrams/src/c4/components/EDA/
```

These copy commands replace destination files with the same names. Review the destination before updating an existing site.

## Render the diagram sources

Use your PlantUML installation or your site's diagram build step to render each copied `.puml` file as SVG. Place the resulting images in:

```text
documentation-site/docs/diagrams/out/c4/components/EDA/
├── asyncapi.svg
├── order-service.svg
├── billing-service.svg
└── OrderCreated.svg
```

Preserve the source basenames. AsyncAPI Mate does not run this rendering step. Renderer installation and invocation depend on your publishing environment; consult the [PlantUML command-line documentation](https://plantuml.com/command-line).

## Add the page to navigation

In the destination project's MkDocs configuration, add this entry to its existing `nav`:

```yaml
nav:
  - Event pipeline: c4/components/EDA/asyncapi.md
```

Build or preview that site and check that the overview, application, and payload images appear. The relative image paths are correct for the page location used above.

## Check operation hyperlinks separately

Image placement does not repair the hyperlinks inside the diagrams. The current templates target `asyncapi_events.html` and reference-derived operation anchors. If these links are needed, update their targets for your site's URL layout and provide matching explicit anchors in the generated page before rendering and publishing.

See [Output reference](../reference/output.md) for the current link behavior. AsyncAPI Mate does not publish the site itself.
