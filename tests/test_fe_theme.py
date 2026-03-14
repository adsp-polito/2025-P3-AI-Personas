"""Frontend theme helper checks."""

from adsp.fe.app import _hex_to_rgba


def test_hex_to_rgba_supports_short_and_long_hex() -> None:
    assert _hex_to_rgba("#7CC6FF", 0.18) == "rgba(124, 198, 255, 0.18)"
    assert _hex_to_rgba("#abc", 0.5) == "rgba(170, 187, 204, 0.5)"


def test_hex_to_rgba_falls_back_for_invalid_values() -> None:
    assert _hex_to_rgba("not-a-color", 0.2) == "rgba(128, 128, 128, 0.2)"
