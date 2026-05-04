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

from .__about__ import __version__

from functools import wraps
from http import HTTPStatus
from httpx import Client, Headers, Request, RequestNotRead, Response
from jsonref import replace_refs
from loguru import logger
from pathlib import Path
from typing import Any, Dict, Mapping, MutableMapping

import yaml
import re

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
    return identifier.translate(translation)


def get_operation_anchor_link(operation: Dict[str, Any]) -> str:
    if operation.__reference__:  # type: ignore
        return f"operation-{operation['action']}-{str(operation.__reference__.get('$ref', '')).split('/')[-1]}"  # type: ignore
    return ""


def _decode(value):
    if not value:
        return ""

    if isinstance(value, str):
        return value

    return value.decode("utf-8")


def _log_request(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        request: Request = func(*args, **kwargs)

        logger.warning(f"{request.method} {request.url}")

        headers: Headers = request.headers
        for name, value in headers.raw:
            header_value = re.sub(
                r"(\bBearer\s+)[^\s]+",
                r"\1********",
                _decode(value),
                flags=re.IGNORECASE,
            )
            logger.warning(f"> {_decode(name)}: {header_value}")

        logger.warning(">")
        try:
            if request.content:
                logger.warning(_decode(request.content))
        except RequestNotRead:
            logger.warning("[REQUEST BUILT FROM STREAM, OMISSING]")

        return request

    return wrapper


def _log_response(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        response: Response = func(*args, **kwargs)

        if HTTPStatus.MULTIPLE_CHOICES._value_ <= response.status_code:
            log = logger.error
        else:
            log = logger.success

        status: HTTPStatus = HTTPStatus(response.status_code)
        log(f"< {status._value_} {status.phrase}")

        headers: Mapping[str, str] = response.headers
        for name, value in headers.items():
            log(f"< {_decode(name)}: {_decode(value)}")

        log("")

        if response.content:
            log(_decode(response.content))

        return response

    return wrapper


def load_aysncapi(source: str | Path) -> Mapping[str, Any]:
    if isinstance(source, Path):
        with source.open() as input_stream:
            data: MutableMapping[str, Any] = yaml.safe_load(input_stream)
    else:
        with Client() as http_client:
            http_client.build_request = _log_request(http_client.build_request)  # type: ignore
            http_client.request = _log_response(http_client.request)  # type: ignore
            response: Response = http_client.get(url=source, timeout=30)

            response.raise_for_status()  # Raise an error for HTTP error codes
            data: MutableMapping[str, Any] = yaml.safe_load(response.read())

    return replace_refs(
        data,
        base_uri=str(source),
        loader=load_aysncapi,
        lazy_load=True,
        load_on_repr=False,
        proxies=True,
        jsonschema=False,
        merge_props=True,
    )  # type: ignore
