from __future__ import annotations

import json

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from laos_v8.errors import DuplicateKeyError, ParseError, ResourceLimitError
from laos_v8.parser import ParseLimits, strict_loads


def test_duplicate_keys_are_rejected_before_overwrite() -> None:
    with pytest.raises(DuplicateKeyError) as captured:
        strict_loads(b'{"role":"builder","role":"signer"}')
    assert captured.value.code == "JSON_DUPLICATE_KEY"


@pytest.mark.parametrize("payload", [b'{"n":NaN}', b'{"n":Infinity}', b'{"n":-Infinity}'])
def test_non_finite_numbers_are_rejected(payload: bytes) -> None:
    with pytest.raises(ParseError) as captured:
        strict_loads(payload)
    assert captured.value.code == "JSON_NON_FINITE_NUMBER"


def test_invalid_utf8_is_rejected() -> None:
    with pytest.raises(ParseError) as captured:
        strict_loads(b'{"x":"\xff"}')
    assert captured.value.code == "JSON_INVALID_UTF8"


def test_byte_depth_string_collection_and_node_limits() -> None:
    with pytest.raises(ResourceLimitError):
        strict_loads(b'"12345"', ParseLimits(max_bytes=4))
    with pytest.raises(ResourceLimitError):
        strict_loads(b"[[[0]]]", ParseLimits(max_depth=2))
    with pytest.raises(ResourceLimitError):
        strict_loads(b'"12345"', ParseLimits(max_string_length=4))
    with pytest.raises(ResourceLimitError):
        strict_loads(b"[1,2,3]", ParseLimits(max_collection_length=2))
    with pytest.raises(ResourceLimitError):
        strict_loads(b'{"a":1,"b":2}', ParseLimits(max_total_nodes=3))


json_scalars = (
    st.none() | st.booleans() | st.integers(min_value=-(2**53) + 1, max_value=2**53 - 1) | st.text(max_size=64)
)
json_values = st.recursive(
    json_scalars,
    lambda children: (
        st.lists(children, max_size=5) | st.dictionaries(st.text(min_size=1, max_size=12), children, max_size=5)
    ),
    max_leaves=20,
)


@given(json_values)
@settings(max_examples=200, deadline=None)
def test_strict_parser_round_trips_bounded_json(value: object) -> None:
    encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    assert strict_loads(encoded) == value
