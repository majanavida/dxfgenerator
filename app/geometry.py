"""Расчёт упрощённых плоских деталей салфетницы NotesHolder."""

from dataclasses import dataclass, replace
from typing import Iterable

from .parameters import NotesHolderParameters

Point = tuple[float, float]
Contour = list[Point]


@dataclass(frozen=True)
class Part:
    """Одна плоская деталь: внешний контур и внутренние пазы."""

    name: str
    label: str
    width: float
    height: float
    outline: Contour
    cutouts: list[Contour]
    label_point: Point


def _finger_intervals(length: float, finger_width: float) -> list[tuple[float, float]]:
    """Равномерные интервалы шипов вдоль кромки."""

    safe_width = max(abs(finger_width), 0.1)
    count = max(1, int(abs(length) // (safe_width * 2.0)))
    step = abs(length) / count
    actual_width = min(safe_width, step * 0.65)
    return [
        (index * step + (step - actual_width) / 2.0,
         index * step + (step + actual_width) / 2.0)
        for index in range(count)
    ]


def _tabbed_edge(
    start: Point,
    end: Point,
    *,
    normal: Point,
    tab_depth: float,
    finger_width: float,
) -> Contour:
    """Точки осевой кромки с прямоугольными выступающими шипами."""

    x1, y1 = start
    x2, y2 = end
    dx, dy = x2 - x1, y2 - y1
    length = abs(dx) + abs(dy)
    if length == 0:
        return [end]
    ux, uy = dx / length, dy / length
    nx, ny = normal
    points: Contour = []
    for interval_start, interval_end in _finger_intervals(length, finger_width):
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


def _wall_outline(
    width: float,
    height: float,
    thickness: float,
    finger_width: float,
) -> Contour:
    """Прямоугольная стенка с шипами снизу и по бокам."""

    outline: Contour = [(0.0, 0.0)]
    outline.extend(
        _tabbed_edge(
            (0.0, 0.0),
            (width, 0.0),
            normal=(0.0, -1.0),
            tab_depth=thickness,
            finger_width=finger_width,
        )
    )
    outline.extend(
        _tabbed_edge(
            (width, 0.0),
            (width, height),
            normal=(1.0, 0.0),
            tab_depth=thickness,
            finger_width=finger_width,
        )
    )
    outline.append((0.0, height))
    outline.extend(
        _tabbed_edge(
            (0.0, height),
            (0.0, 0.0),
            normal=(-1.0, 0.0),
            tab_depth=thickness,
            finger_width=finger_width,
        )
    )
    return outline


def _bottom_slots(params: NotesHolderParameters) -> list[Contour]:
    """Пазы дна под нижние шипы четырёх стенок."""

    slot_width = max(0.1, abs(params.finger_width) + params.joint_clearance)
    slot_depth = max(0.1, abs(params.material_thickness) + params.joint_clearance)
    edge_offset = max(abs(params.material_thickness), 0.5)
    slots: list[Contour] = []

    for start, end in _finger_intervals(params.inner_width, params.finger_width):
        center = (start + end) / 2.0
        x = center - slot_width / 2.0
        slots.append(_rectangle(x, edge_offset, slot_width, slot_depth))
        slots.append(
            _rectangle(
                x,
                params.inner_depth - edge_offset - slot_depth,
                slot_width,
                slot_depth,
            )
        )

    for start, end in _finger_intervals(params.inner_depth, params.finger_width):
        center = (start + end) / 2.0
        y = center - slot_width / 2.0
        slots.append(_rectangle(edge_offset, y, slot_depth, slot_width))
        slots.append(
            _rectangle(
                params.inner_width - edge_offset - slot_depth,
                y,
                slot_depth,
                slot_width,
            )
        )
    return slots


def _side_slots(
    depth: float,
    front_height: float,
    back_height: float,
    params: NotesHolderParameters,
) -> list[Contour]:
    """Вертикальные пазы боковины под шипы передней и задней стенок."""

    slot_width = max(0.1, abs(params.material_thickness) + params.joint_clearance)
    slot_height = max(0.1, abs(params.finger_width) + params.joint_clearance)
    edge_offset = max(abs(params.material_thickness), 0.5)
    slots: list[Contour] = []

    for start, end in _finger_intervals(back_height, params.finger_width):
        center = (start + end) / 2.0
        slots.append(
            _rectangle(edge_offset, center - slot_height / 2.0, slot_width, slot_height)
        )
    for start, end in _finger_intervals(front_height, params.finger_width):
        center = (start + end) / 2.0
        slots.append(
            _rectangle(
                depth - edge_offset - slot_width,
                center - slot_height / 2.0,
                slot_width,
                slot_height,
            )
        )
    return slots


def _side_outline(
    depth: float,
    front_height: float,
    back_height: float,
    thickness: float,
    finger_width: float,
) -> Contour:
    """Боковина с наклонной верхней кромкой и нижними шипами."""

    outline: Contour = [(0.0, 0.0)]
    outline.extend(
        _tabbed_edge(
            (0.0, 0.0),
            (depth, 0.0),
            normal=(0.0, -1.0),
            tab_depth=thickness,
            finger_width=finger_width,
        )
    )
    outline.extend([(depth, front_height), (0.0, back_height), (0.0, 0.0)])
    return outline


def build_parts(params: NotesHolderParameters) -> list[Part]:
    """Построить пять деталей в локальных координатах."""

    width = params.inner_width
    depth = params.inner_depth
    back_height = params.inner_height
    front_height = params.front_height
    thickness = params.material_thickness

    bottom = Part(
        name="bottom",
        label="Дно",
        width=width,
        height=depth,
        outline=_rectangle(0.0, 0.0, width, depth),
        cutouts=_bottom_slots(params),
        label_point=(width / 2.0, depth / 2.0),
    )
    front = Part(
        name="front",
        label="Передняя стенка",
        width=width,
        height=front_height,
        outline=_wall_outline(width, front_height, thickness, params.finger_width),
        cutouts=[],
        label_point=(width / 2.0, front_height / 2.0),
    )
    back = Part(
        name="back",
        label="Задняя стенка",
        width=width,
        height=back_height,
        outline=_wall_outline(width, back_height, thickness, params.finger_width),
        cutouts=[],
        label_point=(width / 2.0, back_height / 2.0),
    )
    side_outline = _side_outline(
        depth,
        front_height,
        back_height,
        thickness,
        params.finger_width,
    )
    side_slots = _side_slots(depth, front_height, back_height, params)
    left = Part(
        name="left_side",
        label="Левая боковина",
        width=depth,
        height=back_height,
        outline=side_outline,
        cutouts=side_slots,
        label_point=(depth / 2.0, min(front_height, back_height) / 2.0),
    )
    right = Part(
        name="right_side",
        label="Правая боковина",
        width=depth,
        height=back_height,
        outline=[(depth - x, y) for x, y in side_outline],
        cutouts=[[(depth - x, y) for x, y in contour] for contour in side_slots],
        label_point=(depth / 2.0, min(front_height, back_height) / 2.0),
    )
    return [bottom, front, back, left, right]


def _translate_contour(contour: Iterable[Point], dx: float, dy: float) -> Contour:
    return [(x + dx, y + dy) for x, y in contour]


def translate_part(part: Part, dx: float, dy: float) -> Part:
    """Перенести деталь на раскладке."""

    return replace(
        part,
        outline=_translate_contour(part.outline, dx, dy),
        cutouts=[_translate_contour(contour, dx, dy) for contour in part.cutouts],
        label_point=(part.label_point[0] + dx, part.label_point[1] + dy),
    )


def layout_parts(parts: list[Part], spacing: float = 10.0) -> list[Part]:
    """Разложить детали рядом, примерно как в исходном SVG."""

    by_name = {part.name: part for part in parts}
    bottom = by_name["bottom"]
    front = by_name["front"]
    back = by_name["back"]
    left = by_name["left_side"]
    right = by_name["right_side"]
    margin = spacing

    return [
        translate_part(bottom, margin, margin),
        translate_part(back, margin, margin + bottom.height + spacing),
        translate_part(
            front,
            margin,
            margin + bottom.height + spacing + back.height + spacing,
        ),
        translate_part(left, margin + bottom.width + spacing, margin),
        translate_part(
            right,
            margin + bottom.width + spacing,
            margin + left.height + spacing,
        ),
    ]
