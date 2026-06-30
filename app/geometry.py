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
    intervals: list[tuple[float, float]] = []
    for index in range(count):
        center = margin + step * (index + 0.5)
        intervals.append(
            (center - actual_width / 2.0, center + actual_width / 2.0)
        )
    return intervals


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


def _notched_bottom_edge(
    length: float,
    thickness: float,
    finger_width: float,
    clearance: float,
) -> Contour:
    notch_height = max(0.1, thickness + clearance)
    points: Contour = []
    for start, end in _finger_intervals(
        length,
        finger_width,
        margin=thickness,
    ):
        notch_start = start - clearance / 2.0
        notch_end = end + clearance / 2.0
        points.extend(
            [
                (notch_start, 0.0),
                (notch_start, notch_height),
                (notch_end, notch_height),
                (notch_end, 0.0),
            ]
        )
    points.append((length, 0.0))
    return points


def _bottom_outline(
    width: float,
    depth: float,
    thickness: float,
    finger_width: float,
) -> Contour:
    outline: Contour = [(0.0, 0.0)]
    outline.extend(
        _tabbed_edge(
            (0.0, 0.0),
            (width, 0.0),
            normal=(0.0, -1.0),
            tab_depth=thickness,
            finger_width=finger_width,
            margin=thickness,
        )
    )
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


def _wall_outline(
    width: float,
    height: float,
    thickness: float,
    finger_width: float,
    vertical_margin: float,
    clearance: float,
    *,
    top_profile: Contour | None = None,
) -> Contour:
    outline: Contour = [(0.0, 0.0)]
    outline.extend(
        _notched_bottom_edge(
            width,
            thickness,
            finger_width,
            clearance,
        )
    )
    outline.extend(
        _tabbed_edge(
            (width, 0.0),
            (width, height),
            normal=(1.0, 0.0),
            tab_depth=thickness,
            finger_width=finger_width,
            margin=vertical_margin,
        )
    )
    if top_profile is None:
        outline.append((0.0, height))
    else:
        outline.extend(top_profile[1:])
    outline.extend(
        _tabbed_edge(
            (0.0, height),
            (0.0, 0.0),
            normal=(-1.0, 0.0),
            tab_depth=thickness,
            finger_width=finger_width,
            margin=vertical_margin,
        )
    )
    return outline


def _side_outline(
    depth: float,
    height: float,
    thickness: float,
    finger_width: float,
    clearance: float,
) -> Contour:
    scoop = min(thickness * 2.0, height * 0.2)
    outline: Contour = [(0.0, 0.0)]
    outline.extend(
        _notched_bottom_edge(
            depth,
            thickness,
            finger_width,
            clearance,
        )
    )
    outline.extend([
        (depth, 0.0),
        (depth, height),
        (depth * 0.78, height),
        (depth * 0.68, height - scoop),
        (depth * 0.32, height - scoop),
        (depth * 0.22, height),
        (0.0, height),
    ])
    return outline


def _side_slots(
    depth: float,
    height: float,
    params: NotesHolderParameters,
    vertical_margin: float,
) -> list[Contour]:
    thickness = max(abs(params.material_thickness), 0.1)
    clearance = params.joint_clearance
    slot_depth = max(0.1, thickness + clearance)
    slots: list[Contour] = []

    for start, end in _finger_intervals(
        height,
        params.finger_width,
        margin=vertical_margin,
    ):
        slot_height = max(0.1, end - start + clearance)
        y = start - clearance / 2.0
        slots.append(_rectangle(thickness, y, slot_depth, slot_height))
        slots.append(
            _rectangle(
                depth - thickness - slot_depth,
                y,
                slot_depth,
                slot_height,
            )
        )
    return slots


def build_parts(params: NotesHolderParameters) -> list[Part]:
    width = params.inner_width
    depth = params.inner_depth
    height = params.inner_height
    thickness = max(abs(params.material_thickness), 0.1)
    clearance = max(params.joint_clearance, 0.0)
    vertical_margin = thickness * 2.0 + clearance

    bottom = Part(
        name="bottom",
        width=width,
        height=depth,
        outline=_bottom_outline(width, depth, thickness, params.finger_width),
        cutouts=[],
    )

    opening_fraction = min(max(params.front_opening_percent / 100.0, 0.0), 0.9)
    opening_width = width * opening_fraction
    wing_width = (width - opening_width) / 2.0
    bridge_height = min(
        height - thickness,
        max(thickness * 3.0, height * 0.25),
    )
    front_top = [
        (width, height),
        (width - wing_width, height),
        (width - wing_width, bridge_height),
        (wing_width, bridge_height),
        (wing_width, height),
        (0.0, height),
    ]
    front = Part(
        name="front",
        width=width,
        height=height,
        outline=_wall_outline(
            width,
            height,
            thickness,
            params.finger_width,
            vertical_margin,
            params.joint_clearance,
            top_profile=front_top,
        ),
        cutouts=[],
    )
    back = Part(
        name="back",
        width=width,
        height=height,
        outline=_wall_outline(
            width,
            height,
            thickness,
            params.finger_width,
            vertical_margin,
            params.joint_clearance,
        ),
        cutouts=[],
    )

    side_outline = _side_outline(
        depth,
        height,
        thickness,
        params.finger_width,
        params.joint_clearance,
    )
    side_cutouts = _side_slots(depth, height, params, vertical_margin)
    left = Part(
        name="left_side",
        width=depth,
        height=height,
        outline=side_outline,
        cutouts=side_cutouts,
    )
    right = Part(
        name="right_side",
        width=depth,
        height=height,
        outline=list(side_outline),
        cutouts=[list(contour) for contour in side_cutouts],
    )
    return [bottom, front, back, left, right]


def _translate_contour(contour: Iterable[Point], dx: float, dy: float) -> Contour:
    return [(x + dx, y + dy) for x, y in contour]


def translate_part(part: Part, dx: float, dy: float) -> Part:
    return replace(
        part,
        outline=_translate_contour(part.outline, dx, dy),
        cutouts=[_translate_contour(contour, dx, dy) for contour in part.cutouts],
    )


def layout_parts(parts: list[Part], spacing: float = 10.0) -> list[Part]:
    by_name = {part.name: part for part in parts}
    bottom = by_name["bottom"]
    front = by_name["front"]
    back = by_name["back"]
    left = by_name["left_side"]
    right = by_name["right_side"]

    tab_depth = max(
        abs(min(x for x, _ in bottom.outline)),
        abs(min(y for _, y in bottom.outline)),
    )
    margin = spacing + tab_depth
    first_wall_y = margin + bottom.height + tab_depth + spacing
    second_wall_y = first_wall_y + max(left.height, back.height) + spacing
    second_column_x = margin + max(bottom.width, left.width) + tab_depth + spacing

    return [
        translate_part(bottom, margin, margin),
        translate_part(left, margin, first_wall_y),
        translate_part(right, margin, second_wall_y),
        translate_part(back, second_column_x, first_wall_y),
        translate_part(front, second_column_x, second_wall_y),
    ]
