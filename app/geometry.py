from dataclasses import dataclass, replace
from typing import Iterable

from .parameters import NotesHolderParameters

Point = tuple[float, float]
Contour = list[Point]


@dataclass(frozen=True)
class Part:
    name: str
    width: float
    height: float
    outline: Contour
    cutouts: list[Contour]


def _finger_intervals(
    length: float,
    finger_width: float,
    *,
    margin: float = 0.0,
) -> list[tuple[float, float]]:
    length = abs(length)
    finger_width = max(abs(finger_width), 0.1)
    margin = min(max(margin, 0.0), length / 2.0)
    usable_length = length - margin * 2.0
    if usable_length <= 0.0:
        return []

    count = max(1, round(usable_length / (finger_width * 2.0)))
    step = usable_length / count
    actual_width = min(finger_width, step * 0.65)
    return [
        (
            margin + step * (index + 0.5) - actual_width / 2.0,
            margin + step * (index + 0.5) + actual_width / 2.0,
        )
        for index in range(count)
    ]


def _tabbed_edge(
    start: Point,
    end: Point,
    *,
    normal: Point,
    tab_depth: float,
    finger_width: float,
    margin: float,
) -> Contour:
    x1, y1 = start
    x2, y2 = end
    dx, dy = x2 - x1, y2 - y1
    length = abs(dx) + abs(dy)
    if length == 0.0:
        return [end]

    ux, uy = dx / length, dy / length
    nx, ny = normal
    points: Contour = []
    for interval_start, interval_end in _finger_intervals(
        length,
        finger_width,
        margin=margin,
    ):
        ax, ay = x1 + ux * interval_start, y1 + uy * interval_start
        bx, by = x1 + ux * interval_end, y1 + uy * interval_end
        points.extend(
            [
                (ax, ay),
                (ax + nx * tab_depth, ay + ny * tab_depth),
                (bx + nx * tab_depth, by + ny * tab_depth),
                (bx, by),
            ]
        )
    points.append(end)
    return points


def _rectangle(x: float, y: float, width: float, height: float) -> Contour:
    return [
        (x, y),
        (x + width, y),
        (x + width, y + height),
        (x, y + height),
    ]


def _bottom_outline(
    width: float,
    depth: float,
    thickness: float,
    finger_width: float,
    opening_fraction: float,
) -> Contour:
    outline: Contour = [(0.0, 0.0)]
    opening_width = width * opening_fraction
    wing_width = (width - opening_width) / 2.0
    wing_intervals = _finger_intervals(
        wing_width,
        finger_width,
        margin=thickness,
    )
    for start, end in wing_intervals:
        outline.extend(
            [
                (start, 0.0),
                (start, -thickness),
                (end, -thickness),
                (end, 0.0),
            ]
        )
    outline.extend(
        [
            (wing_width, 0.0),
            (wing_width, thickness * 3.0),
            (width - wing_width, thickness * 3.0),
            (width - wing_width, 0.0),
        ]
    )
    for start, end in wing_intervals:
        shifted_start = width - wing_width + start
        shifted_end = width - wing_width + end
        outline.extend(
            [
                (shifted_start, 0.0),
                (shifted_start, -thickness),
                (shifted_end, -thickness),
                (shifted_end, 0.0),
            ]
        )
    outline.append((width, 0.0))
    outline.extend(
        _tabbed_edge(
            (width, 0.0),
            (width, depth),
            normal=(1.0, 0.0),
            tab_depth=thickness,
            finger_width=finger_width,
            margin=thickness,
        )
    )
    outline.extend(
        _tabbed_edge(
            (width, depth),
            (0.0, depth),
            normal=(0.0, 1.0),
            tab_depth=thickness,
            finger_width=finger_width,
            margin=thickness,
        )
    )
    outline.extend(
        _tabbed_edge(
            (0.0, depth),
            (0.0, 0.0),
            normal=(-1.0, 0.0),
            tab_depth=thickness,
            finger_width=finger_width,
            margin=thickness,
        )
    )
    return outline


def _wall_slots(
    length: float,
    thickness: float,
    finger_width: float,
    clearance: float,
    *,
    connection_length: float | None = None,
    offset: float = 0.0,
) -> list[Contour]:
    slot_height = max(0.1, thickness + clearance)
    slot_y = thickness * 3.0
    fitted_length = length if connection_length is None else connection_length
    slots: list[Contour] = []
    for start, end in _finger_intervals(
        fitted_length,
        finger_width,
        margin=thickness,
    ):
        slots.append(
            _rectangle(
                offset + start - clearance / 2.0,
                slot_y,
                max(0.1, end - start + clearance),
                slot_height,
            )
        )
    return slots


def _notched_edge(
    start: Point,
    end: Point,
    *,
    normal: Point,
    notch_depth: float,
    finger_width: float,
    clearance: float,
    margin: float,
) -> Contour:
    x1, y1 = start
    x2, y2 = end
    dx, dy = x2 - x1, y2 - y1
    length = abs(dx) + abs(dy)
    ux, uy = dx / length, dy / length
    nx, ny = normal
    points: Contour = []
    for interval_start, interval_end in _finger_intervals(
        length,
        finger_width,
        margin=margin,
    ):
        notch_start = interval_start - clearance / 2.0
        notch_end = interval_end + clearance / 2.0
        ax, ay = x1 + ux * notch_start, y1 + uy * notch_start
        bx, by = x1 + ux * notch_end, y1 + uy * notch_end
        points.extend(
            [
                (ax, ay),
                (ax + nx * notch_depth, ay + ny * notch_depth),
                (bx + nx * notch_depth, by + ny * notch_depth),
                (bx, by),
            ]
        )
    points.append(end)
    return points


def _full_wall_outline(
    length: float,
    height: float,
    thickness: float,
    finger_width: float,
) -> Contour:
    foot_height = thickness * 2.0
    foot_width = min(finger_width * 2.0, length / 3.0)
    edge_margin = thickness * 2.0
    outline: Contour = [(0.0, height), (length, height)]
    outline.extend(
        _tabbed_edge(
            (length, height),
            (length, 0.0),
            normal=(1.0, 0.0),
            tab_depth=thickness,
            finger_width=finger_width,
            margin=edge_margin,
        )
    )
    outline.extend(
        [
            (length - foot_width, 0.0),
            (length - foot_width, foot_height),
            (foot_width, foot_height),
            (foot_width, 0.0),
            (0.0, 0.0),
        ]
    )
    outline.extend(
        _tabbed_edge(
            (0.0, 0.0),
            (0.0, height),
            normal=(-1.0, 0.0),
            tab_depth=thickness,
            finger_width=finger_width,
            margin=edge_margin,
        )
    )
    return outline


def _side_wall_outline(
    depth: float,
    height: float,
    thickness: float,
    finger_width: float,
    clearance: float,
) -> Contour:
    outer_depth = depth + thickness * 2.0
    foot_height = thickness * 2.0
    foot_width = min(finger_width * 2.0, outer_depth / 3.0)
    edge_margin = thickness * 2.0
    notch_depth = thickness + clearance
    outline: Contour = [(0.0, height), (outer_depth, height)]
    outline.extend(
        _notched_edge(
            (outer_depth, height),
            (outer_depth, 0.0),
            normal=(-1.0, 0.0),
            notch_depth=notch_depth,
            finger_width=finger_width,
            clearance=clearance,
            margin=edge_margin,
        )
    )
    outline.extend(
        [
            (outer_depth - foot_width, 0.0),
            (outer_depth - foot_width, foot_height),
            (foot_width, foot_height),
            (foot_width, 0.0),
            (0.0, 0.0),
        ]
    )
    outline.extend(
        _notched_edge(
            (0.0, 0.0),
            (0.0, height),
            normal=(1.0, 0.0),
            notch_depth=notch_depth,
            finger_width=finger_width,
            clearance=clearance,
            margin=edge_margin,
        )
    )
    return outline


def _front_wing_outline(
    width: float,
    height: float,
    thickness: float,
    finger_width: float,
) -> Contour:
    foot_height = thickness * 2.0
    foot_width = min(finger_width * 2.0, width)
    edge_margin = thickness * 2.0
    outline: Contour = [
        (0.0, height),
        (width, height),
        (width, foot_height),
        (foot_width, foot_height),
        (foot_width, 0.0),
        (0.0, 0.0),
    ]
    outline.extend(
        _tabbed_edge(
            (0.0, 0.0),
            (0.0, height),
            normal=(-1.0, 0.0),
            tab_depth=thickness,
            finger_width=finger_width,
            margin=edge_margin,
        )
    )
    return outline


def _front_wing_slots(
    wing_width: float,
    thickness: float,
    finger_width: float,
    clearance: float,
) -> list[Contour]:
    intervals = _finger_intervals(
        wing_width,
        finger_width,
        margin=thickness,
    )
    return [
        _rectangle(
            start - clearance / 2.0,
            thickness * 3.0,
            end - start + clearance,
            thickness + clearance,
        )
        for start, end in intervals
    ]


def _mirror_contour(contour: Contour, width: float) -> Contour:
    return [(width - x, y) for x, y in contour]


def build_parts(params: NotesHolderParameters) -> list[Part]:
    width = params.inner_width
    depth = params.inner_depth
    height = params.inner_height
    thickness = max(abs(params.material_thickness), 0.1)
    clearance = max(params.joint_clearance, 0.0)
    panel_height = height + thickness * 4.0
    opening_fraction = min(max(params.front_opening_percent / 100.0, 0.0), 0.9)
    wing_width = width * (1.0 - opening_fraction) / 2.0

    bottom = Part(
        name="bottom",
        width=width,
        height=depth,
        outline=_bottom_outline(
            width,
            depth,
            thickness,
            params.finger_width,
            opening_fraction,
        ),
        cutouts=[],
    )

    side_width = depth + thickness * 2.0
    left_side = Part(
        name="left_side",
        width=side_width,
        height=panel_height,
        outline=_side_wall_outline(
            depth,
            panel_height,
            thickness,
            params.finger_width,
            clearance,
        ),
        cutouts=_wall_slots(
            side_width,
            thickness,
            params.finger_width,
            clearance,
            connection_length=depth,
            offset=thickness,
        ),
    )
    right_side = replace(left_side, name="right_side")
    back = Part(
        name="back",
        width=width,
        height=panel_height,
        outline=_full_wall_outline(
            width,
            panel_height,
            thickness,
            params.finger_width,
        ),
        cutouts=_wall_slots(
            width,
            thickness,
            params.finger_width,
            clearance,
        ),
    )

    left_wing_outline = _front_wing_outline(
        wing_width,
        panel_height,
        thickness,
        params.finger_width,
    )
    left_wing_slots = _front_wing_slots(
        wing_width,
        thickness,
        params.finger_width,
        clearance,
    )
    front_left = Part(
        name="front_left",
        width=wing_width,
        height=panel_height,
        outline=left_wing_outline,
        cutouts=left_wing_slots,
    )
    front_right = Part(
        name="front_right",
        width=wing_width,
        height=panel_height,
        outline=_mirror_contour(left_wing_outline, wing_width),
        cutouts=[
            _mirror_contour(contour, wing_width)
            for contour in left_wing_slots
        ],
    )
    return [bottom, left_side, back, right_side, front_left, front_right]


def _translate_contour(contour: Iterable[Point], dx: float, dy: float) -> Contour:
    return [(x + dx, y + dy) for x, y in contour]


def translate_part(part: Part, dx: float, dy: float) -> Part:
    return replace(
        part,
        outline=_translate_contour(part.outline, dx, dy),
        cutouts=[_translate_contour(contour, dx, dy) for contour in part.cutouts],
    )


def layout_parts(parts: list[Part], spacing: float = 1.5) -> list[Part]:
    by_name = {part.name: part for part in parts}
    bottom = by_name["bottom"]
    left_side = by_name["left_side"]
    back = by_name["back"]
    right_side = by_name["right_side"]
    front_left = by_name["front_left"]
    front_right = by_name["front_right"]

    tab_depth = abs(min(x for x, _ in bottom.outline))
    margin = 10.0
    side_x = margin
    bottom_x = margin + tab_depth
    right_x = margin + left_side.width + spacing + tab_depth
    lower_y = margin
    upper_y = lower_y + max(right_side.height, front_left.height) + spacing
    bottom_y = upper_y + max(left_side.height, back.height) + spacing + tab_depth

    return [
        translate_part(bottom, bottom_x, bottom_y),
        translate_part(left_side, side_x, upper_y),
        translate_part(back, right_x, upper_y),
        translate_part(right_side, side_x, lower_y),
        translate_part(front_left, right_x, lower_y),
        translate_part(front_right, right_x + front_left.width + spacing, lower_y),
    ]
