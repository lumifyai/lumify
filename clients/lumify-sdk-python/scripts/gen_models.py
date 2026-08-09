#!/usr/bin/env python3
"""
G2 sync gate (Python arm) — generate ``lumify/models.py`` from the SAME OpenAPI
slice the TypeScript SDK consumes: ``clients/lumify-sdk/openapi/openapi.sdk.json``
(produced by ``scripts/export_openapi_sdk.py`` at the repo root).

There is exactly one schema artifact feeding both codegens, so the Python and
TypeScript SDKs can never disagree with each other or drift from the live API.

Like ``clients/lumify-sdk/scripts/gen-models.mjs``, this is a tiny purpose-built
JSON-Schema-subset translator (zero dependencies), not a general OpenAPI
generator. It only understands the shapes FastAPI/Pydantic emit for this API:
object schemas with ``properties``/``required``, ``$ref``, ``anyOf`` (nullable),
``array`` + ``items``, and scalar types.

Models are emitted as ``TypedDict`` classes (``total=False``): responses are
plain ``dict`` objects at runtime (matching the TS SDK, whose interfaces are
compile-time only), and the TypedDicts give editors/type-checkers field
completion without any runtime validation cost.

Usage:
    python scripts/gen_models.py            # write lumify/models.py
    python scripts/gen_models.py --check    # exit 1 if the file is stale
"""

from __future__ import annotations

import json
import keyword
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_PKG_ROOT = _SCRIPT_DIR.parent
_REPO_ROOT = _PKG_ROOT.parent.parent
# Single source of truth — the artifact the TS SDK also generates from.
SCHEMA_PATH = _REPO_ROOT / "clients" / "lumify-sdk" / "openapi" / "openapi.sdk.json"
OUTPUT_PATH = _PKG_ROOT / "lumify" / "models.py"


def _ref_name(ref: str) -> str:
    return ref.rsplit("/", 1)[-1]


def py_type(node) -> str:
    """Map a JSON Schema fragment to a Python type annotation (as a string)."""
    if not node:
        return "Any"
    if "$ref" in node:
        return _ref_name(node["$ref"])

    if isinstance(node.get("anyOf"), list):
        parts = []
        for sub in node["anyOf"]:
            t = py_type(sub)
            if t not in parts:
                parts.append(t)
        has_none = "None" in parts
        non_none = [p for p in parts if p != "None"]
        if not non_none:
            return "None"
        base = non_none[0] if len(non_none) == 1 else "Union[%s]" % ", ".join(non_none)
        return "Optional[%s]" % base if has_none else base

    node_type = node.get("type")
    if node_type == "integer":
        return "int"
    if node_type == "number":
        return "float"
    if node_type == "string":
        return "str"
    if node_type == "boolean":
        return "bool"
    if node_type == "null":
        return "None"
    if node_type == "array":
        return "List[%s]" % py_type(node.get("items"))
    if node_type == "object":
        # Inline objects (with or without declared properties) are surfaced as
        # open dicts — mirrors the TS gen's `Record<string, unknown>` fallback
        # for the `Record`-typed fields this API uses.
        return "Dict[str, Any]"
    return "Any"


def _docstring(text: str, indent: str) -> list[str]:
    """Render a schema/field description as a Python docstring line(s)."""
    clean = " ".join(text.strip().split())
    # Escape a trailing backslash / embedded triple quotes defensively.
    clean = clean.replace('"""', '\\"\\"\\"')
    return ['%s"""%s"""' % (indent, clean)]


def _is_safe_field_name(key: str) -> bool:
    """Whether `key` can be used as a Python class-attribute name — i.e. the
    class-based TypedDict syntax works for it. Field names like "from" (a
    schema field mirroring a REST query param) are valid JSON Schema property
    names but not valid Python identifiers, so those classes fall back to the
    functional TypedDict syntax below, which accepts arbitrary string keys."""
    return key.isidentifier() and not keyword.iskeyword(key)


def gen_class(name: str, schema: dict) -> str:
    props = schema.get("properties") or {}
    doc = schema.get("description")

    if props and not all(_is_safe_field_name(k) for k in props):
        return _gen_functional_typeddict(name, schema)

    lines = ["class %s(TypedDict, total=False):" % name]

    body_started = False
    if doc:
        lines += _docstring(doc, "    ")
        body_started = True

    if not props:
        if not body_started:
            lines.append("    pass")
        return "\n".join(lines)

    for key, val in props.items():
        field_doc = val.get("description")
        lines.append("    %s: %s" % (key, py_type(val)))
        if field_doc:
            lines += _docstring(field_doc, "    ")
        body_started = True

    return "\n".join(lines)


def _gen_functional_typeddict(name: str, schema: dict) -> str:
    """Functional-syntax TypedDict for schemas with a field name that isn't a
    valid Python identifier (e.g. "from"). This form takes a plain dict of
    string keys to types, so any JSON Schema property name works — at the
    cost of per-field docstrings, which class syntax supports but this doesn't."""
    props = schema.get("properties") or {}
    lines = []
    doc = schema.get("description")
    if doc:
        lines.append("# %s" % " ".join(doc.strip().split()))
    entries = ",\n".join(
        "        %r: %s" % (key, py_type(val)) for key, val in props.items()
    )
    lines.append(
        "%s = TypedDict(\n    %r,\n    {\n%s,\n    },\n    total=False,\n)"
        % (name, name, entries)
    )
    return "\n".join(lines)


def build(schema: dict) -> str:
    schemas = (schema.get("components") or {}).get("schemas") or {}
    names = sorted(schemas.keys())

    header = (
        "# AUTO-GENERATED by scripts/gen_models.py from the shared OpenAPI slice\n"
        "# clients/lumify-sdk/openapi/openapi.sdk.json (produced by\n"
        "# scripts/export_openapi_sdk.py at the repo root). Do not edit by hand —\n"
        "# run `python scripts/gen_models.py` after regenerating the schema.\n"
        "#\n"
        "# This is the SDK's data-model layer (sync gate G2): every TypedDict here\n"
        "# maps 1:1 to a component schema in the live OpenAPI contract — the SAME\n"
        "# artifact the TypeScript SDK generates from — so response shapes can never\n"
        "# silently drift from the API or between the two SDKs.\n"
        "\n"
        "from __future__ import annotations\n"
        "\n"
        "from typing import Any, Dict, List, Optional, Union\n"
        "\n"
        "try:  # TypedDict is in typing on 3.8+, but this keeps intent explicit.\n"
        "    from typing import TypedDict\n"
        "except ImportError:  # pragma: no cover - Python < 3.8 unsupported\n"
        "    from typing_extensions import TypedDict  # type: ignore\n"
    )

    all_names = "__all__ = [\n" + "".join('    "%s",\n' % n for n in names) + "]\n"

    body = "\n\n\n".join(gen_class(n, schemas[n]) for n in names)
    return "%s\n\n%s\n\n%s\n" % (header, all_names, body)


def main() -> int:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    content = build(schema)

    if "--check" in sys.argv:
        try:
            current = OUTPUT_PATH.read_text(encoding="utf-8")
        except FileNotFoundError:
            current = ""
        if current != content:
            print(
                "%s is stale. Run: python scripts/gen_models.py" % OUTPUT_PATH,
                file=sys.stderr,
            )
            return 1
        print("%s is up to date." % OUTPUT_PATH)
        return 0

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(content, encoding="utf-8")
    count = len((schema.get("components") or {}).get("schemas") or {})
    print("Wrote %s (%d models)" % (OUTPUT_PATH, count))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
