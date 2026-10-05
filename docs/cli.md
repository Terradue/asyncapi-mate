# CLI reference

The installed console command is `asyncapi-mate`.

```text
asyncapi-mate [OPTIONS] SOURCE
```

## Arguments and options

| Name | Required | Meaning |
| --- | --- | --- |
| `SOURCE` | Yes | Existing, readable local file. Click resolves its path before processing. YAML and JSON documents can be loaded. |
| `--output PATH` | Yes | Directory in which to write artifacts. Parent directories are created as needed. |
| `-h`, `--help` | No | Display help and exit. |
| `--version` | No | Display the package version and exit. The displayed program label is currently `seda-markdown-template`. |

```bash
asyncapi-mate ./asyncapi.yaml --output ./build/documentation
```

The CLI does not accept a URL as `SOURCE`. It has no options for choosing templates, rendering SVG, validating against the AsyncAPI specification, cleaning old files, or forcing payload regeneration.

## Exit behavior

A successful run exits with status `0` and logs `SUCCESS`. Generation errors are logged with diagnostic information and reported as Click errors with a nonzero exit status. Argument validation failures also return a nonzero status.

Generation is not transactional: a failure can leave files written earlier in the run. See [Regenerate documentation](how-to/regenerate.md) for a workflow using a fresh directory.

## Related reference

- [Input document expectations](reference/input.md)
- [Generated paths and overwrite behavior](reference/output.md)
- [Payload diagram support](reference/schema-support.md)
