import pytest

from app.geometry import _finger_intervals, build_parts, layout_parts
from app.parameters import NotesHolderParameters


def test_standard_parameters_create_six_source_parts():
    parts = build_parts(NotesHolderParameters())

    assert len(parts) == 6
    assert {part.name for part in parts} == {
        "bottom",
        "left_side",
        "right_side",
        "back",
        "front_left",
        "front_right",
    }


def test_bottom_dimensions_match_inner_dimensions():
    params = NotesHolderParameters(inner_width=90.0, inner_depth=65.0)
    bottom = next(part for part in build_parts(params) if part.name == "bottom")

    assert bottom.width == pytest.approx(90.0)
    assert bottom.height == pytest.approx(65.0)
    assert bottom.cutouts == []
    assert min(x for x, _ in bottom.outline) < 0
    assert max(x for x, _ in bottom.outline) > bottom.width


def test_bottom_front_edge_has_only_wing_tabs_and_central_opening():
    params = NotesHolderParameters()
    bottom = next(part for part in build_parts(params) if part.name == "bottom")
    wing_width = params.inner_width * (1.0 - params.front_opening_percent / 100.0) / 2.0

    assert (wing_width, params.material_thickness * 3.0) in bottom.outline
    assert (
        params.inner_width - wing_width,
        params.material_thickness * 3.0,
    ) in bottom.outline
    front_tab_corners = [
        (x, y)
        for x, y in bottom.outline
        if y == -params.material_thickness
    ]
    assert len(front_tab_corners) == 4


def test_front_opening_is_split_into_two_equal_wings():
    params = NotesHolderParameters(inner_width=100.0, front_opening_percent=40.0)
    parts = {part.name: part for part in build_parts(params)}

    assert parts["front_left"].width == pytest.approx(30.0)
    assert parts["front_right"].width == pytest.approx(30.0)


def test_default_wall_composition_matches_source_svg():
    params = NotesHolderParameters()
    parts = {part.name: part for part in build_parts(params)}
    expected_height = params.inner_height + params.material_thickness * 4.0

    expected_side_width = params.inner_depth + params.material_thickness * 2.0
    assert parts["left_side"].width == pytest.approx(expected_side_width)
    assert parts["right_side"].width == pytest.approx(expected_side_width)
    assert parts["back"].width == pytest.approx(params.inner_width)
    assert parts["left_side"].height == pytest.approx(expected_height)
    assert len(parts["left_side"].cutouts) == 6
    assert len(parts["right_side"].cutouts) == 6
    assert len(parts["back"].cutouts) == 6
    assert len(parts["front_left"].cutouts) == 1
    assert len(parts["front_right"].cutouts) == 1


def test_side_walls_have_inward_notches_instead_of_teeth():
    params = NotesHolderParameters(material_thickness=4.0)
    parts = {part.name: part for part in build_parts(params)}
    side = parts["left_side"]
    back = parts["back"]
    side_xs = [x for x, _ in side.outline]
    back_xs = [x for x, _ in back.outline]

    assert min(side_xs) == pytest.approx(0.0)
    assert max(side_xs) == pytest.approx(side.width)
    assert params.material_thickness + params.joint_clearance in side_xs
    assert side.width - params.material_thickness - params.joint_clearance in side_xs
    assert min(back_xs) < 0.0
    assert max(back_xs) > back.width


def test_all_outline_corners_are_straight():
    for part in build_parts(NotesHolderParameters()):
        closed = [*part.outline, part.outline[0]]
        for first, second in zip(closed, closed[1:]):
            assert first[0] == pytest.approx(second[0]) or first[1] == pytest.approx(second[1])


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


def test_four_millimeter_slots_match_bottom_tabs():
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

    slots = parts["back"].cutouts
    assert len(slots) == len(intervals)
    for slot, (start, end) in zip(slots, intervals):
        xs = [x for x, _ in slot]
        ys = [y for _, y in slot]
        assert max(xs) - min(xs) == pytest.approx(end - start + 0.1)
        assert max(ys) - min(ys) == pytest.approx(4.1)


@pytest.mark.parametrize("thickness", [3.0, 4.0])
def test_front_wing_slots_align_with_outer_bottom_tabs(thickness):
    params = NotesHolderParameters(
        material_thickness=thickness,
        finger_width=6.0,
        joint_clearance=0.1,
    )
    parts = {part.name: part for part in build_parts(params)}
    wing_width = parts["front_left"].width
    intervals = _finger_intervals(
        wing_width,
        params.finger_width,
        margin=params.material_thickness,
    )
    first_start, first_end = intervals[0]
    last_start, last_end = intervals[-1]

    left_slot = parts["front_left"].cutouts[0]
    left_local_center = (
        min(x for x, _ in left_slot) + max(x for x, _ in left_slot)
    ) / 2.0
    left_assembly_center = left_local_center

    right_slot = parts["front_right"].cutouts[0]
    right_local_center = (
        min(x for x, _ in right_slot) + max(x for x, _ in right_slot)
    ) / 2.0
    right_assembly_center = (
        params.inner_width
        - wing_width
        + right_local_center
    )

    assert left_assembly_center == pytest.approx((first_start + first_end) / 2.0)
    assert right_assembly_center == pytest.approx(
        params.inner_width
        - wing_width
        + (last_start + last_end) / 2.0
    )


def test_layout_parts_do_not_overlap():
    def bounds(part):
        contours = [part.outline, *part.cutouts]
        points = [point for contour in contours for point in contour]
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        return min(xs), min(ys), max(xs), max(ys)

    parts = layout_parts(build_parts(NotesHolderParameters()))
    boxes = [bounds(part) for part in parts]
    for index, first in enumerate(boxes):
        for second in boxes[index + 1:]:
            ax1, ay1, ax2, ay2 = first
            bx1, by1, bx2, by2 = second
            assert not (max(ax1, bx1) < min(ax2, bx2) and max(ay1, by1) < min(ay2, by2))
