from pathlib import Path

import pytest
from click.testing import CliRunner

from asyncapi_mate import get_operation_anchor_link, load_aysncapi
from asyncapi_mate.cli import main


def test_loader_preserves_reference_anchor(tmp_path: Path) -> None:
    source = tmp_path / "api.yaml"
    source.write_text(
        'operations:\n  publish:\n    action: send\nselected:\n  $ref: "#/operations/publish"\n',
        encoding="utf-8",
    )
    document = load_aysncapi(source)
    assert document["selected"]["action"] == "send"
    assert get_operation_anchor_link(document["selected"]) == "operation-send-publish"
    assert get_operation_anchor_link({"action": "send"}) == ""


def test_loader_rejects_non_mapping_document(tmp_path: Path) -> None:
    source = tmp_path / "invalid.yaml"
    source.write_text("- item\n", encoding="utf-8")
    with pytest.raises(ValueError, match="root must be a mapping"):
        load_aysncapi(source)


def test_cli_reports_failure_with_nonzero_exit(tmp_path: Path) -> None:
    source = tmp_path / "invalid.yaml"
    source.write_text("[]", encoding="utf-8")
    result = CliRunner().invoke(main, [str(source), "--output", str(tmp_path / "out")])
    assert result.exit_code == 1
    assert "root must be a mapping" in result.output


def test_cli_renders_all_renamed_templates(tmp_path: Path) -> None:
    source = tmp_path / "api.yaml"
    source.write_text(
        """asyncapi: 3.0.0
info:
  title: Orders & Events
  version: 1.0.0
  contact: {name: Team, email: team@example.org}
  license: {name: Apache, url: 'https://example.org/license'}
servers: {}
x-applications:
  writer:
    operations:
      - action: send
        channel:
          address: orders
          messages:
            defaultMessage:
              name: Order
              examples: []
              payload:
                title: Order
                type: object
                properties:
                  id: {type: string}
""",
        encoding="utf-8",
    )
    output = tmp_path / "output"
    result = CliRunner().invoke(main, [str(source), "--output", str(output)])
    assert result.exit_code == 0, result.output
    assert "Orders & Events" in (output / "asyncapi.md").read_text(encoding="utf-8")
    assert (output / "asyncapi.puml").is_file()
    diagrams = output / "docs/diagrams/src/c4/components/EDA"
    assert "writer -D-> orders" in (diagrams / "writer.puml").read_text(encoding="utf-8")
    assert "#id: string" in (diagrams / "Order.puml").read_text(encoding="utf-8")
