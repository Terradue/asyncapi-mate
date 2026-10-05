"""Types for the jsonref entry point used by the document loader."""

from collections.abc import Callable

def replace_refs(
    obj: object,
    base_uri: str = "",
    loader: Callable[[str], object] | None = None,
    jsonschema: bool = False,
    load_on_repr: bool = True,
    merge_props: bool = False,
    proxies: bool = True,
    lazy_load: bool = True,
) -> object: ...
