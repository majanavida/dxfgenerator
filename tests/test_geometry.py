import pytest

from app.geometry import _finger_intervals, build_parts
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
    assert bottom.cutouts == []
    assert min(x for x, _ in bottom.outline) < 0
    assert max(x for x, _ in bottom.outline) > bottom.width


def test_front_wall_has_a_lower_central_opening():
    params = NotesHolderParameters(inner_height=40.0, front_opening_percent=35.0)
    parts = {part.name: part for part in build_parts(params)}

    front = parts["front"]
    central_points = [
        y
        for x, y in front.outline
        if params.inner_width * 0.3 < x < params.inner_width * 0.7
    ]
    assert min(central_points) < parts["back"].height


def test_cutouts_do_not_overlap_each_other():
    def bounds(contour):
        xs = [point[0] for point in contour]
        ys = [point[1] for point in contour]
        return min(xs), min(ys), max(xs), max(ys)

    def overlaps(first, second):
        ax1, ay1, ax2, ay2 = bounds(first)
        bx1, by1, bx2, by2 = bounds(second)
        return max(ax1, bx1) < min(ax2, bx2) and max(ay1, by1) < min(ay2, by2)

    for part in build_parts(NotesHolderParameters()):
        for index, first in enumerate(part.cutouts):
            for second in part.cutouts[index + 1:]:
                assert not overlaps(first, second), part.name


def test_four_millimeter_bottom_tabs_match_open_wall_notches():
    params = NotesHolderParameters(
        material_thickness=4.0,
        finger_width=6.0,
        joint_clearance=0.1,
    )
    parts = {part.name: part for part in build_parts(params)}
    intervals = _finger_intervals(
        params.inner_width,
        params.finger_width,
        margin=params.material_thickness,
    )

    front_points = set(parts["front"].outline)
    assert parts["front"].cutouts == []
    for start, end in intervals:
        assert (start - 0.05, 4.1) in front_points
        assert (end + 0.05, 4.1) in front_points
