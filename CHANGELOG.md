# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Automated formatting, linting, strict type checking, security checks, and CLI
  regression tests.
- A worked orders example, tutorial, how-to guides, and input, output, and schema
  references in the documentation.

### Changed

- Reorganized the documentation following Diátaxis and updated the site theme.
- Moved the generated overview files, `asyncapi.md` and `asyncapi.puml`, to the
  output directory root; application and message diagrams remain under
  `docs/diagrams/src/c4/components/EDA/`.
- Renamed bundled templates with a `.jinja` suffix while preserving generated
  file extensions.
- Raised the Hatchling build requirement to `>=1.32.4` and included tests,
  documentation, and typing stubs in source distributions.
- Changed the Click dependency pin from `8.3.3` to `8.3.2`.

### Fixed

- Return a nonzero CLI exit status with diagnostic information when documentation
  generation fails.
- Reject AsyncAPI documents whose root is not a mapping.
- Handle operation anchors for operations without reference metadata.

### Security

- Redact authorization, proxy authorization, and cookie request headers, and
  `Set-Cookie` response headers from HTTP logs.

## [0.4.0] - 2026-05-27

### Fixed

- Prevent duplicate channel and message-example declarations from breaking
  PlantUML rendering when operations or applications share a topic.
- Normalize message-example identifiers for use in PlantUML diagrams.

## [0.3.0] - 2026-05-04

### Fixed

- Load bundled Jinja2 templates from the correct `asyncapi_mate` package so
  documentation generation can find its templates.

## [0.2.0] - 2026-05-04

### Changed

- Updated Click from `8.3.2` to `8.3.3`.

### Fixed

- Corrected the installed command name from `asyncapi_mate` to `asyncapi-mate`.

## [0.1.0] - 2026-05-04

### Added

- Initial Python package and command-line interface for generating Markdown
  documentation and PlantUML diagrams from AsyncAPI documents.
- AsyncAPI YAML loading with local and remote reference resolution.
- Templates for event-driven architecture overviews, application diagrams, and
  message payload schema diagrams, using the `x-applications` extension.
- JSON Schema conversion to PlantUML diagram models.
- Hatch-based development tooling, tests, and a MkDocs documentation site.

[Unreleased]: https://github.com/Terradue/asyncapi-mate/compare/v0.4.0...develop
[0.4.0]: https://github.com/Terradue/asyncapi-mate/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/Terradue/asyncapi-mate/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/Terradue/asyncapi-mate/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Terradue/asyncapi-mate/releases/tag/v0.1.0
