# Copyright 2026 Terradue
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Render Markdown documentation and PlantUML diagrams from AsyncAPI files."""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import click
from jinja2 import Environment, PackageLoader, select_autoescape
from loguru import logger

from . import get_operation_anchor_link, load_aysncapi, to_puml_name
from .__about__ import __version__
from .schema_to_plantuml import (
    plantuml_application_channel_definitions,
    plantuml_operation_channel_definitions,
    schema_to_plantuml_model,
)

if TYPE_CHECKING:
    from collections.abc import Mapping


def _render_template(
    environment: Environment, template_name: str, target: Path, **context: object
) -> None:
    """Render a template to disk, creating its parent directories."""
    template = environment.get_template(template_name)
    target.parent.mkdir(exist_ok=True, parents=True)
    target.write_text(template.render(**context), encoding="utf-8")
    logger.success(f"Template {template_name} successfully rendered to {target.absolute()}")


def _render_application(
    environment: Environment, output: Path, name: str, application: Mapping[str, Any]
) -> None:
    """Write application and message diagrams, reusing existing message files."""
    diagram_path = "docs/diagrams/src/c4/components/EDA"
    _render_template(
        environment,
        f"{diagram_path}/application.puml.jinja",
        output / diagram_path / f"{name}.puml",
        application_name=name,
        application=application,
    )
    for operation in application["operations"]:
        message = operation["channel"]["messages"]["defaultMessage"]
        target = output / diagram_path / f"{message['name']}.puml"
        if target.exists():
            logger.info(f"File {target.absolute()} already exists, skipping.")
            continue
        _render_template(
            environment,
            f"{diagram_path}/schema_to_plantuml.puml.jinja",
            target,
            model=schema_to_plantuml_model(message["payload"]),
        )


def _render_document(source: Path, output: Path, start_time: float) -> None:
    """Load a document and write its documentation and application diagrams."""
    data = load_aysncapi(source)
    # Markdown and PlantUML require literal syntax; HTML/XML templates are escaped.
    environment = Environment(
        loader=PackageLoader(package_name="asyncapi_mate"),
        autoescape=select_autoescape(),
    )
    environment.filters.update(
        {
            "to_puml_name": to_puml_name,
            "get_operation_anchor_link": get_operation_anchor_link,
            "plantuml_operation_channel_definitions": plantuml_operation_channel_definitions,
            "plantuml_application_channel_definitions": plantuml_application_channel_definitions,
        }
    )
    for template_name in (
        "docs/c4/components/EDA/asyncapi.md.jinja",
        "docs/diagrams/src/c4/components/EDA/asyncapi.puml.jinja",
    ):
        _render_template(
            environment,
            template_name,
            output / Path(template_name).stem,
            asyncapi=data,
            version=__version__,
            generation_time=datetime.fromtimestamp(start_time).isoformat(timespec="milliseconds"),
        )
    for name, application in data["x-applications"].items():
        _render_application(environment, output, name, application)


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="seda-markdown-template")
@click.argument(
    "source",
    type=click.Path(path_type=Path, exists=True, readable=True, resolve_path=True),
    required=True,
)
@click.option(
    "--output", type=click.Path(path_type=Path), required=True, help="Output directory path"
)
def main(source: Path, output: Path) -> None:
    """Render documentation and diagrams for SOURCE into OUTPUT."""
    start_time = time.time()
    logger.info(f"{source.absolute()} processing started")
    try:
        _render_document(source, output, start_time)
    except Exception as error:
        # The CLI boundary reports failures with diagnostics and a nonzero exit status.
        logger.exception("Documentation generation failed")
        raise click.ClickException(str(error)) from error
    finally:
        logger.info(f"Total time: {time.time() - start_time:.4f} seconds")
    logger.success("SUCCESS")
