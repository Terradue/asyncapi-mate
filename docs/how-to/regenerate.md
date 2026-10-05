# Regenerate documentation after a change

Use a fresh output directory when updating payload schemas. Existing payload diagram files are skipped, and removed messages or applications leave old files behind.

## Generate into a fresh directory

Choose a directory you have not used for an earlier generation:

```bash
asyncapi-mate asyncapi.yaml --output build/documentation-review-2
```

Wait for a successful exit and the `SUCCESS` log entry. If generation fails, correct the input and use another fresh directory so partial output does not cause payload diagrams to be skipped.

## Review the result

Compare the Markdown, application diagrams, and payload diagrams with the previously published output. Confirm that each message name identifies one intended schema and that application names do not collide with message names.

Re-render the `.puml` files to SVG and replace the corresponding published artifacts together. Remove obsolete published pages or diagrams as part of your site's normal review process.

See [Integrate the output](integrate-output.md) for the expected placement and [Output reference](../reference/output.md) for exact overwrite behavior.
