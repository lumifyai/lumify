"""
G6 sync gate (Python SDK arm) — the Python SDK must build exactly the REST
request declared in the shared cross-surface probe matrix. Consumes the SAME
fixture the TypeScript SDK and the REST<->MCP parity test use
(tests/fixtures/agent_contract.json), so the Python SDK can't silently drift
from the REST contract that REST, MCP, and the TS SDK all agree on.

Asserts request *construction* (method + path + query), not live data — the SDK
can't reach the in-process API here, so data/credit parity is owned by the
Python REST<->MCP test. Together they close the loop across all three surfaces.
"""

import json
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

from lumify import Lumify
from lumify._transport import PreparedRequest, RawResponse

_FIXTURE = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "agent_contract.json"
_PROBES = [p for p in json.loads(_FIXTURE.read_text())["probes"] if p.get("sdk")]

_CAMEL_RE = re.compile(r"(?<!^)(?=[A-Z])")


def _camel_to_snake(name: str) -> str:
    return _CAMEL_RE.sub("_", name).lower()


class _Spy:
    def __init__(self, canned):
        self._canned = canned
        self.calls = []

    def __call__(self, req: PreparedRequest, timeout: float) -> RawResponse:
        self.calls.append(req)
        body = self._canned.get("body", {})
        return RawResponse(
            status=self._canned.get("status", 200),
            headers=self._canned.get("headers", {}),
            text=json.dumps(body),
        )


def _invoke(client, sdk):
    resource = getattr(client, sdk["resource"], None)
    assert resource is not None, "SDK has no resource '%s'" % sdk["resource"]
    # The shared fixture's method names follow the TS SDK's camelCase
    # (e.g. "batchGet"); the Python SDK is snake_case ("batch_get").
    method_name = _camel_to_snake(sdk["method"])
    method = getattr(resource, method_name, None)
    assert callable(method), "SDK %s.%s is not a method" % (sdk["resource"], method_name)

    args, kwargs = [], {}
    for arg in sdk.get("args", []):
        if isinstance(arg, dict):
            for key, value in arg.items():
                kwargs[_camel_to_snake(key)] = value
        else:
            args.append(arg)
    return method(*args, **kwargs)


@pytest.mark.parametrize("probe", _PROBES, ids=[p["name"] for p in _PROBES])
def test_python_sdk_builds_declared_rest_request(probe):
    is_error = probe["kind"] == "error"
    if is_error:
        canned = {
            "status": probe["assert"]["rest_status"],
            "body": {"error": {"code": probe["assert"]["error_code"], "status": probe["assert"]["rest_status"]}},
        }
    else:
        canned = {"status": 200, "body": {}}

    spy = _Spy(canned)
    client = Lumify(api_key="lmfy-test", transport=spy, max_retries=0)

    try:
        _invoke(client, probe["sdk"])
    except Exception:
        # Error probes raise (NotFoundError etc.) — the request is still
        # recorded by the spy before the raise, which is all we assert here.
        if not is_error:
            raise

    assert len(spy.calls) == 1, "%s: expected exactly one request" % probe["name"]
    req = spy.calls[0]
    parsed = urlparse(req.url)

    assert req.method == probe["rest"]["method"], "%s: HTTP method" % probe["name"]
    assert parsed.path == probe["rest"]["path"], "%s: path" % probe["name"]

    actual_query = {k: v[0] for k, v in parse_qs(parsed.query).items()}
    assert actual_query == probe["rest"].get("query", {}), (
        "%s: query params must match the REST contract exactly" % probe["name"]
    )

    if "body" in probe["rest"]:
        actual_body = json.loads(req.body) if req.body else None
        assert actual_body == probe["rest"]["body"], (
            "%s: request body must match the REST contract exactly" % probe["name"]
        )
