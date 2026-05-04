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

from . import get_operation_anchor_link, to_puml_name, load_aysncapi
from .__about__ import __version__
from .schema_to_plantuml import schema_to_plantuml_model
from datetime import datetime
from jinja2 import Environment, PackageLoader
from loguru import logger
from pathlib import Path
from typing import Any, List, Mapping

import click
import time


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="seda-markdown-template")
@click.argument(
    "source",
    type=click.Path(path_type=Path, exists=True, readable=True, resolve_path=True),
    required=True,
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    required=True,
    help="Output directory path",
)
def main(source: Path, output: Path):
    """Entry point for the SEDA Markdown template development CLI."""
    start_time = time.time()

    logger.info(
        f"{source.absolute()} processing started at: {datetime.fromtimestamp(start_time).isoformat(timespec='milliseconds')}..."
    )
    try:
        data: Mapping[str, Any] = load_aysncapi(source)

        logger.success(f"{source.absolute()} successfully parsed to a Pydantic model!")

        logger.warning(data)

        jinja_environment = Environment(
            loader=PackageLoader(package_name="seda_markdown_template")
        )

        def _to_mapping(functions: List[Any]):
            mapping: Mapping[str, Any] = {}

            for function in functions:
                name = function.__name__
                mapping[name] = function

            jinja_environment.filters.update(mapping)

        _to_mapping([to_puml_name, get_operation_anchor_link])

        for template_name in [
            "docs/c4/components/EDA/asyncapi.md",
            "docs/diagrams/src/c4/components/EDA/asyncapi.puml",
        ]:
            logger.info(f"Rendering template {template_name}...")
            template = jinja_environment.get_template(template_name)
            target = Path(output, template_name)
            target.parent.mkdir(exist_ok=True, parents=True)

            with target.open("w") as output_stream:
                output_stream.write(
                    template.render(
                        asyncapi=data,
                        version=__version__,
                        generation_time=datetime.fromtimestamp(start_time).isoformat(
                            timespec="milliseconds"
                        ),
                    )
                )

                logger.success(
                    f"Template {template_name} successfully rendered to {target.absolute()}"
                )

        for application_name, application in data["x-applications"].items():
            logger.info(f"Rendering template for application {application_name}...")
            template = jinja_environment.get_template(
                "docs/diagrams/src/c4/components/EDA/application.puml"
            )
            target = Path(
                output, f"docs/diagrams/src/c4/components/EDA/{application_name}.puml"
            )
            target.parent.mkdir(exist_ok=True, parents=True)

            with target.open("w") as output_stream:
                output_stream.write(
                    template.render(
                        application_name=application_name, application=application
                    )
                )

                logger.success(
                    f"Template for application {application_name} successfully rendered to {target.absolute()}"
                )

            for operation in application["operations"]:
                logger.info(
                    f"[{application_name}] Rendering template for operation {operation['action']} {operation['channel']['address']}..."
                )

                target = Path(
                    output,
                    f"docs/diagrams/src/c4/components/EDA/{operation['channel']['messages']['defaultMessage']['name']}.puml",
                )

                if target.exists():
                    logger.info(f"File {target.absolute()} already exist, skipping.")
                    continue

                schema = operation["channel"]["messages"]["defaultMessage"]["payload"]
                schema_model = schema_to_plantuml_model(schema)

                template = jinja_environment.get_template(
                    "docs/diagrams/src/c4/components/EDA/schema_to_plantuml.puml"
                )

                with target.open("w") as output_stream:
                    output_stream.write(template.render(model=schema_model))

                    logger.success(
                        f"[{application_name}] operation {operation['action']} {operation['channel']['address']} successfully rendered to {target.absolute()}!"
                    )

        logger.success(
            "------------------------------------------------------------------------"
        )
        logger.success("SUCCESS")
        logger.success(
            "------------------------------------------------------------------------"
        )
    except Exception as e:
        logger.error(
            "------------------------------------------------------------------------"
        )
        logger.error("FAIL")
        logger.error(e)
        logger.error(
            "------------------------------------------------------------------------"
        )

    end_time = time.time()

    logger.info(f"Total time: {end_time - start_time:.4f} seconds")
    logger.info(
        f"Finished at: {datetime.fromtimestamp(end_time).isoformat(timespec='milliseconds')}"
    )
