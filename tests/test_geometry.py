import pytest

from app.geometry import build_parts
from app.parameters import NotesHolderParameters


def test_standard_parameters_create_five_parts():
    parts = build_parts(NotesHolderParameters())

    assert len(parts) == 5
    assert {part.name for part in parts} == {
        "bottom",
        "front",
        "back",
        "left_side",
        "right_side",
    }


def test_bottom_dimensions_match_inner_dimensions():
    params = NotesHolderParameters(inner_width=90.0, inner_depth=65.0)
    bottom = next(part for part in build_parts(params) if part.name == "bottom")

    assert bottom.width == pytest.approx(90.0)
    assert bottom.height == pytest.approx(65.0)
    assert bottom.cutouts


def test_front_wall_is_lower_than_back_wall():
    params = NotesHolderParameters(inner_height=40.0, front_opening_percent=35.0)
    parts = {part.name: part for part in build_parts(params)}

    assert parts["front"].height == pytest.approx(26.0)
    assert parts["front"].height < parts["back"].height
