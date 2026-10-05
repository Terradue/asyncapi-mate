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

"""Load reference-aware AsyncAPI documents and normalize diagram identifiers."""

from collections.abc import Mapping
from http import HTTPStatus
from pathlib import Path
from typing import Any

import yaml
from httpx import Client, Request, RequestNotRead, Response
from jsonref import replace_refs
from loguru import logger

from .__about__ import __version__

__all__ = ["__version__"]


translation = str.maketrans(
    {
        " ": "_",
        "-": "_",
        "/": "_",
        ".": "_",
        ":": "_",
        "{": "",
        "}": "",
        "[": "",
        "]": "",
    }
)


def to_puml_name(identifier: str) -> str:
    """Normalize an identifier for use in PlantUML."""
    return identifier.translate(translation)


def get_operation_anchor_link(operation: Mapping[str, object]) -> str:
    """Return the anchor for a referenced operation, or an empty string."""
    reference = getattr(operation, "__reference__", None)
    if isinstance(reference, Mapping):
        return f"operation-{operation['action']}-{str(reference.get('$ref', '')).split('/')[-1]}"
    return ""


def _decode(value: str | bytes | None) -> str:
    if not value:
        return ""

    if isinstance(value, str):
        return value

    return value.decode("utf-8")


def _log_request(request: Request) -> None:
    """Log an outgoing request with authorization credentials redacted."""
    logger.warning(f"{request.method} {request.url}")
    for name, value in request.headers.items():
        header_value = (
            "********"
            if name.lower() in {"authorization", "proxy-authorization", "cookie"}
            else value
        )
        logger.warning(f"> {name}: {header_value}")
    try:
        if request.content:
            logger.warning(_decode(request.content))
    except RequestNotRead:
        logger.warning("[REQUEST BUILT FROM STREAM, OMITTING]")


def _log_response(response: Response) -> None:
    """Read and log an HTTP response."""
    response.read()
    log = logger.error if response.status_code >= HTTPStatus.MULTIPLE_CHOICES else logger.success
    log(f"< {response.status_code} {response.reason_phrase}")
    for name, value in response.headers.items():
        log(f"< {name}: {'********' if name.lower() == 'set-cookie' else value}")
    if response.content:
        log(_decode(response.content))


def load_aysncapi(source: str | Path) -> Mapping[str, Any]:
    """Load a local file or URL and resolve its JSON references.

    Raises:
        ValueError: If the document root is not a mapping.
        httpx.HTTPStatusError: If a remote request fails.
    """
    if isinstance(source, Path):
        with source.open() as input_stream:
            data = yaml.safe_load(input_stream)
    else:
        with Client(
            event_hooks={"request": [_log_request], "response": [_log_response]}
        ) as http_client:
            response: Response = http_client.get(url=source, timeout=30)

            response.raise_for_status()  # Raise an error for HTTP error codes
            data = yaml.safe_load(response.read())

    if not isinstance(data, dict):
        raise ValueError("The AsyncAPI document root must be a mapping")
    resolved = replace_refs(
        data,
        base_uri=str(source),
        loader=load_aysncapi,
        lazy_load=True,
        load_on_repr=False,
        proxies=True,
        jsonschema=False,
        merge_props=True,
    )
    if not isinstance(resolved, Mapping):
        raise ValueError("The resolved AsyncAPI document root must be a mapping")
    return resolved
